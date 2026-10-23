import React, { useRef, useState } from 'react'
import { Modal, ScrollView, Text, View } from 'react-native'
import { Body, Button, styles, useColors } from './ui'

export default function SignOutAction({ onSignOut, onError, disabled = false, message }: {
  onSignOut: () => Promise<void>; onError: (message: string) => void; disabled?: boolean; message?: string
}) {
  const c = useColors(), [open, setOpen] = useState(false), [busy, setBusy] = useState(false), inFlight = useRef(false)
  async function confirm() {
    if (inFlight.current || disabled) return
    inFlight.current = true; setOpen(false); setBusy(true)
    try { await onSignOut() } catch (error: any) { onError(error.message || 'Sign-out could not be confirmed.') }
    finally { inFlight.current = false; setBusy(false) }
  }
  return <>
    <Button label={busy ? 'Signing out...' : 'Sign out'} secondary icon="logout" disabled={disabled || busy} onPress={() => setOpen(true)} />
    <Modal visible={open} transparent animationType="none" onRequestClose={() => setOpen(false)}>
      <View style={{ flex: 1, justifyContent: 'center', padding: 24, backgroundColor: 'rgba(0,0,0,0.48)' }}>
        <View role="dialog" accessibilityViewIsModal accessibilityLabel="Sign out of GraphiScan?"
          style={{ width: '100%', maxWidth: 420, maxHeight: '90%', alignSelf: 'center', borderRadius: 16, backgroundColor: c.surface }}>
          <ScrollView contentContainerStyle={{ padding: 24, gap: 16 }} keyboardShouldPersistTaps="handled">
            <Text accessibilityRole="header" style={[styles.heading, { color: c.text }]}>Sign out of GraphiScan?</Text>
            <Body>{message || 'You will need to sign in again to access your account.'}</Body>
            <View style={[styles.wrap, { justifyContent: 'flex-end' }]}>
              <Button label="Cancel" secondary onPress={() => setOpen(false)} />
              <Button label="Sign out" disabled={disabled} onPress={confirm} />
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  </>
}
