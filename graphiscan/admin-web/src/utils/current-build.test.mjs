import test from 'node:test'
import assert from 'node:assert/strict'
import { hasNewAdminBuild } from './current-build.mjs'

const currentScript = 'https://admin.example/assets/index-old.js'
const parseScript = html => html
const check = (fetchPage, script = currentScript) => hasNewAdminBuild({ fetchPage, currentScript: script, parseScript })

test('detects a newer deployed script before signing in', async () => {
  assert.equal(await check(async () => ({ ok: true, text: async () => '/assets/index-new.js' })), true)
  assert.equal(await check(async () => ({ ok: true, text: async () => '/assets/index-old.js' })), false)
})

test('failed or unrecognizable update checks do not prevent sign-in', async () => {
  assert.equal(await check(async () => { throw Error('offline') }), false)
  assert.equal(await check(async () => ({ ok: false })), false)
  assert.equal(await check(async () => ({ ok: true, text: async () => '' })), false)
  assert.equal(await check(async () => { throw Error('unexpected fetch') }, ''), false)
})
