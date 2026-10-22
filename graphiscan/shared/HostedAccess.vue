<template>
  <component :is="action === 'ready' && $slots.workspace ? 'div' : 'main'" class="access-page" :class="{ 'access-login-layout': !profile && $slots.welcome, 'access-onboarding-layout': ['change_password','accept_privacy'].includes(action), 'access-privacy-layout': action === 'accept_privacy' }">
    <slot v-if="action === 'ready' && $slots.workspace" name="workspace" :client="client" :profile="profile" :refresh-account="refreshAccount" :sign-out="signOut" :change-password="submitAccountPassword" :busy="busy" :error="error" :message="message" :navigation-block="setNavigationBlock" />
    <header v-if="!(action === 'ready' && $slots.workspace)" class="access-header"><RouterLink to="/login" class="access-brand"><slot name="brand">GraphiScan</slot></RouterLink><span v-if="workspaceLabel">{{ workspaceLabel }}</span></header>
    <section v-if="!(action === 'ready' && $slots.workspace)" class="access-content" :class="{ 'workspace-ready': action === 'ready', 'custom-signin': !profile && $slots['sign-in'] }" aria-labelledby="access-title" :aria-busy="busy">
      <nav v-if="profile" aria-label="Account setup progress" class="access-steps">
        <ol><li :aria-current="action === 'change_password' ? 'step' : undefined">Password</li><li :aria-current="action === 'accept_privacy' || action === 'agreement_unavailable' ? 'step' : undefined">Privacy notice</li><li :aria-current="action === 'ready' ? 'step' : undefined">Ready</li></ol>
      </nav>
      <template v-if="!profile">
        <slot name="sign-in" :fields="signInFields" :busy="busy" :error="error" :message="message" :submit="signIn">
        <h1 id="access-title">{{ signInTitle }}</h1>
        <p>{{ signInDescription }}</p>
        <form @submit.prevent="signIn">
          <label for="hosted-email">Email address</label>
          <input id="hosted-email" v-model="email" type="email" required autocomplete="username" :disabled="busy" />
          <label for="hosted-password">Password</label>
          <input id="hosted-password" v-model="password" :type="showPassword ? 'text' : 'password'" required autocomplete="current-password" :disabled="busy" />
          <button class="access-text-button" type="button" :aria-pressed="showPassword" aria-controls="hosted-password" @click="showPassword = !showPassword">{{ showPassword ? 'Hide password' : 'Show password' }}</button>
          <button class="access-primary" type="submit" :disabled="busy">{{ busy ? 'Signing in…' : 'Sign in' }}</button>
        </form>
        <RouterLink v-if="showExistingSignIn" to="/login" class="access-return">Return to existing workspace sign-in</RouterLink>
        </slot>
      </template>
      <template v-else-if="action === 'change_password'">
        <div class="password-setup-symbol" aria-hidden="true"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></svg></div>
        <h1 id="access-title">Choose your own password</h1>
        <p class="password-setup-description">Set a personal password to secure your account before continuing.</p>
        <form class="password-setup-form" @submit.prevent="changePassword">
          <div class="password-setup-field">
          <label for="hosted-current">Current password</label><input id="hosted-current" v-model="currentPassword" type="password" required autocomplete="current-password" :disabled="busy" />
          </div>
          <div class="password-setup-field">
          <label for="hosted-new">New password</label><input id="hosted-new" v-model="newPassword" type="password" required minlength="8" autocomplete="new-password" aria-describedby="hosted-strength" :disabled="busy" />
          <p id="hosted-strength" class="access-hint">At least eight characters with uppercase, lowercase, a number and a symbol. Use a different password.</p>
          </div>
          <div class="password-setup-field">
          <label for="hosted-confirm">Confirm new password</label><input id="hosted-confirm" v-model="confirmPassword" type="password" required autocomplete="new-password" :disabled="busy" />
          </div>
          <button class="access-primary" type="submit" :disabled="busy">{{ busy ? 'Saving…' : 'Save password and sign in again' }}</button>
          <p class="password-signin-note">You will sign in again with your new password.</p>
        </form>
      </template>
      <template v-else-if="action === 'accept_privacy'">
        <h1 id="access-title">Data Privacy Agreement</h1>
        <p class="privacy-setup-description">Review how your information is used and your responsibilities when using GraphiScan.</p>
        <template v-if="notice">
          <div class="privacy-document-header"><h2>{{ notice.title }}</h2><span class="access-hint">Version {{ notice.version }}</span></div>
          <div class="access-notice" tabindex="0" role="region" aria-label="Full privacy notice">
            <template v-for="(block, index) in privacyBlocks" :key="index">
              <h3 v-if="/^\d+\.\s/.test(block)">{{ block }}</h3>
              <p v-else>{{ block }}</p>
            </template>
          </div>
          <form @submit.prevent="acceptNotice">
            <label class="access-checkbox"><input v-model="accepted" type="checkbox" required :disabled="busy" /><span>I have read and agree to the terms described above.</span></label>
            <button class="access-primary" type="submit" :disabled="busy || !accepted">{{ busy ? 'Saving…' : 'Accept and continue' }}</button>
          </form>
        </template>
        <p v-else>The notice could not be loaded. Refresh to try again.</p>
      </template>
      <template v-else-if="action === 'agreement_unavailable'">
        <h1 id="access-title">Privacy notice unavailable</h1>
        <p>Your account cannot continue until a notice is available. Contact your GraphiScan administrator.</p>
      </template>
      <template v-else>
        <h1 id="access-title">Account setup complete</h1>
        <p>Signed in as {{ profile.full_name }}.</p>
        <p>Your password and privacy steps are complete. Open the records available to your account below.</p>
        <HostedDirectory v-if="action === 'ready'" :client="client" :profile="profile" @access-change="refreshAccount" @navigation-block="directoryPending = $event" />
        <slot v-if="action === 'ready'" name="records" :client="client" :profile="profile" :refresh-account="refreshAccount" />
      </template>
      <p v-if="error && (profile || !$slots['sign-in'])" class="access-error" role="alert">{{ error }}</p>
      <p v-if="message && (profile || !$slots['sign-in'])" class="access-message" role="status">{{ message }}</p>
      <div v-if="profile" class="access-actions"><slot name="refresh-action" :busy="busy" :refresh="refreshAccount"><button type="button" :disabled="busy" @click="refreshAccount">Refresh account</button></slot><button type="button" :disabled="busy" @click="signOut">Sign out</button></div>
      <p class="access-session-note">For your privacy, reloading this page requires signing in again.</p>
    </section>
    <slot v-if="!profile" name="welcome" />
  </component>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, toRefs, watch } from 'vue'
