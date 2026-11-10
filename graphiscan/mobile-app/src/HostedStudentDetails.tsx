import React from 'react'
import { Text, View } from 'react-native'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import type { Student } from './core/hosted-directory'
import { Body, Button, Heading, Notice, Screen, styles, useColors } from './ui'
import { ActionRow, StudentAvatar } from './WorkspaceUI'
import { useRecords } from './use-records'
import LoadingSkeleton from './LoadingSkeleton'

export default function HostedStudentDetails({ request, id, teacher, onHistory, onFinalReport, onEdit }: {
  request: HostedClient['request']; id: string; teacher: boolean; onHistory: () => void; onFinalReport: () => void; onEdit: () => void;
}) {
  const colors=useColors(),record=useRecords<Student>(()=>request('/students/'+encodeURIComponent(id)),[request,id]),student=record.data
  return <Screen>
    {record.loading&&!student&&<LoadingSkeleton kind="detail" label="Loading student details"/>}
    <Notice error message={record.error}/>
    {Boolean(record.error)&&<Button label="Try again" secondary disabled={record.loading} onPress={record.refresh}/>}
    {student&&<>
      <View style={{flexDirection:'row',alignItems:'center',gap:16,paddingBottom:4}}>
        <StudentAvatar size={56}/>
        <View style={{flex:1,minWidth:0,gap:4}}><Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{student.full_name}</Text><Body muted>Grade {student.grade_level}</Body></View>
        {teacher&&<Button label="Edit" icon="edit" secondary style={{paddingHorizontal:12}} onPress={onEdit}/>}
      </View>
      <View style={{borderTopWidth:1,borderTopColor:colors.border}}>
        {([
          {label:'School',value:student.school_name||'School name unavailable',icon:'school'},
          {label:'Age',value:student.age===null?'Not recorded':String(student.age),icon:'cake'},
          {label:'Parent / Guardian',value:student.parent_id?(student.parent_name||'Parent linked'):'No parent linked',icon:'family-restroom'},
        ] as const).map(item=><View key={item.label} style={{flexDirection:'row',alignItems:'center',gap:14,paddingVertical:16,borderBottomWidth:1,borderBottomColor:colors.border}}>
          <MaterialIcons name={item.icon} size={22} color={colors.muted} accessible={false}/>
          <View style={{flex:1,minWidth:0,gap:4}}><Text style={[styles.hint,{color:colors.muted}]}>{item.label}</Text><Body>{item.value}</Body></View>
        </View>)}
      </View>
      {teacher&&!student.parent_id&&<Body muted>You can link an existing parent account in Edit.</Body>}
      <View style={{gap:8}}><Heading>Screening records</Heading>
        <ActionRow title="Screening history" detail="Initial and follow-up screenings" icon="history" onPress={onHistory}/>
        <ActionRow title="Final report" detail="Expert conclusion and recommendation" icon="assignment-turned-in" onPress={onFinalReport} last/>
      </View>
    </>}
  </Screen>
}
