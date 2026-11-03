// sessionStorage survives reloads in this tab; no password, bearer or records saved.
export function createTabSessionStore(origin, storage) {
  const key = 'graphiscan:admin:refresh:' + new URL(origin).origin
  return {
    read() {
      try {
        const token = storage?.getItem(key)
        if (typeof token === 'string' && token.length > 0 && token.length <= 16384) return token
        storage?.removeItem(key)
      } catch { /* Browsers may deny storage; keep the memory-only client usable. */ }
      return null
    },
    write(token) { try { storage?.setItem(key, token) } catch { /* Memory session still works. */ } },
    remove() { try { storage?.removeItem(key) } catch { /* Nothing accessible to remove. */ } }
  }
}
