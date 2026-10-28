<template>
  <AdminLayout class="hosted-workspace" :sign-out="signOut">
    <template #brand>
      <div class="workspace-brand"><img :src="brandLogo" alt="" width="36" height="36" /><span>Graphi<span>Scan</span></span></div>
    </template>
    <template #topbar><span class="mobile-header-brand">GraphiScan</span></template>
    <template #navigation="{ closeMenu }">
      <div v-for="group in navigation" :key="group.label" class="sidebar-section">
        <p class="sidebar-label">{{ group.label }}</p>
        <nav class="nav-menu" :aria-label="group.label">
          <button v-for="item in group.items" :key="item.key" type="button" class="nav-link" :class="{ 'router-link-active': navActive(item.key) }" :aria-current="navActive(item.key) ? 'page' : undefined" @click="navigate(item.key, closeMenu)">
            <span class="nav-icon"><component :is="item.icon" :size="17" :stroke-width="1.8" /></span>{{ item.label }}
          </button>
        </nav>
      </div>
    </template>

    <p v-if="navigationError" class="workspace-alert" role="alert">{{ navigationError }}</p>
    <p v-if="error" class="workspace-alert" role="alert">{{ error }}</p>
    <p v-if="message" role="status">{{ message }}</p>

    <div v-show="section === 'dashboard'" class="dashboard-page modern-admin-dashboard">
      <section class="dashboard-toolbar admin-page-header">
        <div><h1 ref="pageTitle" tabindex="-1">Dashboard</h1></div>
        <RefreshButton :busy="refreshing" @click="refreshDashboard" />
      </section>
      <p v-if="screening.error || directory.error" class="workspace-alert" role="alert">Some dashboard information could not be loaded. Refresh to try again.</p>
      <AdminSummaryCards :items="cards" label="Loaded record counts" interactive @select="navigate($event.target)" />
      <section v-if="!screening.rows.length" class="clean-panel dashboard-empty-panel" aria-labelledby="dashboard-empty-title" aria-live="polite">
        <div class="dashboard-empty-copy">
          <span class="dashboard-empty-icon"><FileText :size="21" aria-hidden="true" /></span>
          <h2 id="dashboard-empty-title">{{ screening.busy ? 'Loading screenings' : screening.error ? 'Screenings unavailable' : !screening.allowed ? 'No screening access' : 'No screening results yet' }}</h2>
          <p>{{ screening.busy ? 'Screening records will appear here when they finish loading.' : screening.error ? 'Refresh the dashboard to try loading records again.' : !screening.allowed ? 'Screening records require school assignment permission.' : 'When screenings are recorded, their review status and recent results will appear here.' }}</p>
        </div>
      </section>
      <div v-else class="workspace-dashboard-grid" :class="{ 'workspace-dashboard-has-activity': activity.distinctDays > 0 }">
        <div class="workspace-dashboard-primary">
          <section v-if="activity.distinctDays > 0" class="clean-panel workspace-activity" aria-labelledby="activity-title">
            <div class="clean-panel-head split-head"><div><h2 id="activity-title">Screening activity</h2><p>{{ activity.period }}</p></div></div>
            <figure class="workspace-activity-chart"><svg viewBox="0 0 600 170" role="img" :aria-label="activity.description" preserveAspectRatio="none"><defs><linearGradient id="screening-activity-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="currentColor" stop-opacity=".16" /><stop offset="100%" stop-color="currentColor" stop-opacity="0" /></linearGradient></defs><g class="workspace-chart-grid"><line v-for="y in [20,70,120]" :key="y" x1="0" :y1="y" x2="600" :y2="y" /></g><text x="0" y="13">{{ activity.maximum }}</text><text x="0" y="154">0</text><path :d="activity.area" fill="url(#screening-activity-fill)" /><polyline :points="activity.points" fill="none" stroke="currentColor" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" /><circle v-for="point in activity.coordinates" :key="point.x" :cx="point.x" :cy="point.y" r="3.5" fill="white" stroke="currentColor" stroke-width="2" /></svg><figcaption><span v-for="day in activity.days" :key="day.key">{{ day.label }}</span></figcaption></figure>
            <p class="workspace-data-note">Loaded screenings by date.</p>
          </section>
          <section class="clean-panel workspace-recent-panel">
            <div class="clean-panel-head split-head"><h2>Recent screenings</h2><button type="button" class="mini-view-link" @click="navigate('results')">View all <ArrowUpRight :size="14" /></button></div>
            <div v-if="recent.length" class="recent-screening-list">
              <div class="recent-screening-head" aria-hidden="true"><span>Student</span><span>Result</span><span>Review</span><span>Date</span></div>
              <button v-for="row in recent" :key="row.result_id" type="button" class="recent-screening-item" @click="openResult(row.result_id)">
                <strong>{{ studentName(row.student_id) }}</strong><span class="recent-classification">{{ row.classification || 'Not recorded' }}</span>
                <span class="workspace-badge" :class="statusTone(row.review?.status)">{{ row.review?.status || 'Not recorded' }}</span>
                <time :datetime="row.date_generated">{{ date(row.date_generated) }}</time>
              </button>
            </div>
            <div v-else class="clean-empty-state small"><FileText :size="24" /><h3>{{ screening.busy ? 'Loading screenings' : screening.error ? 'Screenings unavailable' : !screening.allowed ? 'No screening access' : 'No recent results' }}</h3><p>{{ screening.error ? 'Use Refresh to try again.' : 'Records available to your account will appear here.' }}</p></div>
          </section>
        </div>
        <div v-if="screening.rows.length" class="workspace-dashboard-secondary">
        <section class="clean-panel workspace-review-panel">
          <div class="clean-panel-head"><h2>Review status</h2></div>
          <div class="analytics-bar-list">
            <div v-for="item in reviewBars" :key="item.label" class="analytics-bar-item">
              <div class="analytics-bar-top"><div><strong>{{ item.label }}</strong><small>{{ item.description }}</small></div><span>{{ screening.loaded ? item.count : '—' }}</span></div>
              <div class="analytics-bar-track" aria-hidden="true"><div class="analytics-bar-fill" :class="item.tone" :style="{ width: percent(item.count, screening.rows.length) + '%' }"></div></div>
            </div>
          </div>
          <p v-if="!screening.allowed" class="workspace-scope">Screening records require school assignment permission.</p>
        </section>
        <section class="clean-panel workspace-breakdown-panel">
          <div class="clean-panel-head"><h2>Result breakdown</h2></div>
          <div class="classification-ring-wrap">
            <div class="classification-ring" :style="{ background: ringBackground }" aria-hidden="true"><div><strong>{{ screening.loaded ? screening.rows.length : '—' }}</strong><span>Results loaded</span></div></div>
            <div class="classification-legend"><div v-for="item in classifications" :key="item.label"><span class="legend-dot" :style="{ background: item.color }"></span><p>{{ item.label }}</p><strong>{{ item.count }}</strong></div></div>
          </div>
        </section>
        </div>
      </div>
    </div>

    <!-- Keep existing editors mounted: switching sections must not discard drafts or requests. -->
    <section v-show="section === 'students' || section === 'schools'" class="workspace-record-panel">
      <HostedDirectory ref="directoryRef" :client="client" :profile="profile" :sign-out="signOut" admin-presentation @access-change="refreshAccount" @navigation-block="setNavigationBlock" @snapshot="directory = $event" />
    </section>
    <section v-show="section === 'results'" class="workspace-record-panel">
      <HostedScreenings ref="screeningsRef" :client="client" :profile="profile" @access-change="refreshAccount" @snapshot="screening = $event" />
    </section>
    <section v-show="section === 'settings'" class="workspace-account">
      <header class="page-header workspace-page-header admin-page-header"><h1 ref="accountTitle" tabindex="-1">Settings</h1><RefreshButton :busy="busy" @click="refreshAccount" /></header>
      <HostedAdminSettings v-if="section === 'settings'" :change-password="changePassword" :busy="busy" />
    </section>
    <HostedAdminProgress v-if="section === 'progress'" ref="progressRef" :client="client" :profile="profile" :students="directory.records || []" @access-change="refreshAccount" @open-result="openResult" />
    <HostedAdminRecords v-if="section === 'users' || section === 'audit'" ref="recordsRef" :kind="section === 'users' ? 'accounts' : 'audit'" :client="client" :profile="profile" @access-change="refreshAccount" @navigation-block="setNavigationBlock" />
  </AdminLayout>
</template>

<script setup>
import RefreshButton from '../../../shared/RefreshButton.vue'
import AdminSummaryCards from '../../../shared/AdminSummaryCards.vue'
import { computed, nextTick, ref } from 'vue'
import { AlertTriangle, ArrowUpRight, FileText, GraduationCap, History, LayoutDashboard, School, Settings, TrendingUp, Users } from 'lucide-vue-next'
import brandLogo from '../assets/graphiscan-logo.png'
import AdminLayout from '../layouts/AdminLayout.vue'
import HostedDirectory from '../../../shared/HostedDirectory.vue'
import HostedScreenings from './HostedScreenings.vue'
import HostedAdminProgress from './HostedAdminProgress.vue'
import HostedAdminSettings from './HostedAdminSettings.vue'
import HostedAdminRecords from './HostedAdminRecords.vue'
const props = defineProps({ client: { type: Object, required: true }, profile: { type: Object, required: true }, refreshAccount: { type: Function, required: true }, signOut: { type: Function, required: true }, changePassword: { type: Function, required: true }, busy: Boolean, error: String, message: String })
const emit = defineEmits(['navigation-block'])
const section=ref('dashboard'), directoryRef=ref(null), screeningsRef=ref(null), pageTitle=ref(null), accountTitle=ref(null), recordsRef=ref(null), progressRef=ref(null), blocked=ref(false), navigationError=ref('')
const directory=ref({ students:0, schools:0, studentsLoaded:false, schoolsLoaded:false, busy:true, error:'' })
const screening=ref({ rows:[], loaded:false, busy:true, error:'', allowed:false })
const navigation=[{label:'Overview',items:[{key:'dashboard',label:'Dashboard',icon:LayoutDashboard}]},{label:'Management',items:[{key:'users',label:'Users',icon:Users},{key:'students',label:'Students',icon:GraduationCap}]},{label:'Screening',items:[{key:'results',label:'Results',icon:FileText},{key:'progress',label:'Progress',icon:TrendingUp}]},{label:'System',items:[{key:'audit',label:'Audit Logs',icon:History},{key:'settings',label:'Settings',icon:Settings}]}]
const refreshing=computed(()=>props.busy || directory.value.busy || screening.value.busy)
const cards=computed(()=>[
  {label:'Screenings loaded',value:screening.value.loaded?screening.value.rows.length:'—',icon:FileText,target:'results'},
  {label:'Students loaded',value:directory.value.studentsLoaded?directory.value.students:'—',icon:GraduationCap,target:'students'},
  {label:'Schools loaded',value:directory.value.schoolsLoaded?directory.value.schools:'—',icon:School,target:'schools'},
  {label:'Follow-ups loaded',value:screening.value.loaded?screening.value.rows.filter(r=>r.review?.follow_up_needed===true).length:'—',icon:AlertTriangle,target:'results'}
])
const activity=computed(()=>{
  const dates=screening.value.rows.filter(row=>row.date_generated).map(row=>new Date(row.date_generated)).filter(date=>!Number.isNaN(date.getTime()))
  const end=dates.length?new Date(Math.max(...dates.map(date=>date.getTime()))):new Date()
  end.setHours(0,0,0,0)
  const key=date=>`${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
  const days=Array.from({length:7},(_,index)=>{const date=new Date(end);date.setDate(end.getDate()-6+index);return {key:key(date),label:date.toLocaleDateString(undefined,{month:'short',day:'numeric'}),date,count:0}})
  for(const date of dates){const day=days.find(day=>day.key===key(date));if(day)day.count++}
  const maximum=Math.max(1,...days.map(day=>day.count))
  const coordinates=days.map((day,index)=>({x:12+index*96,y:134-day.count/maximum*106}))
  return {days,coordinates,maximum,distinctDays:days.filter(day=>day.count>0).length,points:coordinates.map(point=>`${point.x},${point.y}`).join(' '),area:`M 12 150 L ${coordinates.map(point=>`${point.x} ${point.y}`).join(' L ')} L 588 150 Z`,period:days[0].date.toLocaleDateString(undefined,{month:'short',day:'numeric'})+' – '+end.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'}),description:'Screenings in loaded records: '+days.map(day=>`${day.label}: ${day.count}`).join(', ')}
})
const reviewBars=computed(()=>[
  {label:'Pending',description:'Waiting for expert review',tone:'pending'},
  {label:'Validated',description:'Reviewed records',tone:'validated'},
  {label:'Flagged',description:'Needs attention',tone:'flagged'}
].map(item=>({...item,count:screening.value.rows.filter(r=>r.review?.status===item.label).length})))
// Preserve exact API classifications, including unfamiliar historical labels.
const classifications=computed(()=>{
  const groups=new Map()
  for(const row of screening.value.rows){const label=row.classification || 'Not recorded';groups.set(label,(groups.get(label)||0)+1)}
  return [...groups].map(([label,count])=>({label,count,color:label.toLowerCase()==='normal'?'var(--success)':/high potential|potential dysgraphia/i.test(label)?'var(--danger)':'var(--blue-700)'}))
})
const ringBackground=computed(()=>{
  if(!screening.value.rows.length)return 'var(--border)'
  let end=0
  return 'conic-gradient('+classifications.value.map(item=>{const start=end;end+=percent(item.count,screening.value.rows.length);return `${item.color} ${start}% ${end}%`}).join(',')+')'
})
const recent=computed(()=>[...screening.value.rows].sort((a,b)=>new Date(b.date_generated)-new Date(a.date_generated)).slice(0,5))
function percent(value,total){return total?value/total*100:0}
function statusTone(value){return value==='Validated'?'success':value==='Flagged'?'danger':value==='Pending'?'warning':''}
function date(value){const parsed=new Date(value);return Number.isNaN(parsed.getTime())?'Date unavailable':parsed.toLocaleDateString()}
function studentName(id){return directory.value.records?.find(student=>String(student.student_id)===String(id))?.full_name || 'Student '+id}
function setNavigationBlock(value){blocked.value=value;emit('navigation-block',value)}
function navActive(key){return section.value===key || (key==='students' && section.value==='schools')}
async function navigate(target,closeMenu){
  if(blocked.value && target!==section.value){navigationError.value='Confirm the pending submission before leaving this section. You can still sign out.';return false}
  navigationError.value='';section.value=target
  if(target==='students'||target==='schools')directoryRef.value?.showTab(target)
  closeMenu?.();await nextTick()
  const heading=target==='dashboard'?pageTitle.value:target==='settings'?accountTitle.value:target==='results'?screeningsRef.value?.$el.querySelector('h2'):target==='progress'?progressRef.value?.$el.querySelector('h1'):target==='users'||target==='audit'?recordsRef.value?.$el.querySelector('h1'):directoryRef.value?.$el.querySelector('h2')
  if(heading){heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true})}
  window.scrollTo({top:0,behavior:'instant'});return true
}
async function openResult(id){if(await navigate('results'))await screeningsRef.value?.openResult(id)}
async function refreshDashboard(){await Promise.all([directoryRef.value?.refresh(),screeningsRef.value?.refresh()])}
</script>

<style scoped>
.hosted-workspace { --sidebar-width:240px; --topbar-height:72px; --admin-page-title:28px; --admin-section-title:16px; --workspace-page-inset:32px; --workspace-section-gap:24px; --workspace-card-padding:24px; --workspace-control-gap:16px; --workspace-metric-padding:20px; --workspace-metric-height:112px; background:var(--page-bg); font:400 14px/1.55 var(--font-ui); color:var(--text); }
/* Short sections share the same full-height canvas as populated pages. */
.hosted-workspace :deep(.main-panel) { display:flex; flex-direction:column; min-height:100vh; min-height:100dvh; background:var(--page-bg); }
.hosted-workspace :deep(.topbar) { flex-shrink:0; }
.hosted-workspace :deep(.content) { flex:1; background:var(--page-bg); }
.hosted-workspace :deep(.sidebar) { padding:22px 16px; gap:22px; background:var(--sidebar-bg); border-right:1px solid var(--border); box-shadow:none; }
.hosted-workspace :deep(.brand) { min-height:44px; padding:0 6px 20px; margin-bottom:2px; border:0; }
.workspace-brand { display:flex; align-items:center; gap:9px; white-space:nowrap; font-size:19px; font-weight:650; letter-spacing:-.035em; }
.workspace-brand img { width:36px; height:36px; object-fit:contain; }
.workspace-brand > span > span { color:var(--brand-blue); }
.hosted-workspace :deep(.sidebar-label) { padding:0 12px; color:var(--muted); text-transform:none; letter-spacing:0; font-size:11px; font-weight:500; }
.hosted-workspace :deep(.nav-menu) { gap:4px; }
.nav-link { position:relative; width:100%; min-height:44px; padding:10px 12px; border:0; border-radius:8px; color:var(--text-soft); background:transparent; text-align:left; cursor:pointer; font:500 14px/1.5 var(--font-ui); }
.hosted-workspace :deep(.nav-icon) { color:inherit; width:20px; height:20px; }
.nav-link:focus-visible { outline-color:var(--blue-700); }
.nav-link:hover { background:var(--border-soft); color:var(--text); }
.nav-link.router-link-active { background:var(--blue-50); color:var(--blue-700); font-weight:600; }
.nav-link.router-link-active::before { content:''; position:absolute; left:0; top:11px; bottom:11px; width:3px; background:var(--blue-700); border-radius:3px; }
.hosted-workspace :deep(.nav-link.router-link-active .nav-icon) { color:var(--blue-700); }
.hosted-workspace :deep(.logout-btn) { position:relative; margin-top:auto; justify-content:center; padding:10px 38px; border:0; background:#fff1f2; }
.hosted-workspace :deep(.logout-btn > svg) { position:absolute; left:14px; }
.hosted-workspace :deep(.logout-btn:hover) { background:var(--danger); color:white; }
.hosted-workspace :deep(.sidebar-close-btn) { color:var(--text); background:var(--page-bg); }
.hosted-workspace :deep(.topbar) { display:flex; min-height:72px; height:72px; padding:0 32px; justify-content:flex-start; background:var(--white); border-bottom:1px solid var(--border); }
.hosted-workspace :deep(.content) { padding:28px var(--workspace-page-inset) 36px; max-width:1480px; }
@media(min-width:1101px) { .hosted-workspace :deep(.topbar) { display:none; } }
.modern-admin-dashboard { gap:var(--workspace-section-gap); }
.dashboard-toolbar { align-items:center; gap:20px; min-height:44px; padding:0; }
.dashboard-toolbar p { margin:8px 0 0; font-size:14px; }
.dashboard-toolbar .workspace-scope { display:block; margin-top:10px; }
.workspace-scope { margin:0; color:var(--muted); font-size:12px; }
.workspace-alert { padding:14px 16px; color:var(--danger-text); background:var(--white); border:1px solid var(--control-border); border-radius:8px; }
.workspace-dashboard-grid { display:grid; grid-template-columns:minmax(0,1.7fr) minmax(285px,1fr); gap:var(--workspace-section-gap); align-items:start; }
.workspace-dashboard-primary,.workspace-dashboard-secondary { display:grid; gap:var(--workspace-section-gap); min-width:0; }
.clean-panel { padding:var(--workspace-card-padding); border:1px solid var(--border); border-radius:14px; box-shadow:0 2px 3px rgb(17 24 39 / .015); }
.dashboard-empty-panel { display:grid; place-items:center; min-height:360px; text-align:center; }
.dashboard-empty-copy { max-width:560px; }
.dashboard-empty-icon { display:grid; width:42px; height:42px; place-items:center; margin-bottom:18px; border-radius:10px; color:var(--blue-700); background:var(--blue-50); }
.dashboard-empty-copy h2 { margin:0; font-size:20px; line-height:1.35; font-weight:600; }
.dashboard-empty-copy p { max-width:460px; margin:12px auto 0; color:var(--muted); font-size:14px; }
.clean-panel-head { align-items:center; margin-bottom:var(--workspace-section-gap); flex-wrap:wrap; }
.clean-panel-head h2 { margin:0; font-size:var(--admin-section-title); line-height:1.4; font-weight:600; }
.clean-panel-head p { margin:6px 0 0; color:var(--muted); font-size:12px; }
.mini-view-link { display:inline-flex; align-items:center; justify-content:center; gap:5px; min-height:44px; width:auto; border:0; border-radius:6px; padding:8px 0 8px 8px; background:transparent; color:var(--blue-700); font:500 13px/1.5 var(--font-ui); cursor:pointer; }
.workspace-activity-chart { margin:0; color:var(--blue-700); }
.workspace-activity-chart svg { display:block; width:100%; height:150px; overflow:visible; }
.workspace-activity-chart svg text { fill:var(--muted);font:11px var(--font-ui); }
.workspace-chart-grid line { stroke:var(--border); stroke-dasharray:4 6; stroke-width:1; }
.workspace-activity-chart figcaption { display:flex; justify-content:space-between; gap:4px; color:var(--muted); font-size:10px; }
.workspace-data-note { margin:18px 0 0; padding-top:13px; border-top:1px solid var(--border-soft); color:var(--muted); font-size:10px; }
.analytics-bar-list { gap:18px; }
.analytics-bar-top strong { font-size:14px; }
.analytics-bar-top small { font-size:12px; }
.analytics-bar-track { height:6px; background:var(--border-soft); }
.analytics-bar-fill.pending { background:var(--warning); }
.analytics-bar-fill.validated { background:var(--success); }
.analytics-bar-fill.flagged { background:var(--danger); }
.classification-ring-wrap { grid-template-columns:1fr; gap:18px; justify-items:center; }
.classification-ring { width:156px; height:auto; aspect-ratio:1; }
.classification-ring strong { font-size:28px; }
.classification-legend { width:100%; }
.classification-legend div { padding:10px 0; background:transparent; border:0; border-bottom:1px solid var(--border-soft); border-radius:0; }
.classification-legend div:last-child { border-bottom:0; padding-bottom:0; }
.classification-legend :is(p,strong) { font-size:13px; }
.classification-legend p { overflow-wrap:anywhere; }
.recent-screening-list { display:block; gap:0; border:1px solid var(--border); border-radius:10px; overflow:hidden; }
.recent-screening-head,.recent-screening-item { display:grid; grid-template-columns:minmax(70px,.9fr) minmax(80px,1.2fr) minmax(70px,.8fr) minmax(75px,.8fr); align-items:center; gap:10px; }
.recent-screening-head { padding:12px 16px; color:var(--muted); background:var(--page-bg); font-size:12px; font-weight:500; }
.recent-screening-item { width:100%; padding:16px; border:0; border-top:1px solid var(--border); border-radius:0; background:var(--white); text-align:left; cursor:pointer; font-family:inherit; overflow-wrap:anywhere; }
.recent-screening-item:hover { background:var(--blue-50); }
.recent-screening-item strong { font-size:14px; font-weight:500; }
.recent-screening-item .recent-classification,.recent-screening-item time { font-size:13px; color:var(--muted); }
.recent-screening-item .workspace-badge { justify-self:start; }
.workspace-badge { padding:4px 7px; background:var(--blue-50); color:var(--blue-700); border-radius:5px; font-size:12px; }
.workspace-badge.success { background:#ecfdf3; color:var(--success-text); }
.workspace-badge.warning { background:#fffbeb; color:#92400e; }
.workspace-badge.danger { background:#fff1f2; color:var(--danger-text); }
.workspace-record-panel { padding:0; background:transparent; border:0; border-radius:0; min-width:0; }
.workspace-record-panel :deep(:is(.directory,.hosted-screenings)) { margin:0; padding:0; border-top:0; color:var(--text); }
.workspace-record-panel :deep(h2) { margin:0 0 24px; font-size:28px; font-weight:600; }
.workspace-record-panel :deep(:is(.directory-page-description,.screening-page-description)) { margin:-12px 0 24px; color:var(--muted); font-size:14px; }
.workspace-record-panel :deep(.table-wrapper) { margin:24px 0; border-radius:12px; border:1px solid var(--border); background:var(--white); }
.workspace-record-panel :deep(table) { min-width:760px; width:100%; }
.workspace-record-panel :deep(.hosted-results-table table) { min-width:930px; table-layout:fixed; }
.workspace-record-panel :deep(.hosted-results-table :is(th,td)) { white-space:normal; overflow-wrap:anywhere; }
.workspace-record-panel :deep(.hosted-schools-table table) { min-width:0; }
.workspace-record-panel :deep(:is(th,td)) { padding:16px; }
.workspace-record-panel :deep(th) { font-size:12px; font-weight:600; background:var(--page-bg); }
.workspace-record-panel :deep(td) { font-size:14px; }
.workspace-record-panel :deep(.directory-toolbar) { padding:0; align-items:center; }
.workspace-record-panel :deep(.user-summary-grid) { margin:0 0 var(--workspace-section-gap); grid-template-columns:repeat(4,minmax(0,1fr)); gap:var(--workspace-control-gap); }
.workspace-record-panel :deep(.user-summary-card) { padding:var(--workspace-metric-padding); min-height:var(--workspace-metric-height); border-radius:14px; }
.workspace-record-panel :deep(.user-summary-card span) { font-size:13px; color:var(--muted); }
.workspace-record-panel :deep(.user-summary-card strong) { font-size:28px; font-weight:600; }
.workspace-record-panel :deep(.directory-toolbar > p) { margin:0; color:var(--muted); font-size:13px; }
.workspace-record-panel :deep(.directory-toolbar > button),
.workspace-record-panel :deep(.directory-actions button[type=submit]),
.workspace-record-panel :deep(.assignment-form button[type=submit]) { background:var(--blue-700); color:var(--white); border-color:var(--blue-700); font-weight:600; }
.workspace-record-panel :deep(.directory-toolbar > button:hover:not(:disabled)),
.workspace-record-panel :deep(.directory-actions button[type=submit]:hover:not(:disabled)),
.workspace-record-panel :deep(.assignment-form button[type=submit]:hover:not(:disabled)) { background:var(--blue-hover); color:var(--white); }
.workspace-record-panel :deep(dialog.hosted-directory-modal) { position:fixed; inset:0; width:min(600px,calc(100vw - 32px)); max-height:calc(100dvh - 48px); overflow:auto; margin:auto; padding:28px; border:1px solid var(--border); border-radius:14px; color:var(--text); background:var(--white); box-shadow:var(--shadow-md); }
.workspace-record-panel :deep(dialog.hosted-directory-modal::backdrop) { background:rgb(17 24 39 / .48); }
.workspace-record-panel :deep(dialog.hosted-directory-modal) { overscroll-behavior:contain; }
.workspace-record-panel :deep(dialog.hosted-directory-modal h2) { font-size:24px; margin:0 0 24px; }
.workspace-record-panel :deep(.directory-editor fieldset) { border:0; padding:0; margin:0; display:grid; gap:16px; }
.workspace-record-panel :deep(.directory-editor label) { margin:0; font-size:14px; font-weight:500; }
.workspace-record-panel :deep(.directory-signout) { background:#fff1f2; color:var(--danger-text); border-color:#fecdd3; }
.workspace-record-panel :deep(.directory-actions) { padding-top:20px; border-top:1px solid var(--border); justify-content:flex-end; }
.workspace-record-panel :deep(.screening-detail) { padding:24px; background:var(--page-bg); border:1px solid var(--border); border-radius:12px; margin-top:24px; }
.workspace-record-panel :deep(.assignment-form) { padding:24px; border:1px solid var(--border); border-radius:12px; background:var(--white); }
.workspace-record-panel :deep(.assignment-form h4) { font-size:18px; font-weight:600; }
.workspace-record-panel :deep(button) { color:var(--blue-700); border-color:var(--control-border); background:var(--white); font-size:14px; }
.workspace-record-panel :deep(button:hover:not(:disabled)) { background:var(--blue-50); }
.workspace-record-panel :deep(button[aria-pressed=true]) { background:var(--blue-700); color:var(--white); }
.workspace-record-panel :deep(:is(button,input,select,[tabindex]):focus-visible) { outline:3px solid var(--blue-700); outline-offset:3px; }
.workspace-record-panel :deep(:is(input,select)) { border-color:var(--control-border); color:var(--text); font:400 16px/1.5 var(--font-ui); }
.workspace-record-panel :deep(.directory-nav) { margin-bottom:24px; }
.workspace-record-panel :deep(:is(.directory-filters,.screening-filters)) { padding:20px; background:var(--white); border:1px solid var(--border); border-radius:12px; }
.workspace-record-panel :deep(:is(.directory-list,.screening-list) span) { color:var(--muted); }
.workspace-account { display:grid;gap:var(--workspace-section-gap); }
.workspace-page-header { margin:0; }
.workspace-account :deep(.hosted-security) { margin:0;width:100%;max-width:680px; }
.hosted-workspace :deep(.user-summary-card) { min-height:var(--workspace-metric-height); padding:var(--workspace-metric-padding); border:1px solid var(--border); border-radius:14px; box-shadow:0 2px 3px rgb(17 24 39 / .015); }
.hosted-workspace :deep(.user-summary-grid) { gap:var(--workspace-control-gap); }
.hosted-workspace :deep(:is(.hosted-admin-records,.hosted-progress)) { gap:var(--workspace-section-gap); }
.hosted-workspace :deep(:is(.hosted-record-panel,.compact-panel,.hosted-security)) { padding:var(--workspace-card-padding); }
.hosted-workspace :deep(.hosted-security) { margin:0; }
.hosted-workspace :deep(.compact-panel h2) { margin-bottom:var(--workspace-section-gap); }

/* One page rhythm for every hosted section; dialogs keep their own layout. */
.hosted-workspace :deep(:is(.modern-admin-dashboard,.hosted-admin-records,.hosted-progress,.workspace-account,.directory,.hosted-screenings)) { display:flex; flex-direction:column; gap:var(--workspace-section-gap); min-width:0; margin:0; }
.hosted-workspace :deep(.content :is(.directory,.hosted-screenings) > :not(dialog):not(.directory-editor)) { margin-block:0; }
.hosted-workspace :deep(.content .admin-page-header) { display:grid; grid-template-columns:minmax(0,1fr) auto; grid-auto-rows:minmax(48px,auto); align-items:center; gap:16px; flex:none; min-height:48px; margin:0; padding:0; }
.hosted-workspace :deep(.content .admin-page-header :is(h1,h2)) { display:block; min-height:0; margin:0; padding:0; font:600 var(--admin-page-title)/1.25 var(--font-ui); letter-spacing:-.025em; }
.hosted-workspace :deep(.admin-page-header > div) { min-width:0; }
.hosted-workspace :deep(.admin-page-header .account-page-actions) { width:auto; flex-wrap:nowrap; }
.hosted-workspace :deep(.admin-page-header .account-page-actions > button) { width:auto; flex:none; }
.hosted-workspace :deep(.admin-page-header :is(.primary-action-btn,.soft-action-btn)) { min-height:48px; }
.hosted-workspace :deep(.hosted-security) { max-width:none; border-radius:14px; }
.hosted-workspace :deep(.account-editor-form select option) { color:var(--text); background:var(--white); font:400 14px/1.5 var(--font-ui); }
.hosted-workspace :deep(.hosted-security form) { gap:var(--workspace-control-gap); }
.hosted-workspace :deep(.user-summary-card span) { font-size:13px; }
.hosted-workspace :deep(.user-summary-card strong) { font-size:28px; }
.hosted-workspace :deep(.hosted-record-panel) { border-radius:14px; }
.hosted-workspace :deep(:is(.hosted-security h2,.compact-panel h2,.clean-panel h2)) { font:600 var(--admin-section-title)/1.4 var(--font-ui); }
.hosted-workspace :deep(.hosted-record-filters) { margin-top:0;margin-bottom:0;padding:0;background:transparent; }
.hosted-workspace :deep(:is(.directory-filters,.screening-filters,.hosted-record-filters,.history-toolbar) label) { font:500 14px/1.5 var(--font-ui); }
.hosted-workspace :deep(.hosted-record-table) { margin-bottom:0; }
.hosted-workspace :deep(.hosted-load-more) { margin-top:20px; }
.hosted-workspace :deep(:is(.soft-action-btn,.primary-action-btn)) { min-height:44px;border-radius:8px;padding:10px 14px;font:500 14px/1.5 var(--font-ui); }
.hosted-workspace :deep(:is(.screening-filters,.directory-filters,.hosted-record-filters) button) { min-height:48px; }
.hosted-workspace :deep(.history-toolbar .primary-action-btn) { min-height:48px; }
.hosted-workspace :deep(.hosted-page-header>button) { margin:0; }
.hosted-workspace :deep(.small-action-btn) { min-height:36px;padding:7px 12px;border:1px solid var(--control-border);border-radius:8px;background:white;color:var(--blue-700);font:500 13px/1.5 var(--font-ui);box-shadow:none; }
.hosted-workspace .workspace-record-panel :deep(:is(.directory-filters,.screening-filters)) { background:white;border:1px solid var(--border);border-radius:14px; }
.hosted-workspace :deep(.table-wrapper th) { font:500 12px/1.5 var(--font-ui);text-transform:none;letter-spacing:0;color:var(--muted);background:var(--page-bg); }
.hosted-workspace :deep(.page-header p) { color:var(--muted); font-size:14px; }
.hosted-workspace :deep(.hosted-record-table th) { text-transform:none; letter-spacing:0; }
:is(button,a):focus-visible { outline:3px solid var(--blue-700); outline-offset:3px; }
@media(max-width:1250px) and (min-width:1101px){.workspace-dashboard-grid{grid-template-columns:minmax(0,1.4fr) minmax(270px,1fr);gap:24px}.hosted-workspace :deep(.content){padding:24px}.dashboard-highlight-card{padding:20px}}
@media(min-width:901px){.hosted-workspace :deep(.hosted-record-filters.audit-filters){grid-template-columns:minmax(180px,1fr) minmax(140px,200px) auto}}
@media(min-width:851px){.workspace-dashboard-has-activity{grid-template-areas:'activity review' 'recent breakdown';align-items:stretch}.workspace-dashboard-has-activity>.workspace-dashboard-primary,.workspace-dashboard-has-activity>.workspace-dashboard-secondary{display:contents}.workspace-dashboard-has-activity .workspace-activity{grid-area:activity}.workspace-dashboard-has-activity .workspace-review-panel{grid-area:review;display:flex;flex-direction:column}.workspace-dashboard-has-activity .workspace-review-panel .analytics-bar-list{flex:1}.workspace-dashboard-has-activity .workspace-recent-panel{grid-area:recent;display:flex;flex-direction:column}.workspace-dashboard-has-activity .recent-screening-list{display:flex;flex-direction:column;flex:1}.workspace-dashboard-has-activity .recent-screening-item{flex:1}.workspace-dashboard-has-activity .workspace-breakdown-panel{grid-area:breakdown}}
@media(max-width:1100px){.hosted-workspace :deep(.sidebar){width:min(280px,calc(100vw - 48px));height:100dvh}.hosted-workspace :deep(.main-panel){width:100%;margin-left:0}}
@media(max-width:850px){.workspace-dashboard-grid{grid-template-columns:1fr;gap:22px}.workspace-dashboard-secondary{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start}.recent-screening-head,.recent-screening-item{grid-template-columns:1fr 1.3fr .8fr .8fr}}
@media(max-width:760px){.clean-panel{padding:24px}.dashboard-empty-panel{min-height:300px}.clean-panel-head{flex-direction:row;align-items:center;text-align:left;gap:10px}.clean-panel-head .mini-view-link{width:auto;flex:none}.recent-screening-head{display:none}.recent-screening-item{grid-template-columns:1fr auto;gap:8px 12px;padding:16px 14px}.recent-screening-item .recent-classification{grid-column:1}.recent-screening-item .workspace-badge{grid-column:2;grid-row:1}.recent-screening-item time{grid-column:2;grid-row:2}.workspace-record-panel :deep(.directory-filters){grid-template-columns:1fr}.workspace-record-panel :deep(:is(.screening-detail,.assignment-form)){padding:16px}}
@media(max-width:700px){.hosted-workspace :deep(.content){padding:24px 16px 32px}.hosted-workspace :deep(.topbar){height:64px;min-height:64px;padding:0 16px;gap:12px}.workspace-account-name,.workspace-account-menu>svg{display:none}.workspace-account-menu{min-width:44px;min-height:44px;padding:0;justify-content:center}.workspace-dashboard-secondary{grid-template-columns:1fr}.dashboard-toolbar{gap:16px;flex-direction:row}.dashboard-highlight-card{min-height:124px;padding:16px;display:grid;grid-template-columns:1fr auto;gap:8px 6px}.dashboard-highlight-card .workspace-metric{padding-right:0}.dashboard-highlight-card .workspace-metric>span{min-height:40px}.dashboard-highlight-card .highlight-icon{position:static;width:20px;height:20px}.dashboard-highlight-card strong{margin-top:12px}.workspace-activity-chart figcaption{font-size:9px}.modern-admin-dashboard{gap:18px}.hosted-workspace :deep(.user-summary-card){padding:16px}.hosted-workspace :deep(.small-action-btn){min-height:44px}}
@media(max-width:700px){.workspace-record-panel :deep(table){min-width:0}.workspace-record-panel :deep(.hosted-results-table table){min-width:0}.workspace-record-panel :deep(td){padding:10px 0}.workspace-record-panel :deep(dialog.hosted-directory-modal){padding:20px}}
@media(max-width:980px){.workspace-record-panel :deep(.user-summary-grid){grid-template-columns:repeat(2,minmax(0,1fr))}}

/* One spacing rhythm across every hosted admin page. */
.hosted-workspace :deep(.content) { padding:28px var(--workspace-page-inset) 36px; }
.hosted-workspace :deep(:is(.modern-admin-dashboard,.hosted-admin-records,.hosted-progress,.workspace-account)) { gap:var(--workspace-section-gap); }
.hosted-workspace :deep(.workspace-dashboard-grid) { gap:var(--workspace-section-gap); }
.hosted-workspace :deep(:is(.workspace-dashboard-primary,.workspace-dashboard-secondary)) { gap:var(--workspace-section-gap); }
.hosted-workspace :deep(.dashboard-highlight-grid) { gap:var(--workspace-control-gap); }
.hosted-workspace :deep(.dashboard-highlight-card) { min-height:var(--workspace-metric-height); padding:var(--workspace-metric-padding); }
.hosted-workspace :deep(:is(.clean-panel,.compact-panel,.hosted-record-panel,.hosted-security)) { padding:var(--workspace-card-padding); }
.hosted-workspace :deep(.clean-panel-head) { margin-bottom:var(--workspace-section-gap); }
.hosted-workspace :deep(:is(.directory h2,.hosted-screenings h2)) { margin:0 0 var(--workspace-section-gap); }
.hosted-workspace :deep(.directory-nav) { margin:0 0 var(--workspace-section-gap); }
.hosted-workspace :deep(.directory-toolbar) { margin:var(--workspace-section-gap) 0; }
.hosted-workspace :deep(:is(.directory-filters,.screening-filters)) { gap:var(--workspace-control-gap); margin:0; padding:var(--workspace-card-padding); }
.hosted-workspace :deep(.table-wrapper) { margin:var(--workspace-section-gap) 0; }
.hosted-workspace :deep(.hosted-record-table) { margin:var(--workspace-section-gap) 0 0; }
.hosted-workspace :deep(.user-summary-grid) { gap:var(--workspace-control-gap); }
.hosted-workspace :deep(.user-summary-card) { min-height:var(--workspace-metric-height); padding:var(--workspace-metric-padding); border-radius:14px; }
.hosted-workspace :deep(:is(.hosted-record-stats,.history-summary) .user-summary-card) { min-height:var(--workspace-metric-height); padding:var(--workspace-metric-padding); border-radius:14px; }
.hosted-workspace :deep(.history-hint) { margin:var(--workspace-section-gap) 0; }
.hosted-workspace :deep(.hosted-security) { margin:0; }
.hosted-workspace :deep(.hosted-security form) { gap:var(--workspace-control-gap); }
.hosted-workspace :deep(.compact-panel h2) { margin-bottom:var(--workspace-section-gap); }

@media (min-width:701px) and (max-width:1250px) { .hosted-workspace { --workspace-page-inset:24px; } }
@media (max-width:700px) {
  .hosted-workspace { --workspace-page-inset:16px; --workspace-section-gap:20px; --workspace-card-padding:20px; --workspace-control-gap:12px; --workspace-metric-padding:16px; --workspace-metric-height:104px; }
  .hosted-workspace :deep(.content) { padding:24px var(--workspace-page-inset) 32px; }
  .hosted-workspace :deep(.dashboard-empty-panel) { min-height:300px; }
  .hosted-workspace :deep(.recent-screening-item) { padding:16px; }
  .hosted-workspace :deep(.hosted-record-panel) { padding:var(--workspace-card-padding); }
  .hosted-workspace :deep(.directory-filters) { grid-template-columns:1fr; }
}
@media (max-width:380px) {
  .hosted-workspace :deep(.content .admin-page-header:has(.account-page-actions)) { grid-template-columns:minmax(0,1fr); }
  .hosted-workspace :deep(.content .admin-page-header .account-page-actions) { justify-content:flex-start; }
}
</style>
