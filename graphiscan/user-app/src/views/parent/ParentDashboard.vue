<template>
  <UserLayout title="Parent Dashboard">
    <section class="parent-dashboard-page parent-dashboard-clean">
      <section class="parent-hero-card parent-hero-clean">
        <div class="parent-hero-copy">
          <span>Parent Workspace</span>
          <h2>Hi, {{ firstName }}</h2>
          <p>View linked child reports, validation status, and follow-up recommendations.</p>
        </div>

        <div class="parent-hero-icon">
          <FileText :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <div v-if="loading || error" class="parent-dashboard-status">
        <p v-if="loading" class="mobile-muted">Loading dashboard...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section class="parent-stats-grid-clean">
        <RouterLink
          v-for="item in statCards"
          :key="item.label"
          class="parent-stat-card-clean parent-stat-link-clean"
          :to="item.to"
          :aria-label="`Open ${item.label}`"
        >
          <div class="parent-stat-icon-clean" :class="item.tone">
            <component :is="item.icon" :size="20" :stroke-width="1.9" />
          </div>

          <div>
            <span>{{ item.label }}</span>
            <strong>{{ loading ? '...' : item.value }}</strong>
          </div>
        </RouterLink>
      </section>

      <section class="parent-action-panel-clean">
        <div class="parent-panel-head-clean">
          <div>
            <span>Quick Access</span>
            <h3>Parent Tools</h3>
          </div>

          <button
            class="parent-refresh-btn-clean"
            type="button"
            :disabled="loading"
            @click="loadDashboardData"
          >
            <RefreshCw :size="16" :stroke-width="1.9" />
          </button>
        </div>

        <div class="parent-action-list-clean">
          <RouterLink class="parent-action-card-clean" to="/parent/results">
            <div class="parent-action-icon-clean">
              <FileText :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Child Results</strong>
              <p>View screening reports and expert validation.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>

          <RouterLink
            v-if="latestResult?.student_id"
            class="parent-action-card-clean"
            :to="`/parent/students/${latestResult.student_id}/progress`"
          >
            <div class="parent-action-icon-clean">
              <TrendingUp :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Latest Progress</strong>
              <p>{{ latestResult.student_name || 'View child progress record.' }}</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>

          <RouterLink class="parent-action-card-clean" to="/profile">
            <div class="parent-action-icon-clean">
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

      <section class="parent-info-card parent-info-clean">
        <div class="parent-info-icon">
          <ShieldCheck :size="22" :stroke-width="1.9" />
        </div>

        <div>
          <strong>Report Access</strong>
          <p>Only records linked to your parent or guardian account will appear here.</p>
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
  Baby,
  ChevronRight,
  FileText,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
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
  const fullname = userData.fullname || 'Parent'
  return fullname.split(' ')[0]
})

const linkedChildren = computed(() => {
  const childIds = new Set()

  results.value.forEach((result) => {
    const childKey = result.student_id || result.student_name

    if (childKey) {
      childIds.add(String(childKey))
    }
  })

  return childIds.size
})

const totalReports = computed(() => {
  return results.value.length
})

const followUpNeeded = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.follow_up_needed) === 'yes'
  }).length
})

const latestResult = computed(() => {
  if (!results.value.length) return null

  return [...results.value].sort((a, b) => {
    return getDateValue(b.date_generated) - getDateValue(a.date_generated)
  })[0]
})

const statCards = computed(() => {
  return [
    {
      label: 'Children With Reports',
      value: linkedChildren.value,
      icon: Baby,
      tone: '',
      to: latestResult.value?.student_id
        ? `/parent/students/${latestResult.value.student_id}/progress`
        : '/parent/results'
    },
    {
      label: 'Reports',
      value: totalReports.value,
      icon: FileText,
      tone: '',
      to: '/parent/results'
    },
    {
      label: 'Follow-up Needed',
      value: followUpNeeded.value,
      icon: AlertTriangle,
      tone: followUpNeeded.value > 0 ? 'warning' : 'success',
      to: '/parent/results'
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
    const response = await userApi.get('/parent/results')

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      results.value = []
      error.value = response.data.message || 'Unable to load parent dashboard.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load parent dashboard. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function getDateValue(value) {
  const dateValue = new Date(value).getTime()

  if (Number.isNaN(dateValue)) {
    return 0
  }

  return dateValue
}
</script>