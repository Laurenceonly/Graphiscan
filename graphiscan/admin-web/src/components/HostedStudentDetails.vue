<template>
  <section class="student-profile" aria-labelledby="student-profile-title">
    <header class="admin-page-header student-profile-header">
      <div><button type="button" class="student-back" @click="$emit('close')"><ArrowLeft :size="16" aria-hidden="true" />{{ backLabel }}</button><h2 id="student-profile-title" ref="heading" tabindex="-1">{{ student?.full_name || 'Student details' }}</h2></div>
      <div v-if="student && canEdit" class="student-profile-actions single-action"><button type="button" class="primary-action-btn" :disabled="editingBusy" @click="$emit('edit')">Edit student</button></div>
    </header>
    <div class="student-profile-content">
      <p v-if="error" class="workspace-alert" role="alert">{{ error }} <button type="button" class="soft-action-btn" :disabled="busy" @click="loadStudent">Try again</button></p>
      <AdminLoadingSkeleton v-if="busy && !student" label="Loading student details" :rows="3" />
      <template v-if="student">
        <section aria-labelledby="student-information-title"><h3 id="student-information-title">Student details</h3>
          <dl class="student-information">
            <div><dt>Name</dt><dd>{{ student.full_name }}</dd></div><div><dt>Student ID</dt><dd>{{ student.student_id }}</dd></div>
            <div><dt>Age</dt><dd>{{ student.age ?? 'Not recorded' }}</dd></div><div><dt>Grade</dt><dd>{{ student.grade_level }}</dd></div>
            <div><dt>School</dt><dd>{{ schools.find(s => String(s.school_id) === String(student.school_id))?.name || 'School ' + student.school_id }}</dd></div>
            <div><dt>Assigned teacher</dt><dd>{{ personName(student.teacher_id, 'No teacher assigned') }}</dd></div>
            <div><dt>Parent or guardian</dt><dd>{{ personName(student.parent_id, 'No linked parent') }}</dd></div>
            <div><dt>Registered</dt><dd>{{ date(student.created_at) }}</dd></div><div><dt>Last updated</dt><dd>{{ date(student.updated_at) }}</dd></div>
          </dl>
        </section>
        <section class="student-screenings" aria-labelledby="student-screenings-title"><div class="student-screenings-heading"><h3 id="student-screenings-title">Screenings</h3></div>
          <p v-if="historyError" role="alert" class="workspace-alert">{{ historyError }} <button type="button" class="soft-action-btn" :disabled="historyBusy" @click="loadHistory(false)">Try again</button></p>
          <AdminLoadingSkeleton v-if="historyBusy && !historyLoaded" label="Loading student screenings" :rows="3" />
          <p v-else-if="historyLoaded && !rows.length" class="student-history-empty">No screenings are available for this student.</p>
          <div v-if="rows.length" class="table-wrapper compact-table-scroll" role="region" aria-label="Student screenings" tabindex="0"><table><thead><tr><th>Date</th><th>Screening type</th><th>Model output</th><th>Review status</th><th>Reviewed by</th><th>Follow-up needed</th><th>Actions</th></tr></thead><tbody><tr v-for="row in rows" :key="row.result_id">
            <td data-label="Date">{{ date(row.date_generated) }}</td><td data-label="Screening type">{{ formatReportType(row.report?.report_type) }}</td><td data-label="Model output">{{ row.classification || 'Not recorded' }}</td><td data-label="Review status"><span class="result-badge" :class="tone(row.review?.status)">{{ row.review?.status || 'Not recorded' }}</span></td><td data-label="Reviewed by">{{ personName(row.review?.expert_id, ['Validated','Flagged'].includes(row.review?.status) ? 'Reviewer not recorded' : 'Not reviewed') }}</td><td data-label="Follow-up needed">{{ row.review?.follow_up_needed === true ? 'Yes' : row.review?.follow_up_needed === false ? 'No' : 'Not recorded' }}</td><td data-label="Actions"><button type="button" class="small-action-btn" :aria-label="'View screening ' + row.result_id" @click="$emit('open-result', row.result_id)">View</button></td>
          </tr></tbody></table></div>
          <button v-if="cursor" type="button" class="soft-action-btn" :disabled="historyBusy" @click="loadHistory(true)">Load more screenings</button>
        </section>
      </template>
    </div>
  </section>
