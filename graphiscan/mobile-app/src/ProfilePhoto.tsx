import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { Platform } from 'react-native'
import * as ImagePicker from 'expo-image-picker'
import * as FileSystem from 'expo-file-system/legacy'

type Photo = { uri: string; busy: boolean; error: string; choose: () => Promise<void>; remove: () => Promise<void> }
const Context = createContext<Photo | null>(null)
export function useProfilePhoto() { const value = useContext(Context); if (!value) throw new Error('Profile photo is unavailable.'); return value }

export function ProfilePhotoProvider({ userId, children }: { userId: string; children: React.ReactNode }) {
  const [uri, setUri] = useState(''), [busy, setBusy] = useState(true), [error, setError] = useState('')
  const alive = useRef(true), locked = useRef(true)
  const key = 'graphiscan-profile-photo-' + encodeURIComponent(userId)
  const directory = FileSystem.documentDirectory ? FileSystem.documentDirectory + key + '/' : null
  useEffect(() => {
    alive.current = true
    async function load() {
      try {
        if (Platform.OS === 'web') { const saved = localStorage.getItem(key); if (alive.current && saved?.startsWith('data:image/')) setUri(saved) }
        else if (directory) {
          const index = directory + 'current.txt'
          if (!(await FileSystem.getInfoAsync(index)).exists) return
          const name = await FileSystem.readAsStringAsync(index)
          if (!/^photo-\d+\.jpg$/.test(name)) return
          const saved = directory + name
          if ((await FileSystem.getInfoAsync(saved)).exists && alive.current) setUri(saved)
        }
      } catch { if (alive.current) setError('Your saved photo could not be loaded. Choose it again.') }
      finally { locked.current = false; if (alive.current) setBusy(false) }
    }
    void load()
    return () => { alive.current = false }
  }, [key, directory])
  async function choose() {
    if (locked.current) return
    locked.current = true; setBusy(true); setError('')
    let pendingFile = ''
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: true, aspect: [1, 1], quality: .7 })
      if (result.canceled || !alive.current) return
      const asset = result.assets[0]
      if (asset.fileSize && asset.fileSize > 5 * 1024 * 1024) throw new Error('Choose a photo smaller than 5 MB.')
      let next = ''
      if (Platform.OS === 'web') {
        const blob = await (await fetch(asset.uri)).blob()
        if (!blob.type.startsWith('image/') || blob.size > 5 * 1024 * 1024) throw new Error('Choose a photo smaller than 5 MB.')
        next = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Unable to read this photo.')); reader.readAsDataURL(blob) })
        if (!alive.current) return
        localStorage.setItem(key, next)
      } else {
        if (!directory) throw new Error('Photo storage is unavailable on this device.')
        const info = await FileSystem.getInfoAsync(asset.uri)
        if (!info.exists || info.isDirectory || info.size > 5 * 1024 * 1024) throw new Error('Choose a photo smaller than 5 MB.')
        await FileSystem.makeDirectoryAsync(directory, { intermediates: true })
        const name = 'photo-' + Date.now() + '.jpg'
        next = directory + name; pendingFile = next
        await FileSystem.copyAsync({ from: asset.uri, to: next })
        if (!alive.current) { await FileSystem.deleteAsync(next, { idempotent: true }); return }
        await FileSystem.writeAsStringAsync(directory + 'current.txt', name)
        pendingFile = ''
      }
      if (alive.current) setUri(next)
      if (Platform.OS !== 'web' && uri && uri !== next && directory && uri.startsWith(directory)) await FileSystem.deleteAsync(uri, { idempotent: true }).catch(() => {})
    } catch (failure: any) {
      if (pendingFile) await FileSystem.deleteAsync(pendingFile, { idempotent: true }).catch(() => {})
      if (alive.current) setError(failure.message || 'Your photo could not be saved. Try again.')
    } finally { locked.current = false; if (alive.current) setBusy(false) }
  }
  async function remove() {
    if (locked.current) return
    locked.current = true; setBusy(true); setError('')
    try {
      if (Platform.OS === 'web') localStorage.removeItem(key)
      else if (directory) await FileSystem.deleteAsync(directory, { idempotent: true })
      if (alive.current) setUri('')
    } catch { if (alive.current) setError('Your photo could not be removed. Try again.') }
    finally { locked.current = false; if (alive.current) setBusy(false) }
  }
  return <Context.Provider value={{ uri, busy, error, choose, remove }}>{children}</Context.Provider>
}
