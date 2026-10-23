import React, { useEffect, useState } from 'react'
import { Pressable, StyleSheet, Switch, Text, TextInput, View } from 'react-native'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import { Body, Button, Notice, Screen, styles, useColors } from './ui'
import { AppBrand } from './WorkspaceUI'
import LoadingSkeleton from './LoadingSkeleton'

type Agreement = { title: string; content: string; version: string }
type Props = { client: HostedClient; action: string; refresh: () => Promise<void>; logout: () => Promise<void>; passwordChanged: () => void }

function PasswordField({ label, value, onChange, disabled, current = false }: { label: string; value: string; onChange: (value: string) => void; disabled: boolean; current?: boolean }) {
  const [visible, setVisible] = useState(false), [focused, setFocused] = useState(false), colors = useColors()
  useEffect(() => { if (!value) setVisible(false) }, [value])
  return <View style={s.passwordField}>
    <Text style={[styles.label,{color:colors.text}]}>{label}</Text>
    <View style={[s.passwordFrame,{backgroundColor:colors.surface,borderColor:focused?colors.primary:colors.border}]}>
    <TextInput accessibilityLabel={label} value={value} onChangeText={onChange} secureTextEntry={!visible} editable={!disabled}
      autoCapitalize="none" autoCorrect={false} autoComplete={current ? 'current-password' : 'new-password'}
      textContentType={current ? 'password' : 'newPassword'} maxLength={128} onFocus={()=>setFocused(true)} onBlur={()=>setFocused(false)} style={[s.passwordInput,{color:colors.text}]} />
    <Pressable accessibilityRole="button" accessibilityLabel={(visible ? 'Hide ' : 'Show ') + label.toLowerCase()} accessibilityState={{ disabled, expanded: visible }} disabled={disabled} onPress={() => setVisible(!visible)} style={s.visibility}>
      <MaterialIcons name={visible?'visibility-off':'visibility'} size={20} color={colors.muted} accessible={false}/>
    </Pressable>
    </View>
  </View>
}

