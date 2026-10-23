import React, { useState } from 'react'
import { FlatList, Text, View } from 'react-native'
import { Body, Button, Field, Notice, Screen, styles, useColors } from './ui'
import { StudentRow } from './WorkspaceUI'
import LoadingSkeleton from './LoadingSkeleton'
import { DirectorySelect, SchoolSelect, grades, useScopedPage, type Request } from './HostedDirectoryControls'
import { studentQuery, type School, type Student, type StudentFilters } from './core/hosted-directory'

const allFilters:StudentFilters={search:'',school:'',grade:''}
export default function HostedStudents({request,teacher,onHistory,onEdit,onAdd}:{request:Request;teacher:boolean;onHistory:(id:string)=>void;onEdit:(id:string)=>void;onAdd:()=>void}) {
  const c=useColors(),[showFilters,setShowFilters]=useState(false),[search,setSearch]=useState(''),[school,setSchool]=useState<School|null>(null)
  const [grade,setGrade]=useState(''),[filters,setFilters]=useState<StudentFilters>({...allFilters}),[schoolLabel,setSchoolLabel]=useState(''),[cursor,setCursor]=useState<string|null>(null),[error,setError]=useState('')
  const students=useScopedPage<Student>(request,studentQuery(filters,cursor))
  function apply(){
    const next={search,school:school?.school_id??'',grade}
    try{studentQuery(next);setError('');setFilters(next);setSchoolLabel(school?.name??'');setCursor(null);if(JSON.stringify(next)===JSON.stringify(filters)&&!cursor)students.refresh();setShowFilters(false)}catch(failure:any){setError(failure.message)}
  }
  function clear(){setSearch('');setSchool(null);setSchoolLabel('');setGrade('');setFilters({...allFilters});setCursor(null);setError('');if(!filters.search&&!filters.school&&!filters.grade&&!cursor)students.refresh()}
  function first(){setCursor(null);if(!cursor)students.refresh()}
  return <Screen scroll={false}><FlatList data={students.data?.data??[]} keyExtractor={row=>row.student_id} contentContainerStyle={[styles.content,{gap:0}]}
    refreshing={students.loading} onRefresh={first}
    ListHeaderComponent={<View style={{gap:16,paddingBottom:20}}>
      <View style={[styles.row,{flexWrap:'wrap'}]}>
        <Button label={showFilters?'Hide filters':'Filters'} secondary icon="filter-list" onPress={()=>setShowFilters(!showFilters)}/>
        {teacher&&<Button label="Add student" icon="add" onPress={onAdd}/>}
      </View>
      {showFilters&&<View style={{gap:16}}>
        <Field label="Search students" value={search} onChangeText={setSearch} maxLength={120} returnKeyType="search" onSubmitEditing={apply}/>
        <SchoolSelect request={request} value={school} onChange={setSchool} all/>
        <DirectorySelect label="Grade" value={grade} options={grades} placeholder="All grades" onChange={setGrade}/>
        <Notice error message={error}/>
        <View style={styles.wrap}><Button label="Apply filters" onPress={apply}/><Button label="Clear filters" secondary onPress={clear}/></View>
      </View>}
      {Boolean(filters.search||filters.school||filters.grade)&&<View style={{gap:8}}>
        <Text style={[styles.hint,{color:c.muted}]}>{[filters.search?'Search: '+filters.search.trim():null,filters.school?schoolLabel||'Selected school':null,filters.grade?'Grade '+filters.grade:null].filter(Boolean).join(' / ')}</Text>
        {!showFilters&&<Button label="Clear filters" secondary onPress={clear}/>}
      </View>}
      <Notice error message={students.error}/>
      {Boolean(students.error)&&<Button label="Reload students" secondary disabled={students.loading} onPress={students.refresh}/>}
    </View>}
    ListEmptyComponent={students.loading?<LoadingSkeleton kind="student" count={3}/>:!students.error?<Body muted>No students are available for your account and these filters.</Body>:undefined}
    renderItem={({item})=><StudentRow student={item} onPress={()=>onHistory(item.student_id)} onEdit={teacher?()=>onEdit(item.student_id):undefined}/>}
    ListFooterComponent={<View style={{gap:12,paddingTop:20}}>
      {students.data?.page.next_cursor&&<Button label="Next students page" disabled={students.loading} onPress={()=>setCursor(students.data!.page.next_cursor)}/>}
      {cursor&&<Button label="First students page" secondary disabled={students.loading} onPress={first}/>}
    </View>}/></Screen>
}
