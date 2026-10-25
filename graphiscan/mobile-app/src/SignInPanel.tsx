import React, { useEffect, useState } from 'react'
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { useColors } from './ui'
import BrandLogo from './BrandLogo'

type Props = {
  email: string; password: string; busy: boolean; error: string; notice?: string
  onEmail: (value: string) => void; onPassword: (value: string) => void
  onSubmit: () => void; onForgotPassword?: () => void
}

export default function SignInPanel({ email, password, busy, error, notice, onEmail, onPassword, onSubmit, onForgotPassword }: Props) {
  const [visible, setVisible] = useState(false)
  const [focused, setFocused] = useState<'email' | 'password' | null>(null)
  const c = useColors(), dark=useColorScheme()==='dark'
  useEffect(() => { if (!password) setVisible(false) }, [password])
  const disabled = busy || !email.trim() || !password
  return <SafeAreaView edges={['top','bottom']} style={[s.page,{backgroundColor:c.surface}]}>
    <StatusBar style={dark?'light':'dark'} />
    <KeyboardAvoidingView style={[s.page,{backgroundColor:c.surface}]} behavior={Platform.OS === 'ios' ? 'padding' : Platform.OS === 'android' ? 'height' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
        <View style={s.brandRegion}>
          <View style={s.brand} accessible accessibilityLabel="GraphiScan">
            <BrandLogo size={80} />
            <Text style={[s.wordmark,{color:c.text}]}>Graphi<Text style={{color:c.brandAccent}}>Scan</Text></Text>
          </View>
        </View>
        <View style={s.main}>
          <Text accessibilityRole="header" style={[s.title,{color:c.text}]}>Sign in to your account</Text>
          <View style={s.form}>
            <View style={s.field}>
              <Text style={[s.label,{color:c.text}]}>Email address</Text>
              <View style={[s.inputFrame,{backgroundColor:c.bg,borderColor:focused==='email'?c.primary:c.border}]}>
                <TextInput accessibilityLabel="Email address" value={email} onChangeText={onEmail}
                  placeholder="Enter your email" placeholderTextColor={c.muted} keyboardType="email-address"
                  autoCapitalize="none" autoCorrect={false} autoComplete="email" textContentType="username"
                  editable={!busy} style={[s.input,{color:c.text}]} onFocus={() => setFocused('email')} onBlur={() => setFocused(null)} />
              </View>
            </View>
            <View style={s.field}>
              <Text style={[s.label,{color:c.text}]}>Password</Text>
              <View style={[s.inputFrame,{backgroundColor:c.bg,borderColor:focused==='password'?c.primary:c.border}]}>
                <TextInput accessibilityLabel="Password" value={password} onChangeText={onPassword}
                  placeholder="Enter your password" placeholderTextColor={c.muted} secureTextEntry={!visible}
                  autoCapitalize="none" autoCorrect={false} autoComplete="current-password" textContentType="password"
                  editable={!busy} style={[s.input,{color:c.text}]} onSubmitEditing={onSubmit} returnKeyType="go"
                  onFocus={() => setFocused('password')} onBlur={() => setFocused(null)} />
                <Pressable accessibilityRole="button" accessibilityLabel={visible ? 'Hide password' : 'Show password'}
                  accessibilityState={{ disabled: busy }} disabled={busy}
                  onPress={() => setVisible(value => !value)} style={s.eye}>
                  <MaterialIcons name={visible ? 'visibility-off' : 'visibility'} size={20} color={c.muted} accessible={false} />
                </Pressable>
              </View>
            </View>
            {!!notice && <Text accessibilityLiveRegion="polite" style={[s.notice,{color:c.primary}]}>{notice}</Text>}
            {!!error && <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={[s.error,{color:c.error}]}>{error}</Text>}
            <Pressable accessibilityRole="button" accessibilityLabel={busy ? 'Signing in...' : 'Sign in'}
              accessibilityState={{ disabled, busy }} disabled={disabled} onPress={onSubmit}
              style={({ pressed }) => [s.submit,{backgroundColor:pressed?c.brandPressed:c.brand,opacity:disabled ? .7 : 1}]}>
              <Text style={[s.submitLabel,{color:c.onBrand}]}>{busy ? 'Signing in...' : 'Sign in'}</Text>
            </Pressable>
            {onForgotPassword && <Pressable accessibilityRole="button" disabled={busy} onPress={onForgotPassword} style={s.forgot}>
              <Text style={[s.forgotLabel,{color:c.primary}]}>Forgot password?</Text>
            </Pressable>}
          </View>
          {!onForgotPassword&&<Text style={[s.help,{color:c.muted}]}>Need help signing in?{ '\n' }Contact your administrator.</Text>}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>
}

const s = StyleSheet.create({
  page: { flex: 1 },
  content: { flexGrow: 1, justifyContent:'center',paddingHorizontal:28,paddingVertical:32,gap:36,width: '100%', maxWidth: 460, alignSelf: 'center' },
  brandRegion: { alignItems:'center' },
  brand: { alignItems: 'center', gap: 4 },
  wordmark: { fontSize: 28,lineHeight:36,fontWeight: '700', letterSpacing: -.6 },
  main: { gap:24 },
  title: { fontSize: 22, lineHeight: 30, fontWeight: '600', letterSpacing: -.3,textAlign:'center' },
  form: { gap: 20 },
  field: { gap: 9 },
  label: { fontSize: 14, lineHeight: 21, fontWeight: '500' },
  inputFrame: { flexDirection: 'row', alignItems: 'center', minHeight: 56, paddingLeft: 16, borderWidth: 1, borderRadius: 12 },
  input: { flex: 1, minWidth: 0, minHeight: 54, paddingVertical: 14, paddingRight: 12, fontSize: 16 },
  eye: { width: 48, minHeight: 54, alignItems: 'center', justifyContent: 'center' },
  submit: { alignItems: 'center', justifyContent: 'center', minHeight: 56,borderRadius: 12, marginTop: 4, paddingHorizontal: 18 },
  submitLabel: { fontSize: 15, fontWeight: '600', lineHeight: 22 },
  error: { color: '#a72535', fontSize: 13, lineHeight: 20 },
  notice: { color: '#145c8f', fontSize: 13, lineHeight: 20 },
  help: { fontSize:13,lineHeight:21,textAlign:'center' },
  forgot: { minHeight: 48, alignItems: 'center', justifyContent: 'center', marginTop: -12 },
  forgotLabel: { color: '#145c8f', fontSize: 13, fontWeight: '500' },
})
