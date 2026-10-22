import React, { createContext, useContext, useRef, useState } from 'react'
import { FlatList, Pressable, Text, View, useColorScheme } from 'react-native'
import { NavigationContainer, DarkTheme, DefaultTheme, useNavigation } from '@react-navigation/native'
import { createNativeStackNavigator, type NativeStackNavigationProp } from '@react-navigation/native-stack'
import { createBottomTabNavigator, type BottomTabNavigationProp } from '@react-navigation/bottom-tabs'
import { SafeAreaProvider, SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { createHostedClient, type HostedClient } from '../../shared/hosted-client.mjs'
import { Body, Button, Heading, Loading, Notice, Screen, Status, styles, useColors } from './ui'
import { useRecords } from './use-records'
import { dateLabel, screeningType } from './core/presentation'
import { hostedPercent } from './core/hosted-presentation'
import {HostedImage,HostedReview,HostedUpload} from './HostedScreeningActions'
import SignInPanel from './SignInPanel'
import AccountSetup from './AccountSetup'

type Routes = { Main: undefined; Screening: { id: string }; History: { id: string }; Report: { id: string } }
type TabRoutes = { Home: undefined; Results: undefined; Students: undefined; Upload: undefined; Profile: undefined }
interface Profile { user_id: string; full_name: string; role: string; account_status: string; onboarding: { next_action: string } }
interface HostedSession { profile: Profile; request: HostedClient['request']; refresh: () => Promise<void>; logout: () => Promise<void> }
const Context = createContext<HostedSession | null>(null)
function useHosted() { const value = useContext(Context); if (!value) throw new Error('Sign in required.'); return value }
const Stack = createNativeStackNavigator<Routes>(), Tabs = createBottomTabNavigator<TabRoutes>()
const origin = process.env.EXPO_PUBLIC_HOSTED_API_ORIGIN || 'https://graphiscan-admin-api.onrender.com'

function HostedLogin({ login, notice }: { login: (email: string, password: string) => Promise<void>; notice: string }) {
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('')
  async function submit() { if(busy||!email.trim()||!password)return;setBusy(true);setError('');try{await login(email.trim().toLowerCase(),password)}catch(e){setError((e as Error).message)}finally{setPassword('');setBusy(false)} }
  return <SignInPanel email={email} password={password} busy={busy} error={error} notice={notice}
    onEmail={setEmail} onPassword={setPassword} onSubmit={submit}/>
}
function Home() {
  const {profile, request}=useHosted(), colors=useColors(), navigation=useNavigation<BottomTabNavigationProp<TabRoutes>>()
  const records=useRecords(async()=>{const [students,screenings]=await Promise.all([request('/students?limit=25',{envelope:true}),request('/screenings?limit=25',{envelope:true})]);return {students,screenings}},[request])
  const items=records.data?.screenings.data??[], students=records.data?.students.data??[]
  const roleName=profile.role==='expert'?'Expert':profile.role==='parent'?'Parent / Guardian':'Teacher'
  return <Screen><View style={{gap:4}}><Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{profile.full_name}</Text><Body muted>{roleName}</Body></View>
    {records.loading&&<Loading/>}<Notice error message={records.error}/>
    {!records.error&&<View style={styles.metricGrid}>{[{label:profile.role==='parent'?'Linked children loaded':'Students loaded',value:students.length},{label:profile.role==='expert'?'Pending reviews loaded':profile.role==='parent'?'Reviewed reports loaded':'Screenings loaded',value:profile.role==='expert'?items.filter((row:any)=>row.review.status==='Pending').length:items.length}].map(item=><View key={item.label} style={[styles.metric,{backgroundColor:colors.surface,borderColor:colors.border}]}><Text style={[styles.metricLabel,{color:colors.muted}]}>{item.label}</Text><Text style={[styles.metricValue,{color:colors.text}]}>{records.loading?'—':item.value}</Text></View>)}</View>}
    <View style={{gap:12}}>
      <Button label={profile.role==='expert'?'Open reviews':profile.role==='parent'?'View reviewed reports':'View screening results'} onPress={()=>navigation.navigate('Results')}/>
      <Button label={profile.role==='parent'?'View linked children':'View students'} secondary onPress={()=>navigation.navigate('Students')}/>
      {profile.role==='teacher'&&<Button label="Screen handwriting" secondary onPress={()=>navigation.navigate('Upload')}/>}</View>
    <Button label="Refresh" secondary disabled={records.loading} onPress={records.refresh}/>
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
    ListHeaderComponent={historyId||profile.role==='parent'||record.error?<View style={{gap:16}}>
      {profile.role==='parent'&&<Body muted>Only currently reviewed reports for your linked children are shown.</Body>}
      {historyId&&<Button label={order==='newest'?'Show oldest first':'Show newest first'} secondary onPress={()=>{setCursor(null);setOrder(order==='newest'?'oldest':'newest')}}/>}<Notice error message={record.error}/></View>:undefined}
    ListEmptyComponent={record.loading?<Loading/>:!record.error?<Body>No screening records are available for your account.</Body>:undefined}
    renderItem={({item}:any)=><Pressable accessibilityRole="button" accessibilityLabel={'Open screening '+item.result_id} onPress={()=>navigation.navigate('Screening',{id:item.result_id})} style={({pressed})=>[styles.listRow,{borderColor:colors.border,backgroundColor:colors.surface,opacity:pressed?.8:1}]}>
      <Heading>{screeningType(item.report?.report_type)}</Heading><Body muted>{dateLabel(item.date_generated)}</Body><Status value={item.classification}/><View style={styles.wrap}><Body muted>Expert review</Body><Status value={item.review.status}/></View></Pressable>}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary onPress={start}/>}</View>}/></Screen>
}
function Results(){return <RecordList/>}
function History({route}: {route:{params:{id:string}}}){return <RecordList historyId={route.params.id}/>}
function Students(){
  const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors(),[cursor,setCursor]=useState<string|null>(null)
  const record=useRecords(()=>request('/students?limit=25'+(cursor?'&cursor='+encodeURIComponent(cursor):''),{envelope:true}),[request,cursor])
  function start(){setCursor(null);record.refresh()}
  return <Screen scroll={false}><FlatList data={record.data?.data??[]} keyExtractor={(row:any)=>row.student_id} refreshing={record.loading} onRefresh={start} contentContainerStyle={styles.content}
    ListHeaderComponent={record.error?<Notice error message={record.error}/>:undefined}
    ListEmptyComponent={record.loading?<Loading/>:!record.error?<Body>No students are available for your account.</Body>:undefined}
    renderItem={({item}:any)=><Pressable accessibilityRole="button" accessibilityLabel={'View history for '+item.full_name} onPress={()=>navigation.navigate('History',{id:item.student_id})} style={({pressed})=>[styles.listRow,{borderColor:colors.border,backgroundColor:colors.surface,opacity:pressed?.8:1}]}><Heading>{item.full_name}</Heading><Body muted>Grade {item.grade_level}</Body><Text style={[styles.label,{color:colors.primary}]}>View history</Text></Pressable>}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary onPress={start}/>}</View>}/></Screen>
}
function Detail({route,report=false}:{route:{params:{id:string}};report?:boolean}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors()
  const record=useRecords(()=>request((report?'/reports/':'/screenings/')+encodeURIComponent(route.params.id)),[request,route.params.id,report]),row=record.data
  return <Screen>{record.loading&&<Loading/>}<Notice error message={record.error}/>{row&&<>
    <View style={{gap:8}}><Heading>{screeningType(report?row.report_type:row.report?.report_type)}</Heading><Body muted>{dateLabel(row.date_generated)}</Body></View>
    <View style={[styles.panel,{borderColor:colors.border,backgroundColor:colors.surface}]}><Heading>Model output</Heading><Status value={row.classification}/>
    <Body>Reported-class model score: {hostedPercent(row.predicted_class_score)}</Body><Body>High Potential model score: {hostedPercent(row.class_scores?.high_potential)}</Body>
    <Body muted>Model scores are not a clinical probability or diagnosis.</Body><Body>Model: {row.model.model_key??'Not recorded'}</Body><Body muted>Version {row.model.model_version??'not recorded'}</Body>
    {row.provenance==='legacy_unverified'&&<Body muted>Historical model provenance has not been verified.</Body>}
    </View><View style={[styles.panel,{borderColor:colors.border,backgroundColor:colors.surface}]}><Heading>Expert review</Heading><Status value={row.review.status}/><Body>Remarks: {row.review.remarks||'Not recorded'}</Body><Body>Expert recommendation: {row.review.expert_recommendation||'Not recorded'}</Body><Body>Follow-up needed: {row.review.follow_up_needed===true?'Yes':row.review.follow_up_needed===false?'No':'Not recorded'}</Body>
    {row.review.validation_date&&<Body muted>Reviewed {dateLabel(row.review.validation_date)}</Body>}
    </View><HostedImage request={request} id={row.result_id}/>
    {!report&&profile.role==='expert'&&row.review.assigned_expert_id===profile.user_id&&<HostedReview request={request} id={row.result_id} review={row.review} onSaved={record.refresh}/>}
    {!report&&row.report?.report_id&&<Button label="Open report" secondary onPress={()=>navigation.navigate('Report',{id:row.report.report_id})}/>}
    <Button label="View student history" secondary onPress={()=>navigation.navigate('History',{id:row.student_id})}/></>}
    <Button label="Refresh record" secondary disabled={record.loading} onPress={record.refresh}/></Screen>
}
function Report({route}:{route:{params:{id:string}}}){return <Detail route={route} report/>}
function Profile(){const {profile,refresh,logout}=useHosted(),[error,setError]=useState('');return <Screen><Heading>{profile.full_name}</Heading><Body>Role: {profile.role}</Body><Body>Status: {profile.account_status}</Body><Notice error message={error}/><Button label="Refresh account" secondary onPress={()=>refresh().catch(e=>setError(e.message))}/><Button label="Sign out" onPress={()=>logout().catch(e=>setError(e.message))}/></Screen>}
function Upload(){const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>();return <HostedUpload request={request} onComplete={id=>navigation.navigate('Screening',{id})}/>}
function Main(){
  const {profile}=useHosted(),colors=useColors(),insets=useSafeAreaInsets()
  const icons: Record<keyof TabRoutes,React.ComponentProps<typeof MaterialIcons>['name']>={Home:'home',Students:'groups',Results:'assignment',Upload:'upload-file',Profile:'person'}
  return <Tabs.Navigator screenOptions={({route})=>({headerShadowVisible:false,headerTitleStyle:{fontSize:18,fontWeight:'600'},tabBarActiveTintColor:colors.primary,tabBarInactiveTintColor:colors.muted,tabBarStyle:{backgroundColor:colors.surface,borderTopColor:colors.border,height:64+insets.bottom,paddingTop:6,paddingBottom:Math.max(insets.bottom,8)},tabBarLabelStyle:{fontSize:12,lineHeight:16},tabBarIcon:({color,size})=><MaterialIcons name={icons[route.name]} color={color} size={size}/>})}>
    <Tabs.Screen name="Home" component={Home} options={{title:'GraphiScan',tabBarLabel:'Home',tabBarAccessibilityLabel:'Home'}}/>
    <Tabs.Screen name="Students" component={Students} options={{title:profile.role==='parent'?'Children':'Students',tabBarAccessibilityLabel:profile.role==='parent'?'Children':'Students'}}/>
    {profile.role==='teacher'&&<Tabs.Screen name="Upload" component={Upload} options={{title:'Screen handwriting',tabBarLabel:'Screen',tabBarAccessibilityLabel:'Screen handwriting'}}/>}
    <Tabs.Screen name="Results" component={Results} options={{title:profile.role==='expert'?'Reviews':profile.role==='parent'?'Reports':'Results',tabBarAccessibilityLabel:profile.role==='expert'?'Reviews':profile.role==='parent'?'Reports':'Results'}}/>
    <Tabs.Screen name="Profile" component={Profile} options={{tabBarAccessibilityLabel:'Profile'}}/>
  </Tabs.Navigator>
}

