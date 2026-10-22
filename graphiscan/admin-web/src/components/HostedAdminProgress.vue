<template>
  <section class="hosted-progress compact-page">
    <header class="page-header compact-header"><h1 tabindex="-1">Student Progress</h1></header>
    <section class="panel-card compact-panel">
      <h2>Assessment history</h2>
      <form class="history-toolbar" @submit.prevent="loadHistory(false)">
        <label>Student<select aria-label="Student" v-model="studentId" :disabled="busy" required><option value="" disabled>Choose a student</option><option v-for="student in students" :key="student.student_id" :value="String(student.student_id)">{{ student.full_name }}</option></select></label>
        <button type="submit" class="primary-action-btn" :disabled="busy || !studentId">{{ busy ? 'Loading…' : 'View history' }}</button>
      </form>
      <p v-if="error" class="error-message" role="alert">{{ error }}</p>
      <p v-if="!students.length">No students are currently loaded. Open Students to check the available records.</p>
      <p v-else-if="!loaded && !busy">Choose a student to view their screening history.</p>
      <p v-if="loaded && !rows.length && !busy">No screening history is available for this student.</p>
      <p v-if="busy" role="status">Loading screening history…</p>
      <div v-if="rows.length" class="table-wrapper compact-table-scroll" role="region" aria-label="Student screening history" tabindex="0"><table><thead><tr><th>Date</th><th>Screening type</th><th>Model output</th><th>Review status</th><th>Follow-up needed</th><th>Action</th></tr></thead><tbody><tr v-for="row in rows" :key="row.result_id">
        <td data-label="Date">{{ date(row.date_generated) }}</td><td data-label="Screening type">{{ formatReportType(row.report?.report_type) }}</td><td data-label="Model output">{{ row.classification || 'Not recorded' }}</td><td data-label="Review status"><span class="result-badge" :class="tone(row.review?.status)">{{ row.review?.status || 'Not recorded' }}</span></td><td data-label="Follow-up needed">{{ row.review?.follow_up_needed === true ? 'Yes' : row.review?.follow_up_needed === false ? 'No' : 'Not recorded' }}</td><td data-label="Action"><button class="small-action-btn" type="button" :disabled="busy" :aria-label="'View history result ' + row.result_id" @click="$emit('open-result',row.result_id)">View</button></td>
      </tr></tbody></table></div>
      <button v-if="cursor" class="soft-action-btn" type="button" :disabled="busy" @click="loadHistory(true)">Load more history</button>
    </section>
  </section>
</template>
<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { formatReportType } from '../utils/hosted-screenings.mjs'
const props=defineProps({client:{type:Object,required:true},profile:{type:Object,required:true},students:{type:Array,default:()=>[]}})
const emit=defineEmits(['access-change','open-result'])
const studentId=ref(''),rows=ref([]),cursor=ref(null),busy=ref(false),loaded=ref(false),error=ref('')
let alive=true,requestVersion=0
function clear(){requestVersion++;rows.value=[];cursor.value=null;loaded.value=false;error.value=''}
watch(studentId,clear)
watch(()=>props.profile,()=>{studentId.value='';clear()})
watch(()=>props.students,students=>{if(studentId.value&&!students.some(student=>String(student.student_id)===studentId.value))studentId.value=''}, {deep:true})
async function loadHistory(more=false){
  if(busy.value||!studentId.value)return
  busy.value=true;error.value=''
  const version=++requestVersion
  if(!more){rows.value=[];cursor.value=null;loaded.value=false}
  try{
    const query=new URLSearchParams({limit:'25'});if(more&&cursor.value)query.set('cursor',cursor.value)
    const response=await props.client.request('/students/'+encodeURIComponent(studentId.value)+'/history?'+query,{envelope:true})
    if(!alive||version!==requestVersion)return
    rows.value=more?[...rows.value,...response.data]:response.data;cursor.value=response.page.next_cursor;loaded.value=true
  }catch(failure){if(!alive||version!==requestVersion)return;error.value=failure.message||'Screening history could not be loaded.';if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code))emit('access-change')}
  finally{if(alive)busy.value=false}
}
function date(value){if(!value)return 'Not recorded';const parsed=new Date(value);return Number.isNaN(parsed.getTime())?'Not recorded':parsed.toLocaleString()}
function tone(value){return value==='Validated'?'success':value==='Flagged'?'danger':value==='Pending'?'warning':'secondary'}
onBeforeUnmount(()=>{alive=false})
</script>
<style scoped>
.hosted-progress{display:flex;flex-direction:column;gap:24px;min-height:0}.hosted-progress .compact-panel{flex:none;min-height:0;padding:24px;border-radius:12px}.hosted-progress .compact-header{margin:0}.history-summary{margin:0;gap:16px}.history-summary .user-summary-card{min-height:100px;padding:20px}.history-summary strong{font-size:28px}h1{font-size:28px;margin:0}.compact-panel h2{margin:0 0 20px;font-size:18px;font-weight:600}.history-toolbar{display:flex;align-items:end;gap:16px;flex-wrap:wrap}label{display:grid;gap:8px;font-size:14px;font-weight:500;flex:1;min-width:180px}select{min-height:48px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:400 16px/1.5 var(--font-ui)}.history-hint{font-size:12px;color:var(--muted);margin:20px 0}.table-wrapper{margin:24px 0;border:1px solid var(--border);border-radius:12px}table{min-width:850px}td{white-space:normal}button:focus-visible,select:focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}@media(max-width:700px){table{min-width:0}.history-summary{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.history-summary .user-summary-card{min-height:100px;padding:14px}.hosted-progress .compact-panel{padding:20px}.history-toolbar{align-items:stretch}.history-toolbar label{min-width:0;width:100%;flex:auto}}
</style>