export default function AccountSetup({ client, action, refresh, logout, passwordChanged }: Props) {
  const colors = useColors(), privacy = action === 'accept_privacy', passwordStep = action === 'change_password'
  const [current, setCurrent] = useState(''), [password, setPassword] = useState(''), [confirm, setConfirm] = useState('')
  const [agreement, setAgreement] = useState<Agreement | null>(null), [accepted, setAccepted] = useState(false)
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState(''), [attempt, setAttempt] = useState(0)
  const mismatch = Boolean(confirm && password !== confirm)
  const validPassword = password.length >= 8 && password.length <= 128 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password) && password !== current
  useEffect(() => {
    let alive = true
    setAgreement(null); setAccepted(false); setError(''); setLoading(privacy)
    if (privacy) client.request('/privacy-agreement').then(value => {
      if (typeof value?.title !== 'string' || typeof value?.content !== 'string' || typeof value?.version !== 'string') throw new Error('The agreement could not be loaded. Try again.')
      if (alive) setAgreement(value)
    }).catch(failure => { if (alive) setError(failure.message) }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [client, action, attempt, privacy])
  async function submit() {
    if (busy || (passwordStep && (!current || !validPassword || password !== confirm)) || (privacy && (!agreement || !accepted))) return
    setBusy(true); setError('')
    try {
      if (passwordStep) {
        await client.request('/me/password', { method: 'POST', body: { current_password: current, new_password: password, confirm_password: confirm } })
        client.clear(); passwordChanged()
      } else if (privacy && agreement) {
        await client.request('/me/privacy-acceptance', { method: 'POST', body: { agreement_version: agreement.version, accepted: true } })
        await refresh()
      }
    } catch (failure: any) {
      setError(failure.message)
      if (failure.code === 'AGREEMENT_CHANGED') { setAccepted(false); setAttempt(value => value + 1); await refresh().catch(() => {}) }
      if (failure.code === 'PASSWORD_CHANGE_RECOVERY_REQUIRED' || failure.status === 401) await logout().catch(() => {})
    } finally { setCurrent(''); setPassword(''); setConfirm(''); setBusy(false) }
  }
  return <Screen>
    <View style={{paddingVertical:8}}><AppBrand/></View>
    <View style={s.intro}>
      <Text accessibilityRole="header" style={[s.title, { color: colors.text }]}>{passwordStep ? 'Set your password' : privacy ? 'Data Privacy Agreement' : 'Account setup'}</Text>
      <Body muted>{passwordStep ? 'Replace your temporary password before continuing.' : privacy ? 'Review the agreement before accessing GraphiScan.' : 'The privacy agreement is not available for your account. Contact your administrator.'}</Body>
    </View>
    {passwordStep && <View style={[s.card, { backgroundColor: colors.surface }]}>
      <PasswordField label="Current password" value={current} onChange={setCurrent} disabled={busy} current />
      <PasswordField label="New password" value={password} onChange={setPassword} disabled={busy} />
      <PasswordField label="Confirm new password" value={confirm} onChange={setConfirm} disabled={busy} />
      <Body muted>Use 8–128 characters with uppercase and lowercase letters, a number and a symbol. Choose a different password.</Body>
      {mismatch && <Notice error message="The new passwords do not match." />}
    </View>}
    {privacy && <>
      {loading && <LoadingSkeleton kind="agreement"/>}
      {agreement && <View style={[s.card, { backgroundColor: colors.surface }]}>
        {agreement.title !== 'Data Privacy Agreement' && <Text accessibilityRole="header" style={[s.agreementTitle, { color: colors.text }]}>{agreement.title}</Text>}
        <Body muted>Version {agreement.version}</Body><Body>{agreement.content}</Body>
        <View style={[s.consent, { borderTopColor: colors.border }]}>
          <Text style={[s.consentText, { color: colors.text }]}>I have read and agree to this version of the Data Privacy Agreement.</Text>
          <Switch accessibilityLabel="I agree to this version of the Data Privacy Agreement" value={accepted} onValueChange={setAccepted} disabled={busy} trackColor={{ true: colors.primary }} />
        </View>
      </View>}
      {!loading && !agreement && <Button label="Reload agreement" secondary disabled={busy} onPress={() => setAttempt(value => value + 1)} />}
    </>}
    <Notice error message={error} />
    {(passwordStep || privacy) && <Button label={busy ? 'Saving…' : privacy ? 'Agree and continue' : 'Save password'} disabled={busy || (passwordStep ? !current || !validPassword || !confirm || mismatch : !agreement || !accepted || loading)} onPress={submit} />}
    {!passwordStep && !privacy && <Button label="Check account access" secondary disabled={busy} onPress={async () => { setBusy(true); setError(''); try { await refresh() } catch (failure: any) { setError(failure.message) } finally { setBusy(false) } }} />}
    <Button label="Sign out" secondary disabled={busy} onPress={() => logout().catch(failure => setError(failure.message))} />
  </Screen>
}
const s = StyleSheet.create({
  brand: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8 }, logo: { width: 36, height: 36 }, wordmark: { fontSize: 22, fontWeight: '700', letterSpacing: -.6 },
  intro: { gap: 8 }, title: { fontSize: 26, lineHeight: 34, fontWeight: '600', letterSpacing: -.5 },
  card: { padding: 20, borderRadius: 16, gap: 20 }, passwordField: { gap: 8 },
  passwordFrame: { flexDirection:'row',alignItems:'center',minHeight:52,borderWidth:1,borderRadius:10 }, passwordInput: { flex:1,minWidth:0,minHeight:50,paddingHorizontal:14,paddingVertical:12,fontSize:16 },
  visibility: { minHeight: 50, minWidth:48, alignItems:'center', justifyContent: 'center' },
  agreementTitle: { fontSize: 18, lineHeight: 26, fontWeight: '600' },
  consent: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 20, borderTopWidth: 1 }, consentText: { flex: 1, minWidth: 0, fontSize: 14, lineHeight: 21 },
})
