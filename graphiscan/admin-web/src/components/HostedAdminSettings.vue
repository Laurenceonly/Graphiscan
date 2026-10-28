<template>
  <section class="hosted-security" aria-labelledby="security-title">
    <h2 id="security-title">Change password</h2>
    <p>Changing your password will sign you out.</p>
    <form @submit.prevent="submit">
      <div v-for="field in fields" :key="field.key" class="security-field">
        <label :for="'settings-' + field.key">{{ field.label }}</label>
        <div class="security-input">
          <input :id="'settings-' + field.key" v-model="draft[field.key]" :type="visible[field.key] ? 'text' : 'password'" :autocomplete="field.key === 'current_password' ? 'current-password' : 'new-password'" :minlength="field.key === 'current_password' ? undefined : 8" required :disabled="busy" :aria-invalid="field.key === 'confirm_password' && mismatch || undefined" :aria-describedby="field.key === 'new_password' ? 'settings-password-help' : field.key === 'confirm_password' && mismatch ? 'settings-password-mismatch' : undefined" />
          <button type="button" :aria-label="(visible[field.key] ? 'Hide ' : 'Show ') + field.label.toLowerCase()" :aria-pressed="visible[field.key]" :disabled="busy" @click="visible[field.key] = !visible[field.key]">{{ visible[field.key] ? 'Hide' : 'Show' }}</button>
        </div>
      </div>
      <p v-if="mismatch" id="settings-password-mismatch" class="security-warning" role="status">New passwords do not match.</p>
      <div id="settings-password-help" class="security-rules"><p>Use a different password with:</p><ul><li v-for="rule in rules" :key="rule.label" :class="{ met: rule.met }">{{ rule.label }}</li></ul></div>
      <div class="security-actions"><button type="button" class="soft-action-btn" :disabled="busy" @click="clear">Clear</button><button type="submit" class="primary-action-btn" :disabled="busy || mismatch">{{ busy ? 'Saving…' : 'Change password' }}</button></div>
    </form>
  </section>
</template>
<script setup>
import { computed, onBeforeUnmount, reactive } from 'vue'
const props=defineProps({changePassword:{type:Function,required:true},busy:Boolean})
const draft=reactive({current_password:'',new_password:'',confirm_password:''})
const visible=reactive({current_password:false,new_password:false,confirm_password:false})
const fields=[{key:'current_password',label:'Current password'},{key:'new_password',label:'New password'},{key:'confirm_password',label:'Confirm new password'}]
const mismatch=computed(()=>Boolean(draft.confirm_password&&draft.new_password!==draft.confirm_password))
const rules=computed(()=>[{label:'At least 8 characters',met:draft.new_password.length>=8},{label:'One uppercase letter',met:/[A-Z]/.test(draft.new_password)},{label:'One lowercase letter',met:/[a-z]/.test(draft.new_password)},{label:'One number',met:/[0-9]/.test(draft.new_password)},{label:'One symbol',met:/[^A-Za-z0-9]/.test(draft.new_password)}])
function clear(){for(const key of Object.keys(draft)){draft[key]='';visible[key]=false}}
async function submit(){if(props.busy||mismatch.value)return;try{await props.changePassword({...draft})}finally{clear()}}
onBeforeUnmount(clear)
</script>
<style scoped>
.hosted-security{max-width:600px;margin:24px 0;padding:24px;border:1px solid var(--border);border-radius:12px;background:var(--white)}
h2{margin:0;font-size:18px;font-weight:600}p{color:var(--muted);font-size:14px;line-height:1.6}form{display:grid;gap:20px;max-width:680px}.security-field{display:grid;gap:8px}label{font-size:14px;font-weight:500}.security-input{display:flex;border:1px solid var(--control-border);border-radius:8px;min-width:0;overflow:hidden}.security-input:focus-within{outline:3px solid var(--blue-700);outline-offset:3px}input{min-width:0;width:100%;padding:12px;border:0;outline:none;background:var(--white);color:var(--text);font:400 16px/1.5 var(--font-ui)}.security-input button{min-height:48px;min-width:60px;border:0;background:var(--blue-50);color:var(--blue-700);cursor:pointer}button:focus-visible{outline:3px solid var(--blue-700);outline-offset:-3px}.security-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.security-actions button{margin:0}.security-warning{margin:0;color:var(--danger-text)}.security-rules p{margin:0 0 8px}.security-rules ul{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 14px;margin:0;padding-left:20px;color:var(--muted);font-size:12px}.security-rules li.met{color:var(--success-text)}.primary-action-btn{min-height:44px}@media(max-width:600px){.hosted-security{padding:20px 16px}.security-rules ul{grid-template-columns:1fr}.security-actions button{flex:1}}
</style>
