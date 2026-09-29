<template>
  <UserLayout title="Guest Dashboard">
    <section class="guest-dashboard-page">
      <section class="guest-hero-card">
        <div>
          <span>Guest Preview</span>
          <h2>Welcome, {{ firstName }}</h2>
          <p>
            Explore GRAPHISCAN in limited preview mode. Official student records,
            screening reports, and validation tools are available only to approved users.
          </p>
        </div>

        <div class="guest-hero-icon">
          <Sparkles :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="guest-access-card">
        <div class="guest-access-icon">
          <LockKeyhole :size="22" :stroke-width="1.9" />
        </div>

        <div>
          <strong>Limited Access</strong>
          <p>
            Guest accounts are for preview only. You cannot manage students,
            upload official samples, view official reports, or validate results.
          </p>
        </div>
      </section>

      <section class="guest-preview-grid">
        <RouterLink
          class="guest-preview-card"
          to="/guest/demo-screening"
          aria-label="Open demo screening workflow"
        >
          <div class="guest-preview-icon">
            <ScanLine :size="22" :stroke-width="1.9" />
          </div>

          <div>
            <span>Preview</span>
            <h3>Screening Workflow</h3>
            <p>
              Learn how handwriting samples are submitted for screening.
            </p>
          </div>
        </RouterLink>

        <RouterLink
          class="guest-preview-card"
          to="/guest/demo-screening"
          aria-label="Open demo report structure"
        >
          <div class="guest-preview-icon">
            <FileText :size="22" :stroke-width="1.9" />
          </div>

          <div>
            <span>Preview</span>
            <h3>Report Structure</h3>
            <p>
              Understand what information appears in a GRAPHISCAN result report.
            </p>
          </div>
        </RouterLink>

        <RouterLink
          class="guest-preview-card"
          to="/profile"
          aria-label="Open guest profile"
        >
          <div class="guest-preview-icon">
            <UserRound :size="22" :stroke-width="1.9" />
          </div>

          <div>
            <span>Account</span>
            <h3>Profile</h3>
            <p>
              View your guest account details or log out from this device.
            </p>
          </div>
        </RouterLink>
      </section>

      <section class="guest-upgrade-card">
        <div>
          <span>Need Full Access?</span>
          <h3>Register with the correct role</h3>
          <p>
            To use official GRAPHISCAN features, create an account as a teacher,
            parent, or expert and wait for administrator approval.
          </p>
        </div>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import {
  FileText,
  LockKeyhole,
  ScanLine,
  Sparkles,
  UserRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

const userData = getStoredUserData()

const firstName = computed(() => {
  const fullname = userData.fullname || 'Guest'
  return fullname.split(' ')[0]
})
</script>
