<template>
  <div class="admin-loading" :class="{ 'admin-loading-dashboard': dashboard }" role="status" aria-live="polite" aria-busy="true">
    <span class="loading-label">{{ label }}</span>
    <div class="loading-shapes" aria-hidden="true">
      <div v-if="dashboard" class="loading-chart"><span class="loading-bar loading-heading"></span><span class="loading-chart-area"></span></div>
      <div class="loading-rows">
        <div v-for="row in rows" :key="row" class="loading-row">
          <span class="loading-avatar"></span><span class="loading-copy"><span class="loading-bar"></span><span class="loading-bar loading-short"></span></span><span class="loading-bar loading-cell"></span><span class="loading-bar loading-cell"></span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
defineProps({ label: { type: String, default: 'Loading records…' }, rows: { type: Number, default: 5 }, dashboard: Boolean })
</script>
<style scoped>
.admin-loading{margin:24px 0;min-width:0;color:var(--muted);font:400 13px/1.5 var(--font-ui)}
.loading-label{display:block;margin-bottom:12px}
.loading-shapes{border:1px solid var(--border);border-radius:12px;background:var(--white);overflow:hidden}
.loading-row{display:flex;align-items:center;gap:20px;padding:22px 20px;min-height:80px;box-sizing:border-box;border-bottom:1px solid var(--border-soft)}
.loading-row:last-child{border:0}
.loading-bar,.loading-avatar,.loading-chart-area{display:block;background:var(--border);animation:admin-loading-pulse 1.4s ease-in-out infinite;border-radius:5px}
.loading-avatar{width:36px;height:36px;flex:none;border-radius:50%}
.loading-copy{display:grid;gap:10px;flex:2;min-width:0}
.loading-bar{height:13px;width:80%}.loading-short{width:48%;height:10px}.loading-cell{flex:1;max-width:160px}
.loading-chart{display:grid;gap:24px;padding:24px;border-bottom:1px solid var(--border-soft)}
.loading-heading{width:150px;height:18px}.loading-chart-area{height:150px;opacity:.5}
@keyframes admin-loading-pulse{0%,100%{opacity:.5}50%{opacity:1}}
@media(prefers-reduced-motion:reduce){.loading-bar,.loading-avatar,.loading-chart-area{animation:none;opacity:.75}}
@media(max-width:600px){.loading-row{padding:20px 16px;gap:12px}.loading-cell{display:none}}
</style>
