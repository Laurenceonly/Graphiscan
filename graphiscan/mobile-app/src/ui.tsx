import React from 'react'
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme, type TextInputProps } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
export function useColors() {
  const dark = useColorScheme() === 'dark'
  return dark ? { bg: '#111827', surface: '#1f2937', text: '#f8fafc', muted: '#c0ccdd', border: '#4b5a70', primary: '#83cafa', onPrimary: '#102a40', error: '#ffb4b0', normal: '#9bd8ac', high: '#f7cc83' }
    : { bg: '#f8fafc', surface: '#ffffff', text: '#111827', muted: '#475467', border: '#cbd5e1', primary: '#145c8f', onPrimary: '#ffffff', error: '#a72535', normal: '#176b3a', high: '#895500' }
}
export const styles = StyleSheet.create({
  page: { flex: 1 }, content: { padding: 20, gap: 20, width: '100%', maxWidth: 760, alignSelf: 'center', paddingBottom: 40 },
  title: { fontSize: 28, lineHeight: 35, fontWeight: '700' }, heading: { fontSize: 21, lineHeight: 28, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24 }, hint: { fontSize: 14, lineHeight: 21 }, label: { fontSize: 15, fontWeight: '600' },
  section: { paddingVertical: 16, gap: 12 }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  button: { minHeight: 48, borderRadius: 12, paddingHorizontal: 18, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 10 },
  input: { borderWidth: 1, borderRadius: 12, minHeight: 50, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  listRow: { borderBottomWidth: 1, paddingVertical: 18, gap: 6 }, wrap: { flexDirection: 'row', gap: 12, flexWrap: 'wrap' }
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
    <Text style={[styles.label, { color: secondary ? c.primary : c.onPrimary }]}>{label}</Text>
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
