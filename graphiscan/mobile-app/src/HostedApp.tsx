import React, { createContext, useContext, useRef, useState } from 'react'
import { FlatList, Pressable, Text, View, useColorScheme, useWindowDimensions } from 'react-native'
import { NavigationContainer, DarkTheme, DefaultTheme, useNavigation } from '@react-navigation/native'
import { createNativeStackNavigator, type NativeStackNavigationProp } from '@react-navigation/native-stack'
import { createBottomTabNavigator, type BottomTabNavigationProp } from '@react-navigation/bottom-tabs'
import { SafeAreaProvider, SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { createHostedClient, type HostedClient } from '../../shared/hosted-client.mjs'
import { Body, Button, Heading, Notice, Screen, Status, styles, useColors } from './ui'
import { useRecords } from './use-records'
import { dateLabel, screeningType } from './core/presentation'
import { hostedPercent, modelLabel } from './core/hosted-presentation'
import {HostedImage,HostedReview,HostedUpload} from './HostedScreeningActions'
import SignInPanel from './SignInPanel'
import AccountSetup from './AccountSetup'
import HostedHome from './HostedHome'
import LoadingSkeleton from './LoadingSkeleton'
import SignOutAction from './SignOutAction'
import HostedStudents from './HostedStudents'
import HostedStudentEditor from './HostedStudentEditor'
import { AppBrand, Avatar, RecordValue, ScreeningRow, StudentRow, workspaceStyles } from './WorkspaceUI'

type Routes = { Main: undefined; Screening: { id: string }; History: { id: string }; Report: { id: string }; StudentEditor: {id?:string} }
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
  const {profile, request}=useHosted(), navigation=useNavigation<BottomTabNavigationProp<TabRoutes>>()
  const records=useRecords(async()=>{const [students,screenings]=await Promise.all([request('/students?limit=25',{envelope:true}),request('/screenings?limit=25',{envelope:true})]);return {students,screenings}},[request])
  return <HostedHome name={profile.full_name} role={profile.role} students={records.data?.students.data??[]} screenings={records.data?.screenings.data??[]}
    loading={records.loading} hasLoaded={records.data!==null} error={records.error} onStudents={()=>navigation.navigate('Students')} onResults={()=>navigation.navigate('Results')}
    onUpload={()=>navigation.navigate('Upload')} onRefresh={records.refresh} onRecord={id=>navigation.getParent<NativeStackNavigationProp<Routes>>()?.navigate('Screening',{id})}/>
}
function RecordList({ historyId }: { historyId?: string }) {
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  const {height:windowHeight}=useWindowDimensions(),[listHeight,setListHeight]=useState(0)
  const students=useRecords(()=>request('/students?limit=100',{envelope:true}),[request])
  const [cursor,setCursor]=useState<string|null>(null),[order,setOrder]=useState('newest')
  const path=historyId?'/students/'+encodeURIComponent(historyId)+'/history':'/screenings'
  const record=useRecords(()=>request(path+'?limit=25'+(historyId?'&order='+order:'')+(cursor?'&cursor='+encodeURIComponent(cursor):''),{envelope:true}),[request,path,cursor,order])
  function start(){setCursor(null);record.refresh()}
  return <Screen scroll={false}><FlatList data={record.data?.data??[]} keyExtractor={(row:any)=>row.result_id} contentContainerStyle={[styles.content,{gap:0}]}
    onLayout={event=>setListHeight(event.nativeEvent.layout.height)}
    refreshing={record.loading&&record.data!==null} onRefresh={start}
    ListHeaderComponent={historyId||profile.role==='parent'||record.error?<View style={{gap:16,paddingBottom:20}}>
      {profile.role==='parent'&&<Body muted>Only currently reviewed reports for your linked children are shown.</Body>}
      {historyId&&<Button label={order==='newest'?'Show oldest first':'Show newest first'} secondary onPress={()=>{setCursor(null);setOrder(order==='newest'?'oldest':'newest')}}/>}<Notice error message={record.error}/></View>:undefined}
    ListEmptyComponent={record.loading?<LoadingSkeleton fillHeight={listHeight||windowHeight}/>:!record.error?<Body>No screening records are available for your account.</Body>:undefined}
    renderItem={({item,index}:any)=>{const student=students.data?.data.find((student:any)=>student.student_id===item.student_id);return <ScreeningRow record={item} studentName={student?.full_name} grade={student?.grade_level} last={index===(record.data?.data.length??0)-1} onPress={()=>navigation.navigate('Screening',{id:item.result_id})}/>}}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary onPress={start}/>}</View>}/></Screen>
}
function Results(){return <RecordList/>}
function History({route}: {route:{params:{id:string}}}){return <RecordList historyId={route.params.id}/>}
function Students(){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  return <HostedStudents request={request} teacher={profile.role==='teacher'} onHistory={id=>navigation.navigate('History',{id})} onAdd={()=>navigation.navigate('StudentEditor',{})} onEdit={id=>navigation.navigate('StudentEditor',{id})}/>
}
function StudentEditor({route}:{route:{params:{id?:string}}}){
  const {request,profile,logout}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  return <HostedStudentEditor request={request} teacherId={profile.user_id} id={route.params.id} onHistory={id=>navigation.replace('History',{id})} onCancel={()=>navigation.goBack()} logout={logout}/>
}
function Detail({route,report=false}:{route:{params:{id:string}};report?:boolean}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors()
  const record=useRecords(()=>request((report?'/reports/':'/screenings/')+encodeURIComponent(route.params.id)),[request,route.params.id,report]),row=record.data
  const student=useRecords(()=>row?.student_id?request('/students/'+encodeURIComponent(row.student_id)):Promise.resolve(null),[request,row?.student_id])
  return <Screen>{record.loading&&!row&&<LoadingSkeleton kind="detail"/>}<Notice error message={record.error}/>{row&&<>
    <View style={{gap:8}}>{student.loading&&!student.data?<LoadingSkeleton kind="heading" label="Loading student details"/>:<Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{student.data?.full_name||'Student '+row.student_id}</Text>}<Body muted>{student.data?.grade_level?'Grade '+student.data.grade_level+' / ':''}{screeningType(report?row.report_type:row.report?.report_type)}</Body><Body muted>{dateLabel(row.date_generated)}</Body></View>
    <View style={[styles.panel,{borderWidth:0,backgroundColor:colors.surface}]}><View style={[styles.row,{flexWrap:'wrap'}]}><Heading>Model output</Heading><Status value={row.classification}/></View>
    <RecordValue label="Reported-class model score" value={hostedPercent(row.predicted_class_score)}/><RecordValue label="High Potential model score" value={hostedPercent(row.class_scores?.high_potential)}/>
    <Body muted>Model scores are not a clinical probability or diagnosis.</Body><View style={{borderTopWidth:1,borderTopColor:colors.border,paddingTop:16,gap:4}}><Body>{modelLabel(row.model.model_key)}</Body><Body muted>Version {row.model.model_version??'not recorded'}</Body></View>
    {row.provenance==='legacy_unverified'&&<Body muted>Historical model provenance has not been verified.</Body>}
    </View><View style={[styles.panel,{borderWidth:0,backgroundColor:colors.surface}]}><View style={[styles.row,{flexWrap:'wrap'}]}><Heading>Expert review</Heading><Status value={row.review.status}/></View><RecordValue label="Remarks" value={row.review.remarks||'Not recorded'}/><RecordValue label="Expert recommendation" value={row.review.expert_recommendation||'Not recorded'}/><RecordValue label="Follow-up needed" value={row.review.follow_up_needed===true?'Yes':row.review.follow_up_needed===false?'No':'Not recorded'}/>
    {row.review.validation_date&&<Body muted>Reviewed {dateLabel(row.review.validation_date)}</Body>}
    </View><HostedImage request={request} id={row.result_id}/>
    {!report&&profile.role==='expert'&&row.review.assigned_expert_id===profile.user_id&&<HostedReview request={request} id={row.result_id} review={row.review} onSaved={record.refresh}/>}
    {!report&&row.report?.report_id&&<Button label="Open report" secondary onPress={()=>navigation.navigate('Report',{id:row.report.report_id})}/>}
    <Button label="View student history" secondary onPress={()=>navigation.navigate('History',{id:row.student_id})}/></>}
    <Button label="Refresh record" secondary disabled={record.loading} onPress={record.refresh}/></Screen>
}
function Report({route}:{route:{params:{id:string}}}){return <Detail route={route} report/>}
function Profile(){
  const {profile,refresh,logout}=useHosted(),[error,setError]=useState(''),[busy,setBusy]=useState(false),c=useColors()
  async function update(){setBusy(true);setError('');try{await refresh()}catch(e:any){setError(e.message)}finally{setBusy(false)}}
  return <Screen><View style={{alignItems:'center',gap:14,paddingVertical:16}}><Avatar name={profile.full_name} size={72}/><Text accessibilityRole="header" style={[styles.title,{color:c.text,textAlign:'center'}]}>{profile.full_name}</Text></View>
    <View style={[styles.panel,{borderWidth:0,backgroundColor:c.surface}]}><RecordValue label="Account role" value={profile.role==='parent'?'Parent / Guardian':profile.role==='teacher'?'Teacher':'Expert'}/><View style={{borderTopWidth:1,borderTopColor:c.border,paddingTop:16}}><RecordValue label="Account status" value={profile.account_status==='active'?'Active':profile.account_status}/></View></View>
    <Notice error message={error}/><Button label={busy?'Refreshing...':'Refresh account'} secondary disabled={busy} onPress={update}/><SignOutAction disabled={busy} onSignOut={logout} onError={setError}/></Screen>
}
function Upload(){const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>();return <HostedUpload request={request} onComplete={id=>navigation.navigate('Screening',{id})}/>}
function Main(){
  const {profile}=useHosted(),colors=useColors(),insets=useSafeAreaInsets()
  const icons: Record<keyof TabRoutes,React.ComponentProps<typeof MaterialIcons>['name']>={Home:'home',Students:'groups',Results:'assignment',Upload:'upload-file',Profile:'person'}
  return <Tabs.Navigator screenOptions={({route,navigation})=>({headerShadowVisible:false,headerTitleStyle:{fontSize:18,fontWeight:'600'},headerTitle:route.name==='Home'?()=> <AppBrand/>:undefined,headerRight:route.name==='Home'?()=> <Pressable accessibilityRole="button" accessibilityLabel="Open profile" onPress={()=>navigation.navigate('Profile')} style={workspaceStyles.headerButton}><Avatar name={profile.full_name} size={36}/></Pressable>:undefined,tabBarActiveTintColor:colors.primary,tabBarInactiveTintColor:colors.muted,tabBarItemStyle:{marginHorizontal:3,borderRadius:12},tabBarStyle:{backgroundColor:colors.surface,borderTopColor:colors.border,height:74+insets.bottom,paddingTop:8,paddingBottom:Math.max(insets.bottom,10)},tabBarLabelStyle:{fontSize:12,lineHeight:16},tabBarIcon:({color,size,focused})=><View style={{width:56,height:32,borderRadius:16,alignItems:'center',justifyContent:'center',backgroundColor:focused?colors.soft:'transparent'}}><MaterialIcons name={icons[route.name]} color={color} size={size} accessible={false}/></View>})}>
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
      {profile.role==='teacher'&&<Stack.Screen name="StudentEditor" component={StudentEditor} options={({route})=>({title:route.params.id?'Edit student':'Add student'})}/>}
    </Stack.Navigator></Context.Provider>}
  </NavigationContainer>
}
export default function HostedApp(){return <SafeAreaProvider><HostedRoot/></SafeAreaProvider>}
