<template>
  <section class="hosted-screenings" aria-labelledby="screenings-title" :aria-busy="busy">
    <h2 id="screenings-title">Screening results</h2>
    <p v-if="!canManage">Screening records require permission to manage assignments for the relevant school.</p>
    <template v-else>
      <form class="screening-filters" @submit.prevent="loadList(false)">
        <label>Validation status<select v-model="status" :disabled="busy"><option value="">All statuses</option><option>Pending</option><option>Validated</option><option>Flagged</option></select></label>
        <label>Grade<select v-model="grade" :disabled="busy"><option value="">All grades</option><option v-for="value in 3" :key="value" :value="String(value)">Grade {{ value }}</option></select></label>
        <button type="submit" :disabled="busy">Refresh results</button>
      </form>
      <p v-if="error" role="alert" class="screening-error">{{ error }}</p>
      <p v-if="message" role="status">{{ message }}</p>
      <p v-if="busy" role="status">Loading or saving screening records…</p>
      <p v-if="!loaded && !busy">Screening results have not loaded. Use Refresh results to try again.</p>
      <p v-if="loaded && !rows.length && !busy">No screening results are available for your account and these filters.</p>
      <ul class="screening-list">
        <li v-for="row in rows" :key="row.result_id">
          <div><strong>{{ row.classification }}</strong><span>Student {{ row.student_id }} · {{ reportType(row.report?.report_type) }}</span><span>{{ row.review?.status || 'Not recorded' }} · {{ date(row.date_generated) }}</span></div>
          <button type="button" :disabled="busy" @click="openDetail(row.result_id)">View result {{ row.result_id }}</button>
        </li>
      </ul>
      <button v-if="cursor" type="button" :disabled="busy" @click="loadList(true)">Load more results</button>
      <section v-if="detail" ref="detailRegion" class="screening-detail" tabindex="-1" aria-labelledby="screening-detail-title">
        <div class="screening-actions"><h3 id="screening-detail-title">Result {{ detail.result_id }}</h3><button type="button" :disabled="busy" @click="openDetail(detail.result_id)">Reload details</button><button type="button" :disabled="busy" @click="closeDetail">Close details</button></div>
        <dl>
          <dt>Student</dt><dd>{{ student?.full_name || 'Student ' + detail.student_id }}</dd>
          <dt>School and grade</dt><dd>{{ student ? 'School ' + student.school_id + ' · Grade ' + student.grade_level : 'Current student details unavailable. Reload details to try again.' }}</dd>
          <dt>Screening type</dt><dd>{{ reportType(detail.report?.report_type) }}</dd>
          <dt>Model output</dt><dd>{{ detail.classification }} · {{ score(detail.predicted_class_score) }}</dd>
          <dt>Model version</dt><dd>{{ detail.model?.model_key ? detail.model.model_key + ' / ' + detail.model.model_version : 'Historical model identity not verified' }}</dd>
          <dt>Generated</dt><dd>{{ date(detail.date_generated) }}</dd>
          <dt>Review status</dt><dd>{{ detail.review?.status || 'Not recorded' }}</dd>
          <dt>Assigned expert</dt><dd>{{ expertName(detail.review?.assigned_expert_id) }}</dd>
          <dt>Reviewed by</dt><dd>{{ detail.review?.expert_id || 'Not recorded' }}</dd>
          <dt>Review date</dt><dd>{{ date(detail.review?.validation_date) }}</dd>
          <dt>Expert remarks</dt><dd class="screening-prose">{{ detail.review?.remarks || 'Not recorded' }}</dd>
          <dt>Expert recommendation</dt><dd class="screening-prose">{{ detail.review?.expert_recommendation || 'Not recorded' }}</dd>
          <dt>Follow-up needed</dt><dd>{{ detail.review?.follow_up_needed === true ? 'Yes' : detail.review?.follow_up_needed === false ? 'No' : 'Not recorded' }}</dd>
        </dl>
        <p>Model scores are screening outputs, not a diagnosis.</p>
        <button type="button" :disabled="busy" @click="loadImage">{{ imageUrl ? 'Reload handwriting image' : 'View handwriting image' }}</button>
        <img v-if="imageUrl" :src="imageUrl" alt="Submitted handwriting sample" class="screening-image" />
        <form v-if="student" class="assignment-form" @submit.prevent="saveAssignment">
          <h4>Expert assignment</h4>
          <p>Choose an active expert eligible for this student's current school. Reassignment preserves existing review authorship and status.</p>
          <label for="hosted-assigned-expert">Assigned expert</label><select id="hosted-assigned-expert" v-model="selectedExpert" :disabled="busy || mustReload || !optionsLoaded">
            <option value="">No assigned expert</option>
            <option v-if="selectedExpert && !experts.some(person => person.user_id === selectedExpert)" :value="selectedExpert" disabled>Current expert — eligibility not confirmed</option>
            <option v-for="person in experts" :key="person.user_id" :value="person.user_id">{{ person.full_name }}</option>
          </select>
          <p v-if="optionsLoaded && !experts.length">No eligible experts loaded.{{ optionCursor ? ' Load more choices to continue.' : ' Ask your administrator to check school eligibility.' }}</p>
          <button v-if="optionCursor" type="button" :disabled="busy || mustReload" @click="loadMoreOptions">Load more eligible people</button>
          <p v-if="mustReload" role="status">Reload details and check the current assignment before saving again.</p>
          <button type="submit" :disabled="busy || mustReload || !optionsLoaded || !assignmentChanged || !validSelection">Save expert assignment</button>
        </form>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { formatScore, formatReportType } from '../utils/hosted-screenings.mjs'
