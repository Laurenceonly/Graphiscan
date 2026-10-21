import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { FlatList, Platform, Pressable, Switch, Text, View, useColorScheme } from 'react-native'
import { NavigationContainer, DarkTheme, DefaultTheme, useNavigation } from '@react-navigation/native'
import { createNativeStackNavigator, type NativeStackNavigationProp } from '@react-navigation/native-stack'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { createHostedClient, type HostedClient } from '../../shared/hosted-client.mjs'
import { Body, Button, Field, Heading, Loading, Notice, Screen, Status, styles, useColors } from './ui'
import { useRecords } from './use-records'
import { dateLabel, screeningType } from './core/presentation'
import { hostedPercent } from './core/hosted-presentation'
import {HostedImage,HostedReview,HostedUpload} from './HostedScreeningActions'
import SignInPanel from './SignInPanel'

type Routes = { Main: undefined; Screening: { id: string }; History: { id: string }; Report: { id: string } }
interface Profile { user_id: string; full_name: string; role: string; account_status: string; onboarding: { next_action: string } }
interface HostedSession { profile: Profile; request: HostedClient['request']; refresh: () => Promise<void>; logout: () => Promise<void> }
const Context = createContext<HostedSession | null>(null)
function useHosted() { const value = useContext(Context); if (!value) throw new Error('Sign in required.'); return value }
const Stack = createNativeStackNavigator<Routes>(), Tabs = createBottomTabNavigator()
const origin = process.env.EXPO_PUBLIC_HOSTED_API_ORIGIN || (Platform.OS === 'android' ? 'http://10.0.2.2:5002' : 'http://127.0.0.1:5002')

function HostedLogin({ login }: { login: (email: string, password: string) => Promise<void> }) {
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('')
  async function submit() { if(busy)return;setBusy(true);setError('');try{await login(email.trim().toLowerCase(),password)}catch(e){setError((e as Error).message)}finally{setPassword('');setBusy(false)} }
  return <SignInPanel email={email} password={password} busy={busy} error={error}
    onEmail={setEmail} onPassword={setPassword} onSubmit={submit}/>
}
function Onboarding({ client, profile, refresh, logout }: { client: HostedClient; profile: Profile; refresh: () => Promise<void>; logout: () => Promise<void> }) {
  const action=profile.onboarding.next_action
  const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirm,setConfirm]=useState(''),[accepted,setAccepted]=useState(false)
  const [notice,setNotice]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[loading,setLoading]=useState(false),[attempt,setAttempt]=useState(0)
  const required=action==='accept_privacy'
  useEffect(()=>{
    let alive=true;setNotice(null);setAccepted(false)
    if(required){setLoading(true);client.request('/privacy-agreement').then(value=>{if(alive)setNotice(value)}).catch(e=>{if(alive)setError(e.message)}).finally(()=>{if(alive)setLoading(false)})}
    return()=>{alive=false}
  },[client,action,attempt])
  const agreement=notice
  async function submit() {
    if(busy)return;setBusy(true);setError('')
    try {
      if(action==='change_password') {
        if(password!==confirm)throw new Error('The new passwords do not match.')
        await client.request('/me/password',{method:'POST',body:{current_password:current,new_password:password,confirm_password:confirm}})
        client.clear();await logout()
      } else if(required&&accepted&&agreement) {
        await client.request('/me/privacy-acceptance',{method:'POST',body:{agreement_version:agreement.version,accepted:true}})
        await refresh()
      }
    } catch(e:any) {
      setError(e.message)
      if(e.code==='AGREEMENT_CHANGED'){setAccepted(false);setNotice(null);setAttempt(value=>value+1);await refresh().catch(()=>{})}
      if(e.code==='PASSWORD_CHANGE_RECOVERY_REQUIRED'||e.status===401)await logout().catch(()=>{})
    } finally{setCurrent('');setPassword('');setConfirm('');setBusy(false)}
  }
  return <Screen><Heading>{action==='change_password'?'Change your temporary password':required?'Read the privacy agreement':'Account access unavailable'}</Heading>
    {action==='change_password'?<><Field label="Current password" value={current} onChangeText={setCurrent} secureTextEntry editable={!busy} autoCapitalize="none" />
      <Field label="New password" value={password} onChangeText={setPassword} secureTextEntry editable={!busy} autoCapitalize="none" />
      <Field label="Confirm new password" value={confirm} onChangeText={setConfirm} secureTextEntry editable={!busy} autoCapitalize="none" />
      <Body muted>Use at least eight characters, including uppercase, lowercase, a number and a symbol. Sign in again after saving.</Body></>:required?<>
      {loading&&<Loading/>}
      {agreement&&<><Heading>{agreement.title}</Heading><Body>{agreement.content}</Body><Body muted>Version: {agreement.version}</Body>
        <View style={styles.row}><Body>I agree to this version of the notice.</Body><Switch accessibilityLabel="I agree to this version of the notice" value={accepted} onValueChange={setAccepted} disabled={busy}/></View></>}
    </>:<Body>The current agreement is unavailable. Contact your project administrator.</Body>}
    <Notice error message={error}/>{(action==='change_password'||required)&&<Button label={busy?'Saving...':required?'Accept and continue':'Save password'} onPress={submit} disabled={busy||(required&&(!accepted||!agreement))}/>}
    <Button label="Refresh account" secondary disabled={busy} onPress={()=>refresh().catch(e=>setError(e.message))}/><Button label="Sign out" secondary disabled={busy} onPress={()=>logout().catch(e=>setError(e.message))}/>
  </Screen>
}

