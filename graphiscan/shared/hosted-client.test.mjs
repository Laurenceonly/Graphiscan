import test from 'node:test'
import assert from 'node:assert/strict'
import { createHostedClient } from './hosted-client.mjs'
const tokens=(suffix='one')=>({access_token:'access-'+suffix,refresh_token:'refresh-'+suffix,token_type:'bearer',expires_in:3600})
const response=(data,status=200,code='DENIED')=>({ok:status<400,status,json:async()=>status<400?{data}:{error:{code,message:'Fixed failure'}}})

test('multipart screening uploads retain the key and leave the boundary to fetch',async()=>{
  const calls=[],form=new FormData();form.append('student_id','1')
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url,options)=>{calls.push(options);return response(url.endsWith('/login')?tokens():{result_id:'1'})}})
  await client.login('fixture@example.invalid','synthetic')
  await client.request('/screenings',{method:'POST',form,idempotencyKey:'fictional-upload-key-0001'})
  assert.equal(calls[1].body,form);assert.equal(calls[1].headers['Content-Type'],undefined)
  assert.equal(calls[1].headers['Idempotency-Key'],'fictional-upload-key-0001')
})
test('authenticated image reads accept binary data and reject HTML',async()=>{
  let type='image/png'
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url)=>url.endsWith('/login')?response(tokens()):new Response('fictional',{headers:{'Content-Type':type}})})
  await client.login('fixture@example.invalid','synthetic')
  assert.equal((await client.request('/screenings/1/image',{image:true})).type,'image/png')
  type='text/html';await assert.rejects(client.request('/screenings/1/image',{image:true}),/image response was invalid/)
})

test('a late hosted record read cannot return data after logout',async()=>{
  let complete
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url)=>{
    if(url.endsWith('/login'))return response(tokens())
    if(url.endsWith('/logout'))return response({})
    return new Promise(resolve=>{complete=resolve})
  }})
  await client.login('fixture@example.invalid','synthetic')
  const pending=client.request('/screenings');await client.logout()
  complete(response([{result_id:'1'}]));await assert.rejects(pending,/session has ended/)
})
test('hosted credentials cannot be sent to configured userinfo or a path escape',async()=>{
  assert.throws(()=>createHostedClient('https://user:private@synthetic.invalid'),/public API origin/)
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async()=>response(tokens())})
  await client.login('fixture@example.invalid','synthetic')
  for(const path of ['//elsewhere','/../other','/a\\b'])await assert.rejects(client.request(path),/Invalid request path/)
})

test('list envelopes and retry keys survive the client boundary without extra write replay',async()=>{
  const calls=[]
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url,options)=>{
    calls.push(options)
    if(url.endsWith('/login'))return response(tokens())
    return {ok:true,status:201,json:async()=>({data:[{student_id:'1'}],page:{next_cursor:'next'},warnings:['duplicate_name']})}
  }})
  await client.login('x@y','synthetic')
  const result=await client.request('/students',{method:'POST',body:{age:8},envelope:true,idempotencyKey:'synthetic-key-0001'})
  assert.equal(result.page.next_cursor,'next')
  assert.deepEqual(result.warnings,['duplicate_name'])
  assert.equal(calls[1].headers['Idempotency-Key'],'synthetic-key-0001')
  assert.equal(calls[1].headers.Authorization,'Bearer access-one')
  assert.equal(calls.length,2)
})

test('login tokens are used only in bearer requests and never exposed by client API',async()=>{
  const calls=[]
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url,options)=>{
    calls.push([url,options]);return response(url.endsWith('/login')?tokens():{role:'teacher'})
  }})
  assert.equal(await client.login('fixture@example.invalid','synthetic'),undefined)
  assert.deepEqual(await client.request('/me'),{role:'teacher'})
  assert.equal(calls[1][1].headers.Authorization,'Bearer access-one')
  assert.equal(calls[1][1].credentials,'omit')
  assert.deepEqual(Object.keys(client),['login','logout','clear','request'])
})

test('a recoverable read 401 refreshes once and retries with the rotated bearer',async()=>{
  let reads=0,refreshes=0
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url,options)=>{
    if(url.endsWith('/login'))return response(tokens())
    if(url.endsWith('/refresh')){refreshes++;return response(tokens('two'))}
    reads++;if(reads===1)return response(null,401)
    assert.equal(options.headers.Authorization,'Bearer access-two');return response({ready:true})
  }})
  await client.login('x@y','synthetic');assert.deepEqual(await client.request('/me'),{ready:true})
  assert.equal(reads,2);assert.equal(refreshes,1)
})

test('mutating requests are not replayed after a 401',async()=>{
  const calls=[]
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url)=>{
    calls.push(url);return url.endsWith('/login')?response(tokens()):response(null,401)
  }})
  await client.login('x@y','synthetic')
  await assert.rejects(client.request('/me/password',{method:'POST',body:{new_password:'synthetic'}}))
  assert.equal(calls.length,2)
  await assert.rejects(client.request('/me'),/Sign in/)
})

test('logout clears local state even on a network failure',async()=>{
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url)=>{
    if(url.endsWith('/login'))return response(tokens());throw new Error('private network detail')
  }})
  await client.login('x@y','synthetic');await assert.rejects(client.logout(),/Unable to reach/)
  await assert.rejects(client.request('/me'),/Sign in/)
})

test('concurrent expiring reads share one refresh',async()=>{
  let time=0,refreshes=0
  const client=createHostedClient('https://synthetic.invalid',{now:()=>time,fetchImpl:async(url)=>{
    if(url.endsWith('/login'))return response(tokens())
    if(url.endsWith('/refresh')){refreshes++;await Promise.resolve();return response(tokens('two'))}
    return response({ok:true})
  }})
  await client.login('x@y','synthetic');time=3590000
  await Promise.all([client.request('/me'),client.request('/privacy-agreement')])
  assert.equal(refreshes,1)
})

test('a late login cannot resurrect state after logout',async()=>{
  let deliver,cleaned=false
  const client=createHostedClient('https://synthetic.invalid',{fetchImpl:async(url)=>{
    if(url.endsWith('/login'))return await new Promise(resolve=>{deliver=()=>resolve(response(tokens()))})
    if(url.endsWith('/logout')){cleaned=true;return response({success:true})}
    return response({ok:true})
  }})
  const pending=client.login('x@y','synthetic');await client.logout();deliver()
  await assert.rejects(pending,/cancelled/);assert.equal(cleaned,true)
  await assert.rejects(client.request('/me'),/Sign in/)
})

test('a late refresh cannot resurrect state after logout',async()=>{
  let deliver,time=0
  const revoked=[]
  const client=createHostedClient('https://synthetic.invalid',{now:()=>time,fetchImpl:async(url,options)=>{
    if(url.endsWith('/login'))return response(tokens())
    if(url.endsWith('/refresh'))return await new Promise(resolve=>{deliver=()=>resolve(response(tokens('two')))})
    if(url.endsWith('/logout')){revoked.push(options.headers.Authorization);return response({success:true})}
    return response({ok:true})
  }})
  await client.login('x@y','synthetic');time=3590000
  const pending=client.request('/me');await client.logout();deliver()
  await assert.rejects(pending,/cancelled/)
  assert.deepEqual(revoked,['Bearer access-one','Bearer access-two'])
})
