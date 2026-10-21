import test from 'node:test'
import assert from 'node:assert/strict'
import {createReviewSubmission} from './screening-submission.mjs'
test('uncertain review retry retains result, revision, body and key',async()=>{
  const calls=[];let attempt=0
  const client={request:async(path,options)=>{calls.push({path,options});if(attempt++===0)throw Object.assign(new Error('uncertain'),{status:503});return {status:'Validated'}}}
  const submission=createReviewSubmission(()=> 'fictional-review-key-0001')
  const body={status:'Validated',remarks:'Fictional',expected_revision:4}
  await assert.rejects(submission.submit(client,'1',body));body.remarks='Changed after failure'
  assert.equal(submission.pending,true)
  await submission.submit(client,'2',{status:'Flagged',expected_revision:100})
  assert.deepEqual(calls[0],calls[1]);assert.equal(submission.pending,false)
})
test('revision conflict retains the original review until explicit discard',async()=>{
  const submission=createReviewSubmission(()=> 'fictional-review-key-0001')
  await assert.rejects(submission.submit({request:async()=>{throw Object.assign(new Error('stale'),{status:409})}},'1',{}))
  assert.equal(submission.pending,true);submission.discard();assert.equal(submission.pending,false)
})
