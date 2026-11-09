import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { ActivityIndicator, View } from 'react-native'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import type { School } from './core/hosted-directory'
import { AppBrand } from './WorkspaceUI'
import { Body, Screen, useColors } from './ui'

type SchoolsState = { data: School[] | null; error: string; loading: boolean; refresh: () => void }
const Context = createContext<SchoolsState | null>(null)

export function useProfileSchools() {
  const value = useContext(Context)
  if (!value) throw new Error('Workspace required.')
  return value
}

export function ProfileSchoolsProvider({ request, userId, role, schoolIds, children }: {
  request: HostedClient['request']; userId: string; role: string; schoolIds: string[]; children: React.ReactNode;
}) {
  const colors = useColors(), ids = JSON.stringify(schoolIds)
  const scope = useMemo(() => ({}), [request, userId, role, ids])
  const [snapshot, setSnapshot] = useState<{ scope: object; data: School[] | null; error: string } | null>(null)
  const [loading, setLoading] = useState(true), [attempt, setAttempt] = useState(0)
  const current = snapshot?.scope === scope ? snapshot : null
  useEffect(() => {
    let alive = true
    setLoading(true)
    async function load() {
      const rows: School[] = [], seen = new Set<string>()
      let cursor: string | null = null
      do {
        const page = await request('/schools?limit=100' + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''), { envelope: true })
        if (!alive) return
        rows.push(...page.data)
        cursor = page.page?.next_cursor ?? null
        if (cursor && seen.has(cursor)) throw new Error('School details could not be loaded. Try again.')
        if (cursor) seen.add(cursor)
      } while (cursor)
      const assigned: string[] = JSON.parse(ids)
      setSnapshot({ scope, data: role === 'parent' ? rows : rows.filter(school => assigned.includes(school.school_id)), error: '' })
    }
    load().catch(failure => {
      if (alive) setSnapshot(previous => ({ scope, data: previous?.scope === scope && ![401, 403, 404].includes(failure.status) ? previous.data : null, error: failure.message || 'Unable to load schools.' }))
    }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [scope, attempt])
  if (!current) return <Screen><AppBrand/><View style={{ gap: 16, paddingVertical: 32 }}><ActivityIndicator color={colors.primary} accessibilityLabel="Opening your workspace"/><Body muted>Opening your workspace…</Body></View></Screen>
  return <Context.Provider value={{ data: current.data, error: current.error, loading, refresh: () => setAttempt(value => value + 1) }}>{children}</Context.Provider>
}
