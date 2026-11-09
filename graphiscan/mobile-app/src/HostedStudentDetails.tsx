import React from 'react'
import { Text, View } from 'react-native'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import type { Student } from './core/hosted-directory'
import { Body, Button, Notice, Screen, styles, useColors } from './ui'
import { RecordValue } from './WorkspaceUI'
import { useRecords } from './use-records'
import LoadingSkeleton from './LoadingSkeleton'

export default function HostedStudentDetails({ request, id, teacher, onHistory, onEdit }: {
  request: HostedClient['request']; id: string; teacher: boolean; onHistory: () => void; onEdit: () => void;
}) {
  const colors=useColors(),record=useRecords<Student>(()=>request('/students/'+encodeURIComponent(id)),[request,id]),student=record.data
  return <Screen>
    {record.loading&&!student&&<LoadingSkeleton kind="detail" label="Loading student details"/>}
    <Notice error message={record.error}/>
    {Boolean(record.error)&&<Button label="Try again" secondary disabled={record.loading} onPress={record.refresh}/>}
    {student&&<>
      <View style={{gap:4}}>
        <Text accessibilityRole="header" style={[styles.title,{color:colors.text}]}>{student.full_name}</Text>
        <Body muted>Grade {student.grade_level}</Body>
      </View>
      <View style={{gap:20}}>
        <RecordValue label="School" value={student.school_name||'School name unavailable'}/>
        <RecordValue label="Age" value={student.age===null?'Not recorded':String(student.age)}/>
      </View>
      <View style={{borderTopWidth:1,borderTopColor:colors.border,paddingTop:20,gap:12}}>
        <RecordValue label="Parent / Guardian" value={student.parent_id?(student.parent_name||'Parent linked'):'No parent linked'}/>
        {teacher&&!student.parent_id&&<Body muted>You can link an existing parent account in Edit student.</Body>}
      </View>
      <View style={{gap:12,borderTopWidth:1,borderTopColor:colors.border,paddingTop:20}}>
        <Button label="View screening history" onPress={onHistory}/>
        {teacher&&<Button label="Edit student" secondary onPress={onEdit}/>}
      </View>
    </>}
  </Screen>
}
