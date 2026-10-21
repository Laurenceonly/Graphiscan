import React, { useState } from 'react'
import { View } from 'react-native'
import { useSession } from '../session'
import { useRecords } from '../use-records'
import { Body, Button, Field, Heading, Loading, Notice, Screen, styles } from '../ui'

export function StudentAddScreen() {
  const { api } = useSession(), parents = useRecords(() => api.parents(), [api])
  const [name, setName] = useState(''), [age, setAge] = useState(''), [grade, setGrade] = useState('Grade 1')
  const [parent, setParent] = useState<number | null>(null), [busy, setBusy] = useState(false)
  const [error, setError] = useState(''), [saved, setSaved] = useState(false)
  async function save() {
    if (busy || saved) return
    if (name.trim().length < 2 || !/^\d+$/.test(age) || Number(age) < 1 || Number(age) > 30) {
      setError('Enter the student name and an age from 1 to 30.'); return
    }
    setBusy(true); setError('')
    try {
      await api.request('/teacher/students/add', { method: 'POST', body: { fullname: name.trim(), age: Number(age), grade_level: grade, parent_id: parent ?? '' } })
      setSaved(true)
    } catch (e) { setError((e as Error).message + ' If the connection was interrupted, check Students before submitting again.') }
    finally { setBusy(false) }
  }
  return <Screen><Heading>Add student</Heading>
    {saved ? <Notice message="Student saved. Return to Students to view the updated list." /> : <>
      <Field label="Student full name" value={name} onChangeText={setName} editable={!busy} autoCapitalize="words" />
      <Field label="Age" value={age} onChangeText={setAge} editable={!busy} keyboardType="number-pad" maxLength={2} />
      <Body>Grade level</Body><View style={styles.wrap}>{['Grade 1', 'Grade 2', 'Grade 3'].map(value => <Button key={value} label={value} secondary={grade !== value} disabled={busy} onPress={() => setGrade(value)} />)}</View>
      <Heading>Linked parent</Heading><Body muted>Select an existing parent account, or leave unassigned.</Body>
      {parents.loading && <Loading />}<Notice error message={parents.error} />
      <Button label="Unassigned" secondary={parent !== null} disabled={busy} onPress={() => setParent(null)} />
      {(parents.data ?? []).map(row => <Button key={row.user_id} label={row.fullname} secondary={parent !== row.user_id} disabled={busy} onPress={() => setParent(row.user_id)} />)}
      <Notice error message={error} /><Button label={busy ? 'Saving…' : 'Save student'} disabled={busy} onPress={save} />
    </>}
  </Screen>
}
