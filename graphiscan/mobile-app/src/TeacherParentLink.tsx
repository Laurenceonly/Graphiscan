import React, { useEffect, useRef, useState } from 'react'
import { View } from 'react-native'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import { Body, Button, Field, Notice } from './ui'
import { RecordValue } from './WorkspaceUI'
import type { AssignmentOption } from './core/hosted-directory'

export default function TeacherParentLink({ request, school, grade, value, disabled, onChange }: {
  request: HostedClient['request']; school: string; grade: string; value: string;
  disabled: boolean; onChange: (id: string) => void;
}) {
  const [email,setEmail]=useState(''),[match,setMatch]=useState<AssignmentOption|null>(null)
  const [selected,setSelected]=useState<AssignmentOption|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[searched,setSearched]=useState(false)
  const generation=useRef(0),inFlight=useRef(false)
  useEffect(()=>{generation.current++;setMatch(null);setSearched(false);setError('');setBusy(false);inFlight.current=false;return()=>{generation.current++}},[school,grade])
  async function find(){
    if(disabled||inFlight.current||!school)return
    const address=email.trim().toLowerCase()
    if(address.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)){setError('Enter the parent’s full login email.');return}
    const current=++generation.current;inFlight.current=true;setBusy(true);setMatch(null);setSearched(false);setError('')
    try{
      const result=await request('/schools/'+encodeURIComponent(school)+'/assignment-options?grade_level='+encodeURIComponent(grade)+'&parent_email='+encodeURIComponent(address),{envelope:true})
      if(current!==generation.current)return
      const candidate=result.data?.length===1?result.data[0]:null
      if(candidate&&(candidate.role!=='parent'||typeof candidate.user_id!=='string'||typeof candidate.full_name!=='string'))throw new Error('The parent account could not be checked. Try again.')
      setMatch(candidate);setSearched(true)
    }catch(failure:any){if(current===generation.current)setError(failure.message||'Unable to find the parent account. Try again.')}
    finally{if(current===generation.current){inFlight.current=false;setBusy(false)}}
  }
  return <View style={{gap:12}}>
    <RecordValue label="Parent / Guardian" value={value?(selected?.user_id===value?selected.full_name:'Current linked parent'):'Not linked'}/>
    <Body muted>Find an existing parent using the login email provided by your administrator.</Body>
    <Field label="Parent login email" placeholder="parent@graphiscan.com" value={email} editable={!disabled&&!busy} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} returnKeyType="search" onSubmitEditing={find}
      onChangeText={text=>{generation.current++;setEmail(text);setMatch(null);setSearched(false);setError('')}}/>
    <Button label={busy?'Finding parent…':'Find parent'} secondary disabled={disabled||busy||!school||!email.trim()} onPress={find}/>
    {!school&&<Body muted>Choose a school before finding a parent.</Body>}
    {match&&match.user_id!==value&&<View style={{gap:8}}><Body>{match.full_name}</Body><Button label="Select parent" disabled={disabled} onPress={()=>{setSelected(match);onChange(match.user_id)}}/></View>}
    {searched&&!match&&<Body muted>No eligible parent account was found for that email. Check it with your administrator.</Body>}
    {value&&<Button label="Remove parent link" secondary disabled={disabled||busy} onPress={()=>{onChange('');setSelected(null);setMatch(null);setSearched(false)}}/>}
    <Notice error message={error}/>
  </View>
}