function RecordList({ historyId }: { historyId?: string }) {
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors()
  const [cursor,setCursor]=useState<string|null>(null),[order,setOrder]=useState('newest')
  const path=historyId?'/students/'+encodeURIComponent(historyId)+'/history':'/screenings'
  const record=useRecords(()=>request(path+'?limit=25'+(historyId?'&order='+order:'')+(cursor?'&cursor='+encodeURIComponent(cursor):''),{envelope:true}),[request,path,cursor,order])
  function start(){setCursor(null);record.refresh()}
  return <Screen scroll={false}><FlatList data={record.data?.data??[]} keyExtractor={(row:any)=>row.result_id} contentContainerStyle={styles.content}
    refreshing={record.loading} onRefresh={start}
    ListHeaderComponent={<View style={{gap:16}}><Heading>{historyId?'Screening history':profile.role==='parent'?'Reviewed reports':'Screening results'}</Heading>
      {profile.role==='parent'&&<Body muted>Only currently reviewed reports for your linked children are shown.</Body>}
      {historyId&&<Button label={order==='newest'?'Show oldest first':'Show newest first'} secondary onPress={()=>{setCursor(null);setOrder(order==='newest'?'oldest':'newest')}}/>}<Notice error message={record.error}/></View>}
    ListEmptyComponent={!record.loading&&!record.error?<Body>No accessible screening records.</Body>:undefined}
    renderItem={({item}:any)=><Pressable accessibilityRole="button" accessibilityLabel={'Open screening '+item.result_id} onPress={()=>navigation.navigate('Screening',{id:item.result_id})} style={[styles.listRow,{borderColor:colors.border}]}>
      <Heading>Screening {item.result_id}</Heading><Body>{screeningType(item.report?.report_type)}</Body><Body muted>{dateLabel(item.date_generated)}</Body><Status value={item.classification}/><Status value={item.review.status}/></Pressable>}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary onPress={start}/>}</View>}/></Screen>
}
function Results(){return <RecordList/>}
function History({route}: {route:{params:{id:string}}}){return <RecordList historyId={route.params.id}/>}
function Students(){
  const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors(),[cursor,setCursor]=useState<string|null>(null)
  const record=useRecords(()=>request('/students?limit=25'+(cursor?'&cursor='+encodeURIComponent(cursor):''),{envelope:true}),[request,cursor])
  function start(){setCursor(null);record.refresh()}
  return <Screen scroll={false}><FlatList data={record.data?.data??[]} keyExtractor={(row:any)=>row.student_id} refreshing={record.loading} onRefresh={start} contentContainerStyle={styles.content}
    ListHeaderComponent={<View style={{gap:16}}><Heading>Students</Heading><Notice error message={record.error}/></View>}
    ListEmptyComponent={!record.loading&&!record.error?<Body>No students are available for your account.</Body>:undefined}
    renderItem={({item}:any)=><Pressable accessibilityRole="button" onPress={()=>navigation.navigate('History',{id:item.student_id})} style={[styles.listRow,{borderColor:colors.border}]}><Heading>{item.full_name}</Heading><Body>Grade {item.grade_level}</Body><Body muted>View screening history</Body></Pressable>}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary onPress={start}/>}</View>}/></Screen>
}
function Detail({route,report=false}:{route:{params:{id:string}};report?:boolean}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  const record=useRecords(()=>request((report?'/reports/':'/screenings/')+encodeURIComponent(route.params.id)),[request,route.params.id,report]),row=record.data
  return <Screen>{record.loading&&<Loading/>}<Notice error message={record.error}/>{row&&<><Heading>{report?'Screening report':'Screening result'}</Heading>
    <Body>{screeningType(report?row.report_type:row.report?.report_type)}</Body><Body muted>{dateLabel(row.date_generated)}</Body><Status value={row.classification}/>
    <Body>Reported-class model score: {hostedPercent(row.predicted_class_score)}</Body><Body>High Potential model score: {hostedPercent(row.class_scores?.high_potential)}</Body>
    <Body muted>Model scores are not a clinical probability or diagnosis.</Body><Body>Model: {row.model.model_key??'Not recorded'} · Version {row.model.model_version??'not recorded'}</Body>
    {row.provenance==='legacy_unverified'&&<Body muted>Historical model provenance has not been verified.</Body>}
    <Heading>Expert review</Heading><Status value={row.review.status}/><Body>Remarks: {row.review.remarks||'Not recorded'}</Body><Body>Expert recommendation: {row.review.expert_recommendation||'Not recorded'}</Body><Body>Follow-up needed: {row.review.follow_up_needed?'Yes':'No'}</Body>
    {row.review.validation_date&&<Body muted>Reviewed {dateLabel(row.review.validation_date)}</Body>}
    <HostedImage request={request} id={row.result_id}/>
    {!report&&profile.role==='expert'&&row.review.assigned_expert_id===profile.user_id&&<HostedReview request={request} id={row.result_id} review={row.review} onSaved={record.refresh}/>}
    {!report&&<Button label="Open report" secondary onPress={()=>navigation.navigate('Report',{id:row.report.report_id})}/>}
    <Button label="View student history" secondary onPress={()=>navigation.navigate('History',{id:row.student_id})}/></>}
    <Button label="Refresh record" secondary disabled={record.loading} onPress={record.refresh}/></Screen>
}
function Report({route}:{route:{params:{id:string}}}){return <Detail route={route} report/>}
function Profile(){const {profile,refresh,logout}=useHosted(),[error,setError]=useState('');return <Screen><Heading>{profile.full_name}</Heading><Body>Role: {profile.role}</Body><Body>Status: {profile.account_status}</Body><Notice error message={error}/><Button label="Refresh account" secondary onPress={()=>refresh().catch(e=>setError(e.message))}/><Button label="Sign out" onPress={()=>logout().catch(e=>setError(e.message))}/></Screen>}
function Upload(){const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>();return <HostedUpload request={request} onComplete={id=>navigation.navigate('Screening',{id})}/>}
function Main(){const {profile}=useHosted();return <Tabs.Navigator screenOptions={({route})=>({tabBarIcon:({color,size})=><MaterialIcons name={route.name==='Students'?'groups':route.name==='Profile'?'person':route.name==='Upload'?'upload-file':'assignment'} color={color} size={size}/>})}><Tabs.Screen name="Results" component={Results}/><Tabs.Screen name="Students" component={Students}/>{profile.role==='teacher'&&<Tabs.Screen name="Upload" component={Upload}/>}<Tabs.Screen name="Profile" component={Profile}/></Tabs.Navigator>}

