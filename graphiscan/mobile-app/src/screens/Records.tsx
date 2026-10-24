import React, { useMemo, useState } from 'react'
import { FlatList, Pressable, Text, View, useWindowDimensions } from 'react-native'
import { useNavigation } from '@react-navigation/native'
import type { NativeStackNavigationProp } from '@react-navigation/native-stack'
import type { RootRoutes } from '../navigation-types'
import { useSession } from '../session'
import { useRecords } from '../use-records'
import type { Result } from '../core/api'
import { dateLabel, resultCounts, screeningType } from '../core/presentation'
import { Body, Button, Field, Heading, Notice, Screen, Status, styles, useColors } from '../ui'
import LoadingSkeleton from '../LoadingSkeleton'
import SignOutAction from '../SignOutAction'

export function HomeScreen() {
  const { user, api } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>(), colors = useColors()
  const record = useRecords(async () => {
    const results = await api.results(user!.role)
    const students = user!.role === 'teacher' ? await api.students() : []
    return { results, students }
  }, [user!.role, api])
  const counts = record.data ? resultCounts(record.data.results) : null
  const firstName = user!.fullname.split(' ')[0]
  return <Screen><Text style={[styles.title, { color: colors.text }]}>Welcome, {firstName}</Text>
    <Body muted>{user!.role === 'teacher' ? 'Manage students, upload handwriting samples, and review screening progress.' : user!.role === 'expert' ? 'Review screening records and provide your professional validation.' : 'View reviewed screening reports and progress for your linked children.'}</Body>
    {record.loading && !record.data && <LoadingSkeleton />}<Notice error message={record.error} />
    {counts && <View style={[styles.section, { borderColor: colors.border, borderBottomWidth: 1 }]}>
      <Body>{user!.role === 'teacher' ? record.data!.students.length + ' students' : new Set(record.data!.results.map(r => r.student_id || r.student_name)).size + ' students with accessible reports'}</Body>
      <Body>{counts.total} {user!.role === 'parent' ? 'reviewed reports' : 'screenings'}</Body>
      {user!.role !== 'parent' && <Body>{counts.pending} pending reviews</Body>}<Body>{counts.followUp} marked for follow-up</Body>
    </View>}
    <Heading>{user!.role === 'teacher' ? 'Teacher tools' : user!.role === 'expert' ? 'Expert tools' : 'Parent tools'}</Heading>
    {user!.role === 'teacher' && <Button label="Add student" icon="person-add" onPress={() => navigation.navigate('AddStudent')} />}
    <Body>Use the navigation below to open {user!.role === 'teacher' ? 'students, uploads and results' : 'results and your profile'}.</Body>
    <Button label="Refresh dashboard" icon="refresh" secondary disabled={record.loading} onPress={record.refresh} />
    <Body muted>Screening results support expert review. They do not establish a diagnosis.</Body>
  </Screen>
}
export function StudentsScreen() {
  const { api } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>(), colors = useColors()
  const {height:windowHeight}=useWindowDimensions(),[listHeight,setListHeight]=useState(0)
  const record = useRecords(() => api.students(), [api]), [search, setSearch] = useState('')
  const rows = useMemo(() => (record.data ?? []).filter(s => s.fullname.toLowerCase().includes(search.toLowerCase().trim())), [record.data, search])
  return <Screen scroll={false}><FlatList data={rows} keyExtractor={row => String(row.student_id)} contentContainerStyle={styles.content}
    onLayout={event=>setListHeight(event.nativeEvent.layout.height)}
    refreshing={record.loading&&record.data!==null} onRefresh={record.refresh} keyboardShouldPersistTaps="handled"
    ListHeaderComponent={<View style={{ gap: 16 }}><Heading>Students</Heading><Button label="Add student" icon="person-add" onPress={() => navigation.navigate('AddStudent')} />
      <Field search label="Search students" placeholder="Search by student name" value={search} onChangeText={setSearch} /><Notice error message={record.error} /></View>}
    ListEmptyComponent={record.loading ? <LoadingSkeleton kind="student" count={3} fillHeight={listHeight||windowHeight}/> : !record.error ? <Body>No matching students.</Body> : undefined}
    renderItem={({ item }) => <Pressable accessibilityRole="button" accessibilityLabel={'View progress for ' + item.fullname} onPress={() => navigation.navigate('Progress', { id: String(item.student_id) })}
      style={[styles.listRow, { borderColor: colors.border }]}><Heading>{item.fullname}</Heading><Body muted>{item.grade_level} · Age {item.age ?? 'not recorded'}</Body><Body muted>Parent: {item.parent_name || 'Not assigned'}</Body><Text style={[styles.label, { color: colors.primary }]}>View progress</Text></Pressable>}
  /></Screen>
}
export function ResultsScreen() {
  const { api, user } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>(), colors = useColors()
  const {height:windowHeight}=useWindowDimensions(),[listHeight,setListHeight]=useState(0)
  const record = useRecords(() => api.results(user!.role), [api, user!.role])
  const [search, setSearch] = useState(''), [status, setStatus] = useState('')
  const rows = useMemo(() => (record.data ?? []).filter(row => row.student_name?.toLowerCase().includes(search.toLowerCase().trim()) && (!status || row.validation_status === status)), [record.data, search, status])
  return <Screen scroll={false}><FlatList<Result> data={rows} keyExtractor={row => String(row.result_id)} contentContainerStyle={styles.content}
    onLayout={event=>setListHeight(event.nativeEvent.layout.height)}
    refreshing={record.loading&&record.data!==null} onRefresh={record.refresh} keyboardShouldPersistTaps="handled"
    ListHeaderComponent={<View style={{ gap: 16 }}><Heading>{user!.role === 'expert' ? 'Validation queue' : user!.role === 'parent' ? 'Child results' : 'Screening results'}</Heading>
      <Field search label="Search by student" placeholder="Search by student name" value={search} onChangeText={setSearch} />
      {user!.role !== 'parent' && <View style={styles.wrap}>{['', 'Pending', 'Validated', 'Flagged'].map(value => <Button key={value} label={value || 'All reviews'} secondary={status !== value} onPress={() => setStatus(value)} />)}</View>}
      <Notice error message={record.error} /></View>}
    ListEmptyComponent={record.loading ? <LoadingSkeleton fillHeight={listHeight||windowHeight}/> : !record.error ? <Body>{user!.role === 'parent' ? 'No reviewed reports are available for your linked children.' : 'No matching screening records.'}</Body> : undefined}
    renderItem={({ item }) => <Pressable accessibilityRole="button" accessibilityLabel={'Open screening for ' + item.student_name} onPress={() => navigation.navigate('Result', { id: String(item.result_id) })}
      style={[styles.listRow, { borderColor: colors.border }]}><Heading>{item.student_name}</Heading><Body>{screeningType(item.report_type)}</Body><Status value={item.classification} /><Body muted>{dateLabel(item.date_generated)} · {item.grade_level || 'Grade not recorded'}</Body><Status value={item.validation_status} /></Pressable>}
  /></Screen>
}
export function ProgressScreen({ route }: { route: { params: { id: string } } }) {
  const { user, api } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>(), colors = useColors()
  const {height:windowHeight}=useWindowDimensions(),[listHeight,setListHeight]=useState(0)
  const record = useRecords(() => api.progress(user!.role, route.params.id), [api, user!.role, route.params.id])
  const rows: Result[] = record.data?.progress ?? []
  return <Screen scroll={false}><FlatList<Result> data={rows} keyExtractor={(row, index) => String(row.result_id ?? index)} contentContainerStyle={styles.content}
    onLayout={event=>setListHeight(event.nativeEvent.layout.height)}
    refreshing={record.loading&&record.data!==null} onRefresh={record.refresh}
    ListHeaderComponent={<View style={{ gap: 16 }}><Heading>{record.data?.student?.fullname || 'Student progress'}</Heading><Body muted>{record.data?.student?.grade_level || 'Screening history'}</Body>
      <Body>{user!.role === 'parent' ? 'Only reviewed reports are included.' : 'Review dated assessments with their expert validation.'}</Body>
      <Notice error message={record.error} /></View>}
    ListEmptyComponent={record.loading ? <LoadingSkeleton fillHeight={listHeight||windowHeight}/> : !record.error ? <Body>No accessible screening history.</Body> : undefined}
    renderItem={({ item }) => <Pressable accessibilityRole="button" accessibilityLabel={'Open screening from ' + dateLabel(item.date_generated)} onPress={() => navigation.navigate('Result', { id: String(item.result_id) })}
      style={[styles.listRow, { borderColor: colors.border }]}><Heading>{dateLabel(item.date_generated)}</Heading><Body>{screeningType(item.report_type)}</Body><Status value={item.classification} /><Status value={item.validation_status} /></Pressable>}
  /></Screen>
}
export function ProfileScreen() {
  const { user, logout } = useSession(), [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function signOut() { if (busy) return; setBusy(true); try { await logout() } catch { setError('Signed out on this device. Server sign-out could not be confirmed.') } finally { setBusy(false) } }
  return <Screen><Heading>{user!.fullname}</Heading><Body>{user!.email}</Body><Body>Role: {user!.role}</Body><Body>Status: {user!.account_status}</Body>
    <Body muted>Sign out when you finish using this device.</Body><Notice error message={error} /><SignOutAction disabled={busy} onSignOut={signOut} onError={setError}/></Screen>
}

