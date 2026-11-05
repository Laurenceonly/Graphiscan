<template>
  <dialog ref="dialog" class="account-action-dialog account-assignment-dialog" aria-labelledby="assignment-access-title" @cancel="onCancel">
    <form class="account-editor-form" @submit.prevent="save">
      <header><div><h2 id="assignment-access-title">Manage assignments</h2><p>{{ section === 'schools' ? 'Choose the schools linked to ' + target.full_name + '.' : 'Choose which staff can select ' + target.full_name + ' for assignments.' }}</p></div><button type="button" class="editor-close" aria-label="Close assignments" :disabled="busy || (uncertain && !checked)" @click="close"><X :size="18" aria-hidden="true" /></button></header>
      <nav v-if="canEditSchools && canAssign" class="assignment-sections" aria-label="Assignment settings"><button type="button" :aria-pressed="section === 'schools'" :disabled="busy || uncertain || (section === 'staff' && staffChanged)" @click="showSection('schools')">Schools</button><button type="button" :aria-pressed="section === 'staff'" :disabled="busy || uncertain || schoolsChanged" @click="showSection('staff')">Assigning staff</button></nav>
      <template v-if="section === 'schools'">
        <div class="assignment-school-list"><label v-for="item in schools" :key="item.school_id"><input v-model="schoolIds" type="checkbox" :value="String(item.school_id)" :disabled="busy || uncertain" />{{ item.name }}</label></div>
        <p v-if="!schools.length">No schools are available to your account.</p>
        <p v-if="schoolNote">{{ schoolNote }}</p>
        <p v-if="schoolsChanged && canAssign">Save school changes before editing assigning staff.</p>
      </template>
      <template v-else>
      <div class="assignment-field"><label for="assignment-access-school">School</label><select id="assignment-access-school" v-model="school" required :disabled="busy || uncertain" @change="loadPair"><option value="">Choose a school</option><option v-for="item in schools" :key="item.school_id" :value="String(item.school_id)">{{ item.name }}</option></select></div>
      <p v-if="schoolNote">{{ schoolNote }}</p>
      <div class="assignment-account-search"><label>Find staff<span class="admin-search-control"><Search :size="18" :stroke-width="1.8" aria-hidden="true" /><input v-model="search" type="search" placeholder="Name or email" maxlength="120" :disabled="busy || uncertain" @keydown.enter.prevent="searchActors(false)" /></span></label><button type="button" class="soft-action-btn" :disabled="busy || uncertain" @click="searchActors(false)">Search</button></div>
      <div class="assignment-field"><label for="assignment-access-actor">Staff member</label><select id="assignment-access-actor" v-model="actor" required :disabled="busy || uncertain" @change="loadPair"><option v-for="item in actorOptions" :key="item.user_id" :value="item.user_id">{{ item.full_name }}{{ item.user_id === profile.user_id ? ' (you)' : '' }}</option></select></div>
      <button v-if="cursor" type="button" class="soft-action-btn assignment-more" :disabled="busy || uncertain" @click="searchActors(true)">Load more accounts</button>
      <p v-if="searchNotice" role="status">{{ searchNotice }}</p><p v-if="loading" role="status">Checking assignment access…</p>
      <section v-if="current" class="assignment-access-state" aria-label="Current assignment access">
        <label class="assignment-access-choice"><input v-model="eligible" type="checkbox" :disabled="busy || uncertain || (!current.can_grant && !current.eligible)" />Allow this staff member to select {{ target.full_name }}</label>
        <p>{{ current.effective ? 'Currently available for assignment.' : 'Not currently available for assignment.' }}</p>
        <p v-if="!current.can_grant">Check the account roles, active status and school access before allowing assignment. You can remove an existing link.</p>
        <p v-if="target.role === 'parent'">Verify the parent or guardian relationship before linking a student.</p>
      </section>
      </template>
      <p v-if="message" role="status">{{ message }}</p><p v-if="error" class="error-message" role="alert">{{ error }}</p>
      <footer><button type="button" class="soft-action-btn" :disabled="busy || (uncertain && !checked)" @click="close">{{ uncertain ? 'Close' : 'Cancel' }}</button><button type="submit" class="primary-action-btn" :disabled="busy || (!uncertain && (section === 'schools' ? !schoolsChanged : !current || !staffChanged))">{{ saving ? 'Saving…' : uncertain ? section === 'schools' ? 'Check current schools' : 'Check current access' : section === 'schools' ? 'Save schools' : 'Save access' }}</button></footer>
    </form>
  </dialog>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { Search, X } from 'lucide-vue-next'
