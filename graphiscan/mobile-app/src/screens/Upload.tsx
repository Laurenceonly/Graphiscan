import React, { useState } from 'react'
import { Image, Platform, View } from 'react-native'
import * as ImagePicker from 'expo-image-picker'
import * as FileSystem from 'expo-file-system/legacy'
import { useNavigation } from '@react-navigation/native'
import type { NativeStackNavigationProp } from '@react-navigation/native-stack'
import type { RootRoutes } from '../navigation-types'
import { useSession } from '../session'
import { useRecords } from '../use-records'
import { Body, Button, Heading, Loading, Notice, Screen, styles } from '../ui'

export function UploadScreen() {
  const { api } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>()
  const students = useRecords(() => api.students(), [api])
  const [student, setStudent] = useState<number | null>(null), [asset, setAsset] = useState<ImagePicker.ImagePickerAsset | null>(null)
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [uncertain, setUncertain] = useState(false)
  async function pick(camera: boolean) {
    setError('')
    try {
      const permission = camera ? await ImagePicker.requestCameraPermissionsAsync() : await ImagePicker.requestMediaLibraryPermissionsAsync()
      if (!permission.granted) { setError('Allow access in device settings to select a handwriting image.'); return }
      const result = camera ? await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 1 }) : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 1 })
      if (result.canceled) return
      const selected = result.assets[0]
      if (selected.fileSize && selected.fileSize > 10 * 1024 * 1024) throw new Error('Choose an image smaller than 10 MB.')
      if (selected.mimeType && !['image/jpeg', 'image/png'].includes(selected.mimeType)) throw new Error('Choose a JPG or PNG image.')
      setAsset(selected)
    } catch (e) { setError((e as Error).message) }
  }
  async function upload() {
    if (busy || uncertain || !asset || !student) return
    setBusy(true); setError('')
    let submitted = false
    try {
      const form = new FormData(); form.append('student_id', String(student))
      const name = asset.fileName || (asset.mimeType === 'image/png' ? 'handwriting.png' : 'handwriting.jpg')
      if (Platform.OS === 'web') {
        const file = asset.file ?? await (await fetch(asset.uri)).blob()
        if (file.size > 10 * 1024 * 1024) throw new Error('Choose an image smaller than 10 MB.')
        form.append('handwriting_image', file, name)
      } else {
        const file = await FileSystem.getInfoAsync(asset.uri)
        if (!file.exists || file.isDirectory) throw new Error('Select the handwriting image again.')
        if (file.size > 10 * 1024 * 1024) throw new Error('Choose an image smaller than 10 MB.')
        form.append('handwriting_image', { uri: asset.uri, name, type: asset.mimeType || 'image/jpeg' } as any)
      }
      submitted = true
      const result = await api.request('/teacher/upload', { method: 'POST', form, timeout: 120000 })
      setAsset(null); navigation.navigate('Result', { id: String(result.result_id) })
    } catch (e) { setUncertain(submitted); setError((e as Error).message + (submitted ? ' Check Results before another upload: the server may have received this sample.' : '')) }
    finally { setBusy(false) }
  }
  return <Screen><Heading>Upload handwriting</Heading><Body>Select the student and a clear JPG or PNG image, up to 10 MB.</Body>
    {students.loading && <Loading />}<Notice error message={students.error} />
    {!students.loading && students.data?.length === 0 && <Body>Add a student before uploading a sample.</Body>}
    <View style={{ gap: 10 }}>{(students.data ?? []).map(row => <Button key={row.student_id} label={row.fullname + ' · ' + row.grade_level} secondary={student !== row.student_id} disabled={busy} onPress={() => setStudent(row.student_id)} />)}</View>
    <View style={styles.wrap}><Button label="Choose image" icon="photo-library" secondary disabled={busy} onPress={() => pick(false)} /><Button label="Use camera" icon="photo-camera" secondary disabled={busy} onPress={() => pick(true)} /></View>
    {asset && <Image source={{ uri: asset.uri }} accessibilityLabel="Selected handwriting sample" resizeMode="contain" style={{ width: '100%', height: 280 }} />}
    <Body muted>The current screening model returns Normal or High Potential. Expert review is required; screening does not establish a diagnosis.</Body>
    <Notice error message={error} /><Button label={busy ? 'Screening image…' : 'Submit for screening'} disabled={busy || !asset || !student || uncertain} onPress={upload} />
    {uncertain && <Button label="I checked Results; prepare another upload" secondary onPress={() => { setAsset(null); setUncertain(false); setError('') }} />}
  </Screen>
}
