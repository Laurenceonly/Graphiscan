<template>
  <AdminLayout title="Student Progress">
    <div class="compact-page admin-progress-detail-clean-page">
      <div class="page-header compact-header">
        <div>
          <span>Individual Progress</span>
          <h1>{{ student?.fullname || 'Student Progress' }}</h1>
          <p>Review assessments, expert decisions, and follow-up status in date order.</p>
        </div>

        <RouterLink class="small-action-btn admin-back-btn" to="/admin/progress">
          <ArrowLeft :size="16" :stroke-width="2" />
          Back to Progress
        </RouterLink>
      </div>

      <p v-if="loading" class="muted-message">Loading student progress...</p>
      <p v-if="error" class="error-message">{{ error }}</p>

      <template v-if="!loading && !error && student">
        <section class="user-summary-grid admin-progress-summary-grid-clean">
          <article
            v-for="item in progressStatCards"
            :key="item.label"
            class="user-summary-card"
          >
            <div class="user-summary-icon" :class="item.tone">
              <component :is="item.icon" :size="19" :stroke-width="1.9" />
            </div>

            <div>
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </article>
        </section>

        <section class="panel-card admin-progress-profile-panel">
          <div class="admin-progress-panel-head">
            <div>
              <span>Student</span>
              <h2>Profile</h2>
            </div>
          </div>

          <div class="admin-progress-info-list">
            <div>
              <span>Age</span>
              <strong>{{ student.age || 'N/A' }}</strong>
            </div>

            <div>
              <span>Grade Level</span>
              <strong>{{ student.grade_level || 'N/A' }}</strong>
            </div>

            <div>
              <span>Teacher</span>
              <strong>{{ student.teacher_name || 'N/A' }}</strong>
            </div>

            <div>
              <span>Parent / Guardian</span>
              <strong>{{ student.parent_name || 'Not assigned' }}</strong>
            </div>
          </div>
        </section>

        <section class="panel-card admin-progress-timeline-panel">
          <div class="admin-progress-panel-head split-head">
            <div>
              <span>Assessment History</span>
              <h2>Screenings and Expert Reviews</h2>
            </div>

          </div>

          <div v-if="progress.length > 0" class="admin-progress-timeline-list-clean">
            <article
              v-for="(item, index) in progress"
              :key="item.result_id"
              class="admin-progress-timeline-item-clean"
            >
              <div class="admin-progress-timeline-number">
                {{ index + 1 }}
              </div>

              <div class="admin-progress-timeline-content-clean">
                <div class="admin-progress-timeline-top-clean">
                  <div>
                    <h3>{{ item.classification || 'Screening Result' }}</h3>
                    <p>{{ item.date_generated || 'No date available' }}</p>
                  </div>

                  <span class="result-badge" :class="validationClass(item.validation_status)">
                    {{ item.validation_status || 'Pending' }}
                  </span>
                </div>

                <div class="admin-progress-timeline-metrics-clean">
                  <div>
                    <span>High Potential model score</span>
                    <strong>{{ formatPercent(item.dysgraphia_probability) }}</strong>
                  </div>

                  <div>
                    <span>Follow-up</span>
                    <strong :class="followUpClass(item.follow_up_needed)">
                      {{ item.follow_up_needed || 'No' }}
                    </strong>
                  </div>

                  <div>
                    <span>Expert Reviewer</span>
                    <strong>{{ item.expert_name || 'Not yet reviewed' }}</strong>
                  </div>
                </div>

                <div class="admin-progress-note-grid">
                  <div>
                    <span>Expert Remarks</span>
                    <p>{{ item.remarks || 'No remarks yet.' }}</p>
                  </div>

                  <div>
                    <span>Expert Recommendation</span>
                    <p>{{ item.expert_recommendation || 'No expert recommendation yet.' }}</p>
                  </div>
                </div>

                <RouterLink
                  class="small-action-btn admin-progress-result-link"
                  :to="`/admin/results/${item.result_id}`"
                >
                  <Eye :size="15" :stroke-width="2" />
                  View Result
                </RouterLink>
              </div>
            </article>
          </div>

          <div v-else class="clean-empty-state">
            <FileQuestion :size="30" :stroke-width="1.8" />
            <h3>No screenings yet</h3>
            <p>This student has no recorded handwriting screening results yet.</p>
          </div>
        </section>
      </template>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  AlertTriangle,
  ArrowLeft,
  Eye,
  FileQuestion,
  ListChecks
} from 'lucide-vue-next'
import AdminLayout from '../layouts/AdminLayout.vue'
import adminApi from '../api/adminApi'

const route = useRoute()

const student = ref(null)
const summary = ref({})
const progress = ref([])
const loading = ref(true)
const error = ref('')

const latestResult = computed(() => {
  return summary.value.latest_result || progress.value[progress.value.length - 1] || null
})

const progressStatCards = computed(() => {
  return [
    {
      label: 'Total Screenings',
      value: displayValue(summary.value.total_screenings || progress.value.length || 0),
      icon: ListChecks,
      tone: ''
    },
    {
      label: 'Follow-up Needed',
      value: latestResult.value?.follow_up_needed || 'No',
      icon: AlertTriangle,
      tone: followUpTone.value
    }
  ]
})

const followUpTone = computed(() => {
  return String(latestResult.value?.follow_up_needed || '').toLowerCase() === 'yes'
    ? 'danger'
    : 'success'
})

onMounted(() => {
  loadProgress()
})

async function loadProgress() {
  loading.value = true
  error.value = ''

  try {
    const response = await adminApi.get(`/students/${route.params.id}/progress`)

    if (response.data.success) {
      student.value = response.data.student
      summary.value = response.data.summary || {}
      progress.value = response.data.progress || []
    } else {
      error.value = response.data.message || 'Unable to load student progress.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load student progress. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizePercent(value) {
  if (value === null || value === undefined || value === '') {
    return 0
  }

  const cleanedValue = String(value).replace('%', '').trim()
  const numberValue = Number(cleanedValue)

  if (Number.isNaN(numberValue)) {
    return 0
  }

  if (numberValue > 0 && numberValue <= 1) {
    return Number((numberValue * 100).toFixed(2))
  }

  return Math.min(100, Number(numberValue.toFixed(2)))
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  return `${normalizePercent(value)}%`
}

function displayValue(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function followUpClass(value) {
  return String(value || '').toLowerCase() === 'yes'
    ? 'follow-up-yes'
    : 'follow-up-no'
}

function validationClass(status) {
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}
</script>