import { RouterLink, onBeforeRouteLeave } from 'vue-router'
import { createHostedClient } from './hosted-client.mjs'
import HostedDirectory from './HostedDirectory.vue'
const props = defineProps({
  allowedRoles: { type: Array, required: true },
  apiOrigin: { type: String, required: true },
  workspaceLabel: { type: String, default: 'Account access' },
  signInTitle: { type: String, default: 'Sign in to your workspace' },
  signInDescription: { type: String, default: 'Use the account issued by your GraphiScan administrator.' },
  showExistingSignIn: { type: Boolean, default: true }
})
const client = createHostedClient(props.apiOrigin)
const emit = defineEmits(['access-state'])
const signInFields=reactive({email:'',password:'',showPassword:false})
const {email,password,showPassword}=toRefs(signInFields)
const currentPassword=ref(''), newPassword=ref(''), confirmPassword=ref('')
const profile=ref(null), notice=ref(null), accepted=ref(false), busy=ref(false), error=ref(''), message=ref('')
const privacyBlocks=computed(()=>(notice.value?.content || '').split(/\n\s*\n/).map(block=>block.trim()).filter(Boolean))
const directoryPending=ref(false)
function setNavigationBlock(value) { directoryPending.value = value }
const action=computed(()=>profile.value?.onboarding?.next_action)
watch(action, value=>emit('access-state', value === 'ready'), { immediate: true })
function clearPasswords() { password.value=currentPassword.value=newPassword.value=confirmPassword.value='' }
async function loadAccount() {
  const me=await client.request('/me')
  if (!props.allowedRoles.includes(me.role)) {
    await client.logout().catch(()=>{})
    throw new Error('This account is for a different workspace. Use the sign-in page for your role.')
  }
  profile.value=me
  if (me.onboarding.next_action==='accept_privacy') {
    notice.value=null;accepted.value=false
    notice.value=await client.request('/privacy-agreement')
  } else { notice.value=null;accepted.value=false }
}
async function run(task) {
  if (busy.value) return
  busy.value=true;error.value='';message.value=''
  try { await task() }
  catch (failure) {
    error.value=failure.message || 'The request could not be completed.'
    if (failure.status===401) { client.clear();profile.value=null;notice.value=null }
  } finally { busy.value=false }
}
function signIn() { return run(async()=>{
  try { await client.login(email.value.trim().toLowerCase(),password.value);await loadAccount() }
  catch (failure) { await client.logout().catch(()=>{});client.clear();profile.value=null;throw failure }
  finally { password.value='' }
}) }
function refreshAccount() { return run(loadAccount) }
function signOut() { return run(async()=>{ try { await client.logout();message.value='Signed out.' } finally { profile.value=null;notice.value=null;accepted.value=false;clearPasswords() } }) }
async function submitAccountPassword(fields) {
  if (busy.value) return
  currentPassword.value=fields.current_password;newPassword.value=fields.new_password;confirmPassword.value=fields.confirm_password
  try { await changePassword() } finally { clearPasswords() }
}
function changePassword() { return run(async()=>{
  if (newPassword.value!==confirmPassword.value) throw new Error('The new passwords do not match.')
  try {
    await client.request('/me/password',{method:'POST',body:{current_password:currentPassword.value,new_password:newPassword.value,confirm_password:confirmPassword.value}})
    client.clear();profile.value=null;message.value='Password saved. Sign in with your new password.'
  } catch (failure) {
    if (failure.code==='PASSWORD_CHANGE_RECOVERY_REQUIRED') { client.clear();profile.value=null }
    throw failure
  } finally { clearPasswords() }
}) }
function acceptNotice() { return run(async()=>{
  if (!accepted.value || !notice.value) return
  try { await client.request('/me/privacy-acceptance',{method:'POST',body:{agreement_version:notice.value.version,accepted:true}});await loadAccount() }
  catch (failure) {
    if (failure.code==='AGREEMENT_CHANGED') { accepted.value=false;await loadAccount();throw new Error('The notice changed. Read the new version before accepting.') }
    throw failure
  }
}) }
onBeforeUnmount(()=>{ clearPasswords();client.logout().catch(()=>{}) })
onBeforeRouteLeave(()=>{if(directoryPending.value){error.value='Confirm the pending submission before leaving this page. You can still sign out.';return false}})
</script>

