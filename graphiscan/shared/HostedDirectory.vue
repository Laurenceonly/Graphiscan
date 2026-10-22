<template>
  <section class="directory" aria-labelledby="directory-title" :aria-busy="busy">
    <h2 id="directory-title">{{ adminPresentation ? (tab === 'students' ? 'Students' : 'Schools') : 'Schools and students' }}</h2>
    <section v-if="adminPresentation && tab === 'students'" class="user-summary-grid" aria-label="Loaded student counts">
      <article class="user-summary-card"><div><span>Students loaded</span><strong>{{ studentsLoaded ? students.length : '—' }}</strong></div></article>
      <article v-for="grade in 3" :key="grade" class="user-summary-card"><div><span>Grade {{ grade }} loaded</span><strong>{{ studentsLoaded ? students.filter(student => Number(student.grade_level) === grade).length : '—' }}</strong></div></article>
    </section>
    <nav class="directory-nav" aria-label="Workspace records">
      <button type="button" :aria-pressed="tab === 'students'" :disabled="busy || frozen || schoolUncertain" @click="tab = 'students'; closeForm()">Students</button>
      <button type="button" :aria-pressed="tab === 'schools'" :disabled="busy || frozen || schoolUncertain" @click="tab = 'schools'; closeForm()">Schools</button>
      <RefreshButton v-if="adminPresentation" :busy="busy" :disabled="frozen || schoolUncertain" @click="refreshRecords" />
      <button v-else type="button" :disabled="busy || frozen || schoolUncertain" @click="refreshRecords">Refresh lists</button>
    </nav>
    <p v-if="error && !(adminPresentation && formKind)" role="alert" class="directory-error">{{ error }}</p>
    <button v-if="error" type="button" :disabled="busy || frozen || schoolUncertain" @click="refreshRecords">Retry loading records</button>
    <p v-if="message" role="status" class="directory-message">{{ message }}</p>
    <template v-if="tab === 'students'">
      <form class="directory-filters" @submit.prevent="loadStudents(false)">
        <label>Search students<input v-model="search" maxlength="120" type="search" :disabled="busy || frozen || schoolUncertain" /></label>
        <label>School<select v-model="filterSchool" :disabled="busy || frozen || schoolUncertain"><option value="">All available schools</option><option v-for="school in schools" :key="school.school_id" :value="school.school_id">{{ school.name }}</option></select></label>
        <label>Grade<select v-model="filterGrade" :disabled="busy || frozen || schoolUncertain"><option value="">All grades</option><option v-for="grade in 3" :key="grade" :value="String(grade)">Grade {{ grade }}</option></select></label>
        <button type="submit" :disabled="busy || frozen || schoolUncertain">Apply filters</button>
      </form>
      <div class="directory-toolbar"><p>{{ studentsLoaded ? students.length + ' students loaded' : 'Student records not loaded' }}</p><button v-if="canWriteStudents" type="button" :disabled="busy || frozen || schoolUncertain" @click="newStudent">Add student</button></div>
      <p v-if="studentsLoaded && !students.length && !busy">No students are available for this account and these filters.</p>
      <div v-if="adminPresentation && students.length" class="table-wrapper compact-table-scroll hosted-students-table" role="region" aria-label="Student records" tabindex="0">
        <table><thead><tr><th>Student</th><th>School</th><th>Grade</th><th>Teacher</th><th>Parent / Guardian</th><th>Action</th></tr></thead><tbody>
          <tr v-for="student in students" :key="student.student_id">
            <td data-label="Student"><div class="user-cell"><span class="user-avatar">{{ student.full_name?.charAt(0) || 'S' }}</span><div><strong>{{ student.full_name }}</strong><small class="table-subtext">Student {{ student.student_id }}</small></div></div></td>
            <td data-label="School">{{ schoolName(student.school_id) }}</td><td data-label="Grade">Grade {{ student.grade_level }}</td>
            <td data-label="Teacher">{{ student.teacher_name || (student.teacher_id ? 'Assigned' : 'Not assigned') }}</td><td data-label="Parent / Guardian">{{ student.parent_name || (student.parent_id ? 'Linked parent' : 'Not linked') }}</td>
            <td data-label="Action"><button type="button" class="small-action-btn" :disabled="busy || frozen || schoolUncertain" @click="viewStudent(student.student_id)">{{ canWriteStudents ? 'View or edit' : 'View details' }}</button></td>
          </tr>
        </tbody></table>
      </div>
      <ul v-else-if="!adminPresentation" class="directory-list"><li v-for="student in students" :key="student.student_id"><div><strong>{{ student.full_name }}</strong><span>{{ schoolName(student.school_id) }} · Grade {{ student.grade_level }}</span></div><button type="button" :disabled="busy || frozen || schoolUncertain" @click="viewStudent(student.student_id)">{{ canWriteStudents ? 'View or edit' : 'View details' }}</button></li></ul>
      <button v-if="studentCursor" type="button" :disabled="busy || frozen || schoolUncertain" @click="loadStudents(true)">Load more students</button>
    </template>
    <template v-else>
      <div class="directory-toolbar"><p>{{ schoolsLoaded ? schools.length + ' schools loaded' : 'School records not loaded' }}</p><button v-if="canWriteSchools" type="button" :disabled="busy || frozen || schoolUncertain" @click="newSchool">Add school</button></div>
      <p v-if="schoolsLoaded && !schools.length && !busy">No schools are available for this account.</p>
      <div v-if="adminPresentation && schools.length" class="table-wrapper compact-table-scroll hosted-schools-table" role="region" aria-label="School records" tabindex="0"><table><thead><tr><th>School</th><th>School ID</th><th v-if="canWriteSchools">Action</th></tr></thead><tbody><tr v-for="school in schools" :key="school.school_id"><td data-label="School"><strong>{{ school.name }}</strong></td><td data-label="School ID">{{ school.school_id }}</td><td v-if="canWriteSchools" data-label="Action"><button type="button" class="small-action-btn" :disabled="busy || frozen || schoolUncertain" @click="editSchool(school)">Edit school</button></td></tr></tbody></table></div>
      <ul v-else-if="!adminPresentation" class="directory-list"><li v-for="school in schools" :key="school.school_id"><strong>{{ school.name }}</strong><button v-if="canWriteSchools" type="button" :disabled="busy || frozen || schoolUncertain" @click="editSchool(school)">Edit school</button></li></ul>
    </template>
    <button v-if="schoolCursor" type="button" :disabled="busy || frozen || schoolUncertain" @click="loadSchools(true)">Load more schools</button>
    <component :is="adminPresentation ? 'dialog' : 'section'" v-if="formKind" ref="formRegion" tabindex="-1" class="directory-editor" :class="{ 'hosted-directory-modal': adminPresentation }" aria-labelledby="editor-title" @cancel="cancelEditor">
      <component :is="adminPresentation ? 'h2' : 'h3'" id="editor-title">{{ formKind === 'school' ? (editing ? 'Edit school' : 'Add school') : (editing ? 'Student details' : 'Add student') }}</component>
      <button v-if="adminPresentation" type="button" class="directory-modal-close" aria-label="Close dialog" :disabled="busy || frozen || schoolUncertain" @click="closeForm"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg></button>
      <p v-if="adminPresentation && error" role="alert" class="directory-error">{{ error }}</p>
      <template v-if="formKind === 'student' && !canWriteStudents">
        <dl><dt>Name</dt><dd>{{ draft.full_name }}</dd><dt>School</dt><dd>{{ schoolName(draft.school_id) }}</dd><dt>Grade</dt><dd>{{ draft.grade_level }}</dd><dt>Age</dt><dd>{{ draft.age ?? 'Not recorded' }}</dd></dl>
        <button type="button" @click="closeForm">Close details</button>
      </template>
      <form v-else @submit.prevent="save">
        <fieldset :disabled="busy || frozen || conflict || schoolUncertain">
          <label>{{ formKind === 'school' ? 'School name' : 'Student name' }}<input v-model="draft.full_name" required maxlength="200" autocomplete="off" /></label>
          <template v-if="formKind === 'student'">
            <div class="directory-fields"><label>Age<input v-model.number="draft.age" type="number" min="1" max="32767" step="1" :required="!editing || draft.age !== null" /></label><label>Grade<select v-model.number="draft.grade_level" required><option v-for="grade in 3" :key="grade" :value="grade">Grade {{ grade }}</option></select></label></div>
            <label>School<select v-model="draft.school_id" required :disabled="isTeacher && Boolean(editing)" @change="schoolChanged"><option disabled value="">Choose a school</option><option v-for="school in schools" :key="school.school_id" :value="school.school_id">{{ school.name }}</option></select></label>
            <p v-if="!schools.length" class="directory-hint">A school must be available to your account before you can add a student.</p>
            <label v-if="!isTeacher">Teacher<select v-model="draft.teacher_id" :required="!editing"><option value="">{{ editing ? 'Keep historical unassigned teacher' : 'Choose an eligible teacher' }}</option><option v-if="draft.teacher_id && !options.some(p => p.user_id === draft.teacher_id)" :value="draft.teacher_id">Current teacher — eligibility must be confirmed</option><option v-for="person in options.filter(p => p.role === 'teacher')" :key="person.user_id" :value="person.user_id">{{ person.full_name }}</option></select></label>
            <p v-else class="directory-hint">You will be the assigned teacher.</p>
            <label>Parent<select v-model="draft.parent_id"><option value="">No linked parent</option><option v-if="draft.parent_id && !options.some(p => p.user_id === draft.parent_id)" :value="draft.parent_id">Current parent — eligibility must be confirmed</option><option v-for="person in options.filter(p => p.role === 'parent')" :key="person.user_id" :value="person.user_id">{{ person.full_name }}</option></select></label>
            <p class="directory-hint">Only people made eligible for this school and your account appear. Contact an administrator if someone is missing.</p>
          </template>
        </fieldset>
        <button v-if="optionCursor && !frozen" type="button" :disabled="busy" @click="loadOptions(true)">Load more eligible people</button>
        <p v-if="frozen" role="status">Saving could not be confirmed. Retry this same submission before starting another. Keep this page open.</p>
        <p v-if="conflict" role="status">The record changed. Reloading will replace your unsaved form with the latest record.</p>
        <p v-if="schoolUncertain" role="status">Saving this school could not be confirmed. Refresh the school list and check for it before trying again.</p>
        <div class="directory-actions">
          <button v-if="adminPresentation && !frozen && !schoolUncertain" type="button" :disabled="busy" @click="closeForm">Cancel</button>
          <button v-if="!conflict && !schoolUncertain" type="submit" :disabled="busy || (formKind === 'student' && !draft.school_id)">{{ busy ? 'Saving…' : frozen ? 'Retry same submission' : 'Save' }}</button>
          <button v-if="conflict || schoolUncertain" type="button" :disabled="busy" @click="reloadRecord">{{ schoolUncertain ? 'Refresh school list' : 'Reload record' }}</button>
          <button v-if="!adminPresentation && !frozen && !schoolUncertain" type="button" :disabled="busy" @click="closeForm">Cancel</button>
        </div>
        <button v-if="adminPresentation && signOut && (frozen || schoolUncertain)" type="button" class="directory-signout" :disabled="busy" @click="signOut">Sign out</button>
      </form>
    </component>
    <p v-if="!adminPresentation" class="directory-hint directory-footnote">Records and assignment choices reflect your current account permissions.</p>
  </section>
