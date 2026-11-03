<template>
  <section class="school-people" aria-labelledby="school-people-title">
    <header><div><h3 id="school-people-title">{{ school.name }}</h3><p>Choose a grade to view students and assigned staff.</p></div><div class="school-grade-actions"><button v-if="canAddStudent" type="button" class="primary-action-btn" @click="$emit('add-student', Number(grade))">Add student</button><button type="button" class="small-action-btn" @click="$emit('close')">Close</button></div></header>
    <nav class="school-grades" aria-label="School grades"><button v-for="level in 3" :key="level" type="button" :aria-pressed="grade === String(level)" @click="grade = String(level)">Grade {{ level }}</button></nav>
    <section aria-labelledby="school-students-title">
      <h4 id="school-students-title">Grade {{ grade }} students</h4>
      <p v-if="studentError" role="alert">{{ studentError }} <button type="button" @click="loadStudents(false)">Try again</button></p>
      <AdminLoadingSkeleton v-if="studentBusy && !students.length" label="Loading students…" :rows="3" />
      <p v-else-if="studentsLoaded && !students.length">No students are available in Grade {{ grade }} for this school.</p>
      <div v-if="students.length" class="table-wrapper compact-table-scroll"><table><thead><tr><th>Student</th><th>Assigned teacher</th><th>Parent or guardian</th><th>Action</th></tr></thead><tbody><tr v-for="student in students" :key="student.student_id"><td data-label="Student">{{ student.full_name }}</td><td data-label="Assigned teacher">{{ personName(student.teacher_id, 'No teacher assigned') }}</td><td data-label="Parent or guardian">{{ personName(student.parent_id, 'No linked parent') }}</td><td data-label="Action"><button type="button" class="small-action-btn" :aria-label="'View student ' + student.full_name" @click="$emit('view-student', student.student_id)">View student</button></td></tr></tbody></table></div>
      <button v-if="studentCursor" type="button" :disabled="studentBusy" @click="loadStudents(true)">Load more students</button>
    </section>
    <section aria-labelledby="school-experts-title">
      <h4 id="school-experts-title">Grade {{ grade }} screening reviews</h4>
      <p>Assigned experts are shown per screening.{{ screeningCursor ? ' Load more to see additional records.' : '' }}</p>
      <p v-if="screeningError" role="alert">{{ screeningError }} <button type="button" @click="loadScreenings(false)">Try again</button></p>
      <AdminLoadingSkeleton v-if="screeningBusy && !screenings.length" label="Loading screening assignments…" :rows="3" />
      <p v-else-if="screeningsLoaded && !screenings.length">No screening records are available in Grade {{ grade }} for this school.</p>
      <div v-if="screenings.length" class="table-wrapper compact-table-scroll"><table><thead><tr><th>Student</th><th>Screening</th><th>Assigned expert</th></tr></thead><tbody><tr v-for="row in screenings" :key="row.result_id"><td data-label="Student">{{ studentName(row.student_id) }}</td><td data-label="Screening">Result {{ row.result_id }}</td><td data-label="Assigned expert">{{ personName(row.review?.assigned_expert_id, 'No expert assigned') }}</td></tr></tbody></table></div>
      <button v-if="screeningCursor" type="button" :disabled="screeningBusy" @click="loadScreenings(true)">Load more screenings</button>
    </section>
  </section>
