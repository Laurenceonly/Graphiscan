<template>
  <div class="workspace-brand"><img :src="brandLogo" alt="" width="36" height="36" /><span>Graphi<span>Scan</span></span></div>
</template>
<script setup>
import brandLogo from '../assets/graphiscan-logo.png'
</script>
<style scoped>
.workspace-brand{display:flex;align-items:center;gap:9px;white-space:nowrap;font-family:var(--font-ui);font-size:19px;font-weight:650;letter-spacing:-.035em;line-height:1.55}
.workspace-brand img{display:block;width:36px;height:36px;object-fit:contain;flex:none}
.workspace-brand>span>span{color:var(--brand-blue)}
</style>
