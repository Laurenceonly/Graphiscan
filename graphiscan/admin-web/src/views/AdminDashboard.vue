<template>
  <AdminLayout>
    <div class="dashboard-page modern-admin-dashboard">
      <section class="dashboard-toolbar">
        <div>
          <h1>Screening overview</h1>
          <p>Current records and expert review activity.</p>
        </div>

        <button
          class="dash-refresh-btn"
          type="button"
          :disabled="loading"
          @click="loadDashboard"
        >
          <RefreshCcw :size="16" :stroke-width="2" />
          Refresh
        </button>
      </section>

      <p v-if="error" class="error-message" role="alert">{{ error }}</p>

      <section class="dashboard-highlight-grid" aria-label="Record totals">
        <RouterLink class="dashboard-highlight-card primary" to="/admin/results">
          <div class="highlight-icon">
            <FileText :size="20" :stroke-width="1.9" />
          </div>
          <div>
            <span>Total screenings</span>
            <strong>{{ displayNumber(totalResults) }}</strong>
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card" to="/admin/students">
          <div class="highlight-icon">
            <GraduationCap :size="20" :stroke-width="1.9" />
          </div>
          <div>
            <span>Students</span>
            <strong>{{ displayNumber(totalStudents) }}</strong>
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card" to="/admin/users">
          <div class="highlight-icon">
            <Users :size="20" :stroke-width="1.9" />
          </div>
          <div>
            <span>Users</span>
            <strong>{{ displayNumber(totalUsers) }}</strong>
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card danger" to="/admin/progress">
          <div class="highlight-icon">
            <AlertTriangle :size="20" :stroke-width="1.9" />
          </div>
          <div>
            <span>Follow-ups</span>
            <strong>{{ displayNumber(progressStats.followUp) }}</strong>
          </div>
        </RouterLink>
      </section>

      <section class="dashboard-visual-grid">
        <section class="clean-panel">
          <div class="clean-panel-head split-head">
            <div>
              <h2>Review status</h2>
            </div>

            <RouterLink class="mini-view-link" to="/admin/results">
              View results
            </RouterLink>
          </div>

          <div class="analytics-bar-list">
            <div
              v-for="item in validationBars"
              :key="item.label"
              class="analytics-bar-item"
            >
              <div class="analytics-bar-top">
                <div>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.description }}</small>
                </div>

                <span>{{ displayNumber(item.value) }}</span>
              </div>

              <div class="analytics-bar-track">
                <div
                  class="analytics-bar-fill"
                  :class="item.tone"
                  :style="{ width: `${item.percent}%` }"
                ></div>
              </div>
            </div>
          </div>
        </section>

        <section class="clean-panel">
          <div class="clean-panel-head split-head">
            <div>
              <h2>Result breakdown</h2>
            </div>

            <RouterLink class="mini-view-link" to="/admin/results">
              View records
            </RouterLink>
          </div>

          <div class="classification-ring-wrap">
            <div class="classification-ring" :style="classificationRingStyle" aria-hidden="true">
              <div>
                <strong>{{ displayNumber(totalResults) }}</strong>
                <span>Results</span>
              </div>
            </div>

            <div class="classification-legend">
              <div>
                <span class="legend-dot success"></span>
                <p>Normal</p>
                <strong>{{ displayNumber(classificationStats.normal) }}</strong>
              </div>

              <div>
                <span class="legend-dot danger"></span>
                <p>High Potential</p>
                <strong>{{ displayNumber(classificationStats.highPotential) }}</strong>
              </div>
            </div>
          </div>
        </section>
      </section>

      <section class="clean-panel">
        <div class="clean-panel-head split-head">
          <div>
            <h2>Recent screenings</h2>
          </div>

          <RouterLink class="mini-view-link" to="/admin/results">
            Open results
          </RouterLink>
        </div>

        <div v-if="recentResults.length > 0" class="recent-screening-list">
          <RouterLink
            v-for="result in recentResults"
            :key="result.result_id"
            class="recent-screening-item"
            :to="getResultPath(result)"
          >
            <div>
              <strong>{{ result.student_name || result.fullname || 'Student Record' }}</strong>
              <p>{{ result.classification || 'No classification' }} · {{ result.date_generated || 'Date unavailable' }}</p>
            </div>

            <span class="result-badge" :class="validationClass(result.validation_status)">
              {{ result.validation_status || 'Pending' }}
            </span>
          </RouterLink>
        </div>

        <div v-else class="clean-empty-state small">
          <FileText :size="28" :stroke-width="1.8" />
          <h3>No recent results</h3>
          <p>Screening records will appear here after uploads.</p>
        </div>
      </section>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertTriangle,
  FileText,
  GraduationCap,
  RefreshCcw,
  Users
} from 'lucide-vue-next'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'