</template>
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AdminLoadingSkeleton from '../../../shared/AdminLoadingSkeleton.vue'
const props=defineProps({school:{type:Object,required:true},client:{type:Object,required:true},profile:{type:Object,required:true},canAddStudent:Boolean,refreshKey:{type:Number,default:0}})
const emit=defineEmits(['close','access-change','add-student','view-student'])
const grade=ref('1')
const students=ref([]),screenings=ref([]),names=ref({}),studentCursor=ref(null),screeningCursor=ref(null),studentBusy=ref(false),screeningBusy=ref(false),studentsLoaded=ref(false),screeningsLoaded=ref(false),studentError=ref(''),screeningError=ref('')
let alive=true,selectionVersion=0
function accessFailure(error){if(error.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(error.code))emit('access-change')}
function personName(id,empty){return id?(names.value[id] || 'Account '+id):empty}
function studentName(id){return students.value.find(s=>String(s.student_id)===String(id))?.full_name || 'Student '+id}
async function resolveNames(ids){if(!props.profile.permissions?.includes('accounts.manage'))return;const version=selectionVersion,unique=[...new Set(ids.filter(id=>id&&!names.value[id]))];await Promise.all(unique.map(async id=>{try{const user=await props.client.request('/accounts/'+encodeURIComponent(id));if(alive&&version===selectionVersion&&props.profile.permissions?.includes('accounts.manage')&&user?.full_name)names.value={...names.value,[id]:user.full_name+(user.account_status&&user.account_status!=='active'?' ('+user.account_status+')':'')}}catch(error){accessFailure(error)}}))}
async function loadStudents(more){if(studentBusy.value)return;const version=selectionVersion;studentBusy.value=true;studentError.value='';try{const q=new URLSearchParams({school_id:String(props.school.school_id),grade_level:grade.value,limit:'25'});if(more&&studentCursor.value)q.set('cursor',studentCursor.value);const result=await props.client.request('/students?'+q,{envelope:true});if(!alive||version!==selectionVersion)return;students.value=more?[...students.value,...result.data]:result.data;studentCursor.value=result.page.next_cursor;studentsLoaded.value=true;await resolveNames(result.data.flatMap(s=>[s.teacher_id,s.parent_id]))}catch(error){if(alive&&version===selectionVersion){studentError.value=error.message||'Students could not be loaded.';accessFailure(error)}}finally{if(alive&&version===selectionVersion)studentBusy.value=false}}
async function loadScreenings(more){if(screeningBusy.value)return;const version=selectionVersion;screeningBusy.value=true;screeningError.value='';try{const q=new URLSearchParams({school_id:String(props.school.school_id),grade_level:grade.value,limit:'25'});if(more&&screeningCursor.value)q.set('cursor',screeningCursor.value);const result=await props.client.request('/screenings?'+q,{envelope:true});if(!alive||version!==selectionVersion)return;screenings.value=more?[...screenings.value,...result.data]:result.data;screeningCursor.value=result.page.next_cursor;screeningsLoaded.value=true;await resolveNames(result.data.map(r=>r.review?.assigned_expert_id))}catch(error){if(alive&&version===selectionVersion){screeningError.value=error.message||'Screening assignments could not be loaded.';accessFailure(error)}}finally{if(alive&&version===selectionVersion)screeningBusy.value=false}}
function reloadGrade(){selectionVersion++;students.value=[];screenings.value=[];studentCursor.value=null;screeningCursor.value=null;studentsLoaded.value=false;screeningsLoaded.value=false;studentError.value='';screeningError.value='';studentBusy.value=false;screeningBusy.value=false;loadStudents(false);loadScreenings(false)}
watch(grade,reloadGrade)
watch(()=>props.refreshKey,()=>{names.value={};reloadGrade()})
watch(()=>props.profile,()=>{names.value={};reloadGrade()})
onMounted(()=>{loadStudents(false);loadScreenings(false)})
onBeforeUnmount(()=>{alive=false})
</script>
<style scoped>
.school-people .school-grade-actions>button{display:inline-flex;align-items:center;justify-content:center;width:auto;min-height:44px;white-space:nowrap}
.school-people .school-grade-actions>.primary-action-btn{padding:10px 16px;border:1px solid var(--blue-700);border-radius:8px;background:var(--blue-700);color:var(--white);font:600 14px/1.5 var(--font-ui);cursor:pointer}
.school-people .school-grade-actions>.primary-action-btn:hover{background:var(--blue-hover);border-color:var(--blue-hover)}
.school-people{display:grid;gap:24px;padding:24px;border:1px solid var(--border);border-radius:14px;background:var(--white)}header{display:flex;justify-content:space-between;align-items:start;gap:16px}h3,h4,p{margin:0}h3{font-size:18px}h4{font-size:16px}p{color:var(--muted);margin-top:8px}section section{display:grid;gap:12px}section section p{margin:0}.table-wrapper{margin:0!important}table{min-width:0!important;width:100%}button{align-self:start}.school-grade-actions,.school-grades{display:flex;gap:12px;flex-wrap:wrap}.school-grades button{min-height:44px;padding:10px 20px;border:1px solid var(--border);border-radius:8px;background:var(--white);color:var(--text);font:500 14px var(--font-ui);cursor:pointer}.school-grades button[aria-pressed=true]{border-color:var(--brand-blue);background:var(--blue-50);color:var(--blue-700)}.school-grades button:focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}@media(max-width:700px){.school-people{padding:20px}.school-people>header{flex-direction:column}.school-grade-actions{width:100%}.school-grades{gap:8px}.school-grades button{flex:1;padding:10px 12px}}
</style>
