import React, { useState } from 'react'
import { Text, View } from 'react-native'
import type { NativeStackScreenProps } from '@react-navigation/native-stack'
import type { RootRoutes } from '../navigation-types'
import { useSession } from '../session'
import { Body, Button, Field, Heading, Notice, Screen, styles, useColors } from '../ui'

export function LoginScreen({ navigation }: NativeStackScreenProps<RootRoutes, 'Login'>) {
  const { login } = useSession(), colors = useColors()
  const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function submit() {
    if (busy) return
    if (!email.trim() || !password) { setError('Enter your email and password.'); return }
    setBusy(true); setError('')
    try { await login(email, password) } catch (failure: any) { setError(failure.message) }
    finally { setPassword(''); setBusy(false) }
  }
  return <Screen><View style={{ paddingTop: 40, gap: 28 }}>
    <Text style={[styles.title, { color: colors.primary }]}>GRAPHI<Text style={{ color: colors.text }}>SCAN</Text></Text>
    <Heading>Welcome back</Heading><Body muted>Sign in with the account provided by your administrator.</Body>
    <Field label="Email address" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" editable={!busy} />
    <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry={!show} autoCapitalize="none" autoComplete="current-password" editable={!busy} onSubmitEditing={submit} />
    <Button label={show ? 'Hide password' : 'Show password'} secondary onPress={() => setShow(!show)} />
    <Notice error message={error} /><Button label={busy ? 'Signing in…' : 'Sign in'} disabled={busy} onPress={submit} />
    <Button label="Forgot password?" secondary disabled={busy} onPress={() => navigation.navigate('ForgotPassword')} />
    <Body muted>GraphiScan is a handwriting screening aid, not a clinical diagnosis.</Body>
  </View></Screen>
}
export function ForgotPasswordScreen() {
  const { api } = useSession()
  const [email, setEmail] = useState(''), [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('')
  async function submit() {
    if (busy || !email.trim()) return
    setBusy(true); setError(''); setMessage('')
    try { const data = await api.request('/forgot-password', { method: 'POST', body: { email: email.trim().toLowerCase() } }); setMessage(data.message) }
    catch (failure: any) { setError(failure.message) } finally { setBusy(false) }
  }
  return <Screen><Heading>Forgot password?</Heading><Body>Enter your account email to request password recovery.</Body>
    <Field label="Email address" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" editable={!busy} />
    <Notice error message={error} /><Notice message={message} /><Button label={busy ? 'Sending…' : 'Request reset'} disabled={busy || !email.trim()} onPress={submit} />
  </Screen>
}
export function ResetPasswordScreen({ route, navigation }: NativeStackScreenProps<RootRoutes, 'ResetPassword'>) {
  const { api } = useSession(), token = route.params?.token
  const [password, setPassword] = useState(''), [confirm, setConfirm] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  async function submit() {
    if (!token || busy) return
    if (password !== confirm || password.length < 8) { setError('Use matching passwords with at least eight characters.'); return }
    setBusy(true); setError('')
    try { await api.request('/reset-password', { method: 'POST', body: { token, password, confirm_password: confirm } }); setSaved(true) }
    catch (failure: any) { setError(failure.message) } finally { setPassword(''); setConfirm(''); setBusy(false) }
  }
  return <Screen><Heading>Reset password</Heading>
    {!token ? <Body>Open the password-reset link provided for your account.</Body> : saved ? <><Notice message="Password saved. Sign in with your new password." /><Button label="Return to sign in" onPress={() => navigation.navigate('Login')} /></> :
      <><Field label="New password" value={password} onChangeText={setPassword} secureTextEntry editable={!busy} autoComplete="new-password" />
        <Field label="Confirm new password" value={confirm} onChangeText={setConfirm} secureTextEntry editable={!busy} autoComplete="new-password" />
        <Body muted>Use uppercase, lowercase, a number and a symbol.</Body><Notice error message={error} /><Button label={busy ? 'Saving…' : 'Save password'} disabled={busy} onPress={submit} /></>}
  </Screen>
}
