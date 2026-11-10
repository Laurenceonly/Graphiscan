import React, { createContext, useContext, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useReducedMotion } from 'react-native-reanimated'
import { ActivityIndicator, FlatList, Keyboard, Platform, Pressable, Text, View, useWindowDimensions } from 'react-native'
import * as FileSystem from 'expo-file-system/legacy'
import {createNativeUploadFetch} from './core/native-upload'
import { NavigationContainer, DefaultTheme, useNavigation, type NavigatorScreenParams } from '@react-navigation/native'
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
import QuickFilters from './QuickFilters'
import HostedStudentEditor from './HostedStudentEditor'
import HostedStudentDetails from './HostedStudentDetails'
import HostedFinalReport from './HostedFinalReport'
import { ProfilePhotoProvider, useProfilePhoto } from './ProfilePhoto'
import { ProfileSchoolsProvider, useProfileSchools } from './ProfileSchools'
import { mobileSessionStore } from './mobile-session-store'
import { AppBrand, Avatar, HistoryRow, RecordValue, ScreeningRow, workspaceStyles } from './WorkspaceUI'

type Routes = { Main: NavigatorScreenParams<TabRoutes>|undefined; Screening: { id: string }; History: { id: string }; Report: { id: string }; FinalReport: {id:string}; StudentEditor: {id?:string}; StudentDetails: {id:string} }
type TabRoutes = { Home: undefined; Results: undefined; Students: undefined; Upload: undefined; Profile: undefined }
interface Profile { user_id: string; full_name: string; role: string; account_status: string; school_ids: string[]; onboarding: { next_action: string } }
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
  const colors=useColors()
  const {height:windowHeight}=useWindowDimensions(),[listHeight,setListHeight]=useState(0)
  const students=useRecords(()=>request('/students?limit=100',{envelope:true}),[request])
  const historyStudent=useRecords(()=>historyId?request('/students/'+encodeURIComponent(historyId)):Promise.resolve(null),[request,historyId])
  const [cursor,setCursor]=useState<string|null>(null),[order,setOrder]=useState('newest')
  const [reviewFilter,setReviewFilter]=useState('All')
  const statusFiltersVisible=['teacher','expert'].includes(profile.role)&&!historyId
  const statusFilter=statusFiltersVisible&&reviewFilter!=='All'?reviewFilter:''
  const path=historyId?'/students/'+encodeURIComponent(historyId)+'/history':'/screenings'
  const record=useRecords(()=>request(path+'?limit=25'+(historyId?'&order='+order:'')+(statusFilter?'&validation_status='+encodeURIComponent(statusFilter):'')+(cursor?'&cursor='+encodeURIComponent(cursor):''),{envelope:true}),[request,path,cursor,order,statusFilter])
  function start(){setCursor(null);if(!cursor)record.refresh()}
  return <Screen scroll={false}><FlatList data={record.data?.data??[]} keyExtractor={(row:any)=>row.result_id} contentContainerStyle={[styles.content,{gap:0}]}
    onLayout={event=>setListHeight(event.nativeEvent.layout.height)}
    refreshing={record.loading&&record.data!==null} onRefresh={start}
    ListHeaderComponent={historyId||statusFiltersVisible||profile.role==='parent'||record.error?<View style={{gap:16,paddingBottom:20}}>
      {statusFiltersVisible&&<QuickFilters label="Review status" hideLabel value={reviewFilter} options={['All','Pending','Flagged','Validated'].map(value=>({value,label:value}))} onChange={value=>{setCursor(null);setReviewFilter(value)}}/>}
      {profile.role==='parent'&&<Body muted>Only currently reviewed reports for your linked children are shown.</Body>}
      {historyId&&<><View style={{gap:4}}>{historyStudent.loading&&!historyStudent.data?<LoadingSkeleton kind="heading" label="Loading student details"/>:historyStudent.data?<><Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{historyStudent.data.full_name}</Text><Body muted>Grade {historyStudent.data.grade_level}</Body></>:null}</View><View style={styles.row}><Heading>Screenings</Heading><Button label={order==='newest'?'Oldest first':'Newest first'} secondary icon="swap-vert" style={{paddingHorizontal:12}} onPress={()=>{setCursor(null);setOrder(order==='newest'?'oldest':'newest')}}/></View></>}
      <Notice error message={record.error}/>{Boolean(record.error)&&<Button label="Try again" secondary disabled={record.loading} onPress={start}/>}</View>:undefined}
    ListEmptyComponent={record.loading?<LoadingSkeleton fillHeight={listHeight||windowHeight}/>:!record.error?<Body>{historyId?'No screening records are available for this student.':statusFilter?'No '+statusFilter.toLowerCase()+' screenings are available in your assigned scope.':'No screening records are available for your account.'}</Body>:undefined}
    renderItem={({item,index}:any)=>{const last=index===(record.data?.data.length??0)-1,onPress=()=>navigation.navigate('Screening',{id:item.result_id});if(historyId)return <HistoryRow record={item} last={last} onPress={onPress}/>;const student=students.data?.data.find((student:any)=>student.student_id===item.student_id);return <ScreeningRow record={item} studentName={student?.full_name} grade={student?.grade_level} last={last} onPress={onPress}/>}}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>{record.data?.page?.next_cursor&&<Button label="Next page" disabled={record.loading} onPress={()=>setCursor(record.data.page.next_cursor)}/>}{cursor&&<Button label="Return to first page" secondary disabled={record.loading} onPress={start}/>}{historyId&&<Button label="Final summary and conclusion" secondary onPress={()=>navigation.navigate('FinalReport',{id:historyId})}/>}</View>}/></Screen>
}
function Results(){return <RecordList/>}
function History({route}: {route:{params:{id:string}}}){return <RecordList historyId={route.params.id}/>}
function FinalReport({route}:{route:{params:{id:string}}}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  return <HostedFinalReport key={route.params.id} request={request} id={route.params.id} expert={profile.role==='expert'} parent={profile.role==='parent'} onScreening={id=>navigation.navigate('Screening',{id})}/>
}
function Students(){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  const colors=useColors()
  useLayoutEffect(()=>{if(profile.role==='teacher')navigation.setOptions({headerRight:()=> <View style={{flexDirection:'row',alignItems:'center',marginRight:8}}>
    <Pressable accessibilityRole="button" accessibilityLabel="Add student" onPress={()=>{Keyboard.dismiss();navigation.navigate('StudentEditor',{})}} style={workspaceStyles.headerButton}><MaterialIcons name="person-add-alt" size={24} color={colors.primary}/></Pressable>
  </View>})},[navigation,profile.role,colors.primary])
  return <HostedStudents request={request} teacher={profile.role==='teacher'} onStudent={id=>navigation.navigate('StudentDetails',{id})}/>
}
function StudentDetails({route}:{route:{params:{id:string}}}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  return <HostedStudentDetails request={request} id={route.params.id} teacher={profile.role==='teacher'} onHistory={()=>navigation.navigate('History',{id:route.params.id})} onFinalReport={()=>navigation.navigate('FinalReport',{id:route.params.id})} onEdit={()=>navigation.navigate('StudentEditor',{id:route.params.id})}/>
}
function StudentEditor({route}:{route:{params:{id?:string}}}){
  const {request,profile,logout}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>()
  return <HostedStudentEditor request={request} teacherId={profile.user_id} id={route.params.id} onStudent={id=>navigation.replace('StudentDetails',{id})} onCancel={()=>navigation.goBack()} logout={logout}/>
}
function Detail({route,report=false}:{route:{params:{id:string}};report?:boolean}){
  const {request,profile}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>(),colors=useColors()
  const [editingReview,setEditingReview]=useState(false)
  useEffect(()=>setEditingReview(false),[route.params.id,report])
  const record=useRecords(()=>request((report?'/reports/':'/screenings/')+encodeURIComponent(route.params.id)),[request,route.params.id,report]),row=record.data
  const student=useRecords(()=>row?.student_id?request('/students/'+encodeURIComponent(row.student_id)):Promise.resolve(null),[request,row?.student_id])
  const models=useRecords(()=>row?.model?.model_id&&row.model?.model_version?request('/models?limit=100',{envelope:true}):Promise.resolve(null),[request,row?.model?.model_id,row?.model?.model_version])
  const evaluatedModel=models.data?.data?.find((model:any)=>model.model_id===row?.model?.model_id&&model.model_version===row?.model?.model_version)
  return <Screen onRefresh={record.refresh} refreshing={record.loading&&Boolean(row)}>{record.loading&&!row&&<LoadingSkeleton kind="detail"/>}<Notice error message={record.error}/>{Boolean(record.error)&&<Button label="Try again" secondary disabled={record.loading} onPress={record.refresh}/>}{row&&<>
    <View style={{gap:8}}>{student.loading&&!student.data?<LoadingSkeleton kind="heading" label="Loading student details"/>:<Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{student.data?.full_name||'Student '+row.student_id}</Text>}<Body muted>{student.data?.grade_level?'Grade '+student.data.grade_level+' / ':''}{screeningType(report?row.report_type:row.report?.report_type)}</Body><Body muted>{dateLabel(row.date_generated)}</Body></View>
    <View style={[styles.panel,{borderWidth:0,paddingHorizontal:0,borderRadius:0,borderTopWidth:1,borderTopColor:colors.border,backgroundColor:colors.surface}]}><View style={{gap:4}}><Heading>Model result</Heading><Body muted>{modelLabel(row.model?.model_key)}{' · Model accuracy: '}{models.loading&&row.model?.model_version?'Loading…':hostedPercent(evaluatedModel?.evaluation?.test_accuracy)}</Body></View>
    <View style={{flexDirection:'row',alignItems:'center',flexWrap:'wrap',gap:8}}><Body muted>Result</Body><Status value={row.classification}/></View>
    <RecordValue label="High Potential score" value={hostedPercent(row.class_scores?.high_potential)}/>
    {row.decision_rule?.kind==='high_potential_threshold'&&row.decision_rule?.threshold===0.75&&<Body muted>High Potential is shown when its score is 75% or higher. Otherwise, the result is Normal.</Body>}
    <Body muted>Model scores are not a clinical probability or diagnosis.</Body>
    {row.provenance==='legacy_unverified'&&<Body muted>Historical model provenance has not been verified.</Body>}
    </View>{report&&<View style={[styles.panel,{borderWidth:0,paddingHorizontal:0,borderRadius:0,borderTopWidth:1,borderTopColor:colors.border,backgroundColor:colors.surface}]}><View style={[styles.row,{flexWrap:'wrap',justifyContent:'flex-start'}]}><Heading>Expert review</Heading><Status value={row.review.status}/></View><RecordValue label="Reviewed by" value={row.review.expert_name||(row.review.expert_id?'Name unavailable':'Not yet reviewed')}/><RecordValue label="Remarks" value={row.review.remarks||'Not recorded'}/><RecordValue label="Expert recommendation" value={row.review.expert_recommendation||'Not recorded'}/><RecordValue label="Follow-up needed" value={row.review.follow_up_needed===true?'Yes':row.review.follow_up_needed===false?'No':'Not recorded'}/>
    {row.review.validation_date&&<Body muted>Reviewed {dateLabel(row.review.validation_date)}</Body>}
    </View>}<HostedImage request={request} id={row.result_id}/>
    {!report&&profile.role==='expert'&&(row.review.status==='Pending'||editingReview)&&<HostedReview request={request} id={row.result_id} review={row.review} onSaved={()=>{setEditingReview(false);navigation.popTo('Main',{screen:'Results'})}} onReload={record.refresh} onCancel={editingReview?()=>setEditingReview(false):undefined}/>}
    {!report&&profile.role==='expert'&&row.review.status!=='Pending'&&!editingReview&&<Button label="Edit review" secondary onPress={()=>setEditingReview(true)}/>}
    {profile.role==='expert'&&row.review.status!=='Pending'&&row.review.follow_up_needed===false&&<Button label="Finalize screening" onPress={()=>navigation.navigate('FinalReport',{id:row.student_id})}/>}
    {!report&&row.report?.report_id&&<Button label="Open report" secondary onPress={()=>navigation.navigate('Report',{id:row.report.report_id})}/>}
    <Button label="View student history" secondary onPress={()=>navigation.navigate('History',{id:row.student_id})}/></>}
    </Screen>
}
function Report({route}:{route:{params:{id:string}}}){return <Detail route={route} report/>}
function Profile(){
  const {profile,logout}=useHosted(),[error,setError]=useState(''),c=useColors(),photo=useProfilePhoto()
  const schools=useProfileSchools()
  return <Screen><View style={{alignItems:'center',gap:12,paddingVertical:16}}>
    <Pressable accessibilityRole="button" accessibilityLabel={photo.uri?'Change profile photo':'Add profile photo'} accessibilityHint="Choose a photo from your gallery" accessibilityState={{disabled:photo.busy}} disabled={photo.busy} onPress={photo.choose} style={{padding:4}}>
      <Avatar name={profile.full_name} size={88} uri={photo.uri}/><View style={{position:'absolute',right:0,bottom:0,width:30,height:30,borderRadius:15,backgroundColor:c.primary,alignItems:'center',justifyContent:'center',borderWidth:2,borderColor:c.surface}}><MaterialIcons name="photo-camera" size={17} color={c.onPrimary}/></View>
    </Pressable>
    <Text accessibilityRole="header" style={[styles.title,{color:c.text,textAlign:'center'}]}>{profile.full_name}</Text>
    <Body muted>{profile.role==='parent'?'Parent / Guardian':profile.role==='teacher'?'Teacher':'Expert'}</Body>
    <Body muted>Profile photo is saved on this device.</Body>
    {photo.uri&&<Button label="Remove photo" secondary disabled={photo.busy} onPress={photo.remove}/>}
    <Notice error message={photo.error}/>
    </View>
    <View style={{borderTopWidth:1,borderTopColor:c.border,paddingTop:20,gap:12}}>
      <Heading>{profile.role==='parent'?"Children’s schools":'Assigned schools'}</Heading>
      {schools.loading&&!schools.data?<LoadingSkeleton kind="field" label="Loading schools"/>:schools.data?.length?schools.data.map(school=><Body key={school.school_id}>{school.name}</Body>):!schools.error?<Body muted>{profile.role==='parent'?'No linked schools.':profile.school_ids.length?'Assigned school names are not available yet.':'No schools assigned.'}</Body>:null}
      {profile.role!=='parent'&&Boolean(schools.data?.length)&&schools.data!.length<profile.school_ids.length&&<Body muted>Some assigned school names are not available yet.</Body>}
      <Notice error message={schools.error}/>{Boolean(schools.error)&&<Button label="Retry schools" secondary disabled={schools.loading} onPress={schools.refresh}/>}
    </View>
    <Notice error message={error}/><SignOutAction disabled={photo.busy} onSignOut={logout} onError={setError}/></Screen>
}
function Upload(){const {request}=useHosted(),navigation=useNavigation<NativeStackNavigationProp<Routes>>();return <HostedUpload request={request} onComplete={id=>navigation.navigate('Screening',{id})}/>}
function Main(){
  const {profile}=useHosted(),colors=useColors(),insets=useSafeAreaInsets(),photo=useProfilePhoto()
  const icons: Record<keyof TabRoutes,React.ComponentProps<typeof MaterialIcons>['name']>={Home:'home',Students:'groups',Results:'assignment',Upload:'upload-file',Profile:'person'}
  return <Tabs.Navigator screenListeners={{tabPress:()=>Keyboard.dismiss()}} screenOptions={({route,navigation})=>({animation:'none',tabBarHideOnKeyboard:route.name!=='Profile',headerShadowVisible:false,headerTitleStyle:{fontSize:18,fontWeight:'600'},headerTitle:route.name==='Home'?()=> <AppBrand/>:undefined,headerRight:route.name==='Home'?()=> <Pressable accessibilityRole="button" accessibilityLabel="Open profile" onPress={()=>{Keyboard.dismiss();navigation.navigate('Profile')}} style={workspaceStyles.headerButton}><Avatar name={profile.full_name} size={36} uri={photo.uri}/></Pressable>:undefined,tabBarActiveTintColor:colors.primary,tabBarInactiveTintColor:colors.muted,tabBarItemStyle:{marginHorizontal:3,borderRadius:12},tabBarStyle:{backgroundColor:colors.surface,borderTopColor:colors.border,height:74+insets.bottom,paddingTop:8,paddingBottom:Math.max(insets.bottom,10)},tabBarLabelStyle:{fontSize:12,lineHeight:16},tabBarIcon:({color,size,focused})=><View style={{width:56,height:32,borderRadius:16,alignItems:'center',justifyContent:'center',backgroundColor:focused?colors.soft:'transparent'}}><MaterialIcons name={icons[route.name]} color={color} size={size} accessible={false}/></View>})}>
    <Tabs.Screen name="Home" component={Home} options={{title:'GraphiScan',tabBarLabel:'Home',tabBarAccessibilityLabel:'Home'}}/>
    {profile.role!=='expert'&&<Tabs.Screen name="Students" component={Students} options={{title:profile.role==='parent'?'Children':'Students',tabBarAccessibilityLabel:profile.role==='parent'?'Children':'Students'}}/>}
    {profile.role==='teacher'&&<Tabs.Screen name="Upload" component={Upload} options={{title:'Screen handwriting',tabBarLabel:'Screen',tabBarAccessibilityLabel:'Screen handwriting'}}/>}
    <Tabs.Screen name="Results" component={Results} options={{title:profile.role==='expert'?'Reviews':profile.role==='parent'?'Reports':'Results',tabBarAccessibilityLabel:profile.role==='expert'?'Reviews':profile.role==='parent'?'Reports':'Results'}}/>
    <Tabs.Screen name="Profile" component={Profile} options={{tabBarAccessibilityLabel:'Profile'}}/>
  </Tabs.Navigator>
}

