<template>
  <section class="hosted-screenings" aria-labelledby="screenings-title" :aria-busy="busy">
    <AdminPageSkeleton v-if="canManage && busy && !loaded && !detail" summary filters label="Loading screening results" />
    <template v-else>
    <header class="admin-page-header"><h2 id="screenings-title">Screening results</h2></header>
    <p v-if="!canManage">Screening records require permission to manage assignments for the relevant school.</p>
    <template v-else>
      <AdminSummaryCards v-if="!detail && !loadingDetail" :items="[{label:'Results',loading:busy && !loaded,value:loaded ? rows.length : '-'},...['Pending','Validated','Flagged'].map(value => ({label:value,loading:busy && !loaded,value:loaded ? rows.filter(row => row.review?.status === value).length : '-'}))]" label="Loaded screening counts" />
      <div class="screening-records-panel">
      <form class="screening-filters" @submit.prevent="loadList(false)">
        <label>Review status<select v-model="status" :disabled="busy"><option value="">All statuses</option><option>Pending</option><option>Validated</option><option>Flagged</option></select></label>
        <label>Grade<select v-model="grade" :disabled="busy"><option value="">All grades</option><option v-for="value in 3" :key="value" :value="String(value)">Grade {{ value }}</option></select></label>
        <button type="submit" :disabled="busy">Apply filters</button>
      </form>
      <p v-if="error && !detail" role="alert" class="screening-error">{{ error }} <button type="button" :disabled="busy" @click="retryFailedRead">Try again</button></p>
      <p v-if="message" role="status">{{ message }}</p>
      <AdminLoadingSkeleton v-if="busy && !loaded" label="Loading screening results..." />
      <p v-else-if="busy" role="status">Updating screening records...</p>
      <p v-if="!loaded && !busy">Screening results have not loaded. Reload the page to try again.</p>
      <p v-if="loaded && !rows.length && !busy">No screening results are available for your account and these filters.</p>
      <div v-if="rows.length" class="table-wrapper compact-table-scroll hosted-results-table" role="region" aria-label="Screening records" tabindex="0">
        <table><thead><tr><th>Student</th><th>Screening type</th><th>Classification</th><th>Predicted-class score</th><th>Review status</th><th>Date</th><th>Action</th></tr></thead><tbody>
          <tr v-for="row in rows" :key="row.result_id">
            <td data-label="Student"><strong>Student {{ row.student_id }}</strong></td>
            <td data-label="Screening type">{{ reportType(row.report?.report_type) }}</td>
            <td data-label="Classification"><span class="result-badge" :class="classificationTone(row.classification)">{{ row.classification }}</span></td>
            <td data-label="Predicted-class score">{{ score(row.predicted_class_score) }}</td>
            <td data-label="Review status"><span class="result-badge" :class="statusTone(row.review?.status)">{{ row.review?.status || 'Not recorded' }}</span></td>
            <td data-label="Date">{{ date(row.date_generated) }}</td>
            <td data-label="Action"><button type="button" class="small-action-btn" :aria-label="'View result ' + row.result_id" :disabled="busy" @click="openDetail(row.result_id)">View</button></td>
          </tr>
        </tbody></table>
      </div>
      <button v-if="cursor" type="button" :disabled="busy" @click="loadList(true)">Load more results</button>
      </div>
      <AdminLoadingSkeleton v-if="loadingDetail && !detail" label="Loading result details..." :rows="3" />
      <section v-if="detail" ref="detailRegion" class="screening-detail" tabindex="-1" aria-labelledby="screening-detail-title">
        <div class="screening-actions"><h3 id="screening-detail-title">{{ screeningTitle(detail.report?.report_type) }}</h3><button type="button" :disabled="busy" @click="closeDetail">Close details</button></div>
        <p v-if="error" role="alert" class="screening-error">{{ error }} <button type="button" :disabled="busy" @click="retryFailedRead">Try again</button></p>
        <dl>
          <dt>Student</dt><dd>{{ student?.full_name || 'Student ' + detail.student_id }}</dd>
          <dt>School and grade</dt><dd>{{ student ? 'School ' + student.school_id + '  /  Grade ' + student.grade_level : 'Current student details unavailable. Reload details to try again.' }}</dd>
          <dt>Screening type</dt><dd>{{ reportType(detail.report?.report_type) }}</dd>
          <dt>Model output</dt><dd>{{ detail.classification }}  /  {{ score(detail.predicted_class_score) }}</dd>
          <dt>Model version</dt><dd>{{ detail.model?.model_key ? detail.model.model_key + ' / ' + detail.model.model_version : 'Historical model identity not verified' }}</dd>
          <dt>Generated</dt><dd>{{ date(detail.date_generated) }}</dd>
          <dt>Review status</dt><dd>{{ detail.review?.status || 'Not recorded' }}</dd>
          <dt>Reviewed by</dt><dd>{{ detail.review?.expert_id ? reviewerName || 'Account ' + detail.review.expert_id : ['Validated','Flagged'].includes(detail.review?.status) ? 'Reviewer not recorded' : 'Not reviewed' }}</dd>
          <dt>Review date</dt><dd>{{ date(detail.review?.validation_date) }}</dd>
          <dt>Expert remarks</dt><dd class="screening-prose">{{ detail.review?.remarks || 'Not recorded' }}</dd>
          <dt>Expert recommendation</dt><dd class="screening-prose">{{ detail.review?.expert_recommendation || 'Not recorded' }}</dd>
          <dt>Follow-up needed</dt><dd>{{ detail.review?.follow_up_needed === true ? 'Yes' : detail.review?.follow_up_needed === false ? 'No' : 'Not recorded' }}</dd>
        </dl>
        <p>Model scores are screening outputs, not a diagnosis.</p>
        <button type="button" :disabled="busy" @click="imageUrl ? clearImage() : loadImage()">{{ imageUrl ? 'Hide handwriting image' : 'View handwriting image' }}</button>
        <img v-if="imageUrl" :src="imageUrl" alt="Submitted handwriting sample" class="screening-image" />
      </section>
    </template>
    </template>
  </section>
