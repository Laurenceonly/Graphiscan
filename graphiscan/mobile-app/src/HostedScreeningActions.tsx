import React,{useEffect,useRef,useState} from 'react'
import {Image,Platform,Switch,View} from 'react-native'
import * as ImagePicker from 'expo-image-picker'
import * as FileSystem from 'expo-file-system/legacy'
import * as Crypto from 'expo-crypto'
import type {HostedClient} from '../../shared/hosted-client.mjs'
import {createReviewSubmission} from '../../shared/screening-submission.mjs'
import {Body,Button,Field,Heading,Loading,Notice,Screen,styles} from './ui'
import {useRecords} from './use-records'
import {exportImage} from './export-image'
import {ChoiceRow} from './WorkspaceUI'

type Request=HostedClient['request']
export function HostedReview({request,id,review,onSaved}:{request:Request;id:string;review:any;onSaved:()=>void}){
  const submission=useRef(createReviewSubmission(()=>Crypto.randomUUID())).current
  const [status,setStatus]=useState('Validated'),[remarks,setRemarks]=useState(''),[recommendation,setRecommendation]=useState(''),[followUp,setFollowUp]=useState(false)
  const [busy,setBusy]=useState(false),[pending,setPending]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('')
  useEffect(()=>{if(!submission.pending){setStatus(review.status==='Flagged'?'Flagged':'Validated');setRemarks(review.remarks||'');setRecommendation(review.expert_recommendation||'');setFollowUp(review.follow_up_needed)}},[review,submission])
  async function save(){
    if(busy)return;setBusy(true);setError('');setMessage('')
    try{await submission.submit({request},id,{status,remarks,expert_recommendation:recommendation.trim()||null,follow_up_needed:followUp,expected_revision:review.revision});setMessage('Review saved.');onSaved()}
    catch(e){setError((e as Error).message)}finally{setPending(submission.pending);setBusy(false)}
  }
  return <View style={{gap:16}}><Heading>Submit expert review</Heading><View style={styles.wrap}>{['Validated','Flagged'].map(value=><Button key={value} label={value} secondary={status!==value} disabled={busy||pending} onPress={()=>setStatus(value)}/>)}</View>
    <Field label="Review remarks" multiline value={remarks} onChangeText={setRemarks} editable={!busy&&!pending}/><Field label="Expert recommendation (optional)" multiline value={recommendation} onChangeText={setRecommendation} editable={!busy&&!pending}/>
    <View style={styles.row}><Body>Follow-up needed</Body><Switch accessibilityLabel="Follow-up needed" value={followUp} onValueChange={setFollowUp} disabled={busy||pending}/></View>
    <Notice error message={error}/><Notice message={message}/><Button label={busy?'Saving review...':pending?'Retry the same review':'Save review'} disabled={busy||!remarks.trim()} onPress={save}/>
    {pending&&<><Body muted>Keep this page open. Check the current record before starting another review.</Body><Button label="Reload current record" secondary disabled={busy} onPress={onSaved}/><Button label="I checked the record; start another review" secondary disabled={busy} onPress={()=>{submission.discard();setPending(false);setError('');onSaved()}}/></>}
  </View>
}
export function HostedImage({request,id}:{request:Request;id:string}){
  const [uri,setUri]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('')
  useEffect(()=>{setUri('');setError('')},[id])
  async function image(save:boolean){
    if(busy)return;setBusy(true);setError('')
    try{const blob=await request('/screenings/'+encodeURIComponent(id)+'/image',{image:true});if(save)await exportImage(blob);else{
      const data=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=()=>reject(new Error('Unable to display this image.'));reader.readAsDataURL(blob)});setUri(data)
    }}catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  return <View style={{gap:12}}><Button label={busy?'Loading image...':'View handwriting image'} secondary disabled={busy} onPress={()=>image(false)}/>{uri?<Image source={{uri}} accessibilityLabel="Authorized handwriting sample" resizeMode="contain" style={{width:'100%',height:300}}/>:null}<Button label="Save handwriting image" secondary disabled={busy} onPress={()=>image(true)}/><Notice error message={error}/></View>
}
export function HostedUpload({request,onComplete}:{request:Request;onComplete:(id:string)=>void}){
  const [studentCursor,setStudentCursor]=useState<string|null>(null),[modelCursor,setModelCursor]=useState<string|null>(null)
  const students=useRecords(()=>request('/students?limit=100'+(studentCursor?'&cursor='+encodeURIComponent(studentCursor):''),{envelope:true}),[request,studentCursor])
  const models=useRecords(()=>request('/models?limit=100'+(modelCursor?'&cursor='+encodeURIComponent(modelCursor):''),{envelope:true}),[request,modelCursor])
  const [student,setStudent]=useState<any>(null),[model,setModel]=useState<any>(null),[asset,setAsset]=useState<ImagePicker.ImagePickerAsset|null>(null)
  const [search,setSearch]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[hasPending,setHasPending]=useState(false),[failed,setFailed]=useState(false)
  const pending=useRef<{key:string;form:FormData}|null>(null)
  useEffect(()=>{if(!model){const next=models.data?.data.find((row:any)=>row.is_default&&row.is_selectable);if(next)setModel(next)}},[models.data,model])
  async function pick(camera:boolean){
    setError('')
    try{
      const permission=camera?await ImagePicker.requestCameraPermissionsAsync():await ImagePicker.requestMediaLibraryPermissionsAsync()
      if(!permission.granted)throw new Error('Allow image access in device settings.')
      const result=camera?await ImagePicker.launchCameraAsync({mediaTypes:['images'],quality:1}):await ImagePicker.launchImageLibraryAsync({mediaTypes:['images'],quality:1})
      if(result.canceled)return
      const image=result.assets[0]
      if(image.fileSize&&image.fileSize>10*1024*1024)throw new Error('Choose an image smaller than 10 MB.')
      if(image.mimeType&&!['image/jpeg','image/png'].includes(image.mimeType))throw new Error('Choose a JPG or PNG image.')
      setAsset(image)
    }catch(e){setError((e as Error).message)}
  }
  async function send(){
    if(busy||!student||!model||!asset)return;setBusy(true);setError('');setMessage('')
    try{
      if(!pending.current){
        const form=new FormData();form.append('student_id',student.student_id);form.append('model_id',model.model_id)
        const name=asset.mimeType==='image/png'?'handwriting.png':'handwriting.jpg'
        if(Platform.OS==='web'){const file=asset.file??await(await fetch(asset.uri)).blob();if(file.size>10*1024*1024)throw new Error('Choose an image smaller than 10 MB.');form.append('handwriting_image',file,name)}else{
          const file=await FileSystem.getInfoAsync(asset.uri);if(!file.exists||file.isDirectory||file.size>10*1024*1024)throw new Error('Select a valid image smaller than 10 MB.');form.append('handwriting_image',{uri:asset.uri,name,type:asset.mimeType||'image/jpeg'} as any)
        }
        pending.current={key:Crypto.randomUUID(),form}
      }
      const row=await request('/screenings',{method:'POST',form:pending.current.form,idempotencyKey:pending.current.key,timeout:120000})
      pending.current=null;setAsset(null);onComplete(row.result_id)
    }catch(e:any){setError(e.message);if(e.status===400||e.status===422)pending.current=null}
    finally{setHasPending(!!pending.current);setBusy(false)}
  }
  async function check(){
    if(busy||!pending.current)return;setBusy(true);setError('')
    try{const state=await request('/screening-requests/'+encodeURIComponent(pending.current.key));if(state.state==='completed'){pending.current=null;setAsset(null);onComplete(state.result_id)}else if(state.state==='failed'){setFailed(true);setMessage('This submission did not complete. You can start another upload.')}else setMessage('The submission is still processing. Check again shortly.')}
    catch(e){setError((e as Error).message)}finally{setHasPending(!!pending.current);setBusy(false)}
  }
  return <Screen><Body muted>Select a student and an available model, then add a handwriting image.</Body><Heading>Student</Heading>
    {students.loading&&<Loading/>}<Notice error message={students.error}/><Field label="Find a student on this page" value={search} onChangeText={setSearch} editable={!busy&&!hasPending}/>
    <View style={{gap:8}}>{(students.data?.data??[]).filter((row:any)=>row.full_name.toLowerCase().includes(search.trim().toLowerCase())).map((row:any)=><ChoiceRow key={row.student_id} label={row.full_name} detail={'Grade '+row.grade_level} selected={student?.student_id===row.student_id} disabled={busy||hasPending} onPress={()=>setStudent(row)}/>)}</View>
    {!students.loading&&!students.error&&!(students.data?.data??[]).some((row:any)=>row.full_name.toLowerCase().includes(search.trim().toLowerCase()))&&<Body muted>{search.trim()?'No students match this search on the current page.':'No students are available for your account.'}</Body>}
    {students.data?.page?.next_cursor&&<Button label="Next students" secondary disabled={busy||hasPending} onPress={()=>setStudentCursor(students.data.page.next_cursor)}/>}
    {studentCursor&&<Button label="First students page" secondary disabled={busy||hasPending} onPress={()=>setStudentCursor(null)}/>}
    <Heading>Screening model</Heading>{models.loading&&<Loading/>}<Notice error message={models.error}/>
    <View style={{gap:8}}>{(models.data?.data??[]).filter((row:any)=>row.is_selectable).map((row:any)=><ChoiceRow key={row.model_id} label={row.model_key} detail={'Version '+row.model_version+(row.is_default?' · Default':'')} selected={model?.model_id===row.model_id} disabled={busy||hasPending} onPress={()=>setModel(row)}/>)}</View>
    {!models.loading&&!models.error&&!(models.data?.data??[]).some((row:any)=>row.is_selectable)&&<Body>No screening model is currently available. Contact your administrator.</Body>}
    {models.data?.page?.next_cursor&&<Button label="More models" secondary disabled={busy||hasPending} onPress={()=>setModelCursor(models.data.page.next_cursor)}/>}
    <Heading>Handwriting image</Heading><View style={styles.wrap}><Button label="Choose image" secondary disabled={busy||hasPending} onPress={()=>pick(false)}/><Button label="Use camera" secondary disabled={busy||hasPending} onPress={()=>pick(true)}/></View>
    {asset&&<Image source={{uri:asset.uri}} accessibilityLabel="Selected handwriting image" resizeMode="contain" style={{width:'100%',height:280}}/>}
    <Body muted>Use an image up to 10 MB and 16 megapixels. Screening supports expert review and does not establish a diagnosis.</Body>
    <Notice error message={error}/><Notice message={message}/>
    <Button label={busy?'Submitting...':hasPending?'Retry the same submission':'Submit for screening'} disabled={busy||!student||!model||!asset||failed} onPress={send}/>
    {hasPending&&<><Body muted>Keep this page open until the submission is confirmed. Do not create another upload for this sample while its status is uncertain.</Body><Button label="Check submission status" secondary disabled={busy} onPress={check}/></>}
    {failed&&<Button label="Start another upload" secondary disabled={busy} onPress={()=>{pending.current=null;setHasPending(false);setFailed(false);setAsset(null);setError('');setMessage('')}}/>}
  </Screen>
}
