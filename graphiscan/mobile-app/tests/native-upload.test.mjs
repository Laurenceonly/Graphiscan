import test from 'node:test'
import assert from 'node:assert/strict'
import {createNativeUploadFetch} from '../src/core/native-upload.ts'
import {createHostedClient} from '../../shared/hosted-client.mjs'

const url='https://fictional.invalid/api/v1/screenings'
const form={getParts:()=>[{fieldName:'student_id',string:'9007199254740993'},{fieldName:'model_id',string:'3'},{fieldName:'handwriting_image',uri:'file:///fictional/sample.png',type:'image/png'}]}
const result={status:201,headers:{'Content-Type':'application/json'},body:JSON.stringify({data:{result_id:'9'}})}
test('Android multipart uses the local file and retains exact IDs, bearer and retry key',async()=>{
  let sent
  const transport=createNativeUploadFetch(async()=>{throw Error('URI body must not use fetch')},(target,uri,options)=>{sent={target,uri,options};return {uploadAsync:async()=>result,cancelAsync:async()=>{}}},1)
  const response=await transport(url,{method:'POST',body:form,headers:{Authorization:'Bearer fictional','Idempotency-Key':'fictional-key','Content-Type':'multipart/form-data'}})
  assert.equal(response.status,201);assert.deepEqual(await response.json(),{data:{result_id:'9'}})
  assert.deepEqual(sent,{target:url,uri:'file:///fictional/sample.png',options:{httpMethod:'POST',uploadType:1,fieldName:'handwriting_image',mimeType:'image/png',parameters:{student_id:'9007199254740993',model_id:'3'},headers:{authorization:'Bearer fictional','idempotency-key':'fictional-key'}}})
})
test('ordinary reads, JSON writes and web multipart continue through fetch',async()=>{
  const calls=[]
  const transport=createNativeUploadFetch(async(...args)=>{calls.push(args);return new Response('{}')},()=>{throw Error('Unexpected native upload')},1)
  for(const [target,options] of [[url,{}],[url,{method:'POST',body:'{}'}],[url,{method:'POST',body:new FormData()}]])await transport(target,options)
  assert.equal(calls.length,3)
})
test('abort promptly cancels an in-flight upload; a pre-aborted request never sends',async()=>{
  const controller=new AbortController();let cancelled=0,started=0
  const transport=createNativeUploadFetch(fetch,()=>{started++;return {uploadAsync:()=>new Promise(()=>{}),cancelAsync:async()=>{cancelled++}}},1)
  const pending=transport(url,{method:'POST',body:form,signal:controller.signal});controller.abort()
  await assert.rejects(pending,/cancelled/);assert.equal(cancelled,1)
  await assert.rejects(transport(url,{method:'POST',body:form,signal:controller.signal}),/cancelled/);assert.equal(started,1)
})
test('HTTP errors stay readable and upload transport failures do not replay writes',async()=>{
  let attempts=0
  const transport=createNativeUploadFetch(async()=>new Response(JSON.stringify({data:{access_token:'fictional',refresh_token:'fictional',expires_in:3600}})),()=>({uploadAsync:async()=>{attempts++;if(attempts===1)throw Error('fictional connection failure');return {...result,status:503,body:JSON.stringify({error:{code:'SCREENING_RECOVERY_REQUIRED',message:'Check submission status.'}})}},cancelAsync:async()=>{}}),1)
  const client=createHostedClient('https://fictional.invalid',{fetchImpl:transport});await client.login('fictional@example.invalid','fictional')
  const options={method:'POST',form,idempotencyKey:'fictional-same-key'}
  await assert.rejects(client.request('/screenings',options),e=>e.code==='NETWORK_ERROR');assert.equal(attempts,1)
  await assert.rejects(client.request('/screenings',options),e=>e.status===503&&e.code==='SCREENING_RECOVERY_REQUIRED');assert.equal(attempts,2)
})
