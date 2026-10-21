<template>
  <div class="login-right">
    <div class="hero-panel login-product-panel">
      <div class="hero-content">
        <h2>Handwriting screening and progress</h2>
        <p>Manage student records, review screenings, and coordinate expert validation.</p>
      </div>
      <div class="login-product-preview" aria-hidden="true">
        <div class="login-laptop-screen"><span class="login-laptop-camera"></span><img :src="workspacePreview" alt="" width="1440" height="1000" /></div>
        <div class="login-laptop-base"><span></span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import workspacePreview from '../assets/admin-workspace-preview.png'
</script>

<style scoped>
.hero-panel.login-product-panel {
  padding: 48px 40px;
  align-items: flex-start;
  justify-content: flex-start;
  gap:32px;
  overflow:hidden;
  background: var(--blue-700);
  font-family: var(--font-ui);
  border-radius: 0;
}
.login-product-panel .hero-content {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 0;
  text-align: left;
}
.login-product-panel .hero-content h2 {
  max-width: none;
  margin: 0 0 16px;
  font-size: 28px;
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: -.025em;
  white-space:nowrap;
}
.login-product-panel .hero-content p {
  max-width: 400px;
  margin:0;
  font-size: 14px;
  line-height: 1.6;
  text-wrap:balance;
  color: var(--white);
  opacity: .88;
}
.login-product-preview {
  position:relative;
  width:min(100%,calc((100dvh - 340px) * 1.44));
  max-width:960px;
  margin:auto;
  align-self:center;
  pointer-events: none;
}
.login-laptop-screen { position:relative; padding:9px 7px 8px; border:1px solid #374151; border-radius:12px 12px 3px 3px; background:var(--text); box-shadow:0 14px 32px rgb(17 24 39 / .14); }
.login-laptop-camera { position:absolute; width:3px; height:3px; top:3px; left:calc(50% - 1.5px); border-radius:50%; background:#64748b; }
.login-product-preview img { display:block; width:100%; height:auto; border-radius:3px; }
.login-laptop-base { position:relative; height:14px; width:calc(100% + 24px); margin-left:-12px; background:#dce2e8; border:1px solid #bac4ce; border-radius:2px 2px 12px 12px; box-shadow:0 12px 20px rgb(17 24 39 / .14); }
.login-laptop-base span { position:absolute; top:-1px; left:40%; width:20%; height:4px; background:#a7b3c0; border-radius:0 0 5px 5px; }
@media (max-width: 1150px) {
  .hero-panel.login-product-panel { padding: 36px 28px; }
  .login-product-panel .hero-content h2 { font-size: 24px; }
  .login-product-preview { width:min(100%,calc((100dvh - 340px) * 1.44)); }
}
@media (min-width: 981px) and (max-height: 760px) {
  .hero-panel.login-product-panel { padding-top: 32px; }
  .hero-panel.login-product-panel { gap:24px; }
}
</style>
