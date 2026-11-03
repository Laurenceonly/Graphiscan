<template>
  <div class="admin-page-skeleton" :class="{ 'skeleton-dashboard': dashboard }" role="status" :aria-label="label" aria-busy="true">
    <div class="page-skeleton-shapes" aria-hidden="true">
      <div class="skeleton-page-header"><span class="shape skeleton-title"></span><span class="shape skeleton-action"></span></div>
      <div v-if="summary" class="skeleton-summary"><div v-for="card in 4" :key="card" class="skeleton-card"><span class="shape skeleton-caption"></span><span class="shape skeleton-value"></span></div></div>
      <div v-if="filters" class="skeleton-filters"><span v-for="field in 3" :key="field" class="shape skeleton-field"></span><span class="shape skeleton-action"></span></div>
      <AdminLoadingSkeleton :dashboard="dashboard" :rows="dashboard ? 3 : 5" label="" />
    </div>
  </div>
</template>
<script setup>
import AdminLoadingSkeleton from './AdminLoadingSkeleton.vue'
defineProps({label:{type:String,default:'Loading page'},dashboard:Boolean,summary:Boolean,filters:Boolean})
</script>
<style scoped>
.admin-page-skeleton{width:100%;min-width:0;min-height:480px}
.page-skeleton-shapes{display:grid;gap:24px}
.skeleton-page-header{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:48px}
.shape{display:block;background:var(--border);border-radius:5px;animation:page-skeleton-pulse 1.4s ease-in-out infinite}
.skeleton-title{height:28px;width:180px;max-width:55%}.skeleton-action{height:44px;width:104px;flex:none}
.skeleton-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.skeleton-card{display:grid;align-content:start;gap:16px;min-height:112px;padding:20px;background:var(--white);border:1px solid var(--border);border-radius:12px;box-sizing:border-box}
.skeleton-caption{height:12px;width:75%}.skeleton-value{height:28px;width:50px}
.skeleton-filters{display:flex;align-items:center;gap:16px;padding:24px;background:var(--white);border:1px solid var(--border);border-radius:12px}
.skeleton-field{height:48px;flex:1;min-width:0}
.admin-page-skeleton :deep(.admin-loading){margin:0}.admin-page-skeleton :deep(.loading-label){display:none}
@keyframes page-skeleton-pulse{0%,100%{opacity:.5}50%{opacity:1}}
@media(prefers-reduced-motion:reduce){.shape{animation:none;opacity:.75}}
@media(max-width:1100px){.skeleton-summary{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.skeleton-summary{grid-template-columns:minmax(0,1fr)}.skeleton-filters{flex-wrap:wrap;padding:20px;gap:12px}.skeleton-field{flex-basis:100%}.skeleton-card{min-height:112px}}
</style>
