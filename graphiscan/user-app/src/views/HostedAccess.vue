<template><HostedAccess :allowed-roles="['teacher','expert','parent']" :api-origin="origin" /></template>
<script setup>
import HostedAccess from '../../../shared/HostedAccess.vue'
const origin=(import.meta.env.VITE_HOSTED_API_ORIGIN || import.meta.env.VITE_API_ORIGIN || 'http://localhost:5000').replace(/\/$/,'')
</script>
