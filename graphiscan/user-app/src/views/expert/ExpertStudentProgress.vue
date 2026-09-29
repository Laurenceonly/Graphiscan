<template>
  <UserLayout title="Student Progress">
    <section class="student-progress-page expert-progress-clean">
      <div v-if="loading || error" class="student-progress-status">
        <p v-if="loading" class="mobile-muted">Loading student progress...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section v-if="!loading && !error && student" class="student-progress-stack expert-progress-stack-clean">
        <section class="progress-hero-card expert-progress-hero-clean">
          <div>
            <span>Expert Progress Review</span>
            <h2>{{ student.fullname || 'Student Progress' }}</h2>
            <p>
              Review assessments, expert decisions, and follow-up status.
            </p>
          </div>

          <div class="progress-hero-icon">
            <FileText :size="28" :stroke-width="1.9" />
          </div>
        </section>

        <section class="progress-student-card expert-progress-card-clean">
          <div class="progress-section-head">
            <span>Student Profile</span>
            <h3>Screening Context</h3>
          </div>

          <div class="progress-info-grid expert-progress-info-clean">
            <div>
              <small>Age</small>
              <strong>{{ student.age || 'N/A' }}</strong>
            </div>

            <div>
              <small>Grade Level</small>
              <strong>{{ student.grade_level || 'N/A' }}</strong>
            </div>

            <div>
              <small>Teacher</small>
              <strong>{{ student.teacher_name || 'N/A' }}</strong>
            </div>

            <div>
              <small>Parent / Guardian</small>
              <strong>{{ student.parent_name || 'Not assigned' }}</strong>
            </div>

            <div>
              <small>Total Screenings</small>
              <strong>{{ summary.total_screenings || progress.length || 0 }}</strong>
            </div>

          </div>
        </section>

        <section class="progress-summary-grid expert-progress-summary-clean">
          <div class="progress-summary-card">
            <small>Latest Classification</small>
            <strong>{{ latestResult?.classification || 'No result yet' }}</strong>
          </div>

          <div class="progress-summary-card">
            <small>Follow-up Needed</small>
            <strong>{{ formatFollowUp(latestResult?.follow_up_needed) }}</strong>
          </div>
        </section>

        <section class="progress-timeline-card expert-progress-card-clean">
          <div class="progress-section-head">
            <span>Screening Timeline</span>
            <h3>Validation and Screening History</h3>
          </div>

          <div v-if="timelineProgress.length > 0" class="progress-timeline-list expert-timeline-list-clean">
            <article
              v-for="(item, index) in timelineProgress"
              :key="item.result_id || index"
              class="progress-timeline-item expert-timeline-item-clean"
            >
              <div class="timeline-number">{{ index + 1 }}</div>

              <div class="timeline-content">
                <div class="timeline-top expert-timeline-top-clean">
                  <div>
                    <h4>{{ item.classification || 'Screening Result' }}</h4>
                    <p>{{ item.date_generated || 'No date available' }}</p>
                  </div>

                  <span class="mobile-badge" :class="validationClass(item.validation_status)">
                    {{ formatValidationStatus(item.validation_status) }}
                  </span>
                </div>

                <div class="timeline-metrics expert-timeline-metrics-clean">
                  <div>
                    <small>High Potential model score</small>
                    <strong>{{ formatPercent(item.dysgraphia_probability) }}</strong>
                  </div>

                  <div>
                    <small>Follow-up</small>
                    <strong>{{ formatFollowUp(item.follow_up_needed) }}</strong>
                  </div>
                </div>

                <div class="timeline-note">
                  <small>Expert Reviewer</small>
                  <p>{{ item.expert_name || 'Not yet reviewed' }}</p>
                </div>

                <div class="timeline-note">
                  <small>Expert Remarks</small>
                  <p>{{ item.remarks || 'No remarks yet.' }}</p>
                </div>

                <div class="timeline-note">
                  <small>Expert Recommendation</small>
                  <p>{{ item.expert_recommendation || 'No expert recommendation yet.' }}</p>
                </div>

                <RouterLink
                  v-if="item.result_id"
                  class="timeline-view-btn expert-timeline-view-clean"
                  :to="`/expert/validate/${item.result_id}`"
                >
                  Open Validation Record
                </RouterLink>
              </div>
            </article>
          </div>

          <div v-else class="mobile-empty-state compact">
            <div>
              <FileQuestion :size="28" :stroke-width="1.8" />
            </div>

            <h3>No screenings yet</h3>
            <p>This student has no recorded handwriting screening results yet.</p>
          </div>
        </section>

        <RouterLink class="progress-back-link expert-progress-back-clean" to="/expert/results">
          <ArrowLeft :size="17" :stroke-width="2" />
          Back to Validation Queue
        </RouterLink>
      </section>

      <section v-if="!loading && !error && !student" class="mobile-empty-state compact">
        <div>
          <FileQuestion :size="28" :stroke-width="1.8" />
        </div>

        <h3>No progress record found</h3>
        <p>This student progress record is unavailable or not linked to your expert account.</p>

        <RouterLink class="mobile-empty-link" to="/expert/results">
          Back to Validation Queue
        </RouterLink>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  ArrowLeft,
  FileQuestion,
  FileText
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const route = useRoute()

const student = ref(null)
const summary = ref({})
const progress = ref([])
const loading = ref(true)
const error = ref('')

const latestResult = computed(() => {
  if (summary.value.latest_result) {
    return summary.value.latest_result
  }

  if (!progress.value.length) {
    return null
  }

  return [...progress.value].sort((a, b) => {
    return getDateValue(b.date_generated) - getDateValue(a.date_generated)
  })[0]
})

const timelineProgress = computed(() => {
  return [...progress.value].sort((a, b) => {
    return getDateValue(b.date_generated) - getDateValue(a.date_generated)
  })
})

onMounted(() => {
  loadProgress()
})

watch(
  () => route.params.id,
  () => {
    loadProgress()
  }
)

async function loadProgress() {
  const studentId = route.params.id

  if (!studentId) {
    error.value = 'Missing student record. Please open progress from the validation queue.'
    student.value = null
    summary.value = {}
    progress.value = []
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  student.value = null
  summary.value = {}
  progress.value = []

  try {
    const response = await userApi.get(`/expert/students/${studentId}/progress`, {
      timeout: 15000
    })

    if (response.data.success) {
      student.value = response.data.student || null
      summary.value = response.data.summary || {}
      progress.value = response.data.progress || []
    } else {
      error.value = response.data.message || 'Unable to load student progress.'
    }
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      error.value = 'Loading took too long. Check your connection and try again.'
    } else if (err.response?.data?.message) {
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

  return Number(numberValue.toFixed(2))
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  return `${normalizePercent(value)}%`
}

function validationClass(status) {
  const text = String(status || '').trim().toLowerCase()

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}

function formatValidationStatus(status) {
  const text = String(status || '').trim().toLowerCase()

  if (text === 'validated') return 'Validated'
  if (text === 'flagged') return 'Flagged'

  return 'Pending'
}

function formatFollowUp(value) {
  const text = String(value || '').trim().toLowerCase()

  if (text === 'yes' || text === 'true' || text === '1') {
    return 'Yes'
  }

  return 'No'
}

function getDateValue(value) {
  const dateValue = new Date(value).getTime()

  if (Number.isNaN(dateValue)) {
    return 0
  }

  return dateValue
}
</script>
