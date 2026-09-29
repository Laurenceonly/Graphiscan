<template>
  <UserLayout title="Expert Dashboard">
    <section class="expert-dashboard-page expert-dashboard-clean">
      <section class="expert-hero-card expert-hero-clean">
        <div class="expert-hero-copy">
          <span>Expert Workspace</span>
          <h2>Hi, {{ firstName }}</h2>
          <p>Review screening outputs, validate results, and provide professional remarks.</p>
        </div>

        <div class="expert-hero-icon">
          <ClipboardCheck :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <div v-if="loading || error" class="expert-dashboard-status">
        <p v-if="loading" class="mobile-muted">Loading dashboard...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section class="expert-stats-grid-clean">
        <article
          v-for="item in statCards"
          :key="item.label"
          class="expert-stat-card-clean"
        >
          <div class="expert-stat-icon-clean" :class="item.tone">
            <component :is="item.icon" :size="20" :stroke-width="1.9" />
          </div>

          <div>
            <span>{{ item.label }}</span>
            <strong>{{ loading ? '...' : item.value }}</strong>
          </div>
        </article>
      </section>

      <section class="expert-action-panel-clean">
        <div class="expert-panel-head-clean">
          <div>
            <span>Quick Access</span>
            <h3>Expert Tools</h3>
          </div>

          <button
            class="expert-refresh-btn-clean"
            type="button"
            :disabled="loading"
            @click="loadDashboardData"
          >
            <RefreshCw :size="16" :stroke-width="1.9" />
          </button>
        </div>

        <div class="expert-action-list-clean">
          <RouterLink class="expert-action-card-clean" to="/expert/results">
            <div class="expert-action-icon-clean">
              <ClipboardList :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Validation Queue</strong>
              <p>Review pending screening results and add expert validation.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>

          <RouterLink class="expert-action-card-clean" to="/profile">
            <div class="expert-action-icon-clean">
              <UserRound :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Profile</strong>
              <p>View account details and session controls.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>
        </div>
      </section>

      <section class="expert-note-card expert-note-clean">
        <div class="expert-note-icon">
          <ShieldCheck :size="22" :stroke-width="1.9" />
        </div>

        <div>
          <strong>Professional Review</strong>
          <p>Review screening results before reports guide follow-up decisions.</p>
        </div>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  RefreshCw,
  ShieldCheck,
  UserRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const results = ref([])
const loading = ref(true)
const error = ref('')

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

const userData = getStoredUserData()

const firstName = computed(() => {
  const fullname = userData.fullname || 'Expert'
  return fullname.split(' ')[0]
})

const pendingCount = computed(() => {
  return results.value.filter((result) => {
    const status = normalizeText(result.validation_status || 'pending')
    return status === 'pending' || !status
  }).length
})

const reviewedCount = computed(() => {
  return results.value.filter((result) => {
    const status = normalizeText(result.validation_status)
    return status === 'validated' || status === 'flagged'
  }).length
})

const flaggedCount = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.validation_status) === 'flagged'
  }).length
})

const statCards = computed(() => {
  return [
    {
      label: 'Pending Review',
      value: pendingCount.value,
      icon: Clock3,
      tone: pendingCount.value > 0 ? 'warning' : 'success'
    },
    {
      label: 'Reviewed',
      value: reviewedCount.value,
      icon: CheckCircle2,
      tone: 'success'
    },
    {
      label: 'Flagged',
      value: flaggedCount.value,
      icon: AlertTriangle,
      tone: flaggedCount.value > 0 ? 'danger' : ''
    }
  ]
})

onMounted(() => {
  loadDashboardData()
})

async function loadDashboardData() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get('/expert/results', {
      timeout: 15000
    })

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      results.value = []
      error.value = response.data.message || 'Unable to load expert dashboard.'
    }
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      error.value = 'Loading took too long. Check your connection and try again.'
    } else if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load expert dashboard. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}
</script>
