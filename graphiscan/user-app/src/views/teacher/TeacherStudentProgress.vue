<template>
  <UserLayout title="Child Progress">
    <section class="student-progress-page student-progress-clean">
      <div class="student-progress-status">
        <p v-if="loading" class="mobile-muted">Loading child progress...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section v-if="!loading && !error && student" class="student-progress-stack progress-stack-clean">
        <section class="progress-hero-card progress-hero-clean">
          <div>
            <span>Child Progress</span>
            <h2>{{ student.fullname }}</h2>
            <p>Review assessments, expert decisions, and follow-up needs.</p>
          </div>

          <div class="progress-hero-icon">
            <FileText :size="28" :stroke-width="1.9" />
          </div>
        </section>

        <section class="progress-student-card progress-card-clean">
          <div class="progress-section-head">
            <span>Student Profile</span>
            <h3>Basic Information</h3>
          </div>

          <div class="progress-info-grid progress-info-grid-clean">
            <div>
              <small>Age</small>
              <strong>{{ student.age || 'N/A' }}</strong>
            </div>

            <div>
              <small>Grade Level</small>
              <strong>{{ student.grade_level || 'N/A' }}</strong>
            </div>

            <div>
              <small>Parent / Guardian</small>
              <strong>{{ student.parent_name || 'Not assigned' }}</strong>
            </div>

          </div>
        </section>

        <section class="progress-summary-grid progress-summary-clean">
          <div class="progress-summary-card">
            <small>Latest Classification</small>
            <strong>{{ latestResult?.classification || 'No result yet' }}</strong>
          </div>

          <div class="progress-summary-card">
            <small>Assessments</small>
            <strong>{{ summary.total_screenings || progress.length || 0 }}</strong>
          </div>
        </section>

        <section class="progress-timeline-card progress-card-clean">
          <div class="progress-section-head">
            <span>Screening Timeline</span>
            <h3>Previous Screening Records</h3>
          </div>

          <div v-if="progress.length > 0" class="progress-timeline-list progress-timeline-list-clean">
            <article
              v-for="(item, index) in progress"
              :key="item.result_id"
              class="progress-timeline-item progress-timeline-item-clean"
            >
              <div class="timeline-number">{{ index + 1 }}</div>

              <div class="timeline-content">
                <div class="timeline-top timeline-top-clean">
                  <div>
                    <h4>{{ item.classification || 'Screening Result' }}</h4>
                    <p>{{ item.date_generated || 'No date available' }}</p>
                  </div>

                  <span class="mobile-badge" :class="validationClass(item.validation_status)">
                    {{ formatValidationStatus(item.validation_status) }}
                  </span>
                </div>

                <div class="timeline-metrics timeline-metrics-clean">
                  <div>
                    <small>High Potential model score</small>
                    <strong>{{ formatPercent(item.dysgraphia_probability) }}</strong>
                  </div>

                  <div>
                    <small>Follow-up</small>
                    <strong>{{ item.follow_up_needed || 'No' }}</strong>
                  </div>
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
                  class="timeline-view-btn timeline-view-clean"
                  :to="`/teacher/results/${item.result_id}`"
                >
                  View Full Result
                </RouterLink>
              </div>
            </article>
          </div>

          <div v-else class="mobile-empty-state compact">
            <div>
              <FileQuestion :size="28" :stroke-width="1.8" />
            </div>

            <h3>No screenings yet</h3>
            <p>This child has no recorded handwriting screening results yet.</p>
          </div>
        </section>

        <RouterLink class="progress-back-link progress-back-clean" to="/teacher/students">
          <ArrowLeft :size="17" :stroke-width="2" />
          Back to Students
        </RouterLink>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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
  return summary.value.latest_result || null
})

onMounted(() => {
  loadProgress()
})

async function loadProgress() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get(`/teacher/students/${route.params.id}/progress`)

    if (response.data.success) {
      student.value = response.data.student
      summary.value = response.data.summary || {}
      progress.value = response.data.progress || []
    } else {
      error.value = response.data.message || 'Unable to load child progress.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load child progress. Check your connection and try again.'
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
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}

function formatValidationStatus(status) {
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'Validated'
  if (text === 'flagged') return 'Flagged'

  return 'Pending'
}
</script>