const props = defineProps({ client: { type: Object, required: true }, profile: { type: Object, required: true } })
const emit = defineEmits(['access-change'])
const canManage = computed(() => ['admin', 'researcher'].includes(props.profile.role) && props.profile.permissions?.includes('assignments.manage'))
const busy=ref(false), error=ref(''), message=ref(''), loaded=ref(false), rows=ref([]), cursor=ref(null)
const status=ref(''), grade=ref(''), detail=ref(null), student=ref(null), detailRegion=ref(null)
const experts=ref([]), optionCursor=ref(null), optionsLoaded=ref(false), selectedExpert=ref(''), mustReload=ref(false), imageUrl=ref('')
let alive=true, filters={}
const score=formatScore, reportType=formatReportType
const assignmentChanged=computed(() => selectedExpert.value !== (detail.value?.review?.assigned_expert_id || ''))
const validSelection=computed(() => !selectedExpert.value || experts.value.some(person => person.user_id === selectedExpert.value))
function date(value) { if(!value)return 'Not recorded'; const parsed=new Date(value); return Number.isNaN(parsed.getTime()) ? 'Not recorded' : parsed.toLocaleString() }
function expertName(id) { return id ? experts.value.find(person=>person.user_id===id)?.full_name || id : 'No assigned expert' }
function report(failure) {
  if(!alive)return
  error.value=failure.message || 'The request could not be completed.'
  if(failure.status===401 || ['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code)) emit('access-change')
}
async function run(task) { if(busy.value)return; busy.value=true;error.value='';message.value='';try{await task()}catch(failure){report(failure)}finally{if(alive)busy.value=false} }
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
function closeDetail() { clearImage();detail.value=null;student.value=null;experts.value=[];optionCursor.value=null;optionsLoaded.value=false;mustReload.value=false }
async function queryOptions(more=false) {
  const query=new URLSearchParams({limit:'25'})
  if(more && optionCursor.value)query.set('cursor',optionCursor.value)
  const response=await props.client.request('/schools/'+student.value.school_id+'/assignment-options?'+query,{envelope:true})
  if(!alive)return
  const eligible=response.data.filter(person=>person.role==='expert')
  experts.value=more ? [...experts.value,...eligible] : eligible;optionCursor.value=response.page.next_cursor;optionsLoaded.value=true
}
function loadMoreOptions() { return run(()=>queryOptions(true)) }
function openDetail(id) { return run(async()=>{
  closeDetail()
  const result=await props.client.request('/screenings/'+id)
  if(!alive)return
  detail.value=result;selectedExpert.value=result.review?.assigned_expert_id || ''
  await nextTick();if(alive)detailRegion.value?.focus()
  const current=await props.client.request('/students/'+result.student_id)
  if(!alive)return
  student.value=current;await queryOptions()
}) }
function loadImage() { return run(async()=>{
  clearImage()
  const blob=await props.client.request('/screenings/'+detail.value.result_id+'/image',{image:true})
  if(alive)imageUrl.value=URL.createObjectURL(blob)
}) }
function saveAssignment() { return run(async()=>{
  if(mustReload.value || !optionsLoaded.value || !assignmentChanged.value || !validSelection.value)return
  const id=detail.value.result_id
  let result
  try {
    result=await props.client.request('/screenings/'+id+'/expert-assignment',{method:'PATCH',body:{assigned_expert_id:selectedExpert.value || null,expected_revision:detail.value.revision}})
  } catch(failure) {
    if(alive){mustReload.value=true;if(failure.status===404)closeDetail()}
    throw failure
  }
  if(!alive)return
  detail.value=result;selectedExpert.value=result.review?.assigned_expert_id || ''
  rows.value=rows.value.map(row=>row.result_id===id ? result : row)
  message.value='Expert assignment saved.'
}) }
watch(canManage, allowed=>{
  if(allowed)loadList()
  else {closeDetail();rows.value=[];cursor.value=null;loaded.value=false;error.value='';message.value=''}
},{immediate:true})
onBeforeUnmount(()=>{alive=false;clearImage()})
</script>

<style scoped>
.hosted-screenings{margin-top:32px;padding-top:24px;border-top:1px solid #d4dfd8;color:#17382d}.hosted-screenings h2{font-size:24px;margin:0 0 20px}.hosted-screenings h3{font-size:20px;margin:0}.hosted-screenings h4{font-size:18px;margin:0}.hosted-screenings button{min-height:44px;padding:10px 16px;border:1px solid #9bab9f;border-radius:8px;background:#fff;color:#17382d;font:inherit;cursor:pointer}.hosted-screenings button:hover{background:#edf4ee}.hosted-screenings button:disabled{opacity:.6;cursor:default}.hosted-screenings :is(button,select,[tabindex]):focus-visible{outline:3px solid #287b59;outline-offset:3px}.hosted-screenings label{display:flex;flex-direction:column;gap:8px;font-weight:600;min-width:0}.hosted-screenings select{min-height:48px;padding:10px 12px;border:1px solid #9bab9f;border-radius:8px;background:#fff;color:#17382d;font:inherit;width:100%}.screening-filters{display:grid;grid-template-columns:1fr 1fr auto;align-items:end;gap:16px}.screening-list{list-style:none;padding:0;margin:20px 0}.screening-list li{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 0;border-bottom:1px solid #d4dfd8}.screening-list span{display:block;color:#466056;margin-top:4px}.screening-list button{flex-shrink:0}.screening-detail{margin-top:28px;padding-top:24px;border-top:1px solid #9bab9f;overflow-wrap:anywhere}.screening-actions{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:24px}.screening-actions h3{margin-right:auto}.screening-detail dl{display:grid;grid-template-columns:minmax(120px,1fr) minmax(0,3fr);gap:12px 24px}.screening-detail dt{font-weight:600}.screening-detail dd{margin:0}.screening-prose{white-space:pre-wrap}.screening-image{display:block;max-width:100%;max-height:560px;object-fit:contain;margin:20px 0}.assignment-form{display:flex;flex-direction:column;gap:16px;margin-top:28px;padding-top:24px;border-top:1px solid #d4dfd8}.assignment-form button{align-self:flex-start}.screening-error{padding:14px;background:#fff0ed;color:#922c24;border-radius:8px}@media(max-width:600px){.screening-filters{grid-template-columns:1fr}.screening-list li{align-items:stretch;flex-direction:column}.screening-detail dl{grid-template-columns:1fr;gap:6px}.screening-detail dd{margin-bottom:12px}.assignment-form button{align-self:stretch}}
</style>
