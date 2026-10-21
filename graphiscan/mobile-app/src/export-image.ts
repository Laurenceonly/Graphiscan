import { Platform } from 'react-native'
import * as FileSystem from 'expo-file-system/legacy'
import * as Sharing from 'expo-sharing'

export async function exportImage(blob: Blob) {
  const extension = blob.type === 'image/png' ? 'png' : 'jpg'
  if (Platform.OS === 'web') {
    const uri = URL.createObjectURL(blob)
    try { const anchor = document.createElement('a'); anchor.href = uri; anchor.download = 'handwriting.' + extension; anchor.click() }
    finally { setTimeout(() => URL.revokeObjectURL(uri), 1000) }
    return
  }
  if (!FileSystem.cacheDirectory || !await Sharing.isAvailableAsync()) throw new Error('File sharing is unavailable on this device.')
  const data = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.onerror = () => reject(new Error('Unable to prepare the image.')); reader.readAsDataURL(blob) })
  const uri = FileSystem.cacheDirectory + 'handwriting-' + Date.now() + '.' + extension
  try {
    await FileSystem.writeAsStringAsync(uri, data, { encoding: FileSystem.EncodingType.Base64 })
    await Sharing.shareAsync(uri, { mimeType: blob.type, dialogTitle: 'Save handwriting image' })
  } finally { await FileSystem.deleteAsync(uri, { idempotent: true }) }
}
