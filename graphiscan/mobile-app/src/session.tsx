import React, { createContext, useContext, useMemo, useRef, useState } from 'react'
import { Platform } from 'react-native'
import { createUserApi, type User, type UserApi } from './core/api'
const configured = process.env.EXPO_PUBLIC_API_ORIGIN
export const API_ORIGIN = configured || (Platform.OS === 'android' ? 'http://10.0.2.2:5000' : 'http://127.0.0.1:5000')
interface Session { user: User | null; api: UserApi; login: (email: string, password: string) => Promise<void>; logout: () => Promise<void> }
const Context = createContext<Session | null>(null)
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const api = useRef<UserApi | null>(null)
  if (!api.current) api.current = createUserApi(API_ORIGIN, { onExpired: () => setUser(null) })
  const client = api.current
  const value = useMemo(() => ({
    user, api: client,
    async login(email: string, password: string) { setUser(await client.login(email, password)) },
    async logout() { try { await client.logout() } finally { setUser(null) } }
  }), [user, client])
  return <Context.Provider value={value}>{children}</Context.Provider>
}
export function useSession() { const value = useContext(Context); if (!value) throw new Error('Session unavailable'); return value }