function HostedRoot(){
  const client=useRef<HostedClient|null>(null);if(!client.current)client.current=createHostedClient(origin)
  const api=client.current,[profile,setProfile]=useState<Profile|null>(null),dark=useColorScheme()==='dark'
  async function logout(){try{await api.logout()}finally{setProfile(null)}}
  async function refresh(){
    try{const next=await api.request('/me');if(!['teacher','expert','parent'].includes(next.role)){await logout().catch(()=>{});throw new Error('Use an issued teacher, expert or parent account.')}setProfile(next)}
    catch(e:any){if(e.status===401){api.clear();setProfile(null)}throw e}
  }
  async function login(email:string,password:string){try{await api.login(email,password);await refresh()}catch(e){await logout().catch(()=>{});throw e}}
  // Stable identity is needed by focus effects; no bearer/refresh token is exposed.
  const request=useRef<HostedClient['request']>(async(path,options)=>{
    try{return await api.request(path,options)}catch(e:any){if(e.status===401){api.clear();setProfile(null)}else if(['PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(e.code)){await refresh().catch(()=>{})}throw e}
  }).current
  const ready=profile?.onboarding.next_action==='ready'
  return <NavigationContainer theme={dark?DarkTheme:DefaultTheme}><StatusBar style={dark?'light':'dark'}/>
    {!profile?<HostedLogin login={login}/>:!ready?<SafeAreaView edges={['top']} style={{flex:1}}><Onboarding client={api} profile={profile} refresh={refresh} logout={logout}/></SafeAreaView>:<Context.Provider value={{profile,request,refresh,logout}}><Stack.Navigator>
      <Stack.Screen name="Main" component={Main} options={{headerShown:false}}/><Stack.Screen name="Screening" component={Detail} options={{title:'Screening result'}}/>
      <Stack.Screen name="History" component={History} options={{title:'Student history'}}/><Stack.Screen name="Report" component={Report} options={{title:'Screening report'}}/>
    </Stack.Navigator></Context.Provider>}
  </NavigationContainer>
}
export default function HostedApp(){return <SafeAreaProvider><HostedRoot/></SafeAreaProvider>}
