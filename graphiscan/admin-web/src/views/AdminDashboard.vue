<template>
  <AdminLayout title="Admin Dashboard">
    <div class="dashboard-page modern-admin-dashboard">
      <section class="dash-head modern-dashboard-hero">
        <div>
          <span class="dash-eyebrow">Admin Overview</span>
          <h1>GRAPHISCAN Analytics</h1>
          <p>Monitor users, students, screenings, validations, and progress indicators.</p>
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

      <p v-if="error" class="error-message">{{ error }}</p>

      <section class="dashboard-highlight-grid">
        <RouterLink class="dashboard-highlight-card primary" to="/admin/results">
          <div>
            <span>Total Screenings</span>
            <strong>{{ displayNumber(totalResults) }}</strong>
            <p>{{ displayNumber(totalSamples) }} uploaded samples</p>
          </div>

          <div class="highlight-icon">
            <FileText :size="24" :stroke-width="1.9" />
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card" to="/admin/students">
          <div>
            <span>Students</span>
            <strong>{{ displayNumber(totalStudents) }}</strong>
            <p>{{ displayNumber(progressStats.screened) }} with screening records</p>
          </div>

          <div class="highlight-icon">
            <GraduationCap :size="24" :stroke-width="1.9" />
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card" to="/admin/users">
          <div>
            <span>Users</span>
            <strong>{{ displayNumber(totalUsers) }}</strong>
            <p>{{ displayNumber(userRoleStats.active) }} active accounts</p>
          </div>

          <div class="highlight-icon">
            <Users :size="24" :stroke-width="1.9" />
          </div>
        </RouterLink>

        <RouterLink class="dashboard-highlight-card danger" to="/admin/progress">
          <div>
            <span>Follow-ups</span>
            <strong>{{ displayNumber(progressStats.followUp) }}</strong>
            <p>Students needing support</p>
          </div>

          <div class="highlight-icon">
            <AlertTriangle :size="24" :stroke-width="1.9" />
          </div>
        </RouterLink>
      </section>

      <section class="dashboard-visual-grid">
        <section class="clean-panel">
          <div class="clean-panel-head split-head">
            <div>
              <span>Validation</span>
              <h2>Review Status</h2>
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
              <span>Screening Classification</span>
              <h2>Result Breakdown</h2>
            </div>

            <RouterLink class="mini-view-link" to="/admin/results">
              View records
            </RouterLink>
          </div>

          <div class="classification-ring-wrap">
            <div class="classification-ring" :style="classificationRingStyle">
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

              <div class="average-probability-card">
                <p>Average Probability</p>
                <strong>{{ averageProbability }}</strong>
              </div>
            </div>
          </div>
        </section>
      </section>

      <section class="dashboard-visual-grid">
        <section class="clean-panel">
          <div class="clean-panel-head split-head">
            <div>
              <span>Users</span>
              <h2>Role Distribution</h2>
            </div>

            <RouterLink class="mini-view-link" to="/admin/users">
              Manage users
            </RouterLink>
          </div>

          <div class="role-pill-grid">
            <RouterLink
              v-for="item in roleCards"
              :key="item.label"
              class="role-pill-card"
              to="/admin/users"
            >
              <div class="role-pill-icon">
                <component :is="item.icon" :size="18" :stroke-width="1.9" />
              </div>

              <div>
                <span>{{ item.label }}</span>
                <strong>{{ displayNumber(item.value) }}</strong>
              </div>
            </RouterLink>
          </div>
        </section>

        <section class="clean-panel">
          <div class="clean-panel-head split-head">
            <div>
              <span>Progress</span>
              <h2>Student Monitoring</h2>
            </div>

            <RouterLink class="mini-view-link" to="/admin/progress">
              View progress
            </RouterLink>
          </div>

          <div class="progress-summary-list">
            <RouterLink class="progress-summary-row" to="/admin/progress">
              <div>
                <strong>With Screenings</strong>
                <small>Students with progress records</small>
              </div>

              <span>{{ displayNumber(progressStats.screened) }}</span>
            </RouterLink>

            <RouterLink class="progress-summary-row success" to="/admin/progress">
              <div>
                <strong>Improving</strong>
                <small>Lower latest probability</small>
              </div>

              <span>{{ displayNumber(progressStats.improving) }}</span>
            </RouterLink>

            <RouterLink class="progress-summary-row danger" to="/admin/progress">
              <div>
                <strong>Follow-up Needed</strong>
                <small>Marked for support</small>
              </div>

              <span>{{ displayNumber(progressStats.followUp) }}</span>
            </RouterLink>
          </div>
        </section>
      </section>

      <section class="clean-panel">
        <div class="clean-panel-head split-head">
          <div>
            <span>Activity</span>
            <h2>Recent Screenings</h2>
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
              <p>{{ result.classification || 'No classification' }}</p>
            </div>

            <span class="result-badge" :class="classificationClass(result.classification)">
              {{ formatProbability(result.dysgraphia_probability) }}
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
  CheckCircle2,
  ClipboardCheck,
  FileText,
  GraduationCap,
  RefreshCcw,
  UserRound,
  Users
} from 'lucide-vue-next'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'

