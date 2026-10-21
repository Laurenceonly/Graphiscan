import React, { useEffect, useState } from 'react'
import { Image, View } from 'react-native'
import { useNavigation } from '@react-navigation/native'
import type { NativeStackNavigationProp } from '@react-navigation/native-stack'
import type { RootRoutes } from '../navigation-types'
import { useSession } from '../session'
import { useRecords } from '../use-records'
import { legacyPercent, dateLabel, screeningType } from '../core/presentation'
import { exportImage } from '../export-image'
import { Body, Button, Field, Heading, Loading, Notice, Screen, Status, styles } from '../ui'

export function ResultScreen({ route }: { route: { params: { id: string } } }) {
  const { api, user } = useSession(), navigation = useNavigation<NativeStackNavigationProp<RootRoutes>>()
  const record = useRecords(() => api.result(user!.role, route.params.id), [api, user!.role, route.params.id])
  const [image, setImage] = useState(''), [imageError, setImageError] = useState(''), [imageBusy, setImageBusy] = useState(false)
  const [review, setReview] = useState('Validated'), [remarks, setRemarks] = useState(''), [recommendation, setRecommendation] = useState(''), [followUp, setFollowUp] = useState('No')
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const result = record.data
  useEffect(() => {
    setImage(''); setImageError('')
    if (result) { setReview(result.validation_status === 'Flagged' ? 'Flagged' : 'Validated'); setRemarks(result.remarks || ''); setRecommendation(result.expert_recommendation || ''); setFollowUp(result.follow_up_needed === 'Yes' ? 'Yes' : 'No') }
  }, [result])
  async function loadImage() {
    if (imageBusy) return
    setImageBusy(true); setImageError('')
    try {
      const blob = await api.image(route.params.id)
      const uri = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Unable to display this image.')); reader.readAsDataURL(blob) })
      setImage(uri)
    } catch (e) { setImageError((e as Error).message) }
    finally { setImageBusy(false) }
  }
  async function saveReview() {
    if (busy || user!.role !== 'expert') return
    if (!remarks.trim() || !recommendation.trim()) { setError('Enter review remarks and your recommendation.'); return }
    setBusy(true); setError(''); setMessage('')
    try {
      await api.request('/expert/results/' + encodeURIComponent(route.params.id) + '/validate', { method: 'POST', body: { validation_status: review, remarks: remarks.trim(), expert_recommendation: recommendation.trim(), follow_up_needed: followUp } })
      setMessage('Review saved.'); record.refresh()
    } catch (e) { setError((e as Error).message + ' Refresh the record before resubmitting if the connection was interrupted.') }
    finally { setBusy(false) }
  }
  async function saveImage() {
    if (imageBusy) return
    setImageBusy(true); setImageError('')
    try { await exportImage(await api.image(route.params.id)) }
    catch (e) { setImageError((e as Error).message) }
    finally { setImageBusy(false) }
  }
  return <Screen>{record.loading && <Loading />}<Notice error message={record.error} />
    {result && <><Heading>{result.student_name}</Heading><Body muted>{dateLabel(result.date_generated)} · {result.grade_level || 'Grade not recorded'}</Body>
      <Body>{screeningType(result.report_type)}</Body><Status value={result.classification} /><Body>Reported-class model score: {legacyPercent(result.confidence_score)}</Body>
      <Body>High Potential model score: {legacyPercent(result.dysgraphia_probability)}</Body>
      <Body muted>These are model scores, not a clinical probability or diagnosis.</Body><Status value={result.validation_status} />
      <Button label={imageBusy ? 'Loading image…' : image ? 'Reload handwriting image' : 'View handwriting image'} icon="image" secondary disabled={imageBusy} onPress={loadImage} />
      <Notice error message={imageError} />{image ? <Image source={{ uri: image }} accessibilityLabel="Handwriting sample for this screening" resizeMode="contain" style={{ width: '100%', height: 320 }} /> : null}
      <Button label="Save handwriting image" secondary disabled={imageBusy} onPress={saveImage} />
      <Heading>Expert review</Heading><Body>Reviewed by: {result.expert_name || 'Not yet reviewed'}</Body>
      <Body>Remarks: {result.remarks || 'Not recorded'}</Body><Body>Recommendation: {result.expert_recommendation || 'Not recorded'}</Body><Body>Follow-up needed: {result.follow_up_needed || 'Not recorded'}</Body>
      {result.student_id && <Button label="View student progress" secondary onPress={() => navigation.navigate('Progress', { id: String(result.student_id) })} />}
      {user!.role === 'expert' && <View style={{ gap: 16 }}><Heading>Submit validation</Heading>
        <View style={styles.wrap}>{['Validated', 'Flagged'].map(value => <Button key={value} label={value} secondary={review !== value} disabled={busy} onPress={() => setReview(value)} />)}</View>
        <Field label="Review remarks" multiline value={remarks} onChangeText={setRemarks} editable={!busy} />
        <Field label="Expert recommendation" multiline value={recommendation} onChangeText={setRecommendation} editable={!busy} />
        <Body>Follow-up needed</Body><View style={styles.wrap}>{['Yes', 'No'].map(value => <Button key={value} label={value} secondary={followUp !== value} disabled={busy} onPress={() => setFollowUp(value)} />)}</View>
        <Notice error message={error} /><Notice message={message} /><Button label={busy ? 'Saving review…' : 'Save validation'} disabled={busy} onPress={saveReview} />
      </View>}
    </>}
    <Button label="Refresh record" secondary disabled={record.loading || busy} onPress={record.refresh} />
  </Screen>
}
