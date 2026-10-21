import { useCallback, useState } from 'react'
import { useFocusEffect } from '@react-navigation/native'
export function useRecords<T>(load: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState(''), [loading, setLoading] = useState(true), [attempt, setAttempt] = useState(0)
  useFocusEffect(useCallback(() => {
    let alive = true
    setLoading(true); setError('')
    load().then(value => { if (alive) setData(value) })
      .catch(failure => { if (alive) { setData(null); setError(failure.message || 'Unable to load records.') } })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [...dependencies, attempt]))
  return { data, error, loading, refresh: () => setAttempt(value => value + 1) }
}
