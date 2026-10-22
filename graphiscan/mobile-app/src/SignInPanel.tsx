import React, { useEffect, useState } from 'react'
import { Image, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'

type Props = {
  email: string; password: string; busy: boolean; error: string; notice?: string
  onEmail: (value: string) => void; onPassword: (value: string) => void
  onSubmit: () => void; onForgotPassword?: () => void
}

export default function SignInPanel({ email, password, busy, error, notice, onEmail, onPassword, onSubmit, onForgotPassword }: Props) {
  const [visible, setVisible] = useState(false)
  const [focused, setFocused] = useState<'email' | 'password' | null>(null)
  useEffect(() => { if (!password) setVisible(false) }, [password])
  const disabled = busy || !email.trim() || !password
  return <SafeAreaView style={s.page}>
    <StatusBar style="dark" />
    <KeyboardAvoidingView style={s.page} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
        <View style={s.brand} accessible accessibilityLabel="GraphiScan">
          <Image source={require('../assets/graphiscan-logo.png')} style={s.logo} resizeMode="contain" accessible={false} />
          <Text style={s.wordmark}>Graphi<Text style={s.accent}>Scan</Text></Text>
        </View>
        <View style={s.main}>
          <View style={s.intro}>
            <Text accessibilityRole="header" style={s.title}>Welcome back</Text>
            <Text style={s.subtitle}>Sign in to your account.</Text>
          </View>
          <View style={s.form}>
            <View style={s.field}>
              <Text style={s.label}>Email address</Text>
              <View style={[s.inputFrame, focused === 'email' && s.focused]}>
                <MaterialIcons name="mail-outline" size={20} color="#77869a" accessible={false} />
                <TextInput accessibilityLabel="Email address" value={email} onChangeText={onEmail}
                  placeholder="Enter your email" placeholderTextColor="#98a2b3" keyboardType="email-address"
                  autoCapitalize="none" autoCorrect={false} autoComplete="email" textContentType="username"
                  editable={!busy} style={s.input} onFocus={() => setFocused('email')} onBlur={() => setFocused(null)} />
              </View>
            </View>
            <View style={s.field}>
              <Text style={s.label}>Password</Text>
              <View style={[s.inputFrame, focused === 'password' && s.focused]}>
                <MaterialIcons name="lock-outline" size={20} color="#77869a" accessible={false} />
                <TextInput accessibilityLabel="Password" value={password} onChangeText={onPassword}
                  placeholder="Your password" placeholderTextColor="#98a2b3" secureTextEntry={!visible}
                  autoCapitalize="none" autoCorrect={false} autoComplete="current-password" textContentType="password"
                  editable={!busy} style={s.input} onSubmitEditing={onSubmit} returnKeyType="go"
                  onFocus={() => setFocused('password')} onBlur={() => setFocused(null)} />
                <Pressable accessibilityRole="button" accessibilityLabel={visible ? 'Hide password' : 'Show password'}
                  accessibilityState={{ disabled: busy }} disabled={busy}
                  onPress={() => setVisible(value => !value)} style={s.eye}>
                  <MaterialIcons name={visible ? 'visibility-off' : 'visibility'} size={20} color="#77869a" accessible={false} />
                </Pressable>
              </View>
            </View>
            {!!notice && <Text accessibilityLiveRegion="polite" style={s.notice}>{notice}</Text>}
            {!!error && <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={s.error}>{error}</Text>}
            <Pressable accessibilityRole="button" accessibilityLabel={busy ? 'Signing in...' : 'Sign in'}
              accessibilityState={{ disabled, busy }} disabled={disabled} onPress={onSubmit}
              style={({ pressed }) => [s.submit, pressed && { backgroundColor: '#104d79' }, busy && { opacity: .65 }]}>
              <Text style={s.submitLabel}>{busy ? 'Signing in...' : 'Sign in'}</Text>
            </Pressable>
            {onForgotPassword && <Pressable accessibilityRole="button" disabled={busy} onPress={onForgotPassword} style={s.forgot}>
              <Text style={s.forgotLabel}>Forgot password?</Text>
            </Pressable>}
          </View>
          <Text style={s.privacy}>For your privacy, restarting the app requires signing in again.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>
}

const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#fff' },
  content: { flexGrow: 1, paddingHorizontal: 20, paddingTop: 28, paddingBottom: 32, width: '100%', maxWidth: 600, alignSelf: 'center' },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  logo: { width: 36, height: 36 },
  wordmark: { fontSize: 22, fontWeight: '700', letterSpacing: -.6, color: '#101828' },
  accent: { color: '#145c8f' },
  main: { flexGrow: 1, justifyContent: 'center', paddingTop: 54, paddingBottom: 88 },
  intro: { alignItems: 'center', gap: 10, marginBottom: 34 },
  title: { fontSize: 26, lineHeight: 34, fontWeight: '600', letterSpacing: -.5, color: '#101828', textAlign: 'center' },
  subtitle: { fontSize: 15, lineHeight: 23, color: '#667085', textAlign: 'center' },
  form: { gap: 22 },
  field: { gap: 9 },
  label: { color: '#344054', fontSize: 14, lineHeight: 21, fontWeight: '500' },
  inputFrame: { flexDirection: 'row', alignItems: 'center', minHeight: 52, paddingLeft: 14, gap: 11, borderWidth: 1, borderColor: '#dce1e8', borderRadius: 10, backgroundColor: '#fff' },
  focused: { borderColor: '#145c8f' },
  input: { flex: 1, minWidth: 0, height: 50, paddingVertical: 12, paddingRight: 12, color: '#101828', fontSize: 16 },
  eye: { width: 44, height: 50, alignItems: 'center', justifyContent: 'center' },
  submit: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', minHeight: 52, backgroundColor: '#145c8f', borderRadius: 10, marginTop: 2, paddingHorizontal: 18 },
  submitLabel: { color: '#fff', fontSize: 14, fontWeight: '500', lineHeight: 21 },
  error: { color: '#a72535', fontSize: 13, lineHeight: 20 },
  notice: { color: '#145c8f', fontSize: 13, lineHeight: 20 },
  privacy: { marginTop: 28, paddingHorizontal: 10, color: '#8590a2', fontSize: 11, lineHeight: 18, textAlign: 'center' },
  forgot: { minHeight: 44, alignItems: 'center', justifyContent: 'center', marginTop: -12 },
  forgotLabel: { color: '#145c8f', fontSize: 13, fontWeight: '500' },
})