</template>
<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import AdminLoadingSkeleton from '../../../shared/AdminLoadingSkeleton.vue'
import { formatReportType } from '../utils/hosted-screenings.mjs'
const props=defineProps({client:{type:Object,required:true},profile:{type:Object,required:true},studentId:{type:String,required:true},schools:{type:Array,default:()=>[]},backLabel:{type:String,default:'Back to Students'},canEdit:Boolean,editingBusy:Boolean,refreshKey:{type:Number,default:0}})
const emit=defineEmits(['close','edit','open-result','access-change'])
const student=ref(null),people=ref({}),rows=ref([]),cursor=ref(null),busy=ref(false),historyBusy=ref(false),historyLoaded=ref(false),error=ref(''),historyError=ref(''),heading=ref(null)
let alive=true,generation=0,historyVersion=0
function accessFailure(failure){if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code))emit('access-change')}
function personName(id,empty){return id ? people.value[id] || 'Account '+id : empty}
function date(value){if(!value)return 'Not recorded';const parsed=new Date(value);return Number.isNaN(parsed.getTime())?'Not recorded':parsed.toLocaleString()}
function tone(value){return value==='Validated'?'success':value==='Flagged'?'danger':value==='Pending'?'warning':'secondary'}
async function loadNames(version,ids=[student.value?.teacher_id,student.value?.parent_id]){
  if(!props.profile.permissions?.includes('accounts.manage'))return
  const unique=[...new Set(ids.filter(id=>id&&!people.value[id]))]
  await Promise.all(unique.map(async id=>{try{const person=await props.client.request('/accounts/'+encodeURIComponent(id));if(alive&&version===generation&&props.profile.permissions?.includes('accounts.manage'))people.value={...people.value,[id]:person.full_name+(person.account_status&&person.account_status!=='active'?' (inactive)':'')}}catch(failure){if(alive&&version===generation)accessFailure(failure)}}))
}
async function loadStudent(){
  const version=++generation;historyVersion++;student.value=null;people.value={};rows.value=[];cursor.value=null;historyLoaded.value=false;historyBusy.value=false;error.value='';historyError.value='';busy.value=true
  try{const data=await props.client.request('/students/'+encodeURIComponent(props.studentId));if(!alive||version!==generation)return;student.value=data;await nextTick();heading.value?.focus({preventScroll:true});await Promise.all([loadNames(version),loadHistory(false)])}catch(failure){if(!alive||version!==generation)return;error.value=failure.message||'Student details could not be loaded.';accessFailure(failure)}finally{if(alive&&version===generation)busy.value=false}
}
async function loadHistory(more=false){
  if(historyBusy.value||!student.value)return
  const version=generation,request=++historyVersion,id=student.value.student_id;historyBusy.value=true;historyError.value=''
  try{const query=new URLSearchParams({limit:'25'});if(more&&cursor.value)query.set('cursor',cursor.value);const response=await props.client.request('/students/'+encodeURIComponent(id)+'/history?'+query,{envelope:true});if(!alive||version!==generation||request!==historyVersion)return;rows.value=more?[...rows.value,...response.data]:response.data;cursor.value=response.page?.next_cursor||null;historyLoaded.value=true;await loadNames(version,response.data.map(row=>row.review?.expert_id))}catch(failure){if(!alive||version!==generation||request!==historyVersion)return;historyError.value=failure.message||'Student screenings could not be loaded.';accessFailure(failure)}finally{if(alive&&version===generation&&request===historyVersion)historyBusy.value=false}
}
watch(()=>[props.studentId,props.profile,props.refreshKey],loadStudent,{immediate:true})
onBeforeUnmount(()=>{alive=false;generation++;historyVersion++})
</script>