</template>

<script setup>
import RefreshButton from './RefreshButton.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { createStudentSubmission } from './directory-submission.mjs'
const props=defineProps({ client:{type:Object,required:true},profile:{type:Object,required:true},adminPresentation:Boolean,signOut:{type:Function,default:null} })
const emit=defineEmits(['access-change','navigation-block','snapshot'])
const tab=ref('students'),busy=ref(false),error=ref(''),message=ref(''),students=ref([]),schools=ref([]),options=ref([])
const studentCursor=ref(null),schoolCursor=ref(null),optionCursor=ref(null),search=ref(''),filterSchool=ref(''),filterGrade=ref('')
const studentsLoaded=ref(false),schoolsLoaded=ref(false)
watch(() => ({ students: students.value.length, schools: schools.value.length, records: students.value, studentsLoaded: studentsLoaded.value, schoolsLoaded: schoolsLoaded.value, hasMore: Boolean(studentCursor.value || schoolCursor.value), busy: busy.value, error: error.value }), value => emit('snapshot', value), { immediate: true })
const formKind=ref(''),editing=ref(null),formRegion=ref(null),frozen=ref(false),conflict=ref(false),schoolUncertain=ref(false)
watch(formKind,async value=>{if(!props.adminPresentation)return;document.body.classList.toggle('hosted-directory-dialog-open',Boolean(value));if(value){await nextTick();if(formRegion.value&&!formRegion.value.open)formRegion.value.showModal()}},{flush:'post'})
function cancelEditor(event){if(!props.adminPresentation)return;event.preventDefault();if(!busy.value&&!frozen.value&&!schoolUncertain.value)closeForm()}
const draft=reactive({full_name:'',age:8,grade_level:1,school_id:'',teacher_id:'',parent_id:''})
const isTeacher=computed(()=>props.profile.role==='teacher')
const canWriteStudents=computed(()=>isTeacher.value || props.profile.permissions.includes('assignments.manage'))
const canWriteSchools=computed(()=>['admin','researcher'].includes(props.profile.role)&&props.profile.permissions.includes('schools.manage'))
let alive=true,submission=createStudentSubmission(),appliedFilters={}
function schoolName(id){return schools.value.find(s=>s.school_id===id)?.name || 'Assigned school'}
function report(failure){if(!alive)return;error.value=failure.message||'The request could not be completed.';if(failure.status===401||['PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED','ACCOUNT_UNAVAILABLE'].includes(failure.code))emit('access-change')}
async function run(task){if(busy.value)return;busy.value=true;error.value='';try{await task()}catch(failure){report(failure)}finally{if(alive)busy.value=false}}
async function querySchools(more=false){const query=new URLSearchParams({limit:'25'});if(more&&schoolCursor.value)query.set('cursor',schoolCursor.value);const result=await props.client.request('/schools?'+query,{envelope:true});if(!alive)return;schools.value=more?[...schools.value,...result.data]:result.data;schoolCursor.value=result.page.next_cursor;schoolsLoaded.value=true}
function loadSchools(more=false){return run(()=>querySchools(more))}
async function queryStudents(more=false){if(!more)appliedFilters={q:search.value.trim(),school_id:filterSchool.value,grade_level:filterGrade.value};const query=new URLSearchParams({limit:'25'});for(const [key,value]of Object.entries(appliedFilters))if(value)query.set(key,value);if(more&&studentCursor.value)query.set('cursor',studentCursor.value);const result=await props.client.request('/students?'+query,{envelope:true});if(!alive)return;students.value=more?[...students.value,...result.data]:result.data;studentCursor.value=result.page.next_cursor;studentsLoaded.value=true}
function loadStudents(more=false){return run(()=>queryStudents(more))}
function refreshRecords(){return run(async()=>{const results=await Promise.allSettled([querySchools(),queryStudents()]);const failed=results.find(result=>result.status==='rejected');if(failed)throw failed.reason})}
async function queryOptions(more=false){if(!draft.school_id)return;const query=new URLSearchParams({limit:'25'});if(more&&optionCursor.value)query.set('cursor',optionCursor.value);const result=await props.client.request('/schools/'+draft.school_id+'/assignment-options?'+query,{envelope:true});if(!alive)return;options.value=more?[...options.value,...result.data]:result.data;optionCursor.value=result.page.next_cursor}
function loadOptions(more=false){return run(()=>queryOptions(more))}
function closeForm(){if(frozen.value)return;formKind.value='';editing.value=null;conflict.value=false;schoolUncertain.value=false;options.value=[];optionCursor.value=null;emit('navigation-block',false)}
async function focusForm(){await nextTick();if(alive)formRegion.value?.focus()}
function newSchool(){closeForm();Object.assign(draft,{full_name:''});formKind.value='school';message.value='';focusForm()}
function editSchool(school){closeForm();editing.value={...school};draft.full_name=school.name;formKind.value='school';message.value='';focusForm()}
function newStudent(){closeForm();submission=createStudentSubmission();Object.assign(draft,{full_name:'',age:8,grade_level:1,school_id:'',teacher_id:'',parent_id:''});formKind.value='student';message.value='';focusForm()}
async function populateStudent(id){const data=await props.client.request('/students/'+id);if(!alive)return;editing.value=data;Object.assign(draft,{...data,teacher_id:data.teacher_id||'',parent_id:data.parent_id||''});formKind.value='student';conflict.value=false;options.value=[];optionCursor.value=null;if(canWriteStudents.value)await queryOptions();await focusForm()}
function viewStudent(id){return run(()=>populateStudent(id))}
function schoolChanged(){options.value=[];optionCursor.value=null;draft.teacher_id='';draft.parent_id='';loadOptions()}
function reloadRecord(){return run(async()=>{if(formKind.value==='student')await populateStudent(editing.value.student_id);else{await querySchools();schoolUncertain.value=false;closeForm();message.value='School list refreshed. Check the list before creating or editing a school again.'}conflict.value=false})}
function save(){return run(async()=>{
  message.value='';let result;emit('navigation-block',true)
  try{
    if(formKind.value==='school'){
      const body={name:draft.full_name};if(editing.value)body.expected_revision=editing.value.revision
      result=await props.client.request('/schools'+(editing.value?'/'+editing.value.school_id:''),{method:editing.value?'PATCH':'POST',body,envelope:true})
    }else{
      const body={full_name:draft.full_name,school_id:draft.school_id,grade_level:draft.grade_level,parent_id:draft.parent_id||null}
      if(draft.age!==null&&draft.age!=='')body.age=Number(draft.age)
      if(!isTeacher.value&&draft.teacher_id)body.teacher_id=draft.teacher_id
      if(editing.value){body.expected_revision=editing.value.revision;result=await props.client.request('/students/'+editing.value.student_id,{method:'PATCH',body,envelope:true})}
      else result=await submission.submit(props.client,body)
    }
  }catch(failure){if(alive){frozen.value=submission.pending;conflict.value=failure.code==='REVISION_CONFLICT';if(formKind.value==='school'&&!editing.value&&(failure.status===0||failure.status>=500))schoolUncertain.value=true}throw failure}
  finally{if(alive)emit('navigation-block',submission.pending||schoolUncertain.value)}
  if(!alive)return;frozen.value=false;message.value=result.warnings?.includes('duplicate_name')?'Saved. A similar name exists in your accessible records. Review it before adding another.':'Saved.';closeForm()
  await querySchools();await queryStudents()
})}
function beforeUnload(event){if(submission.pending||schoolUncertain.value){event.preventDefault();event.returnValue=''}}
onMounted(()=>{window.addEventListener('beforeunload',beforeUnload);refreshRecords()})
onBeforeUnmount(()=>{alive=false;if(props.adminPresentation)document.body.classList.remove('hosted-directory-dialog-open');emit('navigation-block',false);window.removeEventListener('beforeunload',beforeUnload)})
defineExpose({ refresh: refreshRecords, showTab(value) { tab.value=value;closeForm() } })
</script>

