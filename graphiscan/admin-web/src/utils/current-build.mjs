// A tab can keep running a previous deployment even after the site is updated.
export async function hasNewAdminBuild({ fetchPage, currentScript, parseScript, timeoutMs = 3000 }) {
  if (!currentScript) return false
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetchPage('/login', { cache: 'no-store', signal: controller.signal })
    if (!response.ok) return false
    const nextScript = parseScript(await response.text())
    if (!nextScript) return false
    return new URL(nextScript, globalThis.location?.origin || 'http://localhost').pathname !==
      new URL(currentScript, globalThis.location?.origin || 'http://localhost').pathname
  } catch {
    // A failed update check must not prevent sign-in.
    return false
  } finally {
    clearTimeout(timeout)
  }
}
