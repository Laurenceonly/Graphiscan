import test from 'node:test'
import assert from 'node:assert/strict'
import { createHostedClient } from './hosted-client.mjs'
import { createTabSessionStore } from './tab-session.mjs'
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
  assert.deepEqual(Object.keys(client),['login','logout','clear','request','restore'])
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

const tabStorage=()=>{
  const values=new Map()
  return {values,getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}
}
test('an opted-in tab restores through server refresh and saves only the rotated refresh token',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage),calls=[]
  const fetchImpl=async(url,options)=>{
    calls.push([url,options])
    return response(url.endsWith('/login')?tokens():url.endsWith('/refresh')?tokens('two'):{role:'admin'})
  }
  await createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl}).login('private@example.invalid','private-password')
  assert.deepEqual([...storage.values.values()],['refresh-one'])
  const reloaded=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl})
  assert.equal(await reloaded.restore(),true)
  assert.deepEqual(JSON.parse(calls[1][1].body),{refresh_token:'refresh-one'})
  assert.equal(calls[1][1].headers.Authorization,undefined)
  await reloaded.request('/me')
  assert.equal(calls[2][1].headers.Authorization,'Bearer access-two')
  assert.deepEqual([...storage.values.values()],['refresh-two'])
})
test('client construction does not restore or contact the server on the login page',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage)
  store.write('refresh-one');let calls=0
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async()=>{calls++;return response(tokens())}})
  await assert.rejects(client.request('/me'),/Sign in/)
  assert.equal(calls,0)
  assert.deepEqual([...storage.values.values()],['refresh-one'])
})
test('empty storage stays signed out without a provider request',async()=>{
  const store=createTabSessionStore('https://synthetic.invalid',tabStorage())
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async()=>assert.fail('unexpected fetch')})
  assert.equal(await client.restore(),false)
})
test('a restore outage retains the tab session and can be retried',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage)
  store.write('refresh-one');let offline=true
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async()=>{
    if(offline)throw Error('offline');return response(tokens('two'))
  }})
  await assert.rejects(client.restore(),/Unable to reach/)
  assert.deepEqual([...storage.values.values()],['refresh-one'])
  offline=false;assert.equal(await client.restore(),true)
  assert.deepEqual([...storage.values.values()],['refresh-two'])
})
test('server failure retains the saved token, revoked refresh removes it',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage)
  store.write('refresh-one');let status=503
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async()=>response(null,status)})
  await assert.rejects(client.restore());assert.equal(storage.values.size,1)
  status=401;await assert.rejects(client.restore());assert.equal(storage.values.size,0)
  assert.equal(await client.restore(),false)
})
test('sign-out removes a saved session even if the network is unavailable',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage)
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async(url)=>{
    if(url.endsWith('/login'))return response(tokens());throw Error('offline')
  }})
  await client.login('x@y','synthetic');await assert.rejects(client.logout())
  assert.equal(storage.values.size,0)
  assert.equal(await createHostedClient('https://synthetic.invalid',{sessionStore:store}).restore(),false)
})
test('a late restore cannot save credentials after sign-out',async()=>{
  const storage=tabStorage(),store=createTabSessionStore('https://synthetic.invalid',storage)
  store.write('refresh-one');let finish
  const client=createHostedClient('https://synthetic.invalid',{sessionStore:store,fetchImpl:async(url)=>{
    if(url.endsWith('/refresh'))return new Promise(resolve=>{finish=()=>resolve(response(tokens('late')))})
    return response({})
  }})
  const pending=client.restore();await client.logout();finish()
  await assert.rejects(pending,/cancelled/);assert.equal(storage.values.size,0)
})
test('tab stores isolate API origins, reject corrupt values and tolerate unavailable storage',async()=>{
  const storage=tabStorage(),one=createTabSessionStore('https://one.invalid',storage),two=createTabSessionStore('https://two.invalid',storage)
  one.write('refresh-one');assert.equal(two.read(),null);assert.equal(one.read(),'refresh-one')
  one.write('x'.repeat(16385));assert.equal(one.read(),null);assert.equal(storage.values.size,0)
  const denied=createTabSessionStore('https://one.invalid',{getItem(){throw Error()},setItem(){throw Error()},removeItem(){throw Error()}})
  denied.write('synthetic');assert.equal(denied.read(),null);denied.remove()
})
