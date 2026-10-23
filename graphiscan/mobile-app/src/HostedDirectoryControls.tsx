import React, { useState } from 'react'
import { Text, View } from 'react-native'
import { Picker } from '@react-native-picker/picker'
import type { HostedClient } from '../../shared/hosted-client.mjs'
import type { School } from './core/hosted-directory'
import { useRecords } from './use-records'
import { Button, Notice, styles, useColors } from './ui'
import LoadingSkeleton from './LoadingSkeleton'

export type Request=HostedClient['request']
interface Page<T> { data:T[]; page:{next_cursor:string|null} }

// A response belongs to its exact filtered path. Refresh retains the current page;
// a new filter/cursor never displays the previous page under the new selection.
export function useScopedPage<T>(request:Request,path:string) {
  const result=useRecords(async()=>{
    if(!path)return {path,page:null,error:''}
    try{return {path,page:await request(path,{envelope:true}) as Page<T>,error:''}}
    catch(failure:any){return {path,page:null,error:failure.message||'Unable to load records.'}}
  },[request,path])
  const current=result.data?.path===path?result.data:null
  return {data:current?.page??null,error:current?.error??'',loading:Boolean(path)&&(result.loading||!current),refresh:result.refresh}
}

export function DirectorySelect({label,value,options,onChange,disabled=false,placeholder,allowEmpty=true}:{
  label:string;value:string;options:{value:string;label:string}[];onChange:(value:string)=>void;
  disabled?:boolean;placeholder?:string;allowEmpty?:boolean;
}) {
  const c=useColors()
  return <View style={{gap:8,minWidth:0}}><Text style={[styles.label,{color:c.text}]}>{label}</Text>
    <View style={{borderWidth:1,borderColor:c.border,borderRadius:10,backgroundColor:c.surface,overflow:'hidden',minHeight:52}}>
      <Picker accessibilityLabel={label} selectedValue={value} enabled={!disabled} onValueChange={value=>onChange(String(value))} mode="dropdown" dropdownIconColor={c.muted} style={{color:c.text,backgroundColor:c.surface,borderWidth:0,minHeight:52,width:'100%'}}>
        {Boolean(placeholder)&&<Picker.Item label={placeholder!} value="" enabled={allowEmpty} color={c.muted}/>}
        {options.map(option=><Picker.Item key={option.value} value={option.value} label={option.label} color={c.text}/>)}
      </Picker>
    </View>
  </View>
}

export function SchoolSelect({request,value,onChange,disabled=false,all=false}:{request:Request;value:School|null;onChange:(value:School|null)=>void;disabled?:boolean;all?:boolean}) {
  const [cursor,setCursor]=useState<string|null>(null),c=useColors()
  const schools=useScopedPage<School>(request,'/schools?limit=25'+(cursor?'&cursor='+encodeURIComponent(cursor):''))
  const options=(schools.data?.data??[]).map(school=>({value:school.school_id,label:school.name}))
  if(value&&!options.some(option=>option.value===value.school_id))options.unshift({value:value.school_id,label:value.name})
  return <View style={{gap:12}}>
    {schools.loading&&!schools.data?<LoadingSkeleton kind="field" label="Loading schools"/>:<DirectorySelect label="School" value={value?.school_id??''} options={options} placeholder={all?'All available schools':'Choose a school'} allowEmpty={all} disabled={disabled||schools.loading}
      onChange={id=>onChange(schools.data?.data.find(school=>school.school_id===id)??(value?.school_id===id?value:null))}/>}
    <Notice error message={schools.error}/>
    {!schools.loading&&!schools.error&&!schools.data?.data.length&&!cursor&&<Text style={[styles.hint,{color:c.muted}]}>No schools are currently available to your account.</Text>}
    {Boolean(schools.error)&&<Button label="Reload schools" secondary disabled={disabled} onPress={schools.refresh}/>}
    {(schools.data?.page.next_cursor||cursor)&&<View style={styles.wrap}>
      {schools.data?.page.next_cursor&&<Button label="More schools" secondary disabled={disabled||schools.loading} onPress={()=>setCursor(schools.data!.page.next_cursor)}/>}
      {cursor&&<Button label="First schools page" secondary disabled={disabled||schools.loading} onPress={()=>setCursor(null)}/>}
    </View>}
  </View>
}

export const grades=[1,2,3].map(value=>({value:String(value),label:'Grade '+value}))
