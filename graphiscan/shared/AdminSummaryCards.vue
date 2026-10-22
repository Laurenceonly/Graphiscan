<template>
  <section class="admin-summary-grid" :aria-label="label">
    <component :is="interactive ? 'button' : 'article'" v-for="item in items" :key="item.label" class="admin-summary-card" :type="interactive ? 'button' : undefined" @click="interactive && emit('select', item)">
      <div class="admin-summary-value"><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
      <component v-if="item.icon" :is="item.icon" class="admin-summary-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
    </component>
  </section>
</template>
<script setup>
defineProps({ items: { type: Array, required: true }, label: { type: String, required: true }, interactive: Boolean })
const emit = defineEmits(['select'])
</script>
<style scoped>
.admin-summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:var(--workspace-control-gap,16px); min-width:0; margin:0; }
.admin-summary-grid .admin-summary-card { position:relative; display:flex; align-items:flex-start; justify-content:space-between; gap:12px; width:100%; min-width:0; min-height:var(--workspace-metric-height,112px); margin:0; padding:var(--workspace-metric-padding,20px); border:1px solid var(--border); border-radius:12px; background:var(--white); color:var(--text); text-align:left; font:inherit; box-shadow:none; }
.admin-summary-grid button.admin-summary-card { cursor:pointer; }
.admin-summary-grid button.admin-summary-card:hover { border-color:var(--control-border); background:var(--blue-50); }
.admin-summary-grid button.admin-summary-card:focus-visible { outline:3px solid var(--blue-700); outline-offset:3px; }
.admin-summary-grid .admin-summary-value { display:grid; align-content:start; gap:12px; min-width:0; margin:0; }
.admin-summary-grid .admin-summary-value > span { margin:0; color:var(--muted); font:400 13px/20px var(--font-ui); }
.admin-summary-grid .admin-summary-value > strong { display:block; margin:0; color:var(--text); font:600 28px/32px var(--font-ui); font-variant-numeric:tabular-nums; }
.admin-summary-grid .admin-summary-icon { flex:none; margin:1px 0 0; color:var(--blue-700); }
@media(max-width:1100px) { .admin-summary-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:600px) { .admin-summary-grid { grid-template-columns:minmax(0,1fr); } }
</style>
