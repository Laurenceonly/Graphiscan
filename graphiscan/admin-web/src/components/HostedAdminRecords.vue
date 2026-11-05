<template>
  <section class="hosted-admin-records" :class="{ 'users-directory': accounts }" :aria-labelledby="kind + '-title'">
    <AdminPageSkeleton v-if="allowed && busy && !loaded && !selected" :summary="accounts" filters :label="accounts ? 'Loading users' : 'Loading audit logs'" />
    <template v-else>
    <header class="page-header hosted-page-header admin-page-header"><h1 :id="kind + '-title'" tabindex="-1">{{ accounts ? 'Users' : 'Audit Logs' }}</h1><div class="account-page-actions"><button v-if="accounts && allowed" type="button" class="primary-action-btn" :disabled="busy || filterPending || saving || reconcileNeeded || loadingEditor" @click="openCreator">Add user</button></div></header>
    <AdminSummaryCards v-if="allowed && accounts" :items="cards.map(card => ({label:card.label,loading:busy && !loaded,value:loaded ? card.count : '-'}))" label="Loaded account counts" interactive @select="selectUserCard" />
    <section class="clean-panel hosted-record-panel">
      <form v-if="allowed" class="hosted-record-filters" :class="{ 'audit-filters': !accounts }" @submit.prevent="applyFilters">
        <label>{{ accounts ? 'Search users' : 'Search audit logs' }}<span class="admin-search-control"><Search :size="18" :stroke-width="1.8" aria-hidden="true" /><input v-model="search" type="search" :placeholder="accounts ? 'Name or email' : 'Search activity'" maxlength="120" :disabled="accounts ? blocked : busy" /></span></label>
        <label>Role<select v-model="role" :disabled="accounts ? blocked : busy"><option value="">All roles</option><option v-for="item in roles" :key="item" :value="item">{{ roleName(item) }}</option></select></label>
        <label v-if="accounts">Status<select v-model="status" :disabled="blocked"><option value="">All statuses</option><option v-for="item in statuses" :key="item" :value="item">{{ capitalize(item) }}</option></select></label>
        <button type="submit" class="soft-action-btn" :disabled="accounts ? blocked : busy">Apply filters</button>
      </form>
      <div v-if="accounts && allowed" class="users-filter-feedback"><p role="status" aria-live="polite">{{ visibleRows.length }} of {{ rows.length }} loaded {{ rows.length === 1 ? 'user' : 'users' }}</p><button v-if="search || role || status !== 'active'" type="button" class="users-reset-filters" :disabled="blocked" @click="resetFilters">Reset filters</button></div>
      <p v-if="!allowed" class="hosted-record-message">{{ accounts ? 'Account records require account management access.' : 'Audit records require audit access.' }}</p>
      <p v-else-if="error" class="error-message" role="alert">{{ error }} <button type="button" class="soft-action-btn" @click="load(false)">Try again</button></p>
      <AdminLoadingSkeleton v-if="busy && !loaded" :label="accounts ? 'Loading users...' : 'Loading audit logs...'" />
      <p v-else-if="busy && !accounts" role="status" class="hosted-record-message">Loading audit logs...</p>
      <p v-if="!accounts && allowed && loaded && !visibleRows.length && !busy && !filterPending" class="hosted-record-message">{{ accounts ? 'No loaded users match these filters.' : 'No activity matches these filters.' }}</p>
      <div v-if="visibleRows.length || (accounts && allowed && loaded)" class="table-wrapper compact-table-scroll hosted-record-table" :aria-busy="busy || filterPending" role="region" :aria-label="accounts ? 'User accounts' : 'Audit activity'" tabindex="0">
        <table v-if="accounts"><colgroup><col style="width:22%" /><col style="width:26%" /><col style="width:14%" /><col style="width:12%" /><col style="width:16%" /><col style="width:10%" /></colgroup><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Registered</th><th>Actions</th></tr></thead><tbody><tr v-if="!visibleRows.length" class="users-empty-row"><td colspan="6" class="users-table-empty">No loaded users match these filters.</td></tr><tr v-for="row in visibleRows" :key="row.user_id"><td data-label="Name"><strong>{{ row.full_name }}</strong><small v-if="row.user_id === profile.user_id" class="table-subtext">Current account</small></td><td data-label="Email">{{ row.email || 'Not available' }}</td><td data-label="Role">{{ roleName(row.role) }}</td><td data-label="Status"><span class="status-badge" :class="row.account_status">{{ capitalize(row.account_status) }}</span></td><td data-label="Registered">{{ date(row.created_at) }}</td><td data-label="Actions"><div class="account-row-actions"><button class="soft-action-btn account-edit" type="button" :disabled="busy || filterPending || loadingEditor || !canManage(row)" @click="openEditor(row)">Edit</button></div></td></tr></tbody></table>
        <table v-else><thead><tr><th>Person</th><th>Role</th><th>Action</th><th>Date / Time</th></tr></thead><tbody><tr v-for="row in visibleRows" :key="row.log_id"><td data-label="Person"><strong>{{ row.full_name || 'Former or unknown account' }}</strong></td><td data-label="Role">{{ row.role ? roleName(row.role) : 'Unknown' }}</td><td data-label="Action" :title="row.action">{{ auditActionLabel(row.action) }}</td><td data-label="Date / Time">{{ date(row.created_at) }}</td></tr></tbody></table>
      </div>
      <button v-if="cursor" type="button" class="soft-action-btn hosted-load-more" :disabled="busy || filterPending" @click="load(true)">Load more</button>
      <p v-if="notice" class="hosted-record-message" role="status">{{ notice }}</p>
      <section v-if="handover" class="account-handover" aria-labelledby="account-handover-title">
        <h2 id="account-handover-title">Login details for direct handover</h2>
        <p>Give these details privately to the user. <template v-if="handover.temporary">They must change the temporary password on first sign-in. </template>These details disappear when you leave this page.</p>
        <label>Login ID<output class="account-login-id">{{ handover.email }}</output></label>
        <label>{{ handover.temporary ? 'Temporary password' : 'Password' }}<input :value="handover.password" :type="showHandoverPassword ? 'text' : 'password'" readonly autocomplete="off" /></label>
        <div class="account-delivery-actions"><button type="button" class="soft-action-btn" :aria-pressed="showHandoverPassword" @click="showHandoverPassword = !showHandoverPassword">{{ showHandoverPassword ? 'Hide password' : 'Show password' }}</button><button type="button" class="soft-action-btn" @click="clearHandover">Done with these details</button></div>
      </section>
    </section>
    <dialog v-if="accounts" ref="editor" class="account-editor" :class="{'account-creator':creating}" aria-labelledby="account-editor-title" @cancel="onCancel">
      <form v-if="selected" class="account-editor-form" :inert="loadingEditor" :aria-busy="saving || loadingEditor" @submit.prevent="saveAccount">
        <header><div><h2 id="account-editor-title">{{ creating ? 'Add user' : 'Edit user' }}</h2><p>{{ creating ? temporaryAccount ? 'Mobile users change their temporary password on first sign-in.' : 'Admin portal accounts use a permanent password.' : 'Role, status and access changes sign this user out.' }}</p></div><button type="button" class="editor-close" aria-label="Close account editor" :disabled="saving || reconcileNeeded" @click="closeEditor"><X :size="18" :stroke-width="1.8" aria-hidden="true" /></button></header>
        <label>Full name<input v-model="draft.full_name" type="text" maxlength="200" autocomplete="off" required :disabled="saving || reconcileNeeded" /></label>
        <template v-if="creating">
          <label>Give the user their login details<select v-model="draft.delivery_method" :disabled="saving || reconcileNeeded" @change="changeDelivery"><option value="manual">Give details directly (no email)</option><option value="email">Email login details</option></select></label>
          <div class="account-field-group"><label>{{ draft.delivery_method === 'email' ? 'User email address' : 'Login ID' }}<input v-model="draft.email" type="email" maxlength="254" autocomplete="off" required :readonly="draft.delivery_method === 'manual'" :disabled="saving || reconcileNeeded" aria-describedby="account-delivery-help" /></label>
          <p id="account-delivery-help">{{ draft.delivery_method === 'email' ? 'Use their existing Gmail or other inbox. GraphiScan emails their password and access link.' : 'Give this generated login ID and password directly to the user. No email is sent.' }}</p></div>
        </template>
        <div class="account-role-fields" :class="{'account-role-fields-pair':!creating}"><label>Role<select v-model="draft.role" :disabled="saving || reconcileNeeded || selected.user_id === profile.user_id"><option v-if="!creating && !editableRoles.includes(draft.role)" :value="draft.role" disabled hidden>{{ roleName(draft.role) }}</option><option v-for="item in editableRoles" :key="item" :value="item">{{ roleName(item) }}</option></select></label><label v-if="!creating">Status<select v-model="draft.account_status" :disabled="saving || reconcileNeeded || selected.user_id === profile.user_id"><option v-for="item in statuses" :key="item" :value="item">{{ capitalize(item) }}</option></select></label></div>
        <template v-if="creating">
          <div v-if="draft.role !== 'admin'" class="account-field-group"><label>School (optional)<select v-model="draft.school_id" :disabled="saving || reconcileNeeded || schoolsBusy"><option value="">No school assignment</option><option v-for="school in schools" :key="school.school_id" :value="String(school.school_id)">{{ school.name }}</option></select></label>
          <p v-if="schoolsError" role="status">{{ schoolsError }}</p>
          </div><div class="account-field-group"><label>{{ temporaryAccount ? 'Temporary password' : 'Password' }}<input v-model="draft.temporary_password" type="password" minlength="8" maxlength="128" autocomplete="new-password" required :disabled="saving || reconcileNeeded" aria-describedby="temporary-password-help" /></label>
          <p id="temporary-password-help">Use 8-128 characters with uppercase, lowercase, a number and a symbol. This is only for GraphiScan, separate from any email password.</p>
          </div>
        </template>
        <template v-if="!creating">
          <fieldset v-if="canEditPermissions" class="account-permission-options" :disabled="saving || reconcileNeeded"><legend>Permissions</legend><div v-for="(grant,index) in draft.permission_grants" :key="index" class="account-permission-row"><label>Permission<select v-model="grant.permission_key" @change="normalizeScope(grant)"><option v-for="item in permissionChoices" :key="item.key" :value="item.key">{{ item.label }}</option></select></label><label>Scope<select v-model="grant.school_id" :disabled="['accounts.manage','permissions.manage','audit.read'].includes(grant.permission_key)"><option :value="null">All schools</option><option v-for="school in editorSchools" :key="school.school_id" :value="String(school.school_id)">{{ school.name }}</option></select></label><button type="button" class="soft-action-btn" :aria-label="'Remove permission ' + (index+1)" @click="draft.permission_grants.splice(index,1)">Remove</button></div><button type="button" class="soft-action-btn" @click="draft.permission_grants.push({permission_key:'schools.manage',school_id:null})">Add permission</button></fieldset>
          <p v-else>Permission changes require permission-management access. Your own access cannot be changed here.</p>
        </template>
        <section v-if="!creating && selected.user_id !== profile.user_id && canManage(selected)" class="account-editor-actions" aria-labelledby="account-editor-actions-title">
          <h3 id="account-editor-actions-title">Account actions</h3>
          <button v-if="['teacher','parent','expert'].includes(draft.role)" type="button" class="soft-action-btn" :disabled="accountActionsDisabled" @click="openAction(selected,'assignments')">Manage assignments</button>
          <p v-if="hasChanges">Save your changes before using these actions.</p>
          <div class="account-editor-action-buttons">
            <button type="button" class="soft-action-btn" :disabled="accountActionsDisabled" @click="openAction(selected,'status',selected.account_status === 'active' ? 'disabled' : 'active')">{{ selected.account_status === 'active' ? 'Disable account' : 'Activate account' }}</button>
            <button type="button" class="soft-action-btn" :disabled="accountActionsDisabled" @click="openAction(selected,'reset_password')">Reset password</button>
            <button type="button" class="soft-action-btn account-delete-link" :disabled="accountActionsDisabled" @click="openAction(selected,'delete')">Delete account</button>
          </div>
        </section>
        <p v-if="editorError" class="error-message" role="alert">{{ editorError }}</p>
        <footer><button type="button" class="soft-action-btn" :disabled="saving || reconcileNeeded" @click="closeEditor">Cancel</button><button type="submit" class="primary-action-btn" :disabled="saving || busy || (!reconcileNeeded && !hasChanges)">{{ saving ? (creating ? 'Creating...' : 'Saving...') : reconcileNeeded ? 'Check user list' : creating ? 'Create user' : 'Save changes' }}</button></footer>
      </form>
    </dialog>
    <AccountActionDialog v-if="actionTarget && actionKind !== 'assignments'" :client="client" :target="actionTarget" :action="actionKind" :status="actionStatus" @close="closeAction" @completed="actionCompleted" @navigation-block="actionBlocked=$event" @access-change="emit('access-change')" />
    <AccountRoleAssignments v-if="actionTarget && actionKind === 'assignments'" :client="client" :target="actionTarget" :profile="profile" :schools="editorSchools" :school-note="schoolsError" @close="closeAction" @completed="actionCompleted" @navigation-block="actionBlocked=$event" @access-change="emit('access-change')" />
    </template>
  </section>