<style scoped>
.directory{margin-top:32px;border-top:1px solid #d4dfd8;padding-top:24px;color:#17382d}.directory h2{font-size:24px;margin:0 0 20px}.directory h3{font-size:20px;margin:0 0 20px}.directory-nav,.directory-actions,.directory-toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.directory-nav{margin-bottom:24px}.directory button{min-height:44px;padding:10px 16px;border:1px solid #9bab9f;border-radius:8px;color:#17382d;background:#fff;font:inherit;cursor:pointer}.directory button:hover{background:#edf4ee}.directory button[aria-pressed=true],.directory-actions button[type=submit]{background:#176347;color:#fff;border-color:#176347}.directory button:disabled{opacity:.65;cursor:default}.directory :is(button,input,select,[tabindex]):focus-visible{outline:3px solid #287b59;outline-offset:3px}.directory label{display:flex;flex-direction:column;gap:8px;font-weight:600;min-width:0}.directory input,.directory select{font:inherit;color:#17382d;background:#fff;border:1px solid #9bab9f;border-radius:8px;padding:10px 12px;min-height:48px;width:100%;box-sizing:border-box;caret-color:#176347}.directory-filters{display:grid;grid-template-columns:minmax(150px,2fr) minmax(140px,2fr) minmax(100px,1fr) auto;gap:16px;align-items:end}.directory-toolbar{justify-content:space-between;margin:24px 0 12px}.directory-toolbar p{margin:0}.directory-list{list-style:none;padding:0;margin:0 0 20px}.directory-list li{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 0;border-bottom:1px solid #d4dfd8;overflow-wrap:anywhere}.directory-list strong{font-weight:600}.directory-list span{display:block;color:#466056;font-size:14px;margin-top:4px}.directory-list button{flex-shrink:0}.directory-editor{margin-top:32px;padding-top:24px;border-top:1px solid #9bab9f;scroll-margin-top:24px}.directory-editor fieldset{padding:0;border:0;margin:0;display:flex;flex-direction:column;gap:20px;min-width:0}.directory-fields{display:grid;grid-template-columns:1fr 1fr;gap:20px}.directory-actions{margin-top:24px}.directory-error{color:#922c24;background:#fff0ed;padding:14px;border-radius:8px}.directory-message{color:#176347}.directory-hint{font-size:14px;color:#466056;line-height:1.6}.directory-footnote{margin-top:32px}.directory dd{margin:4px 0 16px}.directory dt{font-weight:600}@media(max-width:760px){.directory-filters{grid-template-columns:1fr 1fr}}@media(max-width:460px){.directory-filters,.directory-fields{grid-template-columns:1fr}.directory-list li{align-items:flex-start;flex-direction:column}.directory-list button{width:100%}}
</style>