const dashboard = ref({
  total_users: null,
  total_students: null,
  total_results: null,
  pending_validations: null,
  validated_validations: null,
  flagged_validations: null,
  total_logs: null
})

const users = ref([])
const students = ref([])
const results = ref([])
const progressStudents = ref([])

const loading = ref(true)
const error = ref('')

const totalUsers = computed(() => {
  return dashboard.value.total_users ?? users.value.length
})

const totalStudents = computed(() => {
  return dashboard.value.total_students ?? students.value.length
})

const totalResults = computed(() => {
  return dashboard.value.total_results ?? results.value.length
})

const pendingValidations = computed(() => {
  if (dashboard.value.pending_validations !== null && dashboard.value.pending_validations !== undefined) {
    return dashboard.value.pending_validations
  }

  return results.value.filter((result) => {
    const status = normalizeText(result.validation_status || result.latest_validation_status)
    return !status || status === 'pending'
  }).length
})

const validatedValidations = computed(() => {
  if (dashboard.value.validated_validations !== null && dashboard.value.validated_validations !== undefined) {
    return dashboard.value.validated_validations
  }

  return results.value.filter((result) => {
    return normalizeText(result.validation_status || result.latest_validation_status) === 'validated'
  }).length
})

const flaggedValidations = computed(() => {
  if (dashboard.value.flagged_validations !== null && dashboard.value.flagged_validations !== undefined) {
    return dashboard.value.flagged_validations
  }

  return results.value.filter((result) => {
    return normalizeText(result.validation_status || result.latest_validation_status) === 'flagged'
  }).length
})

const validationTotal = computed(() => {
  return pendingValidations.value + validatedValidations.value + flaggedValidations.value
})

const validationBars = computed(() => {
  return [
    {
      label: 'Pending',
      description: 'Waiting for expert review',
      value: pendingValidations.value,
      percent: getPercent(pendingValidations.value, validationTotal.value),
      tone: 'warning'
    },
    {
      label: 'Validated',
      description: 'Reviewed records',
      value: validatedValidations.value,
      percent: getPercent(validatedValidations.value, validationTotal.value),
      tone: 'success'
    },
    {
      label: 'Flagged',
      description: 'Needs attention',
      value: flaggedValidations.value,
      percent: getPercent(flaggedValidations.value, validationTotal.value),
      tone: 'danger'
    }
  ]
})

const classificationStats = computed(() => {
  const stats = {
    normal: 0,
    highPotential: 0
  }

  results.value.forEach((result) => {
    const classification = normalizeText(result.classification || result.latest_classification)

    if (classification.includes('high potential') || classification.includes('potential dysgraphia')) {
      stats.highPotential += 1
      return
    }

    if (classification.includes('normal')) {
      stats.normal += 1
    }
  })

  return stats
})

