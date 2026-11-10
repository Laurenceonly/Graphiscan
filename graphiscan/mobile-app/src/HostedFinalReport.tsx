import React, {useEffect, useRef, useState} from 'react'
import {Alert, Platform, ScrollView, Text, View} from 'react-native'
import {useNavigation, usePreventRemove} from '@react-navigation/native'
import * as Crypto from 'expo-crypto'
import type {HostedClient} from '../../shared/hosted-client.mjs'
import {Body, Button, Field, Heading, Notice, Screen, Status, styles, useColors} from './ui'
import {RecordValue, ScreeningStatuses} from './WorkspaceUI'
import LoadingSkeleton from './LoadingSkeleton'
import {useRecords} from './use-records'
import {dateLabel} from './core/presentation'
import {modelLabel} from './core/hosted-presentation'

type Draft={conclusion:string;next_steps:string}
type Pending={body:Draft&{summary:string;expected_revision:number;history_fingerprint:string};key:string}
type Props={request:HostedClient['request'];id:string;expert:boolean;parent:boolean;onScreening:(id:string)=>void}

export default function HostedFinalReport({request,id,expert,parent,onScreening}:Props){
  const c=useColors(),navigation=useNavigation()
  const record=useRecords<any>(()=>request('/students/'+encodeURIComponent(id)+'/final-report'),[request,id])
  const [draft,setDraft]=useState<Draft>({conclusion:'',next_steps:''})
  const [preview,setPreview]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('')
  const [pending,setPending]=useState<Pending|null>(null),inFlight=useRef(false)
  const reviewed=useRef<{expected_revision:number;history_fingerprint:string}|null>(null)
  const scroll=useRef<React.ComponentRef<typeof ScrollView>>(null)
  const [message,setMessage]=useState('')
  const data=record.data,final=data?.final_report
  useEffect(()=>{if(final)scroll.current?.scrollTo({y:0,animated:false})},[final?.final_report_id])
  useEffect(()=>{
    const report=record.data?.final_report
    if(pending&&report&&record.data.history_fingerprint===pending.body.history_fingerprint&&report.revision===pending.body.expected_revision+1&&
      report.summary===pending.body.summary.trim()&&report.conclusion===pending.body.conclusion.trim()&&report.next_steps===pending.body.next_steps.trim()){
      setPending(null);setDraft({conclusion:'',next_steps:''});setPreview(false);setError('');setMessage('Final report saved.')
    }
    if(preview&&!pending&&reviewed.current&&record.data&&reviewed.current.history_fingerprint!==record.data.history_fingerprint){
      setPreview(false);reviewed.current=null;setError('The screening history changed. Review the current screenings and your conclusion again.')
    }
  },[record.data,pending,preview])
  const dirty=!final&&Object.values(draft).some(value=>value.trim())
  usePreventRemove(busy||Boolean(pending)||dirty,({data:action})=>{
    if(busy||pending){setError('Finalizing is unconfirmed. Retry the same submission before leaving.');return}
    const leave=()=>navigation.dispatch(action.action)
    if(Platform.OS==='web'){if(window.confirm('Discard your unsaved final report?'))leave()}
    else Alert.alert('Discard final report?','Your unsaved conclusion and recommendation will be lost.',[
      {text:'Keep editing',style:'cancel'},{text:'Discard',style:'destructive',onPress:leave}])
  })
  async function finalize(){
    if(inFlight.current||(!data&&!pending)||!expert)return
    inFlight.current=true;setBusy(true);setError('')
    if(!pending&&(!reviewed.current||reviewed.current.history_fingerprint!==data.history_fingerprint)){
      inFlight.current=false;setBusy(false);setPreview(false);setError('Review the current history before finalizing.');return
    }
    // Keep installed030 and the existing API compatible: its required summary
    // stores the combined conclusion. The form has only two independent fields.
    const submission=pending||{key:Crypto.randomUUID(),body:{summary:draft.conclusion,...draft,...reviewed.current!}}
    setPending(submission)
    try{
      await request('/students/'+encodeURIComponent(id)+'/final-report',{
        method:'POST',idempotencyKey:submission.key,body:submission.body})
      setPending(null);setDraft({conclusion:'',next_steps:''});setPreview(false)
      setMessage('Final report saved.');record.refresh()
    }catch(failure:any){
      if([400,401,403,404,409,422].includes(failure.status)){
        setPending(null);setPreview(false);record.refresh()
        setError(failure.status===409?'The history or final report changed. Review the refreshed history before finalizing again.':failure.message)
      }else setError('Saving could not be confirmed. Retry the same final report; your text is retained.')
    }finally{inFlight.current=false;setBusy(false)}
  }
  function refresh(){setMessage('');record.refresh()}
  const section={gap:12,borderTopWidth:1,borderTopColor:c.border,paddingTop:20}
  return <Screen scrollRef={scroll} onRefresh={busy||pending?undefined:refresh} refreshing={record.loading&&Boolean(data)}>
    {record.loading&&!data&&<LoadingSkeleton kind="detail" label="Loading final report"/>}
    <Notice error message={record.error}/>
    {Boolean(record.error)&&<Button label="Try again" secondary disabled={busy||Boolean(pending)||record.loading} onPress={refresh}/>}
    {data&&<>
      {!final&&!expert&&<Body muted>The expert has not yet provided a final report.</Body>}
      {final&&<View style={{gap:8}}><Text accessibilityRole="header" style={[styles.title,{color:c.text}]}>{data.student.full_name}</Text>
        <Body muted>Grade {data.student.grade_level}</Body>{(final||expert)&&<Status value={data.state}/>}
      </View>}
      {final?<>
        <View style={section}><Heading>Expert conclusion</Heading><Body>{[...new Set([final.summary?.trim(),final.conclusion?.trim()].filter(Boolean))].join('\n\n')}</Body></View>
        <View style={section}><Heading>Recommendation</Heading><Body>{final.next_steps}</Body></View>
        <View style={section}><RecordValue label="Finalized by" value={final.expert_name}/>
          <RecordValue label="Finalized on" value={dateLabel(final.finalized_at)}/>
          <Body muted>This conclusion covers the screenings below. A new screening or a change to a review reopens monitoring.</Body></View>
      </>:expert?<View style={section}><Heading>{data.can_finalize?'Ready for the final report':'Before writing the final report'}</Heading>
        <Body>{data.can_finalize?'You can now write the final report.':data.reason==='The latest review requests a follow-up. Update that review to No when monitoring can conclude.'?'When no more follow-ups are needed, set Follow-up needed to No in the latest review.':data.reason||'Review the screenings below before writing the final report.'}</Body>
      </View>:null}
      {(final||expert)&&<View style={section}><Heading>Screenings covered</Heading>
        {!(final?.screenings||data.screenings).length&&<Body muted>No completed screenings yet.</Body>}
        {(final?.screenings||data.screenings).map((row:any)=><View key={row.result_id} style={{gap:8,paddingVertical:12,borderBottomWidth:1,borderBottomColor:c.border}}>
          <Heading>{row.report.report_type}</Heading><Body muted>{dateLabel(row.date_generated)} · {modelLabel(row.model?.model_key)}</Body>
          <ScreeningStatuses classification={row.classification} reviewStatus={row.review.status}/>
          {row.review.remarks&&<RecordValue label="Expert observations" value={row.review.remarks}/>}
          {row.review.expert_recommendation&&<RecordValue label="Expert recommendation" value={row.review.expert_recommendation}/>}
          {row.review.expert_id&&<RecordValue label="Follow-up needed" value={row.review.follow_up_needed?'Yes':'No'}/>}
          {(!parent||row.review.status==='Validated')&&<Button label="Open screening" secondary onPress={()=>onScreening(row.result_id)} disabled={busy||Boolean(pending)||Boolean(dirty)}/>}
        </View>)}
      </View>}
      {!final&&expert&&data.can_finalize&&<View style={section}><Heading>{preview?'Review final report':'Write final report'}</Heading>
        <Body muted>Combine your screening observations and overall conclusion, then recommend what should happen next.</Body>
        {(['conclusion','next_steps'] as const).map(field=>preview?
          <RecordValue key={field} label={{conclusion:'Expert conclusion',next_steps:'Recommendation'}[field]} value={draft[field]}/>:
          <Field key={field} label={{conclusion:'Expert conclusion',next_steps:'Recommendation'}[field]} multiline maxLength={10000}
            value={draft[field]} editable={!busy&&!pending} onChangeText={value=>setDraft(current=>({...current,[field]:value}))}/>)}
        {preview?<>
          <Body muted>Finalizing saves this conclusion with the full history shown above. The linked parent can read the final report.</Body>
          <Button label={busy?'Finalizing…':pending?'Retry the same final report':'Finalize report'} disabled={busy||record.loading||Boolean(record.error)} onPress={finalize}/>
          {!pending&&<Button label="Edit final report" secondary disabled={busy} onPress={()=>setPreview(false)}/>}
        </>:<Button label="Review final report" disabled={record.loading||Boolean(record.error)||Object.values(draft).some(value=>!value.trim())} onPress={()=>{reviewed.current={expected_revision:data.revision,history_fingerprint:data.history_fingerprint};setPreview(true)}}/>}
      </View>}
    </>}
    {pending&&(!data?.can_finalize||Boolean(final))&&<Button label={busy?'Finalizing…':'Retry the same final report'} disabled={busy} onPress={finalize}/>}
    <Notice error message={error}/>
    <Notice message={message}/>
  </Screen>
}