function HostedRoot(){
  const client=useRef<HostedClient|null>(null);if(!client.current)client.current=createHostedClient(origin,{sessionStore:mobileSessionStore(origin),fetchImpl:Platform.OS==='android'?createNativeUploadFetch(globalThis.fetch,FileSystem.createUploadTask,FileSystem.FileSystemUploadType.MULTIPART):globalThis.fetch})
  const api=client.current,[profile,setProfile]=useState<Profile|null>(null),[signInNotice,setSignInNotice]=useState(''),colors=useColors()
  const [restoring,setRestoring]=useState(true),[restoreError,setRestoreError]=useState(''),restoreGeneration=useRef(0)
  async function logout(){restoreGeneration.current++;setRestoring(false);setRestoreError('');setProfile(null);setSignInNotice('');try{await api.logout()}catch{setSignInNotice('You are signed out on this device. The server could not confirm sign-out.')}}
  async function refresh(){
    try{const next=await api.request('/me');if(!['teacher','expert','parent'].includes(next.role)){await logout().catch(()=>{});throw new Error('Use an issued teacher, expert or parent account.')}setProfile({...next,school_ids:Array.isArray(next.school_ids)?next.school_ids:[]})}
    catch(e:any){if(e.status===401){api.clear();setProfile(null)}throw e}
  }
  async function restoreSession(){
    const attempt=++restoreGeneration.current;setRestoring(true);setRestoreError('')
    try{
      if(await api.restore()){
        const next=await api.request('/me')
        if(attempt!==restoreGeneration.current)return
        if(!['teacher','expert','parent'].includes(next.role)){await logout();setSignInNotice('Use an issued teacher, expert or parent account.');return}
        setProfile({...next,school_ids:Array.isArray(next.school_ids)?next.school_ids:[]})
      }
    }catch(e:any){
      if(attempt!==restoreGeneration.current)return
      if([401,403].includes(e.status)||e.code==='INVALID_SESSION'){api.clear();setProfile(null);setSignInNotice('Your session has ended. Sign in again.')}
      else setRestoreError(e.message||'Unable to reconnect. Try again.')
    }finally{if(attempt===restoreGeneration.current)setRestoring(false)}
  }
  useEffect(()=>{void restoreSession();return()=>{restoreGeneration.current++}},[api])
  async function login(email:string,password:string){setSignInNotice('');try{await api.login(email,password);await refresh()}catch(e){await logout().catch(()=>{});throw e}}
  // Stable identity is needed by focus effects; no bearer/refresh token is exposed.
  const request=useRef<HostedClient['request']>(async(path,options)=>{
    try{return await api.request(path,options)}catch(e:any){if(e.status===401){api.clear();setProfile(null)}else if(['PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(e.code)){await refresh().catch(()=>{})}throw e}
  }).current
  const reducedMotion=useReducedMotion()
  const ready=profile?.onboarding.next_action==='ready'
  const base=DefaultTheme
  return <NavigationContainer theme={{...base,colors:{...base.colors,primary:colors.primary,background:colors.bg,card:colors.surface,text:colors.text,border:colors.border}}}><StatusBar style="dark"/>
    {restoring||restoreError?<SafeAreaView edges={['top']} style={{flex:1,backgroundColor:colors.bg}}><Screen><AppBrand/>{restoring?<View style={{gap:16,paddingVertical:32}}><ActivityIndicator color={colors.primary} accessibilityLabel="Restoring your session"/><Body muted>Opening your workspace…</Body></View>:<><Notice error message={restoreError}/><Button label="Try again" onPress={restoreSession}/><SignOutAction onSignOut={logout} onError={setRestoreError}/></>}</Screen></SafeAreaView>:!profile?<HostedLogin login={login} notice={signInNotice}/>:!ready?<SafeAreaView edges={['top']} style={{flex:1,backgroundColor:colors.bg}}><AccountSetup key={profile.user_id+profile.onboarding.next_action} client={api} action={profile.onboarding.next_action} refresh={refresh} logout={logout} passwordChanged={()=>{setProfile(null);setSignInNotice('Password updated. Sign in with your new password.')}}/></SafeAreaView>:<ProfilePhotoProvider key={profile.user_id} userId={profile.user_id}><Context.Provider value={{profile,request,refresh,logout}}><ProfileSchoolsProvider request={request} userId={profile.user_id} role={profile.role} schoolIds={profile.school_ids}><Stack.Navigator key={profile.user_id} screenOptions={{animation:reducedMotion?'none':'fade_from_bottom',contentStyle:{backgroundColor:colors.bg},headerShadowVisible:false,headerTitleStyle:{fontSize:18,fontWeight:'600'}}}>
      <Stack.Screen name="Main" component={Main} options={{headerShown:false}}/><Stack.Screen name="Screening" component={Detail} options={{title:'Screening result'}}/>
      <Stack.Screen name="StudentDetails" component={StudentDetails} options={{title:profile.role==='parent'?'Child details':'Student details'}}/>
      <Stack.Screen name="History" component={History} options={{title:'Screening history'}}/><Stack.Screen name="Report" component={Report} options={{title:'Screening report'}}/>
      <Stack.Screen name="FinalReport" component={FinalReport} options={{title:'Final summary and conclusion'}}/>
      {profile.role==='teacher'&&<Stack.Screen name="StudentEditor" component={StudentEditor} options={({route})=>({title:route.params.id?'Edit student':'Add student'})}/>}
    </Stack.Navigator></ProfileSchoolsProvider></Context.Provider></ProfilePhotoProvider>}
  </NavigationContainer>
}
export default function HostedApp(){return <SafeAreaProvider><HostedRoot/></SafeAreaProvider>}