<style scoped>
.access-page{min-height:100dvh;background:#f3f6f4;color:#17382d;font:16px/1.55 Arial,sans-serif;padding:24px;box-sizing:border-box}
.access-page *{box-sizing:border-box}.access-header{max-width:1080px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:20px}
.access-brand{font-size:24px;font-weight:700;color:#176347;text-decoration:none}.access-header>span{font-size:14px;color:#466056}
.access-content{width:min(100%,640px);margin:56px auto 40px;background:#fff;border:1px solid #d4dfd8;border-radius:14px;padding:36px}
.access-content.workspace-ready{width:min(100%,1080px)}
.password-setup-symbol,.password-signin-note{display:none}.password-setup-field{display:contents}
.access-content h1{font-size:30px;line-height:1.2;letter-spacing:-.02em;margin:0 0 16px;text-wrap:balance}.access-content h2{font-size:19px;line-height:1.4;margin:24px 0 8px}.access-content p{margin:0 0 24px}
.access-content form{display:flex;flex-direction:column;gap:10px;margin-top:28px}.access-content label{font-weight:600;margin-top:12px}
.access-content input:not([type=checkbox]){width:100%;min-height:48px;padding:10px 12px;border:1px solid #9bab9f;border-radius:8px;background:#fff;color:#17382d;font:inherit;caret-color:#176347}
.access-content button{min-height:44px;border:1px solid #9bab9f;border-radius:8px;padding:10px 16px;font:inherit;font-weight:600;background:#fff;color:#17382d;cursor:pointer}
.access-content button:hover{background:#edf4ee}.access-content button:disabled{opacity:.65;cursor:wait}.access-content .access-primary{background:#176347;border-color:#176347;color:#fff;margin-top:18px}.access-content .access-primary:hover{background:#104c35}
.access-content .access-text-button{align-self:flex-end;border:0;padding:4px 0;min-height:44px;font-size:14px;color:#176347;background:transparent}
.access-content :is(input,button,a,[tabindex]):focus-visible{outline:3px solid #287b59;outline-offset:3px}
.access-content .access-hint{font-size:14px;color:#466056;margin:0 0 10px}.access-return{display:inline-block;margin-top:24px;color:#176347;text-underline-offset:4px}
.access-content .access-notice{white-space:pre-wrap;overflow-wrap:anywhere;max-height:55dvh;overflow-y:auto;padding:20px;background:#f3f6f4;border-radius:8px;scrollbar-color:#738d7e #f3f6f4;line-height:1.65}
.access-content .access-checkbox{display:flex;align-items:flex-start;gap:12px;font-weight:400}.access-checkbox input{accent-color:#176347;width:20px;height:20px;flex-shrink:0;margin-top:3px}
.access-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.access-content .access-error{color:#922c24;background:#fff0ed;padding:14px;border-radius:8px;margin:24px 0 0}.access-content .access-message{color:#176347;margin:24px 0 0}
.access-content .access-session-note{font-size:13px;color:#466056;margin:28px 0 0}.access-steps ol{padding:0 0 24px;margin:0 0 28px;display:flex;gap:24px;flex-wrap:wrap;list-style-position:inside;border-bottom:1px solid #d4dfd8;font-size:14px;color:#466056}.access-steps [aria-current=step]{color:#176347;font-weight:700}
.access-page ::selection{background:#c7e4ce;color:#17382d}@media(max-width:600px){.access-page{padding:18px 14px}.access-content{margin-top:32px;padding:24px 20px}.access-content h1{font-size:26px}.access-steps ol{gap:12px}}
</style>
