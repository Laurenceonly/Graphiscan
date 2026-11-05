<template>
  <dialog ref="dialog" class="account-action-dialog role-assignments-dialog" aria-labelledby="role-assignments-title" @cancel.prevent="close">
    <form class="account-editor-form" @submit.prevent="save">
      <header><h2 id="role-assignments-title">Manage assignments</h2><button type="button" class="editor-close" aria-label="Close assignments" :disabled="cannotClose" @click="close"><X :size="18" aria-hidden="true" /></button></header>
      <p v-if="loading" role="status">Loading assignments…</p>
      <template v-if="loaded">
        <p v-if="target.role === 'expert'">This expert reviews all students and screenings in the assigned schools and grades. Changing these assignments changes their access.</p>
        <div class="role-assignment-filters"><label>School<select v-model="school" :disabled="busy || uncertain"><option value="" disabled>Choose a school</option><option v-for="item in availableSchools" :key="item.school_id" :value="String(item.school_id)">{{ item.name }}</option></select></label><label v-if="parent">Grade<select v-model="grade" :disabled="busy || uncertain"><option v-for="level in 3" :key="level" :value="String(level)">Grade {{ level }}</option></select></label></div>
        <button v-if="schoolCursor" type="button" class="soft-action-btn" :disabled="busy || uncertain || schoolsBusy" @click="loadMoreSchools">Load more schools</button>
        <p v-if="schoolsError" role="alert">{{ schoolsError }}</p>
        <template v-if="!parent">
          <fieldset class="role-grade-options" :disabled="busy || uncertain || !school"><legend>Grades</legend><label v-for="level in 3" :key="level"><input v-model="selectedGrades" type="checkbox" :value="level" />Grade {{ level }}</label></fieldset>
          <section class="role-assignment-summary" aria-label="Assigned schools and grades"><h3>Assigned schools and grades</h3><p v-if="!groupedScopes.length">No schools or grades assigned.</p><div v-for="item in groupedScopes" :key="item.school_id" class="role-assignment-row"><div><strong>{{ schoolName(item.school_id) }}</strong><small>{{ item.grades.map(value => 'Grade ' + value).join(', ') }}</small></div><button type="button" class="soft-action-btn" :aria-label="'Remove ' + schoolName(item.school_id)" :disabled="busy || uncertain" @click="removeSchool(item.school_id)">Remove</button></div></section>
        </template>
        <template v-else>
          <p v-if="!canLinkStudents">Student links require assignment-management access.</p>
          <p v-if="studentsBusy" role="status">Loading students…</p><p v-if="studentsError" role="alert">{{ studentsError }} <button type="button" class="soft-action-btn" :disabled="studentsBusy" @click="loadStudents(false)">Try again</button></p>
          <div v-if="canLinkStudents" class="role-student-options" aria-label="Students in selected school and grade"><label v-for="student in students" :key="student.student_id"><input type="checkbox" :checked="isLinked(student)" :disabled="busy || uncertain || studentsBusy" @change="toggleStudent(student, $event.target.checked)" /><span><strong>{{ student.full_name }}</strong><small>Student {{ student.student_id }} · Grade {{ student.grade_level }}</small><small v-if="student.parent_id && student.parent_id !== target.user_id">{{ isLinked(student) ? 'Saving will replace the existing parent link.' : 'Linked to another parent' }}</small></span></label><p v-if="!studentsBusy && studentsLoaded && !students.length">No students in this school and grade.</p></div>
          <button v-if="studentCursor" type="button" class="soft-action-btn" :disabled="busy || uncertain || studentsBusy" @click="loadStudents(true)">Load more students</button>
          <section class="role-assignment-summary" aria-label="Linked students"><h3>Linked students</h3><p v-if="!linkedStudents.length">No linked students in your access scope.</p><div v-for="student in linkedStudents" :key="student.student_id" class="role-assignment-row"><div><strong>{{ student.full_name }}</strong><small>{{ schoolName(student.school_id) }} · Grade {{ student.grade_level }}</small></div><button type="button" class="soft-action-btn" :aria-label="'Unlink ' + student.full_name" :disabled="busy || uncertain" @click="toggleStudent(student, false)">Unlink</button></div></section>
        </template>
      </template>
      <p v-if="error" class="error-message" role="alert">{{ error }} <button v-if="!loaded && !uncertain" type="button" class="soft-action-btn" :disabled="busy" @click="load">Try again</button></p><p v-if="message" role="status">{{ message }}</p>
      <footer><button type="button" class="soft-action-btn" :disabled="cannotClose" @click="close">{{ uncertain ? 'Close' : 'Cancel' }}</button><button type="submit" class="primary-action-btn" :disabled="busy || (!uncertain && (!loaded || !changed))">{{ saving ? 'Saving…' : uncertain ? 'Reload assignments' : 'Save assignments' }}</button></footer>
    </form>
  </dialog>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { X } from 'lucide-vue-next'
