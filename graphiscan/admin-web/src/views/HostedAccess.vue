<template>
  <div class="hosted-admin">
  <svg class="brand-filter-defs" aria-hidden="true" focusable="false" width="0" height="0">
    <defs>
      <filter id="graphiscan-brand-blue" color-interpolation-filters="sRGB">
        <!-- Map the blue artwork to the primary palette; preserve its white background. -->
        <feColorMatrix type="matrix" values="
          .921569 0 0 0 .078431
          .639216 0 0 0 .360784
          .439216 0 0 0 .560784
          0 0 0 1 0" />
      </filter>
    </defs>
  </svg>
  <HostedAccess :allowed-roles="['admin','researcher']" :api-origin="origin"
    workspace-label="" sign-in-title="Admin sign-in"
    sign-in-description="Sign in with your issued administrator or researcher account."
    :show-existing-sign-in="false" @access-state="syncAccessRoute">
    <template #brand><img class="admin-brand-logo" :src="brandLogo" alt="" width="56" height="56" /><span>Graphi<span class="admin-brand-accent">Scan</span></span></template>
    <template #sign-in="{ fields, busy, error, message, submit }">
      <AdminSignInForm :fields="fields" :busy="busy" :error="error" :message="message" @submit="submit" />
    </template>
    <template #welcome><AdminLoginPanel /></template>
    <template #workspace="{ client, profile, refreshAccount, signOut, changePassword, busy, error, message, navigationBlock }">
      <HostedAdminWorkspace :client="client" :profile="profile" :refresh-account="refreshAccount" :sign-out="signOut" :change-password="changePassword" :busy="busy" :error="error" :message="message" @navigation-block="navigationBlock" />
    </template>
  </HostedAccess>
  </div>
</template>
<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HostedAccess from '../../../shared/HostedAccess.vue'
import HostedAdminWorkspace from '../components/HostedAdminWorkspace.vue'
import AdminLoginPanel from '../components/AdminLoginPanel.vue'
import AdminSignInForm from '../components/AdminSignInForm.vue'
import brandLogo from '../assets/graphiscan-logo.png'
const origin=(import.meta.env.VITE_HOSTED_API_ORIGIN || import.meta.env.VITE_API_ORIGIN || 'http://localhost:5000').replace(/\/$/,'')
const route = useRoute()
const router = useRouter()
const workspaceReady = ref(false)
function syncAccessRoute(ready = workspaceReady.value) {
  workspaceReady.value = ready
  const destination = ready ? '/workspace' : '/login'
  if (['/login', '/workspace'].includes(route.path) && route.path !== destination) {
    router.replace(destination)
  }
}
watch(() => route.path, () => syncAccessRoute())
</script>

