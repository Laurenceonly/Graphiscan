import test from 'node:test'
import assert from 'node:assert/strict'
import { createMobileSessionStore } from '../src/core/mobile-session-store.ts'
import { createHostedClient } from '../../shared/hosted-client.mjs'

const token = suffix => ({access_token:'access-'+suffix,refresh_token:'refresh-'+suffix,expires_in:3600})
const response = (data,status=200) => ({ok:status<400,status,json:async()=>status<400?{data}:{error:{code:'AUTHENTICATION_REQUIRED',message:'Session ended'}}})
function storage() { const values=new Map();return {values,getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)} }

test('mobile reload revalidates and rotates only the saved refresh token',async()=>{
  const disk=storage(),origin='https://fictional.invalid',store=createMobileSessionStore(origin,disk),calls=[]
  const fetchImpl=async(url,options)=>{calls.push({url,options});return response(url.endsWith('/login')?token('first'):url.endsWith('/refresh')?token('next'):{role:'teacher'})}
  const first=createHostedClient(origin,{sessionStore:store,fetchImpl})
  await first.login('fictional@example.invalid','Fictional1!')
  assert.deepEqual([...disk.values.values()],['refresh-first'])
  const next=createHostedClient(origin,{sessionStore:createMobileSessionStore(origin,disk),fetchImpl})
  assert.equal(await next.restore(),true)
  assert.deepEqual(JSON.parse(calls[1].options.body),{refresh_token:'refresh-first'})
  assert.deepEqual(await next.request('/me'),{role:'teacher'})
  assert.deepEqual([...disk.values.values()],['refresh-next'])
  assert.ok([...disk.values.keys()].every(key=>/^[A-Za-z0-9._-]+$/.test(key)))
  await next.logout();assert.equal(createMobileSessionStore(origin,disk).read(),null)
  assert.equal(await createHostedClient(origin,{sessionStore:store,fetchImpl}).restore(),false)
})

test('mobile store isolates origins, rejects malformed values and tolerates unavailable storage',()=>{
  const disk=storage(),one=createMobileSessionStore('https://one.invalid',disk),two=createMobileSessionStore('https://two.invalid',disk)
  one.write('fictional-refresh');assert.equal(two.read(),null);assert.equal(one.read(),'fictional-refresh')
  one.write('x'.repeat(16385));assert.equal(one.read(),null)
  const blocked=createMobileSessionStore('https://blocked.invalid',{getItem(){throw Error('unavailable')},setItem(){throw Error('unavailable')}})
  assert.equal(blocked.read(),null);assert.doesNotThrow(()=>blocked.write('fictional'));assert.doesNotThrow(()=>blocked.remove())
})
