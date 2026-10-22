<template>
  <dialog ref="dialog" class="account-editor account-action-dialog" aria-labelledby="account-action-title" @cancel="onCancel">
    <form class="account-editor-form" @submit.prevent="submit">
      <header><div><h2 id="account-action-title">{{ title }}</h2><p>{{ description }}</p></div><button class="editor-close" type="button" aria-label="Close account action" :disabled="busy || (pending && !checked)" @click="close"><X :size="18" aria-hidden="true" /></button></header>
      <p class="account-action-person"><strong>{{ target.full_name }}</strong><span>{{ target.email }}</span></p>
      <div v-if="action === 'reset_password'" class="account-field-group">
        <label>New temporary password<input v-model="temporary" type="password" autocomplete="new-password" minlength="8" maxlength="128" required :disabled="busy || pending" aria-describedby="reset-password-help" /></label>
        <p id="reset-password-help">Use uppercase, lowercase, a number and a symbol. The user must change this password at their next sign-in.</p>
      </div>
      <label v-if="action === 'delete'">Type DELETE to confirm<input v-model="confirmation" autocomplete="off" required pattern="DELETE" :disabled="busy || pending" /></label>
      <label v-if="action !== 'status'">Your current password<input v-model="password" type="password" autocomplete="current-password" maxlength="4096" required :disabled="busy || pending" /></label>
      <p v-if="error" class="error-message" role="alert">{{ error }}</p>
      <p v-if="pending && action !== 'status'" class="account-operation-reference">Reference: {{ operation }}</p>
      <footer><button type="button" class="soft-action-btn" :disabled="busy || (pending && !checked)" @click="close">{{ pending ? 'Close' : 'Cancel' }}</button><button type="submit" :class="action === 'delete' || disabling ? 'account-danger-action' : 'primary-action-btn'" :disabled="busy">{{ busy ? 'Please wait…' : pending ? 'Check status' : confirmLabel }}</button></footer>
    </form>
  </dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { X } from 'lucide-vue-next'