const props=defineProps({client:{type:Object,required:true},target:{type:Object,required:true},profile:{type:Object,required:true},schools:{type:Array,default:()=>[]},schoolNote:{type:String,default:''}})
const emit=defineEmits(['close','completed','navigation-block','access-change'])
const canEditSchools=computed(()=>props.profile.permissions?.includes('accounts.manage')&&props.target.role!=='admin'&&props.target.user_id!==props.profile.user_id)
const canAssign=computed(()=>props.profile.permissions?.includes('assignments.manage')&&['teacher','parent','expert'].includes(props.target.role))
const section=ref(canEditSchools.value?'schools':'staff'),schoolIds=ref([...(props.target.school_ids||[])])
const schoolsChanged=computed(()=>JSON.stringify([...schoolIds.value].sort())!==JSON.stringify([...(props.target.school_ids||[])].sort()))
const dialog=ref(null),school=ref(''),actor=ref(props.profile.user_id),search=ref(''),cursor=ref(null),searchNotice=ref('')
const actorOptions=ref([{user_id:props.profile.user_id,full_name:props.profile.full_name,role:props.profile.role}])
const current=ref(null),eligible=ref(false),loading=ref(false),saving=ref(false),searching=ref(false),uncertain=ref(false),checked=ref(false),error=ref(''),message=ref('')
const staffChanged=computed(()=>!!current.value&&eligible.value!==current.value.eligible)
const busy=computed(()=>loading.value||saving.value||searching.value),blocked=computed(()=>saving.value||(uncertain.value&&!checked.value))
let alive=true,appliedSearch=''
function accessFailure(failure){if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED'].includes(failure.code))emit('access-change')}
function close(){if(busy.value||(uncertain.value&&!checked.value))return;dialog.value?.close();emit('close',uncertain.value?'Assignment changes were not confirmed. Reload the account before making more changes.':'')}
function showSection(value){if(busy.value||uncertain.value||schoolsChanged.value||staffChanged.value)return;section.value=value;if(value==='staff')loadPair()}
function onCancel(event){event.preventDefault();close()}
async function loadPair(){
  if(saving.value||searching.value)return
  if(!school.value||!actor.value){current.value=null;error.value='Choose a school and assigning account.';return}
  loading.value=true;error.value='';message.value='';current.value=null
  try{
    const query=new URLSearchParams({school_id:school.value,actor_id:actor.value})
    const data=await props.client.request('/accounts/'+props.target.user_id+'/assignment-access?'+query)
    if(!alive)return
    current.value=data;eligible.value=data.eligible
    if(uncertain.value)message.value='Current access loaded. Review it before making another change.'
    uncertain.value=false;checked.value=false
  }catch(failure){if(alive){error.value=failure.message||'Assignment access could not be loaded.';if(uncertain.value)checked.value=true;accessFailure(failure)}}
  finally{if(alive)loading.value=false}
}
async function searchActors(more=false){
  if(busy.value||uncertain.value)return
  searching.value=true;error.value='';searchNotice.value='';if(!more)appliedSearch=search.value.trim()
  const query=new URLSearchParams({limit:'25',account_status:'active'})
  if(appliedSearch)query.set('q',appliedSearch)
  if(more&&cursor.value)query.set('cursor',cursor.value)
  try{
    const response=await props.client.request('/accounts?'+query,{envelope:true});if(!alive)return
    const retained=actorOptions.value.filter(item=>item.user_id===props.profile.user_id||item.user_id===actor.value)
    const choices=response.data.filter(item=>['admin','researcher','teacher'].includes(item.role))
    actorOptions.value=[...new Map([...(more?actorOptions.value:retained),...choices].map(item=>[item.user_id,item])).values()];cursor.value=response.page.next_cursor
    if(!choices.length)searchNotice.value=cursor.value?'No assigning accounts on this page. Load more accounts to continue.':'No matching assigning accounts.'
  }catch(failure){if(alive){error.value=failure.message||'Accounts could not be searched.';accessFailure(failure)}}
  finally{if(alive)searching.value=false}
}
async function save(){
  if(busy.value)return
  if(section.value==='schools'){
    if(!canEditSchools.value||(!uncertain.value&&!schoolsChanged.value))return
    saving.value=true;error.value=''
    try{
      if(uncertain.value){await props.client.request('/accounts/'+props.target.user_id);if(alive){dialog.value?.close();emit('completed','School assignments refreshed. Review the account before making more changes.')}}
      else{await props.client.request('/accounts/'+props.target.user_id,{method:'PATCH',body:{expected_revision:props.target.revision,school_ids:[...schoolIds.value]}});if(alive){dialog.value?.close();emit('completed','School assignments updated.')}}
    }catch(failure){if(alive){error.value=failure.message||'School assignments could not be saved.';if(uncertain.value)checked.value=true;else{uncertain.value=failure.status===0||failure.status===409||failure.status>=500;checked.value=false}accessFailure(failure)}}
    finally{if(alive)saving.value=false}
    return
  }
  if(!canAssign.value)return
  if(uncertain.value){await loadPair();return}
  if(!current.value||eligible.value===current.value.eligible)return
  saving.value=true;error.value='';message.value=''
  try{
    await props.client.request('/accounts/'+props.target.user_id+'/assignment-access',{method:'PATCH',body:{actor_id:actor.value,school_id:school.value,expected_revision:current.value.revision,eligible:eligible.value}})
    if(alive){dialog.value?.close();emit('completed','Assignment access updated.')}
  }catch(failure){if(alive){error.value=failure.message||'Assignment access could not be saved.';uncertain.value=failure.status===0||failure.status===409||failure.status>=500;checked.value=false;accessFailure(failure)}}
  finally{if(alive)saving.value=false}
}
watch(blocked,value=>emit('navigation-block',value),{immediate:true})
onBeforeRouteLeave(()=>!blocked.value)
function beforeUnload(event){if(blocked.value){event.preventDefault();event.returnValue=''}}
onMounted(async()=>{
  window.addEventListener('beforeunload',beforeUnload);school.value=String(props.schools.find(item=>props.target.school_ids?.includes(String(item.school_id)))?.school_id||props.schools[0]?.school_id||'')
  await nextTick();dialog.value?.showModal();dialog.value?.querySelector('input,select')?.focus();if(section.value==='staff')await loadPair()
})
onBeforeUnmount(()=>{alive=false;window.removeEventListener('beforeunload',beforeUnload);dialog.value?.close();emit('navigation-block',false)})
</script>
<style scoped>
.assignment-sections{display:flex;gap:8px}.assignment-sections button{flex:1;min-height:44px;padding:8px 12px;border:1px solid var(--border);border-radius:8px;background:var(--white);color:var(--blue-700);font:500 13px/1.5 var(--font-ui);cursor:pointer}.assignment-sections button[aria-pressed=true]{border-color:var(--blue-700);background:var(--blue-50)}.assignment-sections button:disabled{opacity:.6;cursor:default}.assignment-school-list{display:grid;gap:12px}.account-editor-form .assignment-school-list label{display:flex;flex-direction:row;align-items:center;gap:10px}.account-editor-form .assignment-school-list input{width:18px;height:18px;min-height:18px;flex:0 0 18px;padding:0;accent-color:var(--blue-700)}
.assignment-field{display:grid;gap:8px;min-width:0}
@media(max-width:380px){.account-assignment-dialog .account-editor-form footer{display:grid;grid-template-columns:minmax(0,1fr)}.account-assignment-dialog .account-editor-form footer>button{width:100%}}
.account-assignment-dialog{width:min(calc(100% - 32px),640px);max-height:calc(100dvh - 32px);padding:0;border:1px solid var(--border);border-radius:12px;background:var(--white);color:var(--text)}.account-assignment-dialog::backdrop{background:#10182770}.account-editor-form{display:grid;gap:18px;padding:24px}.account-editor-form header{display:flex;justify-content:space-between;align-items:start;gap:16px}.account-editor-form h2{margin:0;font-size:20px}.account-editor-form p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}.account-editor-form label{display:grid;gap:8px;font-size:14px;font-weight:500;min-width:0}.account-editor-form :is(input,select){width:100%;min-width:0;min-height:46px;padding:10px 12px;border:1px solid var(--control-border);border-radius:8px;background:var(--white);color:var(--text);font:400 16px/1.5 var(--font-ui)}.account-editor-form footer{display:flex;justify-content:flex-end;gap:12px;flex-wrap:wrap}.editor-close{display:grid;place-items:center;min-width:44px;width:44px;min-height:44px;padding:0;border:0;background:transparent}.assignment-account-search{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:12px}.assignment-account-search button{min-height:46px}.assignment-more{justify-self:start}.assignment-access-state{display:grid;gap:10px;padding:16px;border:1px solid var(--border);border-radius:8px}.account-editor-form .assignment-access-choice{display:flex;flex-direction:row;align-items:start;gap:10px;line-height:1.5}.account-editor-form .assignment-access-choice input{min-height:18px;width:18px;height:18px;flex:0 0 18px;padding:0;margin-top:2px;accent-color:var(--blue-700)}.account-editor-form .error-message{color:var(--danger-text)}@media(max-width:600px){.assignment-account-search{grid-template-columns:1fr}.assignment-account-search button{justify-self:start}}
</style>
