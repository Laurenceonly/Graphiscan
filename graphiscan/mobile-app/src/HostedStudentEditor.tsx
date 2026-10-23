import React, { useEffect, useRef, useState } from 'react'
import { Alert, Platform, View } from 'react-native'
import { useNavigation, usePreventRemove } from '@react-navigation/native'
import * as Crypto from 'expo-crypto'
import { createStudentSubmission, type StudentCreateDraft } from '../../shared/directory-submission.mjs'
import { Body, Button, Field, Heading, Notice, Screen, styles } from './ui'
import { RecordValue } from './WorkspaceUI'
import LoadingSkeleton from './LoadingSkeleton'
import { DirectorySelect, SchoolSelect, grades, useScopedPage, type Request } from './HostedDirectoryControls'
import { studentPayload, type AssignmentOption, type School, type Student, type StudentForm } from './core/hosted-directory'
import { useRecords } from './use-records'

const blank:StudentForm={name:'',age:'',school:'',grade:'1',parent:''}
type Props={request:Request;teacherId:string;id?:string;onHistory:(id:string)=>void;onCancel:()=>void;logout:()=>Promise<void>}

export default function HostedStudentEditor({request,teacherId,id,onHistory,onCancel,logout}:Props) {
  const navigation=useNavigation(), submission=useRef(createStudentSubmission(()=>Crypto.randomUUID())).current
  const [form,setForm]=useState<StudentForm>({...blank}),[school,setSchool]=useState<School|null>(null)
  const [optionCursor,setOptionCursor]=useState<string|null>(null),[busy,setBusy]=useState(false),[pending,setPending]=useState(false)
  const [reloadRequired,setReloadRequired]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('')
  const [parentName,setParentName]=useState('')
  const [receipt,setReceipt]=useState<{student:Student;duplicate:boolean}|null>(null)
  const initialized=useRef(!id),baseline=useRef(JSON.stringify(blank)),inFlight=useRef(false),revision=useRef(0),recovering=useRef(false)
  const record=useRecords(()=>id?request('/students/'+encodeURIComponent(id)):Promise.resolve(null),[request,id])
  const options=useScopedPage<AssignmentOption>(request,form.school?'/schools/'+encodeURIComponent(form.school)+'/assignment-options?limit=25'+(optionCursor?'&cursor='+encodeURIComponent(optionCursor):''):'')
  const locked=busy||pending||reloadRequired,dirty=initialized.current&&!receipt&&JSON.stringify(form)!==baseline.current
  usePreventRemove(locked||dirty,({data})=>{
    if(locked){setError(busy?'Wait for saving to finish.':pending?'Saving is unconfirmed. Retry the same submission before leaving.':'Reload the current record before leaving this page.');return}
    if(Platform.OS==='web'){
      if(window.confirm('Discard unsaved student changes?'))navigation.dispatch(data.action)
    }else Alert.alert('Discard changes?','Your unsaved student changes will be lost.',[
      {text:'Keep editing',style:'cancel'},{text:'Discard',style:'destructive',onPress:()=>navigation.dispatch(data.action)},
    ])
  })
  useEffect(()=>{
    if(id&&!record.loading&&record.data&&!initialized.current){
      const row=record.data as Student
      const next={name:row.full_name,age:row.age===null?'':String(row.age),school:row.school_id,grade:String(row.grade_level),parent:row.parent_id??''}
      setForm(next);setSchool({school_id:row.school_id,name:'School '+row.school_id});revision.current=row.revision
      baseline.current=JSON.stringify(next);initialized.current=true;setReloadRequired(false);setError('')
      setParentName('');if(recovering.current){setMessage('Record reloaded. Check the current values before editing.');recovering.current=false}
    }
  },[id,record.data,record.loading])
  function update(key:keyof StudentForm,value:string){setForm(current=>({...current,[key]:value}));setError('')}
  async function save(){
    if(inFlight.current||receipt||reloadRequired)return
    let body:ReturnType<typeof studentPayload>
    try{body=studentPayload(form,Boolean(id),Boolean(id&&record.data?.age===null))}catch(failure:any){setError(failure.message);return}
    inFlight.current=true;setBusy(true);setError('');setMessage('')
    try{
      const result=id?await request('/students/'+encodeURIComponent(id),{method:'PATCH',body:{...body,expected_revision:revision.current},envelope:true}):
        await submission.submit({request},{...body,age:Number(form.age),school_id:form.school} as StudentCreateDraft)
      if(!result?.data?.student_id)throw new Error('Saving could not be confirmed. Reload the current record.')
      setReceipt({student:result.data,duplicate:result.warnings?.includes('duplicate_name')??false})
    }catch(failure:any){
      setError(failure.message)
      if(id&&failure.status!==400&&failure.status!==422)setReloadRequired(true)
    }finally{setPending(submission.pending);setBusy(false);inFlight.current=false}
  }
  function reload(){initialized.current=false;recovering.current=true;setMessage('');setError('');record.refresh()}
  const parentOptions=(options.data?.data??[]).filter(person=>person.role==='parent').map(person=>({value:person.user_id,label:person.full_name}))
  if(form.parent&&!parentOptions.some(person=>person.value===form.parent))parentOptions.unshift({value:form.parent,label:parentName||(id&&form.parent===record.data?.parent_id?'Current linked parent (eligibility checked on save)':'Selected parent (eligibility checked on save)')})

  if(id&&(record.loading&&!initialized.current))return <Screen><LoadingSkeleton kind="detail"/></Screen>
  if(id&&!initialized.current&&record.error)return <Screen><Notice error message={record.error}/><Button label="Reload student" secondary onPress={record.refresh}/><Button label="Back to Students" secondary onPress={onCancel}/></Screen>
  if(id&&record.data&&record.data.teacher_id!==teacherId)return <Screen><Notice error message="This student is not currently assigned to your account."/><Button label="Back to Students" secondary onPress={onCancel}/></Screen>
  if(receipt)return <Screen><Heading>Student saved</Heading><RecordValue label="Student" value={receipt.student.full_name}/><RecordValue label="Grade" value={String(receipt.student.grade_level)}/>
    {receipt.duplicate&&<Body>A similar name exists in your accessible records. Review the records before adding another student.</Body>}
    <Button label="View student history" onPress={()=>onHistory(receipt.student.student_id)}/><Button label="Back to Students" secondary onPress={onCancel}/></Screen>
  return <Screen>
    <View style={{gap:20}}>
      <Field label="Student full name" value={form.name} onChangeText={value=>update('name',value)} maxLength={200} autoCapitalize="words" autoCorrect={false} editable={!locked}/>
      <Field label="Age" value={form.age} onChangeText={value=>update('age',value)} keyboardType="number-pad" maxLength={5} editable={!locked}/>
      <DirectorySelect label="Grade" value={form.grade} options={grades} onChange={value=>update('grade',value)} disabled={locked}/>
      <SchoolSelect request={request} value={school} disabled={locked||Boolean(id)} onChange={value=>{
        setSchool(value);setOptionCursor(null);setParentName('');setForm(current=>({...current,school:value?.school_id??'',parent:''}));setError('')
      }}/>
      <Body muted>{id?'School changes are managed by an administrator. You remain the assigned teacher.':'You will be the assigned teacher. Creation requires current membership in the selected school.'}</Body>
    </View>
    <View style={{gap:12}}>
      <DirectorySelect label="Parent / Guardian (optional)" value={form.parent} options={parentOptions} placeholder="No linked parent" disabled={locked||options.loading||!form.school} onChange={value=>{setParentName(parentOptions.find(option=>option.value===value)?.label??'');update('parent',value)}}/>
      <Body muted>Only parent accounts eligible for this school and your account appear. Contact an administrator if a parent is missing.</Body>
      {options.loading&&<Body muted>Loading eligible parents...</Body>}<Notice error message={options.error}/>
      {Boolean(options.error)&&<Button label="Reload eligible parents" secondary disabled={locked} onPress={options.refresh}/>}
      {(options.data?.page.next_cursor||optionCursor)&&<View style={styles.wrap}>
        {options.data?.page.next_cursor&&<Button label="More eligible people" secondary disabled={locked||options.loading} onPress={()=>setOptionCursor(options.data!.page.next_cursor)}/>}
        {optionCursor&&<Button label="First eligible people page" secondary disabled={locked||options.loading} onPress={()=>setOptionCursor(null)}/>}
      </View>}
    </View>
    <Notice error message={error}/><Notice message={message}/>
    {pending&&<Body>Saving could not be confirmed. Keep this page open and retry the same submission. Do not create a second student record.</Body>}
    {reloadRequired?<Button label="Reload current student" disabled={record.loading} onPress={reload}/>:
      <Button label={busy?'Saving...':pending?'Retry same submission':'Save student'} disabled={busy||!form.school||Boolean(id)&&!dirty} onPress={save}/>}
    {!pending&&!reloadRequired&&<Button label="Cancel" secondary disabled={busy} onPress={onCancel}/>}
    {(pending||reloadRequired)&&<><Body muted>Signing out clears this form. Check Students before creating another record.</Body><Button label="Sign out" secondary disabled={busy} onPress={()=>logout().catch(failure=>setError(failure.message))}/></>}
  </Screen>
}
