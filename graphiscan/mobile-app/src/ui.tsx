import React from 'react'
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme, type TextInputProps } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
export function useColors() {
  const dark = useColorScheme() === 'dark'
  const brand={brand:'#095df1',brandPressed:'#074bc2',onBrand:'#ffffff',brandMuted:'#eaf1ff'}
  return dark ? { ...brand,bg: '#101b2c', surface: '#19283d', text: '#f3f7fc', muted: '#b5c5d8', border: '#3c506a', primary: '#9fc4ff', onPrimary: '#0d2447', soft:'#213754', skeleton:'#334a67',error: '#ffb4b0', normal: '#9bd8ac', normalSurface:'#173f33', high: '#f7cc83', highSurface:'#49381e' }
    : { ...brand,bg: '#f7faff', surface: '#ffffff', text: '#14263c', muted: '#5c6c81', border: '#dce5ef', primary: '#095df1', onPrimary: '#ffffff', soft:'#e7efff', skeleton:'#d8e4f8',error: '#a72535', normal: '#176b3a', normalSurface:'#e7f4ec', high: '#895500', highSurface:'#fff2d9' }
}
export const styles = StyleSheet.create({
  page: { flex: 1 }, content: { padding: 20, gap: 20, width: '100%', maxWidth: 600, alignSelf: 'center', paddingBottom: 32 },
  title: { fontSize: 26, lineHeight: 34, fontWeight: '600', letterSpacing: -.5 }, heading: { fontSize: 18, lineHeight: 26, fontWeight: '600' },
  body: { fontSize: 15, lineHeight: 23 }, hint: { fontSize: 13, lineHeight: 20 }, label: { fontSize: 14, lineHeight: 21, fontWeight: '500' },
  section: { paddingVertical: 16, gap: 12 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  button: { minHeight: 52, maxWidth:'100%', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 10 },
  input: { borderWidth: 1, borderRadius: 10, minHeight: 52, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  listRow: { borderWidth: 1, borderRadius: 12, padding: 16, gap: 8 }, wrap: { flexDirection: 'row', gap: 12, flexWrap: 'wrap' },
  metricGrid: { flexDirection: 'row', gap: 12 }, metric: { flex: 1, minWidth: 0, minHeight: 144, justifyContent: 'space-between', borderWidth: 1, borderRadius: 12, padding: 16, gap: 12 }, metricValue: { fontSize: 28, lineHeight: 34, fontWeight: '600', fontVariant: ['tabular-nums'] },
  metricLabel: { fontSize: 13, lineHeight: 20, minHeight: 40 },
  panel: { borderWidth: 1, borderRadius: 12, padding: 20, gap: 16 },
})
export function Screen({ children, scroll = true }: { children: React.ReactNode; scroll?: boolean }) {
  const c = useColors()
  return <SafeAreaView edges={['left', 'right', 'bottom']} style={[styles.page, { backgroundColor: c.bg }]}>
    <KeyboardAvoidingView style={styles.page} behavior={Platform.OS === 'ios' ? 'padding' : Platform.OS === 'android' ? 'height' : undefined}>
      {scroll ? <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>{children}</ScrollView> : children}
    </KeyboardAvoidingView>
  </SafeAreaView>
}
export function Body({ children, muted = false }: { children: React.ReactNode; muted?: boolean }) {
  const c = useColors(); return <Text style={[styles.body, { color: muted ? c.muted : c.text }]}>{children}</Text>
}
export function Heading({ children }: { children: React.ReactNode }) { const c = useColors(); return <Text accessibilityRole="header" style={[styles.heading, { color: c.text }]}>{children}</Text> }
export function Button({ label, onPress, disabled = false, secondary = false, icon }: { label: string; onPress: () => void; disabled?: boolean; secondary?: boolean; icon?: React.ComponentProps<typeof MaterialIcons>['name'] }) {
  const c = useColors()
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [styles.button, { backgroundColor: secondary ? c.surface : c.primary, borderColor: c.border, borderWidth: secondary ? 1 : 0, opacity: disabled ? .55 : pressed ? .8 : 1 }]}>
    {icon && <MaterialIcons name={icon} size={22} color={secondary ? c.primary : c.onPrimary} />}
    <Text style={[styles.label, { color: secondary ? c.primary : c.onPrimary, flexShrink:1, textAlign:'center' }]}>{label}</Text>
  </Pressable>
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  const c = useColors(); return <View style={{ gap: 8 }}><Text style={[styles.label, { color: c.text }]}>{label}</Text>
    <TextInput accessibilityLabel={label} placeholderTextColor={c.muted} {...props} style={[styles.input, { color: c.text, borderColor: c.border, backgroundColor: c.surface }, props.multiline && { minHeight: 110, textAlignVertical: 'top' }, props.style]} />
  </View>
}
export function Notice({ message, error = false }: { message: string; error?: boolean }) {
  const c = useColors(); if (!message) return null
  return <Text accessibilityRole={error ? 'alert' : undefined} accessibilityLiveRegion="polite" style={[styles.body, { color: error ? c.error : c.primary }]}>{message}</Text>
}
export function Status({ value, prefix }: { value?: string; prefix?: string }) {
  const c = useColors(),normal=value==='Normal'||value==='Validated',high=value==='High Potential'||value==='Flagged'
  return <Text style={{alignSelf:'flex-start',borderRadius:6,paddingHorizontal:8,paddingVertical:4,fontSize:12,lineHeight:18,fontWeight:'500',overflow:'hidden',color:normal?c.normal:high?c.high:c.muted,backgroundColor:normal?c.normalSurface:high?c.highSurface:c.soft}}>{prefix?prefix+': ':''}{value || 'Pending'}</Text>
}