</template>
<script setup>
import { auditActionLabel, auditSearchQuery } from '../utils/audit-actions.mjs'
import AdminPageSkeleton from '../../../shared/AdminPageSkeleton.vue'
import AdminLoadingSkeleton from '../../../shared/AdminLoadingSkeleton.vue'
import AdminSummaryCards from '../../../shared/AdminSummaryCards.vue'
import AccountActionDialog from './AccountActionDialog.vue'
import AccountRoleAssignments from './AccountRoleAssignments.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { X } from 'lucide-vue-next'
import Search from '../../../shared/AdminSearchIcon.vue'
const props=defineProps({kind:{type:String,required:true},client:{type:Object,required:true},profile:{type:Object,required:true},active:{type:Boolean,default:true}})
const emit=defineEmits(['access-change','navigation-block','snapshot','assignments-change'])
const accounts=computed(()=>props.kind==='accounts')
const allowed=computed(()=>props.profile.permissions?.includes(accounts.value?'accounts.manage':'audit.read'))
const userRoles=['admin','teacher','parent','expert']
const roles=computed(()=>accounts.value?userRoles:['admin','researcher','teacher','parent','expert','guest'])
const statuses=['active','pending','disabled','rejected']
const search=ref(''),role=ref(''),status=ref(props.kind==='accounts'?'active':''),rows=ref([]),cursor=ref(null),busy=ref(false),loaded=ref(false),error=ref(''),notice=ref('')
watch(()=>({busy:busy.value,loaded:loaded.value,allowed:allowed.value,error:error.value}),value=>emit('snapshot',value),{immediate:true})
const editor=ref(null),selected=ref(null),saving=ref(false),editorError=ref(''),reconcileNeeded=ref(false)
const creating=ref(false),schools=ref([]),schoolsBusy=ref(false),schoolsError=ref('')
const loadingEditor=ref(false),actionTarget=ref(null),actionKind=ref(''),actionStatus=ref(''),actionBlocked=ref(false)
const handover=ref(null),showHandoverPassword=ref(false)
const draft=reactive({full_name:'',role:'',account_status:'',email:'',delivery_method:'manual',temporary_password:'',school_id:'',school_ids:[],permission_grants:[]})
const temporaryAccount=computed(()=>['teacher','expert','parent'].includes(draft.role))
function clearHandover(){handover.value=null;showHandoverPassword.value=false}
function changeDelivery(){draft.email=draft.delivery_method==='manual'?'gs-'+crypto.randomUUID().replaceAll('-','').slice(0,12)+'@accounts.graphiscan.invalid':''}
let creationKey=null
const editableRoles=computed(()=>props.profile.role==='admin'?userRoles:userRoles.filter(item=>item!=='admin'))
// Preserve the API's self-access protection; another administrator manages legacy links.
const effectiveSchoolIds=computed(()=>draft.role==='admin'&&selected.value?.user_id!==props.profile.user_id?[]:draft.school_ids)
const normalized=value=>JSON.stringify([...value].map(item=>typeof item==='string'?item:{permission_key:item.permission_key,school_id:item.school_id??null}).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b))))
const hasChanges=computed(()=>!!selected.value&&(creating.value || draft.full_name.trim().replace(/\s+/g,' ')!==selected.value.full_name||draft.role!==selected.value.role||draft.account_status!==selected.value.account_status||normalized(effectiveSchoolIds.value)!==normalized(selected.value.school_ids||[])||normalized(draft.permission_grants)!==normalized(selected.value.permission_grants||[])))
const canEditPermissions=computed(()=>props.profile.permissions?.includes('permissions.manage')&&selected.value?.user_id!==props.profile.user_id)
const accountActionsDisabled=computed(()=>saving.value||reconcileNeeded.value||loadingEditor.value||hasChanges.value)
const permissionChoices=[{key:'accounts.manage',label:'Manage accounts'},{key:'permissions.manage',label:'Manage permissions'},{key:'schools.manage',label:'Manage schools'},{key:'assignments.manage',label:'Manage assignments'},{key:'audit.read',label:'Read audit logs'}]
const editorSchools=computed(()=>[...schools.value,...[...new Set([...draft.school_ids,...draft.permission_grants.map(grant=>grant.school_id).filter(Boolean)])].filter(id=>!schools.value.some(school=>String(school.school_id)===id)).map(id=>({school_id:id,name:'Assigned school '+id}))])
const searchKey=value=>String(value??'').normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase()
const visibleRows=computed(()=>{
  if(!allowed.value)return []
  if(!accounts.value)return rows.value
  const terms=searchKey(search.value).trim().split(/\s+/).filter(Boolean)
  return rows.value.filter(row=>(!role.value||row.role===role.value)&&(!status.value||row.account_status===status.value)&&terms.every(term=>searchKey(row.full_name+' '+(row.email||'')).includes(term)))
})
const cards=computed(()=>accounts.value?[{label:'Users',count:rows.value.length},{label:'Active',count:rows.value.filter(row=>row.account_status==='active').length},{label:'Pending',count:rows.value.filter(row=>row.account_status==='pending').length},{label:'Disabled',count:rows.value.filter(row=>row.account_status==='disabled').length}]:[{label:'Activities shown',count:rows.value.length}])
let alive=true,version=0,applied={}
const filterPending=ref(false)
let filterTimer=null
function cancelFilterTimer(){clearTimeout(filterTimer);filterTimer=null;filterPending.value=false}
function reset(){cancelFilterTimer();version++;applied={};rows.value=[];cursor.value=null;loaded.value=false;error.value='';notice.value='';busy.value=false}
function currentFilters(){return {q:accounts.value?'':auditSearchQuery(search.value),role:role.value,account_status:accounts.value?status.value:''}}
function applyFilters(){cancelFilterTimer();if(accounts.value&&loaded.value&&!error.value&&JSON.stringify(currentFilters())===JSON.stringify(applied))return;return load(false)}
function resetFilters(){search.value='';role.value='';status.value='active'}
function selectUserCard(card){if(!blocked.value&&accounts.value)status.value=card.label==='Users'?'':card.label.toLowerCase()}
function scheduleFilters(delay){
  cancelFilterTimer()
  if(!accounts.value||!props.active||!allowed.value||blocked.value)return
  if(JSON.stringify(currentFilters())===JSON.stringify(applied)&&loaded.value&&!error.value)return
  version++;busy.value=false;filterPending.value=true;cursor.value=null
  filterTimer=setTimeout(()=>{filterTimer=null;filterPending.value=false;if(alive&&props.active&&allowed.value&&!blocked.value)load(false)},delay)
}
watch([role,status],()=>scheduleFilters(0))
watch(()=>props.active,active=>{if(!active)cancelFilterTimer();else if(accounts.value)scheduleFilters(0)})
function capitalize(value){return value?value.charAt(0).toUpperCase()+value.slice(1):'Unknown'}
function roleName(value){return value==='admin'?'Administrator':capitalize(value)}
function canManage(row){return props.profile.role==='admin'||!['admin','researcher'].includes(row.role)}
function normalizeScope(grant){if(['accounts.manage','permissions.manage','audit.read'].includes(grant.permission_key))grant.school_id=null}
function date(value){const parsed=new Date(value);return value&&!Number.isNaN(parsed.getTime())?parsed.toLocaleString():'Not recorded'}
async function load(more=false){
  if(!allowed.value||(more&&(busy.value||filterPending.value)))return
  const next=currentFilters()
  if(busy.value&&(!accounts.value||JSON.stringify(next)===JSON.stringify(applied)))return
  cancelFilterTimer()
  if(!more){if(JSON.stringify(next)!==JSON.stringify(applied)){if(!accounts.value)reset();else cursor.value=null}applied=next}
  const current=++version;busy.value=true;error.value=''
  const query=new URLSearchParams({limit:'25'})
  for(const [key,value] of Object.entries(applied))if(value)query.set(key,value)
  if(more&&cursor.value)query.set('cursor',cursor.value)
  try{
    const response=await props.client.request('/'+(accounts.value?'accounts':'audit-logs')+'?'+query,{envelope:true})
    if(!alive||current!==version)return
    rows.value=more?[...rows.value,...response.data]:response.data
    cursor.value=response.page.next_cursor;loaded.value=true;return true
  }catch(failure){
    if(!alive||current!==version)return
    error.value=failure.message||'Records could not be loaded.'
    if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED','FORBIDDEN'].includes(failure.code))emit('access-change')
    return false
  }finally{if(alive&&current===version)busy.value=false}
}
async function openEditor(row){
  if(loadingEditor.value)return
  loadingEditor.value=true;error.value=''
  try{
    const current=await props.client.request('/accounts/'+row.user_id)
    if(!alive)return
    if(current.credential_update_pending)throw new Error('This account has an unfinished credential operation. Contact the system operator before editing it.')
    row=current
    const response=await props.client.request('/schools?limit=100',{envelope:true})
    if(!alive)return
    schools.value=response.data;schoolsError.value=response.page?.next_cursor?'Only the first 100 available schools are shown. Existing assignments are retained.':''
  creating.value=false;draft.temporary_password='';creationKey=null
  draft.school_ids=[...(row.school_ids||[])];draft.permission_grants=(row.permission_grants||[]).map(grant=>({...grant}))
  selected.value=row;draft.full_name=row.full_name;draft.role=row.role;draft.account_status=row.account_status;editorError.value='';reconcileNeeded.value=false
  await nextTick();editor.value?.showModal();editor.value?.querySelector('input')?.focus()
  }catch(failure){error.value=failure.message||'Account details could not be loaded.'}
  finally{loadingEditor.value=false}
}
async function openAction(row,kind,status=''){
  if(accountActionsDisabled.value||creating.value||row.user_id===props.profile.user_id||!canManage(row))return
  loadingEditor.value=true;editorError.value=''
  try{const current=await props.client.request('/accounts/'+row.user_id);if(!alive)return;if(current.credential_update_pending)throw new Error('This account has an unfinished credential operation. Contact the system operator.');if(kind === 'assignments' && current.role === 'admin')throw new Error('This account is now an administrator. Reload the user list.');editor.value?.close();actionKind.value=kind;actionStatus.value=status;actionTarget.value=current}
  catch(failure){editorError.value=failure.message||'Account details could not be loaded.'}
  finally{loadingEditor.value=false}
}
function clearAction(){actionTarget.value=null;actionBlocked.value=false}
async function closeAction(message=''){const target=actionTarget.value;clearAction();if(message){clearEditor();notice.value=message;return}if(target)await openEditor(target)}
async function actionCompleted(message){const assignmentsChanged=actionKind.value==='assignments';clearAction();clearEditor();if(assignmentsChanged)emit('assignments-change');await load(false);notice.value=message}
async function openCreator(){
  clearHandover()
  creating.value=true;selected.value={};creationKey=crypto.randomUUID();editorError.value='';reconcileNeeded.value=false
  Object.assign(draft,{full_name:'',role:'teacher',account_status:'active',email:'',delivery_method:'manual',temporary_password:'',school_id:'',school_ids:[],permission_grants:[]})
  changeDelivery()
  schools.value=[];schoolsError.value='';schoolsBusy.value=true
  await nextTick();editor.value?.showModal();editor.value?.querySelector('input')?.focus()
  try{const response=await props.client.request('/schools?limit=100',{envelope:true});if(alive){schools.value=response.data;schoolsError.value=response.page?.next_cursor?'Only the first 100 available schools are shown. Use a school from this list or assign it later.':''}}
  catch{if(alive)schoolsError.value='Schools could not be loaded. You can create the account without a school assignment.'}
  finally{if(alive)schoolsBusy.value=false}
}
function clearEditor(){editor.value?.close();selected.value=null;editorError.value='';draft.temporary_password='';creationKey=null}
function closeEditor(){if(saving.value||reconcileNeeded.value||loadingEditor.value)return;clearEditor()}
function onCancel(event){if(saving.value||reconcileNeeded.value||loadingEditor.value){event.preventDefault();return}clearEditor()}
watch(()=>props.active,active=>{if(!active)clearEditor()})
watch(()=>props.active,active=>{if(!active)clearHandover()})
async function saveAccount(){
  if(saving.value||loadingEditor.value||!selected.value)return
  if(reconcileNeeded.value){
    search.value=creating.value?draft.email.trim():selected.value.email||'';role.value='';status.value=''
    if(await load(false)){reconcileNeeded.value=false;clearEditor();notice.value='User list refreshed. Check the latest records before creating or editing an account again.'}
    else editorError.value='The user list could not be checked. Try Check user list again before continuing.'
    return
  }
  if(!hasChanges.value)return
  saving.value=true;editorError.value=''
  const row=selected.value,body=creating.value?{email:draft.email.trim().toLowerCase(),delivery_method:draft.delivery_method,role:draft.role,temporary_password:draft.temporary_password,school_ids:draft.role === 'admin' ? [] : draft.school_id?[draft.school_id]:[]}:{expected_revision:row.revision}
  const fullName=draft.full_name.trim().replace(/\s+/g,' ')
  if(creating.value||fullName!==row.full_name)body.full_name=fullName
  if(!creating.value&&draft.role!==row.role)body.role=draft.role
  if(!creating.value&&draft.account_status!==row.account_status)body.account_status=draft.account_status
  if(!creating.value&&normalized(effectiveSchoolIds.value)!==normalized(row.school_ids||[]))body.school_ids=[...effectiveSchoolIds.value]
  if(!creating.value&&canEditPermissions.value&&normalized(draft.permission_grants)!==normalized(row.permission_grants||[]))body.permission_grants=draft.permission_grants.map(grant=>({...grant}))
  try{
    const wasCreating=creating.value
    const result=await props.client.request(creating.value?'/accounts':'/accounts/'+encodeURIComponent(row.user_id),{method:creating.value?'POST':'PATCH',body,...(creating.value?{idempotencyKey:creationKey,timeout:30000,envelope:true}:{})})
    clearHandover()
    const delivery=result?.credential_delivery
    if(wasCreating&&['manual','failed','unknown'].includes(delivery?.status))handover.value={email:body.email,password:body.temporary_password,temporary:result.data?.must_change_password!==false}
    clearEditor()
    await load(false)
    notice.value=!wasCreating?'Account changes saved.':delivery?.status==='accepted'?'User created. The email service accepted their login details. Inbox delivery is not yet confirmed.':delivery?.status==='failed'?'User created, but the email service rejected the email. Give the details directly; do not create the account again.':delivery?.status==='unknown'?'User created. Email delivery could not be confirmed. Check the email service before sending again, or give these same details directly.':delivery?.status==='not_repeated'?'This account was already created. Email was not sent again. Check the original delivery; the password from this request was not verified.':delivery?.status==='manual'?'User created. Give the login details below directly to the user. No email was sent.':'User created. Email delivery was not confirmed.'
  }catch(failure){
    editorError.value=failure.message||'Account changes could not be saved.'
    draft.temporary_password=''
    reconcileNeeded.value=failure.status===0||failure.status===409||(failure.status>=500&&!['ACCOUNT_CREATION_UNAVAILABLE','ACCOUNT_EMAIL_UNAVAILABLE'].includes(failure.code))
    if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED','FORBIDDEN'].includes(failure.code))emit('access-change')
  }finally{saving.value=false}
}
watch(()=>props.profile,()=>{clearHandover();clearAction();clearEditor();reset();if(allowed.value)load(false)})
watch(()=>props.kind,()=>{clearHandover();search.value='';role.value='';status.value=accounts.value?'active':'';reset();if(allowed.value)load(false)})
const blocked=computed(()=>saving.value||reconcileNeeded.value||loadingEditor.value||actionBlocked.value)
watch(blocked,value=>emit('navigation-block',value),{immediate:true})
onBeforeRouteLeave(()=>!blocked.value)
function beforeUnload(event){if(blocked.value){event.preventDefault();event.returnValue=''}}
onMounted(()=>{window.addEventListener('beforeunload',beforeUnload);if(allowed.value)load(false)})
onBeforeUnmount(()=>{alive=false;version++;cancelFilterTimer();clearHandover();draft.temporary_password='';window.removeEventListener('beforeunload',beforeUnload);if(editor.value?.open)editor.value.close()})
</script>
<style scoped>
.users-filter-feedback{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:28px;margin:0 0 12px}.users-filter-feedback p{margin:0;color:var(--muted);font-size:12px}.users-reset-filters{padding:4px 0;border:0;background:transparent;color:var(--blue-700);font:500 12px/20px var(--font-ui);cursor:pointer}.users-reset-filters:hover{text-decoration:underline}.hosted-record-table tbody tr:hover{background:var(--blue-50)}
.account-handover{display:grid;gap:14px;max-width:560px;margin-top:20px;padding:20px;border:1px solid var(--border);border-radius:8px;min-width:0}.account-handover h2{font-size:18px;margin:0}.account-handover p{margin:0;line-height:1.6}.account-handover label{display:grid;gap:8px;min-width:0;font-size:14px;font-weight:600}.account-handover :is(input,output){width:100%;min-width:0;min-height:46px;box-sizing:border-box;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:#fff;color:var(--text);font:400 16px/1.5 var(--font-ui)}.account-login-id{overflow-wrap:anywhere;user-select:text}.account-handover :is(input,button):focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}.account-delivery-actions{display:flex;flex-wrap:wrap;gap:10px}.account-delivery-actions button{min-height:44px}
.account-row-actions{display:flex;gap:8px;flex-wrap:wrap;min-width:170px;max-width:280px}.account-delete-link{color:var(--danger-text)}.account-school-options,.account-permission-options{display:grid;gap:12px;min-width:0;margin:0;padding:16px;border:1px solid var(--border);border-radius:8px}.account-school-options legend,.account-permission-options legend{font-size:14px;font-weight:500;padding:0 6px}.account-editor-form .account-school-options label{display:flex;flex-direction:row;align-items:center;gap:8px}.account-school-options input[type=checkbox]{width:18px;min-height:18px;height:18px;flex:0 0 18px;padding:0;accent-color:var(--blue-700)}.account-permission-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.account-permission-row>button{grid-column:1/-1;justify-self:start}.account-editor:not(.account-creator){max-height:calc(100dvh - 32px)}@media(max-width:600px){.account-permission-row{grid-template-columns:1fr}.account-row-actions{min-width:0;max-width:none}}
.account-page-actions{display:flex;align-items:center;justify-content:flex-end;gap:12px;flex-wrap:wrap}.account-page-actions>.primary-action-btn{min-height:48px;font-size:14px;border-radius:8px}.account-editor-form{overflow-y:auto}
.account-editor.account-creator{max-height:calc(100dvh - 32px)}
.hosted-admin-records{display:grid;gap:24px;min-width:0}.hosted-page-header{margin:0}.hosted-page-header h1{margin:0;font-size:28px;font-weight:600;line-height:1.25;letter-spacing:-.025em}.hosted-record-stats{margin:0;gap:16px}.hosted-record-stats .user-summary-card{min-height:100px;padding:20px}.hosted-record-stats strong{font-size:28px}.hosted-record-panel{padding:24px;border-radius:12px}.hosted-record-toolbar{display:flex;justify-content:space-between;align-items:start;gap:16px;flex-wrap:wrap}.hosted-record-toolbar h2{margin:0;font-size:18px;font-weight:600}.hosted-record-toolbar p{margin:4px 0 0;color:var(--muted);font-size:13px}.hosted-record-filters{display:grid;grid-template-columns:minmax(180px,2fr) repeat(2,minmax(130px,1fr)) auto;align-items:end;gap:16px;margin:24px 0;padding:20px;background:var(--page-bg);border-radius:8px}.hosted-record-filters label{display:grid;gap:8px;min-width:0;font-size:14px;font-weight:600}.hosted-record-filters input,.hosted-record-filters select{width:100%;min-width:0;min-height:48px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:400 16px/1.5 var(--font-ui)}.hosted-record-table{margin:24px 0;border:1px solid var(--border);border-radius:12px}.hosted-record-table table{width:100%;min-width:720px}.hosted-record-table th,.hosted-record-table td{padding:16px;text-align:left;overflow-wrap:anywhere}.hosted-record-table th{background:var(--page-bg);font-size:12px}.hosted-record-table td{font-size:14px}.hosted-record-table small{display:block}.hosted-record-note{margin:20px 0 0;color:var(--muted);font-size:12px}.hosted-record-message{margin:24px 0;color:var(--muted)}.hosted-load-more{margin:0}.hosted-record-filters button{min-height:48px}.hosted-admin-records :is(button,input,select):focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}@media(max-width:900px){.hosted-record-filters{grid-template-columns:repeat(2,minmax(0,1fr))}.hosted-record-table table{min-width:0}}@media(max-width:700px){.hosted-record-filters{grid-template-columns:1fr;padding:16px}.hosted-record-panel{padding:20px}.hosted-record-stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.hosted-record-stats .user-summary-card{min-height:100px;padding:14px}}
.account-edit{min-height:36px;padding:6px 12px}.account-editor{width:min(calc(100% - 32px),520px);max-height:min(90dvh,720px);padding:0;border:1px solid var(--border);border-radius:12px;background:#fff;color:var(--text);box-shadow:0 18px 60px #11182733}.account-editor::backdrop{background:#10182770}.account-editor-form{display:grid;gap:18px;padding:28px}.account-editor-form header{display:flex;justify-content:space-between;align-items:start;gap:16px}.account-editor-form h2{margin:0;font-size:20px}.account-editor-form p{margin:6px 0 0;color:var(--muted);font-size:13px}.account-editor-form label{display:grid;gap:8px;font-size:14px;font-weight:600}.account-editor-form input,.account-editor-form select{width:100%;min-height:46px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:#fff;color:var(--text);font:400 16px/1.5 var(--font-ui)}.account-editor-form footer{display:flex;justify-content:flex-end;gap:12px;flex-wrap:wrap}.account-editor-form .editor-close{min-height:40px;width:40px;padding:0;border:0;border-radius:8px;background:transparent;color:var(--text);font-size:28px}.account-editor-form .error-message{margin:0}.account-editor-form :is(input,select,button):focus-visible{outline:3px solid var(--blue-700);outline-offset:3px}
</style>
