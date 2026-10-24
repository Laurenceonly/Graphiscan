import { useCallback, useMemo, useState } from 'react'
import { useFocusEffect } from '@react-navigation/native'
export function useRecords<T>(load: () => Promise<T>, dependencies: unknown[] = []) {
  const scope = useMemo(() => ({}), dependencies)
  const [snapshot, setSnapshot] = useState<{ scope: object; data: T | null; error: string } | null>(null)
  const [loading, setLoading] = useState(true), [attempt, setAttempt] = useState(0)
  const current = snapshot?.scope === scope ? snapshot : null
  useFocusEffect(useCallback(() => {
    let alive = true
    setLoading(true)
    setSnapshot(previous => ({ scope, data: previous?.scope === scope ? previous.data : null, error: '' }))
    load().then(value => { if (alive) setSnapshot({ scope, data: value, error: '' }) })
      .catch(failure => { if (alive) setSnapshot({ scope, data: null, error: failure.message || 'Unable to load records.' }) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [scope, attempt]))
  return { data: current?.data ?? null, error: current?.error ?? '', loading: loading || !current, refresh: () => setAttempt(value => value + 1) }
}
