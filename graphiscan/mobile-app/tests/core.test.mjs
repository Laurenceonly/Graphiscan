import test from 'node:test'
import assert from 'node:assert/strict'
import { createUserApi } from '../src/core/api.ts'
import { legacyPercent, screeningType } from '../src/core/presentation.ts'
import { hostedPercent } from '../src/core/hosted-presentation.ts'
const reply = data => new Response(JSON.stringify({ success: true, ...data }), { headers: { 'Content-Type': 'application/json' } })
const user = { user_id: 1, role: 'teacher', fullname: 'Fictional Teacher' }
test('hosted fraction scores stay distinct from legacy percent units', () => {
  assert.equal(hostedPercent(.4), '40.00%'); assert.equal(legacyPercent(.4), '0.40%')
  assert.equal(hostedPercent(null), 'Not recorded'); assert.equal(hostedPercent(40), 'Not recorded')
})
test('screening type uses only the recorded supported label, never visible list order', () => {
  assert.equal(screeningType('Follow-up Screening'), 'Follow-up Screening')
  assert.equal(screeningType('Initial Screening'), 'Initial Screening')
  for (const value of [null, undefined, '', 'Initial', 'unreviewed value']) assert.equal(screeningType(value), 'Screening type not recorded')
})

test('legacy percentages preserve their recorded units and reject invalid values', () => {
  assert.equal(legacyPercent(.5), '0.50%'); assert.equal(legacyPercent(75), '75.00%')
  for (const value of [null, undefined, '', -1, 101, 'bad']) assert.equal(legacyPercent(value), 'Not recorded')
})
test('authenticated calls use bearer headers without cookies; logout clears the local bearer', async () => {
  const calls = [], api = createUserApi('https://api.example.test', { fetchImpl: async (url, init) => { calls.push({ url, ...init }); return url.endsWith('/login') ? reply({ token: 'fictional-token', user }) : reply({ students: [] }) } })
  await api.login(' TEST@example.test ', 'fictional-password'); await api.students(); await api.logout(); await api.students()
  assert.equal(calls[1].headers.Authorization, 'Bearer fictional-token')
  assert.equal(calls[1].credentials, 'omit'); assert.equal(calls[3].headers.Authorization, undefined)
  assert.equal(JSON.parse(calls[0].body).email, 'test@example.test')
})
test('unsupported guest sign-in is rejected and its server session revoked', async () => {
  let revoked = false
  const api = createUserApi('https://api.example.test', { fetchImpl: async url => url.endsWith('/login') ? reply({ token: 'fictional-token', user: { ...user, role: 'guest' } }) : (revoked = true, reply({})) })
  await assert.rejects(api.login('test@example.test', 'fictional-password'), /issued teacher/); assert.equal(revoked, true)
})
test('a late sign-in cannot revive a signed-out session and is revoked', async () => {
  let complete, revoked = false
  const api = createUserApi('https://api.example.test', { fetchImpl: url => url.endsWith('/login') ? new Promise(resolve => { complete = resolve }) : (revoked = true, Promise.resolve(reply({}))) })
  const pending = api.login('test@example.test', 'fictional-password'); await api.logout()
  complete(reply({ token: 'fictional-token', user })); await assert.rejects(pending, /cancelled/); assert.equal(revoked, true)
})
test('parents receive only reviewed results as an additional client check', async () => {
  const api = createUserApi('https://api.example.test', { fetchImpl: async () => reply({ results: [{ result_id: 1, validation_status: 'Pending' }, { result_id: 2, validation_status: 'Validated' }] }) })
  assert.deepEqual((await api.results('parent')).map(row => row.result_id), [2])
})
test('failed writes are sent once and do not replay automatically', async () => {
  let calls = 0
  const api = createUserApi('https://api.example.test', { fetchImpl: async () => { calls++; throw new Error('disconnected') } })
  await assert.rejects(api.request('/teacher/upload', { method: 'POST', form: new FormData() }), /Unable to reach/); assert.equal(calls, 1)
})
test('a response arriving after sign-out is not returned to a record screen', async () => {
  let complete
  const api = createUserApi('https://api.example.test', { fetchImpl: url => url.endsWith('/login') ? Promise.resolve(reply({ token: 'fictional-token', user })) : url.endsWith('/logout') ? Promise.resolve(reply({})) : new Promise(resolve => { complete = resolve }) })
  await api.login('test@example.test', 'fictional-password'); const pending = api.students(); await api.logout()
  complete(reply({ students: [] })); await assert.rejects(pending, /ended session/)
})
test('expired sessions clear the bearer and notify the session provider', async () => {
  let expired = 0, lastHeaders
  const api = createUserApi('https://api.example.test', { onExpired: () => expired++, fetchImpl: async (url, init) => {
    lastHeaders = init.headers
    return url.endsWith('/login') ? reply({ token: 'fictional-token', user }) : new Response(JSON.stringify({ success: false, message: 'Sign in again.' }), { status: 401 })
  } })
  await api.login('test@example.test', 'fictional-password'); await assert.rejects(api.students(), /Sign in/)
  assert.equal(expired, 1); await assert.rejects(api.students()); assert.equal(lastHeaders.Authorization, undefined)
})
test('credential-bearing origins and unexpected image content are rejected', async () => {
  assert.throws(() => createUserApi('https://user:secret@example.test'), /public API origin/)
  assert.throws(() => createUserApi('https://example.test/private'), /public API origin/)
  const api = createUserApi('https://api.example.test', { fetchImpl: async () => new Response('<html></html>', { headers: { 'Content-Type': 'text/html' } }) })
  await assert.rejects(api.image('1'), /image response was invalid/)
})