function HostedRoot(){
  const client=useRef<HostedClient|null>(null);if(!client.current)client.current=createHostedClient(origin)
  const api=client.current,[profile,setProfile]=useState<Profile|null>(null),[signInNotice,setSignInNotice]=useState(''),dark=useColorScheme()==='dark',colors=useColors()
  async function logout(){setProfile(null);setSignInNotice('');try{await api.logout()}catch{setSignInNotice('You are signed out on this device. The server could not confirm sign-out.')}}
  async function refresh(){
    try{const next=await api.request('/me');if(!['teacher','expert','parent'].includes(next.role)){await logout().catch(()=>{});throw new Error('Use an issued teacher, expert or parent account.')}setProfile(next)}
    catch(e:any){if(e.status===401){api.clear();setProfile(null)}throw e}
  }
  async function login(email:string,password:string){setSignInNotice('');try{await api.login(email,password);await refresh()}catch(e){await logout().catch(()=>{});throw e}}
  // Stable identity is needed by focus effects; no bearer/refresh token is exposed.
  const request=useRef<HostedClient['request']>(async(path,options)=>{
    try{return await api.request(path,options)}catch(e:any){if(e.status===401){api.clear();setProfile(null)}else if(['PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(e.code)){await refresh().catch(()=>{})}throw e}
  }).current
  const ready=profile?.onboarding.next_action==='ready'
  const base=dark?DarkTheme:DefaultTheme
  return <NavigationContainer theme={{...base,colors:{...base.colors,primary:colors.primary,background:colors.bg,card:colors.surface,text:colors.text,border:colors.border}}}><StatusBar style={dark?'light':'dark'}/>
    {!profile?<HostedLogin login={login} notice={signInNotice}/>:!ready?<SafeAreaView edges={['top']} style={{flex:1,backgroundColor:colors.bg}}><AccountSetup key={profile.user_id+profile.onboarding.next_action} client={api} action={profile.onboarding.next_action} refresh={refresh} logout={logout} passwordChanged={()=>{setProfile(null);setSignInNotice('Password updated. Sign in with your new password.')}}/></SafeAreaView>:<Context.Provider value={{profile,request,refresh,logout}}><Stack.Navigator key={profile.user_id} screenOptions={{headerShadowVisible:false,headerTitleStyle:{fontSize:18,fontWeight:'600'}}}>
      <Stack.Screen name="Main" component={Main} options={{headerShown:false}}/><Stack.Screen name="Screening" component={Detail} options={{title:'Screening result'}}/>
      <Stack.Screen name="History" component={History} options={{title:'Student history'}}/><Stack.Screen name="Report" component={Report} options={{title:'Screening report'}}/>
    </Stack.Navigator></Context.Provider>}
  </NavigationContainer>
}
export default function HostedApp(){return <SafeAreaProvider><HostedRoot/></SafeAreaProvider>}