const classificationRingStyle = computed(() => {
  const total =
    classificationStats.value.normal +
    classificationStats.value.highPotential

  if (!total) {
    return {
      background: 'var(--border)'
    }
  }

  const normal = getPercent(classificationStats.value.normal, total)
  const highPotential = getPercent(classificationStats.value.highPotential, total)

  const normalEnd = normal
  const highPotentialEnd = normal + highPotential

  return {
    background: `conic-gradient(
      var(--success) 0% ${normalEnd}%,
      var(--danger) ${normalEnd}% ${highPotentialEnd}%,
      var(--border) ${highPotentialEnd}% 100%
    )`
  }
})

const progressStats = computed(() => {
  return {
    followUp: progressStudents.value.filter((student) => {
      return normalizeText(getFollowUpNeeded(student)) === 'yes'
    }).length
  }
})

const recentResults = computed(() => {
  return [...results.value]
    .sort((a, b) => {
      return new Date(b.date_generated || 0) - new Date(a.date_generated || 0)
    })
    .slice(0, 5)
})

onMounted(() => {
  loadDashboard()
})

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    const [
      dashboardResponse,
      usersResponse,
      studentsResponse,
      resultsResponse,
      progressResponse
    ] = await Promise.allSettled([
      adminApi.get('/dashboard'),
      adminApi.get('/users'),
      adminApi.get('/students'),
      adminApi.get('/results'),
      adminApi.get('/students/progress')
    ])

    if ([dashboardResponse, usersResponse, studentsResponse, resultsResponse, progressResponse]
      .some((response) => response.status === 'rejected' || !response.value.data.success)) {
      error.value = 'Some dashboard information could not be loaded. Refresh to try again.'
    }

    if (dashboardResponse.status === 'fulfilled' && dashboardResponse.value.data.success) {
      const data = dashboardResponse.value.data.dashboard || dashboardResponse.value.data

      dashboard.value = {
        total_users: data.total_users ?? null,
        total_students: data.total_students ?? null,
        total_results: data.total_results ?? null,
        pending_validations: data.pending_validations ?? null,
        validated_validations: data.validated_validations ?? null,
        flagged_validations: data.flagged_validations ?? null,
        total_logs: data.total_logs ?? null
      }
    }

    if (usersResponse.status === 'fulfilled') {
      users.value = extractArray(usersResponse.value.data, ['users', 'data'])
    }

    if (studentsResponse.status === 'fulfilled') {
      students.value = extractArray(studentsResponse.value.data, ['students', 'data'])
    }

    if (resultsResponse.status === 'fulfilled') {
      results.value = extractArray(resultsResponse.value.data, ['results', 'data'])
    }

    if (progressResponse.status === 'fulfilled') {
      progressStudents.value = extractArray(progressResponse.value.data, ['students', 'progress', 'data'])
    }
  } catch (err) {
    error.value = 'Unable to load dashboard analytics. Check your connection and try again.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function extractArray(payload, keys) {
  if (Array.isArray(payload)) {
    return payload
  }

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) {
      return payload[key]
    }
  }

  return []
}

