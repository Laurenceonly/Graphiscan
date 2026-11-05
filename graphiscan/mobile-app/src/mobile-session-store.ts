import { Platform } from 'react-native'
import * as SecureStore from 'expo-secure-store'
import { createMobileSessionStore } from './core/mobile-session-store'

export function mobileSessionStore(origin: string) {
  return createMobileSessionStore(origin, {
    getItem: key => Platform.OS === 'web' ? globalThis.sessionStorage.getItem(key) : SecureStore.getItem(key),
    setItem: (key, value) => {
      if (Platform.OS === 'web') globalThis.sessionStorage.setItem(key, value)
      else SecureStore.setItem(key, value)
    },
  })
}
