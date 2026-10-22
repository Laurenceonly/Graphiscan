<template>
  <button class="admin-refresh-button" :type="type" :disabled="busy || disabled" :aria-busy="busy || undefined">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </svg>
    <span>{{ busy ? 'Refreshing…' : 'Refresh' }}</span>
  </button>
</template>

<script setup>
defineProps({ busy: Boolean, disabled: Boolean, type: { type: String, default: 'button' } })
</script>
