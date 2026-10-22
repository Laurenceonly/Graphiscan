import React from 'react'
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme, type TextInputProps } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
export function useColors() {
  const dark = useColorScheme() === 'dark'
  return dark ? { bg: '#111827', surface: '#1f2937', text: '#f8fafc', muted: '#c0ccdd', border: '#4b5a70', primary: '#83cafa', onPrimary: '#102a40', error: '#ffb4b0', normal: '#9bd8ac', high: '#f7cc83' }
    : { bg: '#f8fafc', surface: '#ffffff', text: '#111827', muted: '#667085', border: '#dce1e8', primary: '#145c8f', onPrimary: '#ffffff', error: '#a72535', normal: '#176b3a', high: '#895500' }
}
export const styles = StyleSheet.create({
  page: { flex: 1 }, content: { padding: 20, gap: 24, width: '100%', maxWidth: 600, alignSelf: 'center', paddingBottom: 32 },
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
    <KeyboardAvoidingView style={styles.page} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
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
export function Loading() { const c = useColors(); return <ActivityIndicator size="large" color={c.primary} accessibilityLabel="Loading records" /> }
export function Status({ value }: { value?: string }) {
  const c = useColors(); return <Text style={[styles.label, { color: value === 'Normal' || value === 'Validated' ? c.normal : value === 'High Potential' || value === 'Flagged' ? c.high : c.muted }]}>{value || 'Pending'}</Text>
}
