<template>
  <section class="school-people" aria-labelledby="school-people-title">
    <header><div><h3 id="school-people-title">{{ school.name }}</h3><p>People in records available to your account.</p></div><button type="button" class="small-action-btn" @click="$emit('close')">Close</button></header>
    <section aria-labelledby="school-students-title">
      <h4 id="school-students-title">Students and assigned teachers</h4>
      <p v-if="studentError" role="alert">{{ studentError }} <button type="button" @click="loadStudents(false)">Try again</button></p>
      <AdminLoadingSkeleton v-if="studentBusy && !students.length" label="Loading students…" :rows="3" />
      <p v-else-if="studentsLoaded && !students.length">No students are available for this school.</p>
      <div v-if="students.length" class="table-wrapper compact-table-scroll"><table><thead><tr><th>Student</th><th>Grade</th><th>Assigned teacher</th></tr></thead><tbody><tr v-for="student in students" :key="student.student_id"><td data-label="Student">{{ student.full_name }}</td><td data-label="Grade">Grade {{ student.grade_level }}</td><td data-label="Assigned teacher">{{ personName(student.teacher_id, 'No teacher assigned') }}</td></tr></tbody></table></div>
      <button v-if="studentCursor" type="button" :disabled="studentBusy" @click="loadStudents(true)">Load more students</button>
    </section>
    <section aria-labelledby="school-experts-title">
      <h4 id="school-experts-title">Experts assigned to screenings</h4>
      <p>Assignments are shown per screening.{{ screeningCursor ? ' Load more to see additional records.' : '' }}</p>
      <p v-if="screeningError" role="alert">{{ screeningError }} <button type="button" @click="loadScreenings(false)">Try again</button></p>
      <AdminLoadingSkeleton v-if="screeningBusy && !screenings.length" label="Loading screening assignments…" :rows="3" />
      <p v-else-if="screeningsLoaded && !screenings.length">No screening records are available for this school.</p>
      <div v-if="screenings.length" class="table-wrapper compact-table-scroll"><table><thead><tr><th>Student</th><th>Screening</th><th>Assigned expert</th></tr></thead><tbody><tr v-for="row in screenings" :key="row.result_id"><td data-label="Student">{{ studentName(row.student_id) }}</td><td data-label="Screening">Result {{ row.result_id }}</td><td data-label="Assigned expert">{{ personName(row.review?.assigned_expert_id, 'No expert assigned') }}</td></tr></tbody></table></div>
      <button v-if="screeningCursor" type="button" :disabled="screeningBusy" @click="loadScreenings(true)">Load more screenings</button>
    </section>
  </section>
</template>
<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AdminLoadingSkeleton from '../../../shared/AdminLoadingSkeleton.vue'
const props=defineProps({school:{type:Object,required:true},client:{type:Object,required:true},profile:{type:Object,required:true}})
const emit=defineEmits(['close','access-change'])
const students=ref([]),screenings=ref([]),names=ref({}),studentCursor=ref(null),screeningCursor=ref(null),studentBusy=ref(false),screeningBusy=ref(false),studentsLoaded=ref(false),screeningsLoaded=ref(false),studentError=ref(''),screeningError=ref('')
let alive=true
function accessFailure(error){if(error.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(error.code))emit('access-change')}
function personName(id,empty){return id?(names.value[id] || 'Account '+id):empty}
function studentName(id){return students.value.find(s=>String(s.student_id)===String(id))?.full_name || 'Student '+id}
async function resolveNames(ids){if(!props.profile.permissions?.includes('accounts.manage'))return;const unique=[...new Set(ids.filter(id=>id&&!names.value[id]))];await Promise.all(unique.map(async id=>{try{const user=await props.client.request('/accounts/'+encodeURIComponent(id));if(alive&&user?.full_name)names.value={...names.value,[id]:user.full_name}}catch(error){accessFailure(error)}}))}
async function loadStudents(more){if(studentBusy.value)return;studentBusy.value=true;studentError.value='';try{const q=new URLSearchParams({school_id:String(props.school.school_id),limit:'25'});if(more&&studentCursor.value)q.set('cursor',studentCursor.value);const result=await props.client.request('/students?'+q,{envelope:true});if(!alive)return;students.value=more?[...students.value,...result.data]:result.data;studentCursor.value=result.page.next_cursor;studentsLoaded.value=true;await resolveNames(result.data.map(s=>s.teacher_id))}catch(error){if(alive){studentError.value=error.message||'Students could not be loaded.';accessFailure(error)}}finally{if(alive)studentBusy.value=false}}
async function loadScreenings(more){if(screeningBusy.value)return;screeningBusy.value=true;screeningError.value='';try{const q=new URLSearchParams({school_id:String(props.school.school_id),limit:'25'});if(more&&screeningCursor.value)q.set('cursor',screeningCursor.value);const result=await props.client.request('/screenings?'+q,{envelope:true});if(!alive)return;screenings.value=more?[...screenings.value,...result.data]:result.data;screeningCursor.value=result.page.next_cursor;screeningsLoaded.value=true;await resolveNames(result.data.map(r=>r.review?.assigned_expert_id))}catch(error){if(alive){screeningError.value=error.message||'Screening assignments could not be loaded.';accessFailure(error)}}finally{if(alive)screeningBusy.value=false}}
onMounted(()=>{loadStudents(false);loadScreenings(false)})
onBeforeUnmount(()=>{alive=false})
</script>
<style scoped>
.school-people{display:grid;gap:24px;padding:24px;border:1px solid var(--border);border-radius:14px;background:var(--white)}header{display:flex;justify-content:space-between;align-items:start;gap:16px}h3,h4,p{margin:0}h3{font-size:18px}h4{font-size:16px}p{color:var(--muted);margin-top:8px}section section{display:grid;gap:12px}section section p{margin:0}.table-wrapper{margin:0!important}table{min-width:0!important;width:100%}button{align-self:start}@media(max-width:700px){.school-people{padding:20px}}
</style>
