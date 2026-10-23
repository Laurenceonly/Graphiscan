import React from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { Body, Notice, Screen, useColors } from './ui'
import LoadingSkeleton from './LoadingSkeleton'
import { ActionRow, ScreeningRow, SectionTitle, workspaceStyles } from './WorkspaceUI'

type Props = {
  name:string; role:string; students:any[]; screenings:any[]; loading:boolean; hasLoaded:boolean; error:string;
  onStudents:()=>void; onResults:()=>void; onUpload:()=>void; onRefresh:()=>void; onRecord:(id:string)=>void;
}
export default function HostedHome(p:Props) {
  const c=useColors(), teacher=p.role==='teacher', parent=p.role==='parent'
  const roleName=teacher?'Teacher':parent?'Parent / Guardian':'Expert'
  const action=teacher?{title:'New screening',detail:'Choose a student and add handwriting.',icon:'edit' as const,onPress:p.onUpload}:parent?
    {title:'Reviewed reports',detail:'Read your child’s results and expert notes.',icon:'description' as const,onPress:p.onResults}:
    {title:'Review screenings',detail:'Open the records assigned to you.',icon:'assignment-turned-in' as const,onPress:p.onResults}
  const recent=[...p.screenings].sort((a,b)=>new Date(b.date_generated).getTime()-new Date(a.date_generated).getTime()).slice(0,3)
  return <Screen>
    <View style={s.welcome}><Text accessibilityRole="header" style={[s.name,{color:c.text}]}>{p.name}</Text><Text style={[s.role,{color:c.primary,backgroundColor:c.soft}]}>{roleName}</Text></View>
    <Pressable accessibilityRole="button" accessibilityLabel={action.title} onPress={action.onPress} android_ripple={{color:'#ffffff22'}}
      style={({pressed})=>[s.primaryAction,{backgroundColor:pressed?c.brandPressed:c.brand}]}>
      <MaterialIcons name={action.icon} size={24} color={c.onBrand} accessible={false}/>
      <View style={s.primaryCopy}><Text style={[s.primaryTitle,{color:c.onBrand}]}>{action.title}</Text><Text style={[s.primaryDetail,{color:c.brandMuted}]}>{action.detail}</Text></View>
      <MaterialIcons name="arrow-forward" size={24} color="#fff" accessible={false}/>
    </Pressable>
    <Notice error message={p.error}/>
    <View style={[workspaceStyles.group,{backgroundColor:c.surface}]}>
      <ActionRow title={parent?'Children':'Students'} detail={p.loading?'Loading records…':p.error?'Records unavailable':p.students.length+' '+(parent?(p.students.length===1?'linked child':'linked children'):(p.students.length===1?'student':'students'))+' loaded'} icon="groups" onPress={p.onStudents} last={!teacher}/>
      {teacher&&<ActionRow title="Screening results" detail={p.loading?'Loading records…':p.error?'Records unavailable':p.screenings.length+' '+(p.screenings.length===1?'screening':'screenings')+' loaded'} icon="assignment" onPress={p.onResults} last/>}
    </View>
    <View style={workspaceStyles.section}>
      <SectionTitle title={parent?'Recent reports':p.role==='expert'?'Recent reviews':'Recent screenings'} action="View all" onPress={p.onResults}/>
      {p.loading&&!p.hasLoaded?<LoadingSkeleton/>:!p.error&&recent.length?<View style={[workspaceStyles.group,{backgroundColor:c.surface}]}>{recent.map((row,index)=>{const student=p.students.find(student=>String(student.student_id)===String(row.student_id));return <ScreeningRow key={row.result_id} record={row} studentName={student?.full_name} grade={student?.grade_level} onPress={()=>p.onRecord(row.result_id)} last={index===recent.length-1}/>})}</View>:
        <View style={[s.empty,{backgroundColor:c.surface}]}><Text style={[s.emptyTitle,{color:c.text}]}>{p.error?'Records unavailable':parent?'No reports yet':p.role==='expert'?'No assigned reviews yet':'No screenings yet'}</Text><Body muted>{p.error?'Refresh to try loading your records again.':parent?'Released reports for your linked children will appear here.':p.role==='expert'?'Screenings assigned to you will appear here.':'Completed screenings will appear here for you to follow up.'}</Body></View>}
    </View>
    <Pressable accessibilityRole="button" accessibilityLabel="Refresh" disabled={p.loading} onPress={p.onRefresh} style={s.refresh}><MaterialIcons name="refresh" size={18} color={c.primary} accessible={false}/><Text style={{color:c.primary,fontSize:14,fontWeight:'500'}}>{p.loading?'Refreshing…':'Refresh records'}</Text></Pressable>
  </Screen>
}
const s=StyleSheet.create({
  welcome:{flexDirection:'row',alignItems:'center',flexWrap:'wrap',gap:10},name:{flexGrow:1,flexShrink:1,fontSize:22,lineHeight:30,fontWeight:'600',letterSpacing:-.4},
  role:{fontSize:12,lineHeight:18,fontWeight:'500',paddingHorizontal:10,paddingVertical:5,borderRadius:8,overflow:'hidden'},
  primaryAction:{flexDirection:'row',alignItems:'center',gap:14,minHeight:112,padding:18,borderRadius:16},primaryCopy:{flex:1,minWidth:0,gap:6},
  primaryTitle:{fontSize:20,lineHeight:27,fontWeight:'600',letterSpacing:-.3},primaryDetail:{fontSize:14,lineHeight:21},
  empty:{gap:8,padding:20,borderRadius:16},emptyTitle:{fontSize:16,lineHeight:23,fontWeight:'600'},
  refresh:{minHeight:48,flexDirection:'row',gap:8,alignItems:'center',justifyContent:'center'},
})