const props=defineProps({client:{type:Object,required:true},target:{type:Object,required:true},profile:{type:Object,required:true},schools:{type:Array,default:()=>[]},schoolNote:{type:String,default:''}})
const emit=defineEmits(['close','completed','navigation-block','access-change'])
const dialog=ref(null),snapshot=ref(null),loading=ref(false),loaded=ref(false),saving=ref(false),error=ref(''),message=ref(''),uncertain=ref(false),checked=ref(false)
const school=ref(''),grade=ref('1'),scopes=ref([]),studentChanges=ref({}),knownStudents=ref({}),students=ref([]),studentCursor=ref(null),studentsBusy=ref(false),studentsLoaded=ref(false),studentsError=ref('')
const extraSchools=ref([]),schoolCursor=ref(null),schoolsBusy=ref(false),schoolsError=ref('')
const parent=computed(()=>props.target.role==='parent'),canLinkStudents=computed(()=>props.profile.permissions?.includes('assignments.manage'))
const busy=computed(()=>loading.value||saving.value),blocked=computed(()=>saving.value||(uncertain.value&&!checked.value)),cannotClose=computed(()=>busy.value||(uncertain.value&&!checked.value))
let alive=true,studentVersion=0
const availableSchools=computed(()=>[...new Map([...props.schools,...extraSchools.value,...(snapshot.value?.school_grades||[]).map(item=>({school_id:item.school_id,name:item.school_name})),...(snapshot.value?.students||[]).map(item=>({school_id:item.school_id,name:item.school_name}))].map(item=>[String(item.school_id),item])).values()])
function schoolName(id){return availableSchools.value.find(item=>String(item.school_id)===String(id))?.name||'School '+id}
const sortedScopes=value=>JSON.stringify(value.map(item=>({school_id:String(item.school_id),grade_level:Number(item.grade_level)})).sort((a,b)=>a.school_id.localeCompare(b.school_id)||a.grade_level-b.grade_level))
const selectedGrades=computed({get:()=>scopes.value.filter(item=>item.school_id===school.value).map(item=>item.grade_level),set:values=>{scopes.value=[...scopes.value.filter(item=>item.school_id!==school.value),...values.map(level=>({school_id:school.value,grade_level:level}))]}})
const groupedScopes=computed(()=>[...new Set(scopes.value.map(item=>item.school_id))].map(id=>({school_id:id,grades:scopes.value.filter(item=>item.school_id===id).map(item=>item.grade_level).sort()})))
const changed=computed(()=>parent.value?Object.keys(studentChanges.value).length>0:sortedScopes(scopes.value)!==sortedScopes(snapshot.value?.school_grades||[]))
function removeSchool(id){scopes.value=scopes.value.filter(item=>item.school_id!==id)}
function isLinked(student){return studentChanges.value[student.student_id]?.linked ?? student.parent_id===props.target.user_id}
const linkedStudents=computed(()=>Object.values(knownStudents.value).filter(isLinked))
function toggleStudent(student,linked){const next={...studentChanges.value};if(linked===(student.parent_id===props.target.user_id))delete next[student.student_id];else next[student.student_id]={student_id:student.student_id,expected_revision:student.revision,linked};studentChanges.value=next}
function accessFailure(failure){if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED','FORBIDDEN'].includes(failure.code))emit('access-change')}
async function load(){
  if(busy.value)return
  loading.value=true;error.value='';message.value=''
  try{
    const data=await props.client.request('/accounts/'+props.target.user_id+'/assignments');if(!alive)return
    if(data.role!==props.target.role)throw new Error('This user’s role changed. Close and reopen the account.')
    snapshot.value=data;scopes.value=data.school_grades.map(item=>({school_id:item.school_id,grade_level:item.grade_level}));studentChanges.value={};knownStudents.value=Object.fromEntries(data.students.map(item=>[item.student_id,item]));students.value=[];studentCursor.value=null;studentsLoaded.value=false;studentVersion++
    school.value=school.value||data.school_grades[0]?.school_id||data.students[0]?.school_id||String(availableSchools.value[0]?.school_id||'');grade.value=String(data.students[0]?.grade_level||grade.value)
    loaded.value=true;if(uncertain.value)message.value='Assignments reloaded. Review them before saving again.';uncertain.value=false;checked.value=false
  }catch(failure){if(alive){error.value=failure.message||'Assignments could not be loaded.';if(uncertain.value)checked.value=true;accessFailure(failure)}}
  finally{if(alive){loading.value=false;if(loaded.value&&parent.value&&canLinkStudents.value&&school.value)loadStudents(false)}}
}
async function loadStudents(more){
  if(!school.value||!canLinkStudents.value)return
  const version=++studentVersion;studentsBusy.value=true;studentsError.value='';if(!more){students.value=[];studentCursor.value=null;studentsLoaded.value=false}
  try{const query=new URLSearchParams({school_id:school.value,grade_level:grade.value,limit:'25'});if(more&&studentCursor.value)query.set('cursor',studentCursor.value);const result=await props.client.request('/students?'+query,{envelope:true});if(!alive||version!==studentVersion)return;students.value=more?[...students.value,...result.data]:result.data;studentCursor.value=result.page.next_cursor;studentsLoaded.value=true;knownStudents.value={...knownStudents.value,...Object.fromEntries(result.data.map(item=>[item.student_id,item]))}}
  catch(failure){if(alive&&version===studentVersion){studentsError.value=failure.message||'Students could not be loaded.';accessFailure(failure)}}finally{if(alive&&version===studentVersion)studentsBusy.value=false}
}
watch([school,grade],()=>{if(loaded.value&&parent.value&&!loading.value)loadStudents(false)})
async function loadMoreSchools(){if(schoolsBusy.value)return;schoolsBusy.value=true;schoolsError.value='';try{const query=new URLSearchParams({limit:'100'});if(schoolCursor.value)query.set('cursor',schoolCursor.value);const result=await props.client.request('/schools?'+query,{envelope:true});if(alive){extraSchools.value=[...extraSchools.value,...result.data];schoolCursor.value=result.page.next_cursor}}catch(failure){if(alive)schoolsError.value=failure.message||'Schools could not be loaded.'}finally{if(alive)schoolsBusy.value=false}}
async function save(){
  if(busy.value)return;if(uncertain.value){await load();return}if(!loaded.value||!changed.value)return
  saving.value=true;error.value=''
  const body={expected_revision:snapshot.value.revision,...(parent.value?{student_links:Object.values(studentChanges.value)}:{school_grades:scopes.value.map(item=>({...item}))})}
  try{await props.client.request('/accounts/'+props.target.user_id+'/assignments',{method:'PATCH',body});if(alive){dialog.value?.close();emit('completed','Assignments updated.')}}
  catch(failure){if(alive){error.value=failure.message||'Assignments could not be saved.';uncertain.value=failure.status===0||failure.status===409||failure.status>=500;checked.value=false;accessFailure(failure)}}finally{if(alive)saving.value=false}
}
function close(){if(cannotClose.value)return;dialog.value?.close();emit('close',uncertain.value?'Assignments were not confirmed. Reload the account before making more changes.':'')}
watch(blocked,value=>emit('navigation-block',value),{immediate:true})
onBeforeRouteLeave(()=>!blocked.value)
function beforeUnload(event){if(blocked.value){event.preventDefault();event.returnValue=''}}
onMounted(async()=>{window.addEventListener('beforeunload',beforeUnload);await nextTick();dialog.value?.showModal();await load();if(alive){dialog.value?.querySelector('select')?.focus();loadMoreSchools()}})
onBeforeUnmount(()=>{alive=false;studentVersion++;window.removeEventListener('beforeunload',beforeUnload);dialog.value?.close();emit('navigation-block',false)})
</script>
<style scoped>
.role-assignments-dialog{width:min(640px,calc(100% - 32px));max-height:calc(100dvh - 32px);overflow:auto;margin:auto;padding:0;border:1px solid var(--border);border-radius:14px;background:var(--white);color:var(--text)}.role-assignments-dialog::backdrop{background:#10182770}.account-editor-form{display:grid;gap:20px;padding:24px}.account-editor-form header{display:flex;align-items:start;justify-content:space-between;gap:16px}.account-editor-form h2{margin:0;font-size:20px}.account-editor-form h3{margin:0;font-size:14px}.account-editor-form p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}.account-editor-form label{display:grid;gap:8px;min-width:0;font-size:14px;font-weight:500}.account-editor-form select{width:100%;min-width:0;min-height:48px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:400 16px var(--font-ui)}.role-assignment-filters{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:16px}.role-assignment-filters>label:only-child{grid-column:1/-1}.role-grade-options{display:flex;flex-wrap:wrap;gap:16px;margin:0;padding:16px;border:1px solid var(--border);border-radius:8px}.role-grade-options legend{font-size:14px;padding:0 6px}.account-editor-form .role-grade-options label,.account-editor-form .role-student-options label{display:flex;flex-direction:row;align-items:start;gap:10px}.account-editor-form input[type=checkbox]{width:18px;height:18px;min-height:18px;flex:none;margin:2px 0 0;accent-color:var(--blue-700)}.role-student-options{display:grid;gap:14px;max-height:280px;overflow:auto;padding:12px;border:1px solid var(--border);border-radius:8px}.role-assignment-summary{display:grid;gap:12px}.role-assignment-row{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:12px;border-top:1px solid var(--border-soft)}.role-assignment-row>div{min-width:0}.role-assignment-row strong,.role-student-options strong{font-size:13px;overflow-wrap:anywhere}.role-assignment-row small,.role-student-options small{display:block;margin-top:4px;color:var(--muted);font-size:12px;line-height:1.5}.role-assignment-row button{flex:none}.editor-close{display:grid;place-items:center;width:40px;min-height:40px;border:0;border-radius:8px;background:transparent;color:var(--text);cursor:pointer}.account-editor-form footer{display:flex;justify-content:flex-end;gap:12px}.account-editor-form :is(button,input,select):focus-visible{outline:2px solid var(--blue-700);outline-offset:3px}.account-editor-form .error-message{color:var(--danger-text)}@media(max-width:600px){.account-editor-form{padding:20px;gap:16px}.role-assignment-filters{gap:12px}.role-assignment-row{gap:8px}}
</style>