const dashboard = ref({
  total_users: null,
  total_students: null,
  total_samples: null,
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

const totalSamples = computed(() => {
  return dashboard.value.total_samples ?? totalResults.value
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

const userRoleStats = computed(() => {
  return {
    teachers: users.value.filter((user) => normalizeText(user.role) === 'teacher').length,
    parents: users.value.filter((user) => normalizeText(user.role) === 'parent').length,
    experts: users.value.filter((user) => normalizeText(user.role) === 'expert').length,
    admins: users.value.filter((user) => normalizeText(user.role) === 'admin').length,
    active: users.value.filter((user) => isActiveUser(user)).length
  }
})

const roleCards = computed(() => {
  return [
    {
      label: 'Teachers',
      value: userRoleStats.value.teachers,
      icon: ClipboardCheck
    },
    {
      label: 'Parents',
      value: userRoleStats.value.parents,
      icon: UserRound
    },
    {
      label: 'Experts',
      value: userRoleStats.value.experts,
      icon: CheckCircle2
    },
    {
      label: 'Admins',
      value: userRoleStats.value.admins,
      icon: Users
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
      background: 'conic-gradient(#eef3f8 0deg 360deg)'
    }
  }

  const normal = getPercent(classificationStats.value.normal, total)
  const highPotential = getPercent(classificationStats.value.highPotential, total)

  const normalEnd = normal
  const highPotentialEnd = normal + highPotential

  return {
    background: `conic-gradient(
      #16a34a 0% ${normalEnd}%,
      #e11d48 ${normalEnd}% ${highPotentialEnd}%,
      #eef3f8 ${highPotentialEnd}% 100%
    )`
  }
})

const progressStats = computed(() => {
  return {
    screened: progressStudents.value.filter((student) => getTotalScreenings(student) > 0).length,
    improving: progressStudents.value.filter((student) => {
      return normalizeText(student.trend_label || student.progress_trend) === 'improving'
    }).length,
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

const averageProbability = computed(() => {
  const values = results.value
    .map((result) => normalizePercent(result.dysgraphia_probability))
    .filter((value) => value !== null)

  if (!values.length) {
    return 'N/A'
  }

  const total = values.reduce((sum, value) => {
    return sum + value
  }, 0)

  return `${Number((total / values.length).toFixed(2))}%`
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

    if (dashboardResponse.status === 'fulfilled' && dashboardResponse.value.data.success) {
      const data = dashboardResponse.value.data.dashboard || dashboardResponse.value.data

      dashboard.value = {
        total_users: data.total_users ?? null,
        total_students: data.total_students ?? null,
        total_samples: data.total_samples ?? null,
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
    error.value = 'Unable to load dashboard analytics. Please refresh or log in again.'
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

function normalizePercent(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return null
  }

  if (numberValue > 0 && numberValue <= 1) {
    return Number((numberValue * 100).toFixed(2))
  }

  return Number(numberValue.toFixed(2))
}

function getPercent(value, total) {
  if (!total) {
    return 0
  }

  return Math.min(100, Number(((Number(value || 0) / total) * 100).toFixed(2)))
}

function formatProbability(value) {
  const percent = normalizePercent(value)

  if (percent === null) {
    return 'N/A'
  }

  return `${percent}%`
}

function classificationClass(classification) {
  const text = normalizeText(classification)

  if (text.includes('high potential') || text.includes('potential dysgraphia')) {
    return 'danger'
  }

  if (text.includes('normal')) {
    return 'success'
  }

  return 'secondary'
}

function isActiveUser(user) {
  const status = normalizeText(user.status || user.account_status)

  if (!status) {
    return true
  }

  return status === 'active' || status === 'approved'
}

function getTotalScreenings(student) {
  return Number(student.total_screenings ?? student.screening_count ?? student.result_count ?? 0)
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