</template>

<script setup>
import AdminLoadingSkeleton from '../../../shared/AdminLoadingSkeleton.vue'
import AdminPageSkeleton from '../../../shared/AdminPageSkeleton.vue'
import AdminSummaryCards from '../../../shared/AdminSummaryCards.vue'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { formatScore, formatReportType } from '../utils/hosted-screenings.mjs'
const props = defineProps({ client: { type: Object, required: true }, profile: { type: Object, required: true } })
const emit = defineEmits(['access-change', 'snapshot'])
const canManage = computed(() => ['admin', 'researcher'].includes(props.profile.role) && props.profile.permissions?.includes('assignments.manage'))
const busy=ref(false), error=ref(''), message=ref(''), loaded=ref(false), rows=ref([]), cursor=ref(null)
const loadingDetail=ref(false)
const status=ref(''), grade=ref(''), detail=ref(null), student=ref(null), detailRegion=ref(null)
const reviewerName=ref(''), imageUrl=ref('')
let alive=true, filters={}, detailVersion=0
watch(() => ({ rows: rows.value, loaded: loaded.value, hasMore: Boolean(cursor.value), busy: busy.value, error: error.value, allowed: canManage.value }), value => emit('snapshot', value), { deep: true, immediate: true })
const score=formatScore, reportType=formatReportType
function screeningTitle(value){return value==='Initial Screening'?'Initial screening':value==='Follow-up Screening'?'Follow-up screening':'Screening details'}
function statusTone(value){return value==='Validated'?'success':value==='Flagged'?'danger':value==='Pending'?'warning':'secondary'}
function classificationTone(value){const label=String(value||'').toLowerCase();return label==='normal'?'success':label.includes('high potential')||label.includes('potential dysgraphia')?'danger':'secondary'}
function date(value) { if(!value)return 'Not recorded'; const parsed=new Date(value); return Number.isNaN(parsed.getTime()) ? 'Not recorded' : parsed.toLocaleString() }
function report(failure) {
  if(!alive)return
  error.value=failure.message || 'The request could not be completed.'
  if(failure.status===401 || ['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code)) emit('access-change')
}
let failedRead=null
async function run(task) { if(busy.value)return; busy.value=true;error.value='';message.value='';failedRead=null;try{await task()}catch(failure){failedRead=task;report(failure)}finally{if(alive)busy.value=false} }
function retryFailedRead(){if(failedRead)return run(failedRead)}
async function queryList(more) {
  if(!more)filters={validation_status:status.value,grade_level:grade.value}
  const query=new URLSearchParams({limit:'25'})
  for(const [key,value] of Object.entries(filters))if(value)query.set(key,value)
  if(more && cursor.value)query.set('cursor',cursor.value)
  const response=await props.client.request('/screenings?'+query,{envelope:true})
  if(!alive)return
  rows.value=more ? [...rows.value,...response.data] : response.data;cursor.value=response.page.next_cursor;loaded.value=true
}
function loadList(more=false) { return run(()=>queryList(more)) }
function clearImage() { if(imageUrl.value)URL.revokeObjectURL(imageUrl.value);imageUrl.value='' }
function closeDetail() { detailVersion++;clearImage();detail.value=null;student.value=null;reviewerName.value='';error.value='';failedRead=null }
function openDetail(id) { return run(async()=>{
  loadingDetail.value=true
  try {
  closeDetail()
  const version=detailVersion
  const result=await props.client.request('/screenings/'+id)
  if(!alive||version!==detailVersion||!canManage.value)return
  detail.value=result
  await nextTick();if(alive)detailRegion.value?.focus()
  const current=await props.client.request('/students/'+result.student_id)
  if(!alive||version!==detailVersion||!canManage.value)return
  student.value=current
  if(result.review?.expert_id&&props.profile.permissions?.includes('accounts.manage')){
    try{const person=await props.client.request('/accounts/'+encodeURIComponent(result.review.expert_id));if(alive&&version===detailVersion&&props.profile.permissions?.includes('accounts.manage'))reviewerName.value=person.full_name}catch(failure){if(alive&&version===detailVersion&&failure.status===401)report(failure)}
  }
  } finally { loadingDetail.value=false }
}) }
function loadImage() { return run(async()=>{
  clearImage()
  const blob=await props.client.request('/screenings/'+detail.value.result_id+'/image',{image:true})
  if(alive)imageUrl.value=URL.createObjectURL(blob)
}) }
watch(()=>props.profile.permissions?.includes('accounts.manage'),allowed=>{if(!allowed)reviewerName.value=''})
watch(canManage, allowed=>{
  if(allowed)loadList()
  else {closeDetail();rows.value=[];cursor.value=null;loaded.value=false;error.value='';message.value=''}
},{immediate:true})
onBeforeUnmount(()=>{alive=false;clearImage()})
function showReviewStatus(value){if(busy.value||!canManage.value||!['Pending','Validated','Flagged'].includes(value))return;closeDetail();status.value=value;grade.value='';return loadList(false)}
defineExpose({ openResult: openDetail, refresh: loadList, showReviewStatus })
</script>

<style scoped>
.hosted-screenings{margin-top:32px;padding-top:24px;border-top:1px solid #d4dfd8;color:#17382d}.hosted-screenings h2{font-size:24px;margin:0 0 20px}.hosted-screenings h3{font-size:20px;margin:0}.hosted-screenings h4{font-size:18px;margin:0}.hosted-screenings button{min-height:44px;padding:10px 16px;border:1px solid #9bab9f;border-radius:8px;background:#fff;color:#17382d;font:inherit;cursor:pointer}.hosted-screenings button:hover{background:#edf4ee}.hosted-screenings button:disabled{opacity:.6;cursor:default}.hosted-screenings :is(button,select,[tabindex]):focus-visible{outline:3px solid #287b59;outline-offset:3px}.hosted-screenings label{display:flex;flex-direction:column;gap:8px;font-weight:600;min-width:0}.hosted-screenings select{min-height:48px;padding:10px 12px;border:1px solid #9bab9f;border-radius:8px;background:#fff;color:#17382d;font:inherit;width:100%}.screening-filters{display:grid;grid-template-columns:1fr 1fr auto;align-items:end;gap:16px}.screening-list{list-style:none;padding:0;margin:20px 0}.screening-list li{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 0;border-bottom:1px solid #d4dfd8}.screening-list span{display:block;color:#466056;margin-top:4px}.screening-list button{flex-shrink:0}.screening-detail{margin-top:28px;padding-top:24px;border-top:1px solid #9bab9f;overflow-wrap:anywhere}.screening-actions{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:24px}.screening-actions h3{margin-right:auto}.screening-detail dl{display:grid;grid-template-columns:minmax(120px,1fr) minmax(0,3fr);gap:12px 24px}.screening-detail dt{font-weight:600}.screening-detail dd{margin:0}.screening-prose{white-space:pre-wrap}.screening-image{display:block;max-width:100%;max-height:560px;object-fit:contain;margin:20px 0}.assignment-form{display:flex;flex-direction:column;gap:16px;margin-top:28px;padding-top:24px;border-top:1px solid #d4dfd8}.assignment-form button{align-self:flex-start}.screening-error{padding:14px;background:#fff0ed;color:#922c24;border-radius:8px}@media(max-width:600px){.screening-filters{grid-template-columns:1fr}.screening-list li{align-items:stretch;flex-direction:column}.screening-detail dl{grid-template-columns:1fr;gap:6px}.screening-detail dd{margin-bottom:12px}.assignment-form button{align-self:stretch}}
</style>