function displayNumber(value) {
  if (loading.value || value === null || value === undefined) {
    return '...'
  }

  return value
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function getPercent(value, total) {
  if (!total) {
    return 0
  }

  return Math.min(100, Number(((Number(value || 0) / total) * 100).toFixed(2)))
}

function validationClass(status) {
  const text = normalizeText(status)

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}

function getFollowUpNeeded(student) {
  const latest = student.latest_result || student.latestResult || {}

  return (
    student.follow_up_needed ||
    student.latest_follow_up_needed ||
    latest.follow_up_needed ||
    'No'
  )
}

function getResultPath(result) {
  if (!result.result_id) {
    return '/admin/results'
  }

  return `/admin/results/${result.result_id}`
}
</script>

<style scoped>
.modern-admin-dashboard {
  gap: 24px;
  font: 400 14px/1.6 var(--font-ui);
}
.dashboard-toolbar { padding: 0; }
.dashboard-toolbar h1 { font-size: 28px; line-height: 1.25; }
.dashboard-toolbar p { font-size: 14px; line-height: 1.6; margin-top: 8px; }
.dashboard-toolbar .dash-refresh-btn {
  min-height: 44px; border-color: var(--control-border); border-radius: 8px;
  font-size: 14px; font-weight: 500;
}
.dashboard-highlight-grid { gap: 16px; }
.dashboard-highlight-card {
  min-height: 116px; padding: 20px; border-radius: 12px;
  border-color: var(--border); box-shadow: none;
}
.dashboard-highlight-card:hover { background: var(--blue-50); border-color: var(--blue-700); box-shadow: none; }
.dashboard-highlight-card .highlight-icon { width: 40px; height: 40px; border-radius: 8px; }
.dashboard-highlight-card span { font-size: 13px; font-weight: 500; }
.dashboard-highlight-card strong { font-size: 28px; line-height: 1.2; font-weight: 600; }
.dashboard-visual-grid { gap: 24px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.clean-panel { padding: 24px; border-radius: 12px; box-shadow: none; }
.clean-panel-head { margin-bottom: 24px; align-items: center; flex-wrap: wrap; gap: 12px; }
.clean-panel-head h2 { font-size: 18px; font-weight: 600; line-height: 1.4; letter-spacing: -.02em; }
.mini-view-link { min-height: 44px; padding: 8px 12px; border-radius: 8px; font-size: 13px; font-weight: 500; }
.analytics-bar-list { gap: 24px; }
.analytics-bar-top strong { font-size: 14px; font-weight: 500; }
.analytics-bar-top small { font-size: 12px; }
.analytics-bar-top span { font-size: 16px; }
.analytics-bar-track { height: 8px; background: var(--border); }
.analytics-bar-fill.warning { background: var(--warning); }
.analytics-bar-fill.success, .legend-dot.success { background: var(--success); }
.analytics-bar-fill.danger, .legend-dot.danger { background: var(--danger); }
.classification-ring-wrap { grid-template-columns: minmax(140px, 180px) minmax(0, 1fr); gap: 20px; }
.classification-ring { width: 100%; height: auto; aspect-ratio: 1; }
.classification-ring strong { font-size: 28px; font-variant-numeric: tabular-nums; }
.classification-ring span, .classification-legend p { font-size: 13px; }
.classification-legend div { padding: 12px 0; border: 0; border-bottom: 1px solid var(--border); border-radius: 0; background: transparent; }
.classification-legend strong { font-size: 14px; font-variant-numeric: tabular-nums; }
.recent-screening-item { padding: 16px; border-radius: 8px; background: var(--white); }
.result-badge.success { color: var(--success-text); background: #ecfdf3; }
.result-badge.danger { color: var(--danger-text); background: #fff1f2; }
.recent-screening-item strong { font-size: 14px; font-weight: 500; }
.recent-screening-item p { font-size: 13px; line-height: 1.6; }
.clean-empty-state { padding: 32px 16px; }
.clean-empty-state h3 { font-size: 16px; font-weight: 600; }
.clean-empty-state p { font-size: 14px; }
:is(a, button):focus-visible { outline: 3px solid var(--blue-700); outline-offset: 3px; }
@media (max-width: 1280px) {
  .classification-ring-wrap { grid-template-columns: 1fr; justify-items: center; }
  .classification-ring { width: 160px; }
  .classification-legend { width: 100%; }
}
@media (max-width: 760px) {
  .dashboard-visual-grid { grid-template-columns: 1fr; }
  .dashboard-toolbar { flex-direction: row; flex-wrap: wrap; }
  .dashboard-toolbar h1 { font-size: 28px; }
  .clean-panel { padding: 20px; }
  .clean-panel-head { align-items: flex-start; text-align: left; }
  .clean-panel-head h2 { text-align: left; }
  .classification-ring-wrap { grid-template-columns: 1fr; }
  .recent-screening-item { align-items: flex-start; flex-wrap: wrap; gap: 12px; }
}
</style>
