// Hosted bearer/refresh credentials live only in this closure, never web storage.
export function createHostedClient(origin, { fetchImpl = globalThis.fetch, now = Date.now } = {}) {
  const trusted = new URL(origin)
  if (!['http:','https:'].includes(trusted.protocol) || trusted.username || trusted.password || trusted.pathname !== '/' || trusted.search || trusted.hash) throw new Error('Configure a public API origin.')
  const base = trusted.origin + '/api/v1'
  let session = null, generation = 0, refreshing = null
  const failure = (message, code, status) => Object.assign(new Error(message), { code, status })
  function clear() { session = null; generation += 1 }
  async function raw(path, { method = 'GET', body, form, image = false, timeout = 15000, token, envelope = false, idempotencyKey } = {}) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), Math.min(Math.max(timeout,1000),120000))
    try {
      const response = await fetchImpl(base + path, {
        method, credentials: 'omit', cache: 'no-store', signal: controller.signal,
        headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}) },
        ...(form ? {body:form} : body ? { body: JSON.stringify(body) } : {})
      })
      if(response.ok && image){
        const type=(response.headers.get('Content-Type')||'').split(';')[0]
        if(!['image/png','image/jpeg'].includes(type))throw failure('The image response was invalid.','INVALID_IMAGE',502)
        return await response.blob()
      }
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw failure(payload.error?.message || 'The request could not be completed. Please try again.', payload.error?.code, response.status)
      return envelope ? payload : payload.data
    } catch (error) {
      if (error.status) throw error
      throw failure('Unable to reach the server. Check your connection and try again.', 'NETWORK_ERROR', 0)
    } finally { clearTimeout(timer) }
  }
  async function retain(data, expectedGeneration) {
    if (generation !== expectedGeneration) {
      // A late login/refresh must not resurrect a signed-out browser session.
      if (data?.access_token) await raw('/session/logout', { method: 'POST', token: data.access_token }).catch(() => {})
      throw failure('This sign-in was cancelled. Sign in again.', 'SESSION_CANCELLED', 401)
    }
    if (!data?.access_token || !data.refresh_token || !Number.isInteger(data.expires_in)) {
      clear(); throw failure('The session response was incomplete. Sign in again.', 'INVALID_SESSION', 401)
    }
    session = { access: data.access_token, refresh: data.refresh_token, expires: now() + data.expires_in * 1000 }
  }
  async function login(email, password) {
    clear()
    const expected = generation
    await retain(await raw('/session/login', { method: 'POST', body: { email, password }, timeout: 90000 }), expected)
  }
  async function refresh() {
    if (!session) throw failure('Sign in to continue.', 'AUTHENTICATION_REQUIRED', 401)
    if (refreshing) return refreshing
    const expected = generation, token = session.refresh
    const pending = (async () => {
      try { await retain(await raw('/session/refresh', { method: 'POST', body: { refresh_token: token } }), expected) }
      catch (error) { if (expected === generation) clear(); throw error }
    })()
    refreshing = pending
    try { await pending } finally { if (refreshing === pending) refreshing = null }
  }
  async function request(path, options = {}) {
    if (!path.startsWith('/') || path.startsWith('//') || path.includes('://') || path.includes('\\') || path.split('?')[0].split('/').some(part=>part==='.' || part==='..')) throw failure('Invalid request path.','INVALID_REQUEST',400)
    if (!session) throw failure('Sign in to continue.', 'AUTHENTICATION_REQUIRED', 401)
    const expected = generation
    if (session.expires <= now() + 30000) await refresh()
    const current = () => { if (expected !== generation || !session) throw failure('This session has ended. Sign in again.', 'SESSION_CANCELLED', 401) }
    current()
    try { const data=await raw(path, { ...options, token: session.access }); current(); return data }
    catch (error) {
      current()
      // Retry only reads once after refresh. Never replay credential/consent writes.
      if (error.status === 401 && (!options.method || options.method === 'GET')) {
        await refresh()
        try { const data=await raw(path, { ...options, token: session.access }); current(); return data }
        catch (retryError) { if (retryError.status === 401) clear(); throw retryError }
      }
      if (error.status === 401) clear()
      throw error
    }
  }
  async function logout() {
    const token = session?.access
    clear()
    if (token) await raw('/session/logout', { method: 'POST', token })
  }
  return { login, logout, clear, request }
}
