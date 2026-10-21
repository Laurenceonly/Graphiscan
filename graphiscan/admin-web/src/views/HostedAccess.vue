<template>
  <HostedAccess :allowed-roles="['admin','researcher']" :api-origin="origin">
    <template #records="{ client, profile, refreshAccount }">
      <HostedScreenings :client="client" :profile="profile" @access-change="refreshAccount" />
    </template>
  </HostedAccess>
</template>
<script setup>
import HostedAccess from '../../../shared/HostedAccess.vue'
import HostedScreenings from '../components/HostedScreenings.vue'
const origin=(import.meta.env.VITE_HOSTED_API_ORIGIN || import.meta.env.VITE_API_ORIGIN || 'http://localhost:5000').replace(/\/$/,'')
</script>
