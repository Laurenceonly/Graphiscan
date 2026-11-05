export interface TokenStorage { getItem(key: string): string | null; setItem(key: string, value: string): void }

// Only the refresh credential is saved, separately for each API origin.
export function createMobileSessionStore(origin: string, storage: TokenStorage) {
  const key = 'graphiscan.mobile.refresh.' + Array.from(new URL(origin).origin).map(char => char.charCodeAt(0).toString(16)).join('-')
  return {
    read() {
      try {
        const value = storage.getItem(key)
        if (typeof value === 'string' && value.length > 0 && value.length <= 16384) return value
        storage.setItem(key, '')
      } catch { /* Keep memory sign-in available if device storage is unavailable. */ }
      return null
    },
    write(token: string) { try { storage.setItem(key, token) } catch { /* The current memory session remains usable. */ } },
    // A synchronous empty tombstone avoids a delayed deletion racing a new login.
    remove() { try { storage.setItem(key, '') } catch { /* No accessible stored session. */ } },
  }
}