<style scoped>
/* Keep the shared account flow intact; adopt the admin's existing visual system. */
.hosted-admin:has(.hosted-workspace) :deep(.access-page) { padding: 0; }
.hosted-admin:has(.hosted-workspace) :deep(:is(.directory,.hosted-screenings)) { margin:0; padding:0; border:0; }
.hosted-admin:has(.hosted-workspace) :deep(:is(.directory,.hosted-screenings) > h2) { margin:0 0 24px; font-size:28px; }
.hosted-admin :deep(.access-page) {
  background: var(--page-bg);
  color: var(--text);
  font: 400 15px/1.6 var(--font-ui);
  padding: 28px 32px;
}
.hosted-admin :deep(.access-header) {
  max-width: 1184px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.hosted-admin :deep(.access-brand) {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 2px;
  color: var(--text);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -.025em;
}
.brand-filter-defs { position: absolute; pointer-events: none; }
.admin-brand-logo { display: block; width: 64px; height: 64px; object-fit: contain; flex-shrink: 0; filter: url(#graphiscan-brand-blue); }
.admin-brand-accent { color: var(--blue-700); }
.hosted-admin :deep(.access-header > span) { color: var(--muted); }
.hosted-admin :deep(.access-content) {
  width: min(100%, 520px);
  margin: 48px auto;
  padding: 36px;
  border-color: var(--border);
  border-radius: var(--panel-radius);
}
.hosted-admin :deep(.access-content.workspace-ready) { width: min(100%, 1184px); }
.hosted-admin :deep(.access-content h1) {
  margin-bottom: 12px;
  font-size: clamp(1.6rem, 2.5vw, 2rem);
  line-height: 1.2;
  letter-spacing: -.025em;
  font-weight: 600;
}
.hosted-admin :deep(.access-content p) { max-width: 72ch; color: var(--text-soft); }
.hosted-admin :deep(.access-content label) { font-size: 14px; font-weight: 600; }
.hosted-admin :deep(.access-content :is(input:not([type=checkbox]), select, textarea)) {
  min-height: 46px;
  border: 1px solid var(--control-border);
  border-radius: var(--control-radius);
  color: var(--text);
  background: var(--white);
  font: inherit;
  font-size: 16px;
  padding: 10px 12px;
  caret-color: var(--blue-700);
}
.hosted-admin :deep(.access-content button) {
  min-height: 44px;
  border-color: var(--control-border);
  border-radius: var(--control-radius);
  color: var(--text-soft);
  background: var(--white);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  transition: background-color 140ms ease, border-color 140ms ease;
}
.hosted-admin :deep(.access-content button:hover:not(:disabled)) {
  background: var(--blue-50);
  border-color: var(--blue-500);
  color: var(--blue-700);
}
.hosted-admin :deep(.access-content button:disabled) { cursor: default; opacity: .6; }
.hosted-admin :deep(.access-content .access-primary),
.hosted-admin :deep(.directory button[aria-pressed=true]),
.hosted-admin :deep(.directory-actions button[type=submit]),
.hosted-admin :deep(.assignment-form button[type=submit]) {
  background: var(--blue-700);
  border-color: var(--blue-700);
  color: var(--white);
}
.hosted-admin :deep(.access-content .access-primary:hover:not(:disabled)),
.hosted-admin :deep(.directory button[aria-pressed=true]:hover:not(:disabled)),
.hosted-admin :deep(.directory-actions button[type=submit]:hover:not(:disabled)),
.hosted-admin :deep(.assignment-form button[type=submit]:hover:not(:disabled)) {
  background: #104d79;
  border-color: #104d79;
  color: var(--white);
}
.hosted-admin :deep(.access-content .access-text-button) {
  background: transparent;
  border-color: transparent;
  color: var(--blue-700);
}
.hosted-admin :deep(.access-return) {
  display: inline-block;
  color: var(--blue-700);
  font-size: 14px;
  text-underline-offset: 4px;
}
.hosted-admin :deep(.access-return:hover) { text-decoration: underline; }
.hosted-admin :deep(.access-content :is(.access-hint, .access-session-note, .directory-hint)) {
  color: var(--muted);
  font-size: 13px;
}
.hosted-admin :deep(.access-steps ol) {
  border-color: var(--border);
  color: var(--muted);
  font-size: 13px;
}
.hosted-admin :deep(.access-steps [aria-current=step]) { color: var(--blue-700); }
.hosted-admin :deep(:is(.directory, .hosted-screenings)) {
  margin-top: 36px;
  padding-top: 28px;
  border-color: var(--border);
  color: var(--text);
}
.hosted-admin :deep(:is(.directory, .hosted-screenings) h2) {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -.02em;
  margin-bottom: 20px;
}
.hosted-admin :deep(.directory-nav) { gap: 8px; }
.hosted-admin :deep(.directory-nav button:last-child) { margin-left: auto; }
.hosted-admin :deep(:is(.directory-filters, .screening-filters)) {
  padding: 20px;
  background: var(--page-bg);
  border-radius: var(--control-radius);
  margin-top: 0;
}
.hosted-admin :deep(:is(.directory-list, .screening-list) li) { border-color: var(--border); padding: 20px 0; }
.hosted-admin :deep(:is(.directory-list, .screening-list) span) { color: var(--muted); font-size: 14px; }
.hosted-admin :deep(:is(.directory-editor, .screening-detail, .assignment-form)) { border-color: var(--border); }
.hosted-admin :deep(.screening-detail dl) { font-size: 14px; gap: 16px 24px; }
.hosted-admin :deep(.screening-detail dt) { color: var(--muted); font-weight: 500; }
.hosted-admin :deep(.screening-detail dd) { color: var(--text); }
.hosted-admin :deep(:is(.access-error, .directory-error, .screening-error)) {
  color: #991b1b;
  background: #fef2f2;
  padding: 14px 16px;
  border-radius: var(--control-radius);
}
.hosted-admin :deep(:is(.access-message, .directory-message)) { color: var(--success-text); }
.hosted-admin :deep(.access-actions) { border-top: 1px solid var(--border); padding-top: 24px; margin-top: 32px; }
.hosted-admin :deep(.access-onboarding-layout) { background: #fff; padding: 24px 32px 40px; }
.hosted-admin :deep(.access-onboarding-layout .access-header) { border: 0; padding-bottom: 0; }
.hosted-admin :deep(.access-onboarding-layout .access-content) {
  width: min(100%, 560px); margin: 32px auto 0; padding: 36px 40px 28px;
  border: 1px solid #e2e8f0; border-radius: 20px; background: #fff;
}
.hosted-admin :deep(.access-onboarding-layout .access-steps ol) {
  display: grid; grid-template-columns: 1fr 1.25fr .7fr; gap: 16px;
  counter-reset: setup; list-style: none; margin: 0 0 28px; padding: 0 0 24px;
  border-bottom: 1px solid #e8edf3; font-size: 12px; line-height: 1.4;
}
.hosted-admin :deep(.access-onboarding-layout .access-steps li) {
  display: flex; align-items: center; gap: 8px; color: #8290a3; white-space: nowrap;
}
.hosted-admin :deep(.access-onboarding-layout .access-steps li::before) {
  counter-increment: setup; content: counter(setup); display: grid; place-items: center;
  width: 26px; height: 26px; flex: 0 0 26px; border-radius: 50%;
  border: 1px solid #dfe6ee; color: #77869b; font-size: 11px; font-weight: 600;
}
.hosted-admin :deep(.access-onboarding-layout .access-steps [aria-current=step]) { color: var(--blue-700); font-weight: 600; }
.hosted-admin :deep(.access-onboarding-layout .access-steps [aria-current=step]::before) { background: var(--blue-700); color: #fff; border-color: var(--blue-700); }
.hosted-admin :deep(.access-onboarding-layout .password-setup-symbol) {
  display: grid; place-items: center; width: 48px; height: 48px;
  border: 1px solid #dbe6f0; border-radius: 14px; color: var(--blue-700); margin-bottom: 20px;
}
.hosted-admin :deep(.access-onboarding-layout h1) { font-size: 28px; line-height: 1.25; letter-spacing: -.035em; margin: 0 0 10px; }
.hosted-admin :deep(.access-onboarding-layout .password-setup-description) { font-size: 14px; line-height: 1.65; color: #64748b; margin: 0; max-width: 45ch; }
.hosted-admin :deep(.access-onboarding-layout .password-setup-form) { margin-top: 28px; gap: 20px; }
.hosted-admin :deep(.access-onboarding-layout .password-setup-field) { display: flex; flex-direction: column; gap: 8px; }
.hosted-admin :deep(.access-onboarding-layout .password-setup-field label) { margin: 0; font-size: 13px; font-weight: 600; color: #27364b; }
.hosted-admin :deep(.access-onboarding-layout .password-setup-field input) { height: 50px; min-height: 50px; border: 1px solid #d4dde8; border-radius: 9px; padding: 12px 14px; }
.hosted-admin :deep(.access-onboarding-layout #hosted-strength) { margin: 1px 0 0; font-size: 12px; line-height: 1.6; color: #718096; }
.hosted-admin :deep(.access-onboarding-layout .access-primary) { min-height: 50px; margin: 2px 0 0; border-radius: 9px; font-size: 14px; }
.hosted-admin :deep(.access-onboarding-layout .password-signin-note) { display: block; margin: -9px 0 0; text-align: center; color: #718096; font-size: 12px; }
.hosted-admin :deep(.access-onboarding-layout .access-actions) { margin-top: 24px; padding-top: 20px; justify-content: space-between; }
.hosted-admin :deep(.access-onboarding-layout .access-actions button) { min-height: 36px; padding: 7px 0; background: transparent; border: 0; font-size: 12px; color: #64748b; }
.hosted-admin :deep(.access-onboarding-layout .access-actions button:hover:not(:disabled)) { color: var(--blue-700); text-decoration: underline; }
.hosted-admin :deep(.access-onboarding-layout .access-session-note) { margin: 16px 0 0; text-align: center; font-size: 11px; line-height: 1.6; color: #8290a3; }
@media (max-width: 600px) {
  .hosted-admin :deep(.access-page.access-onboarding-layout) { padding: 16px 16px 28px; }
  .hosted-admin :deep(.access-onboarding-layout .access-content) { margin-top: 20px; padding: 24px 20px; border-radius: 16px; }
  .hosted-admin :deep(.access-onboarding-layout .access-steps ol) { gap: 10px; font-size: 11px; }
  .hosted-admin :deep(.access-onboarding-layout .access-steps li) { flex-direction: column; gap: 7px; text-align: center; white-space: normal; }
  .hosted-admin :deep(.access-onboarding-layout .access-actions button) { min-height: 44px; }
  .hosted-admin :deep(.access-onboarding-layout h1) { font-size: 25px; }
}
.hosted-admin :deep(.access-privacy-layout .access-content) { width: min(100%, 760px); margin-top: 24px; padding: 32px 40px 24px; }
.hosted-admin :deep(.access-privacy-layout .privacy-setup-description) { margin: 0; color: #64748b; font-size: 14px; line-height: 1.7; }
.hosted-admin :deep(.access-privacy-layout .privacy-document-header) { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px 16px; margin: 24px 0 12px; }
.hosted-admin :deep(.access-privacy-layout .privacy-document-header h2) { margin: 0; color: #334155; font-size: 13px; font-weight: 600; }
.hosted-admin :deep(.access-privacy-layout .privacy-document-header .access-hint) { margin: 0; font-size: 11px; color: #64748b; border: 1px solid #e2e8f0; border-radius: 6px; padding: 3px 8px; }
.hosted-admin :deep(.access-privacy-layout .access-notice) { max-height: 32dvh; min-height: 240px; padding: 24px; background: #fff; border: 1px solid #dfe6ef; border-radius: 10px; white-space: normal; scrollbar-color: #bac8d8 #fff; scrollbar-width: thin; }
.hosted-admin :deep(.access-privacy-layout .access-notice h3) { margin: 22px 0 8px; font-size: 14px; line-height: 1.5; font-weight: 600; color: #1e293b; }
.hosted-admin :deep(.access-privacy-layout .access-notice h3:first-child) { margin-top: 0; }
.hosted-admin :deep(.access-privacy-layout .access-notice p) { margin: 0 0 14px; font-size: 13px; line-height: 1.85; color: #526176; white-space: pre-line; }
.hosted-admin :deep(.access-privacy-layout .access-notice p:last-child) { margin-bottom: 0; }
.hosted-admin :deep(.access-privacy-layout form) { margin-top: 20px; gap: 16px; }
.hosted-admin :deep(.access-privacy-layout .access-checkbox) { margin: 0; align-items: center; font-weight: 400; font-size: 13px; line-height: 1.6; color: #475569; }
.hosted-admin :deep(.access-privacy-layout .access-checkbox input) { width: 18px; height: 18px; margin: 0; accent-color: var(--blue-700); }
.hosted-admin :deep(.access-privacy-layout .access-primary) { margin-top: 0; }
@media (max-width: 600px) {
  .hosted-admin :deep(.access-privacy-layout .access-content) { padding: 24px 20px; }
  .hosted-admin :deep(.access-privacy-layout .access-notice) { padding: 18px; min-height: 260px; max-height: 42dvh; }
}
.hosted-admin :deep(:is(button, a, input, select, textarea, [tabindex]):focus-visible) {
  outline: 3px solid var(--blue-700);
  outline-offset: 3px;
}
.hosted-admin :deep(::selection) { background: var(--blue-100); color: var(--text); }
/* The original Vue login supplies the shared branded half of both sign-ins. */
.hosted-admin:has(.access-login-layout) {
  /* Three base colors, with neutral/blue tints for supporting surfaces. */
  --muted: color-mix(in srgb, var(--text) 65%, var(--white));
  --control-border: color-mix(in srgb, var(--text) 45%, var(--white));
  --blue-50: color-mix(in srgb, var(--blue-700) 7%, var(--white));
  min-height: 100dvh; display: grid; align-items: center; padding: 0; background: var(--white);
}
.hosted-admin :deep(.access-login-layout) {
  width: 100%;
  min-height: 100dvh;
  margin: 0 auto;
  padding: 0;
  display: grid;
  grid-template-columns: minmax(0, .84fr) minmax(0, 1.16fr);
  grid-template-rows: auto 1fr;
  background: var(--white);
  border: 0;
  border-radius: 0;
  overflow: hidden;
}
.hosted-admin :deep(.access-login-layout .access-header) { grid-column: 1; grid-row: 1; width: 100%; justify-content: flex-start; border: 0; padding: 24px 24px 0; }
.hosted-admin :deep(.access-login-layout .access-header > span) { font-size: 12px; }
.hosted-admin :deep(.access-login-layout .access-content) { grid-column: 1; grid-row: 2; width: 100%; margin: 0; border: 0; border-radius: 0; padding: 48px 56px; }
.hosted-admin :deep(.access-login-layout .access-content h1) { text-wrap: initial; font-size: 32px; }
.hosted-admin :deep(.access-login-layout .login-right) { grid-column: 2; grid-row: 1 / span 2; min-width: 0; padding: 0; }
.hosted-admin :deep(.access-login-layout .hero-panel) { min-height: 100%; }
.hosted-admin :deep(.access-login-layout .custom-signin) {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 28px clamp(28px, 4vw, 64px) 48px;
}
.hosted-admin :deep(.admin-signin-form) { width: min(100%, 440px); margin: 0 auto; }
.hosted-admin :deep(.custom-signin .admin-signin-intro) { text-align:center; }
.hosted-admin :deep(.custom-signin .admin-signin-intro h1) { font-size: 28px; margin: 0 0 10px; }
.hosted-admin :deep(.custom-signin .admin-signin-intro p) { color: var(--muted); font-size: 14px; line-height: 1.6; margin: 0; }
.hosted-admin :deep(.custom-signin .admin-signin-form form) { display: grid; gap: 24px; margin: 32px 0 0; }
.hosted-admin :deep(.custom-signin .admin-signin-field) { display: grid; gap: 8px; }
.hosted-admin :deep(.custom-signin .admin-signin-field label) { margin: 0; color: var(--text); font-size: 14px; font-weight: 500; }
.hosted-admin :deep(.custom-signin .admin-signin-input) {
  display: flex; align-items: center; gap: 12px;
  min-height: 54px; padding: 0 14px; border: 1px solid var(--control-border);
  border-radius: var(--control-radius); background: var(--white); color: var(--muted);
}
.hosted-admin :deep(.custom-signin .admin-signin-input > svg) { flex-shrink: 0; }
.hosted-admin :deep(.custom-signin .admin-signin-input input) {
  width: 100%; min-width: 0; height: 52px; min-height: 0; padding: 0;
  border: 0; border-radius: 0; background: transparent; outline: none;
  font-size: 16px; line-height: 1.5; color: var(--text); box-shadow: none;
}
.hosted-admin :deep(.custom-signin .admin-signin-input input::placeholder) { color: var(--muted); opacity: 1; }
.hosted-admin :deep(.custom-signin .admin-signin-input:focus-within) { border-color: var(--blue-700); outline: 2px solid var(--blue-700); outline-offset: 2px; }
.hosted-admin :deep(.custom-signin .admin-signin-input input:focus-visible) { outline: none; }
.hosted-admin :deep(.custom-signin button.admin-signin-toggle) {
  display: grid; place-items: center; flex-shrink: 0;
  width: 44px; min-height: 44px; padding: 0; margin-right: -8px;
  border: 0; background: transparent; color: var(--muted);
}
.hosted-admin :deep(.custom-signin button.admin-signin-toggle:hover:not(:disabled)) { color: var(--blue-700); background: var(--blue-50); }
.hosted-admin :deep(.custom-signin button.admin-signin-submit) {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  width: 100%; min-height: 52px; margin: 4px 0 0; border: 1px solid var(--blue-700);
  background: var(--blue-700); color: var(--white); font-size: 15px; font-weight: 600;
  appearance: none; box-shadow: none;
}
.hosted-admin :deep(.custom-signin button.admin-signin-submit:hover:not(:disabled)) { background: color-mix(in srgb, var(--blue-700) 88%, var(--text)); border-color: transparent; color: var(--white); }
.hosted-admin :deep(.custom-signin .admin-signin-error) { color: #991b1b; background: #fef2f2; border-radius: 8px; padding: 12px 14px; margin: 0; font-size: 14px; }
.hosted-admin :deep(.custom-signin .admin-signin-message) { color: var(--blue-700); margin: 0; font-size: 14px; }
.hosted-admin :deep(.custom-signin .access-session-note) { width: min(100%, 440px); margin: 28px auto 0; color: var(--muted); text-align: center; font-size: 12px; line-height: 1.6; }
@media (max-width: 980px) {
  .hosted-admin :deep(.access-login-layout) { max-width: none; min-height: 100dvh; grid-template-columns: minmax(0, 1fr); grid-template-rows: auto 1fr; }
  .hosted-admin :deep(.access-login-layout .login-right) { display: none; }
  .hosted-admin :deep(.access-login-layout .custom-signin) { padding: 40px 40px 36px; }
}
@media (max-width: 760px) {
  .hosted-admin:has(.access-login-layout) { padding: 0; }
  .hosted-admin :deep(.access-page) { padding: 20px 16px; }
  .hosted-admin :deep(.access-header) { padding-bottom: 20px; }
  .hosted-admin :deep(.access-content) { padding: 24px; margin: 28px auto; }
  .hosted-admin :deep(.directory-nav button:last-child) { margin-left: 0; }
  .hosted-admin :deep(.screening-filters) { grid-template-columns: 1fr 1fr; }
  .hosted-admin :deep(.screening-filters > button) { grid-column: 1 / -1; }
  .hosted-admin :deep(.access-content :is(input, select, textarea)) { font-size: 16px; }
}
@media (max-width: 460px) {
  .hosted-admin :deep(.access-login-layout .access-header) { width: 100%; padding: 24px 24px 0; }
  .hosted-admin :deep(.access-login-layout .access-content) { padding: 32px 24px 28px; }
  .hosted-admin :deep(.access-login-layout .custom-signin) { justify-content:flex-start; padding: 40px 24px 28px; }
  .hosted-admin :deep(.access-login-layout .access-content h1) { font-size: 28px; }
  .hosted-admin :deep(.access-page) { padding: 16px 12px; }
  .hosted-admin :deep(.access-content) { padding: 24px 18px; }
  .hosted-admin :deep(:is(.directory-filters, .screening-filters)) { padding: 16px; grid-template-columns: 1fr; }
  .hosted-admin :deep(.directory-nav button) { flex: 1 1 auto; }
}
@media (max-width: 760px) {
  .hosted-admin :deep(.access-page.access-login-layout) { padding: 0; }
}
@media (max-width: 600px) {
  .hosted-admin:has(.access-login-layout) { align-items: start; padding: 0; }
}
@media (min-width: 981px) and (max-height: 760px) {
  .hosted-admin:has(.access-login-layout) { padding: 0; }
  .hosted-admin :deep(.access-login-layout) { min-height: 100dvh; }
  .hosted-admin :deep(.access-login-layout .access-header) { padding-top: 16px; }
  .hosted-admin :deep(.access-login-layout .custom-signin) { padding-top: 16px; padding-bottom: 24px; }
  .hosted-admin :deep(.custom-signin .access-session-note) { margin-top: 20px; }
}
@media (prefers-reduced-motion: reduce) {
  .hosted-admin :deep(.access-content button) { transition: none; }
}
</style>