const props=defineProps({client:{type:Object,required:true},target:{type:Object,required:true},action:{type:String,required:true},status:{type:String,default:''}})
const emit=defineEmits(['close','completed','navigation-block','access-change'])
const dialog=ref(null),busy=ref(false),pending=ref(false),checked=ref(false),error=ref(''),password=ref(''),temporary=ref(''),confirmation=ref('')
const operation=crypto.randomUUID()
const disabling=computed(()=>props.action==='status'&&props.status==='disabled')
const title=computed(()=>props.action==='delete'?'Delete unused account?':props.action==='reset_password'?'Reset password?':disabling.value?'Disable account?':'Activate account?')
const description=computed(()=>props.action==='delete'?'Only an unused account can be deleted. Accounts with assignments or history must be disabled instead. This removes sign-in access permanently.':props.action==='reset_password'?'Existing sessions will lose access. Share the new temporary password privately.':disabling.value?'This user will lose access immediately. Their records and assignments will be retained.':'This restores access without restoring previously revoked sessions.')
const confirmLabel=computed(()=>props.action==='delete'?'Delete account':props.action==='reset_password'?'Reset password':disabling.value?'Disable account':'Activate account')
function accessFailure(failure){if(failure.status===401||['ACCOUNT_UNAVAILABLE','PASSWORD_CHANGE_REQUIRED','PRIVACY_ACCEPTANCE_REQUIRED','AGREEMENT_NOT_CONFIGURED','FORBIDDEN'].includes(failure.code))emit('access-change')}
function close(){if(busy.value||(pending.value&&!checked.value))return;dialog.value?.close();emit('close',pending.value?'An account operation is unresolved. Contact the system operator; do not repeat it. Reference: '+operation:'')}
function onCancel(event){event.preventDefault();close()}
async function submit(){
  if(busy.value)return
  if(pending.value){await checkStatus();return}
  busy.value=true;error.value=''
  try{
    if(props.action==='status')await props.client.request('/accounts/'+props.target.user_id,{method:'PATCH',body:{expected_revision:props.target.revision,account_status:props.status}})
    else await props.client.request('/accounts/'+props.target.user_id+(props.action==='reset_password'?'/temporary-password':''),{method:props.action==='delete'?'DELETE':'POST',idempotencyKey:operation,timeout:30000,body:{expected_revision:props.target.revision,current_password:password.value,...(props.action==='reset_password'?{temporary_password:temporary.value}:{confirmation:confirmation.value})}})
    dialog.value?.close();emit('completed',props.action==='delete'?'Unused account deleted.':props.action==='reset_password'?'Password reset. Share the temporary password privately.':disabling.value?'Account disabled.':'Account activated.')
  }catch(failure){
    error.value=failure.message||'This action could not be completed.'
    pending.value=failure.status===0||failure.code==='ACCOUNT_OPERATION_PENDING'||(failure.status>=500&&failure.code!=='ACCOUNT_ACTION_UNAVAILABLE')
    checked.value=false;accessFailure(failure)
  }finally{password.value='';temporary.value='';busy.value=false}
}
async function checkStatus(){
  busy.value=true;error.value=''
  try{
    if(props.action==='status'){
      const current=await props.client.request('/accounts/'+props.target.user_id)
      if(current.account_status===props.status){dialog.value?.close();emit('completed','Account status confirmed.');return}
      checked.value=true;error.value='The requested status change is not confirmed. Close this dialog and inspect the latest account before trying again.'
    }else{
      const current=await props.client.request('/account-operations/'+operation)
      if(current.state==='completed'){dialog.value?.close();emit('completed','Account operation confirmed.');return}
      checked.value=true;error.value='This operation is still pending. Contact the system operator with the reference below. Do not repeat it.'
    }
  }catch(failure){checked.value=failure.status===404;error.value=failure.status===404?'The operation could not be found. Check the account and contact the system operator before trying again.':failure.message;accessFailure(failure)}
  finally{busy.value=false}
}
const blocked=computed(()=>busy.value||(pending.value&&!checked.value))
watch(blocked,value=>emit('navigation-block',value),{immediate:true})
onBeforeRouteLeave(()=>!blocked.value)
function beforeUnload(event){if(blocked.value){event.preventDefault();event.returnValue=''}}
onMounted(async()=>{window.addEventListener('beforeunload',beforeUnload);await nextTick();dialog.value?.showModal();(dialog.value?.querySelector('input')||dialog.value?.querySelector('.editor-close'))?.focus()})
onBeforeUnmount(()=>{password.value='';temporary.value='';window.removeEventListener('beforeunload',beforeUnload);dialog.value?.close();emit('navigation-block',false)})
</script>

<style scoped>
.account-action-dialog{width:min(calc(100% - 32px),520px);max-height:calc(100dvh - 32px);padding:0;border:1px solid var(--border);border-radius:12px;background:var(--white);color:var(--text)}.account-action-dialog::backdrop{background:#10182770}.account-editor-form{display:grid;gap:18px;padding:24px}.account-editor-form header{display:flex;justify-content:space-between;align-items:start;gap:16px}.account-editor-form h2{margin:0;font-size:20px}.account-editor-form p{margin:6px 0 0;font-size:13px;color:var(--muted)}.account-editor-form label{display:grid;gap:8px;font-size:14px;font-weight:500}.account-editor-form input{width:100%;border:1px solid var(--control-border);border-radius:8px}.account-editor-form footer{display:flex;justify-content:flex-end;gap:12px}.editor-close{display:grid;place-items:center;width:44px;min-height:44px;padding:0;border:0;background:transparent}.account-action-person{display:grid;gap:4px}.account-action-person strong{color:var(--text);font-size:14px}.account-action-person span{overflow-wrap:anywhere}.account-danger-action{background:#b42318;color:white;border:1px solid #b42318;cursor:pointer}.account-danger-action:hover:not(:disabled){background:#912018}.account-danger-action:disabled{opacity:.6;cursor:default}.account-operation-reference{overflow-wrap:anywhere;font-size:12px}.account-editor-form .error-message{color:var(--danger-text)}
</style>
