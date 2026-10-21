import test from 'node:test'
import assert from 'node:assert/strict'
import { createStudentSubmission } from './directory-submission.mjs'

test('an uncertain creation retains the exact key/payload until a successful retry',async()=>{
  const submission=createStudentSubmission(()=> 'synthetic-key-0001'), calls=[]
  const draft={full_name:'Fictional Child',age:8}
  const client={request:async(path,options)=>{calls.push([path,options]);if(calls.length===1)throw Object.assign(new Error('Network'),{status:0});return {data:{student_id:'1'}}}}
  await assert.rejects(submission.submit(client,draft))
  assert.equal(submission.pending,true);draft.age=9
  assert.deepEqual(await submission.submit(client,draft),{data:{student_id:'1'}})
  assert.equal(submission.pending,false)
  assert.equal(calls[0][1].idempotencyKey,calls[1][1].idempotencyKey)
  assert.equal(calls[1][1].body.age,8)
})
test('definitive validation failure allows a corrected payload and new key',async()=>{
  let sequence=0
  const submission=createStudentSubmission(()=> 'synthetic-'+(++sequence)),calls=[]
  const client={request:async(path,options)=>{calls.push(options);if(calls.length===1)throw Object.assign(new Error('Invalid'),{status:422});return {data:{}}}}
  await assert.rejects(submission.submit(client,{age:0}))
  assert.equal(submission.pending,false)
  await submission.submit(client,{age:8})
  assert.notEqual(calls[0].idempotencyKey,calls[1].idempotencyKey)
  assert.equal(calls[1].body.age,8)
})
test('server failures and conflicts never discard creation recovery details',async()=>{
  for(const status of [401,403,409,500,503]){
    const submission=createStudentSubmission(()=> 'synthetic-fixed')
    await assert.rejects(submission.submit({request:async()=>{throw Object.assign(new Error('Failed'),{status})}},{age:8}))
    assert.equal(submission.pending,true)
  }
})
