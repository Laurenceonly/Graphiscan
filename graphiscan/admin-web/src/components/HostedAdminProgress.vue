<template>
  <section class="hosted-progress compact-page">
    <AdminPageSkeleton v-if="studentsLoading" filters label="Loading progress" />
    <template v-else>
    <header class="page-header compact-header admin-page-header"><h1 tabindex="-1">Student Progress</h1></header>
    <section class="panel-card compact-panel progress-chart-panel">
      <h2>{{ students.find(student => String(student.student_id) === studentId)?.full_name || 'Select a student below' }}</h2>
      <div class="progress-chart-stage" :aria-busy="busy">
        <StudentScreeningChart :rows="rows" :busy="busy" />
        <div v-if="!rows.length" class="progress-chart-message" role="status">
          <template v-if="busy"><span class="progress-loading-mark" aria-hidden="true"></span><p>Loading screenings...</p></template>
          <template v-else-if="error"><p role="alert">{{ error }}</p><button type="button" class="small-action-btn" @click="loadHistory">Try again</button></template>
          <p v-else-if="!studentId">{{ students.length ? 'Select a student below to view their screenings.' : 'No students are available.' }}</p>
          <p v-else-if="loaded">No screenings recorded for this student.</p>
        </div>
        <p v-if="error && rows.length" class="progress-refresh-error" role="alert">{{ error }}</p>
      </div>
    </section>
    <section class="panel-card compact-panel progress-students-panel">
      <h2>Students</h2>
      <div class="progress-search"><AdminSearchIcon aria-hidden="true" /><input id="progress-search" v-model="search" aria-label="Search student name" type="search" placeholder="Search student name" /></div>
      <p class="history-hint">{{ filteredStudents.length }} {{ filteredStudents.length === 1 ? 'student' : 'students' }} shown</p>
      <div ref="studentList" class="table-wrapper compact-table-scroll" role="region" aria-label="Students" tabindex="0"><table><thead><tr><th>Student name</th><th>Student ID</th><th>Grade</th><th>Action</th></tr></thead><tbody>
      <tr v-for="student in filteredStudents" :key="student.student_id" :class="{ 'progress-student-selected': String(student.student_id) === studentId }"><td data-label="Student name">{{ student.full_name }}</td><td data-label="Student ID">{{ student.student_id }}</td><td data-label="Grade">{{ student.grade_level || 'Not recorded' }}</td><td data-label="Action"><button type="button" class="small-action-btn" :aria-pressed="String(student.student_id) === studentId" @click="selectStudent(student)">View progress</button></td></tr>
      <tr v-if="!filteredStudents.length"><td colspan="4">{{ search ? 'No students match your search.' : 'No students are available.' }}</td></tr>
      </tbody></table></div>
    </section>
    </template>
  </section>
</template>
<script setup>
import AdminPageSkeleton from '../../../shared/AdminPageSkeleton.vue'
import StudentScreeningChart from './StudentScreeningChart.vue'
import AdminSearchIcon from '../../../shared/AdminSearchIcon.vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
const props=defineProps({client:{type:Object,required:true},profile:{type:Object,required:true},students:{type:Array,default:()=>[]},studentsLoading:Boolean})
const emit=defineEmits(['access-change','open-result'])
const studentId=ref(''),rows=ref([]),busy=ref(false),loaded=ref(false),error=ref(''),loadingCount=ref(0)
let alive=true,requestVersion=0
const search=ref('')
const studentList=ref(null)
watch(search,()=>{if(studentList.value)studentList.value.scrollTop=0},{flush:'post'})
const filteredStudents=computed(()=>props.students.filter(student=>String(student.full_name||'').toLowerCase().includes(search.value.trim().toLowerCase())))
function selectStudent(student){studentId.value=String(student.student_id);loadHistory()}
function clear(){requestVersion++;rows.value=[];loaded.value=false;error.value='';busy.value=false;loadingCount.value=0}
watch(studentId,clear,{flush:'sync'})
watch(()=>props.profile,()=>{studentId.value='';clear()})
watch(()=>props.students,students=>{if(studentId.value&&!students.some(student=>String(student.student_id)===studentId.value))studentId.value=''}, {deep:true})
async function loadHistory(){
  if(busy.value||!studentId.value)return
  busy.value=true;error.value='';loadingCount.value=0
  const version=++requestVersion,target=studentId.value
  try{
    const collected=[],seen=new Set();let cursor=null
    do{
      const query=new URLSearchParams({limit:'100',order:'oldest'});if(cursor)query.set('cursor',cursor)
      const response=await props.client.request('/students/'+encodeURIComponent(target)+'/history?'+query,{envelope:true})
      if(!alive||version!==requestVersion)return
      collected.push(...response.data);loadingCount.value=collected.length;cursor=response.page?.next_cursor||null
      if(cursor&&seen.has(cursor))throw new Error('Screening history could not be completed. Try again.')
      if(cursor)seen.add(cursor)
    }while(cursor)
    rows.value=[...new Map(collected.map(row=>[String(row.result_id),row])).values()];loaded.value=true
  }catch(failure){if(!alive||version!==requestVersion)return;error.value=failure.message||'Screening history could not be loaded.';if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code))emit('access-change')}
  finally{if(alive&&version===requestVersion)busy.value=false}
}
onBeforeUnmount(()=>{alive=false})
</script>
<style scoped>input[type="search"]{width:100%;min-height:48px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:inherit}
.hosted-progress{display:flex;flex-direction:column;gap:24px;min-height:0}.hosted-progress .compact-panel{flex:none;min-height:0;padding:24px;border-radius:12px}.hosted-progress .compact-header{margin:0}.history-summary{margin:0;gap:16px}.history-summary .user-summary-card{min-height:100px;padding:20px}.history-summary strong{font-size:28px}h1{font-size:28px;margin:0}.compact-panel h2{margin:0 0 20px;font-size:18px;font-weight:600}.history-toolbar{display:flex;align-items:end;gap:16px;flex-wrap:wrap}label{display:grid;gap:8px;font-size:14px;font-weight:500;flex:1;min-width:180px}select{min-height:48px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:400 16px/1.5 var(--font-ui)}.history-hint{font-size:12px;color:var(--muted);margin:20px 0}.table-wrapper{margin:24px 0;border:1px solid var(--border);border-radius:12px}table{min-width:850px}td{white-space:normal}button:focus-visible,select:focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}@media(max-width:700px){table{min-width:0}.history-summary{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.history-summary .user-summary-card{min-height:100px;padding:14px}.hosted-progress .compact-panel{padding:20px}.history-toolbar{align-items:stretch}.history-toolbar label{min-width:0;width:100%;flex:auto}}
</style>
