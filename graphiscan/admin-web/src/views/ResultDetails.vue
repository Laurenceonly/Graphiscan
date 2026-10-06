<template>
  <AdminLayout>
    <div class="result-page polished-result-page">
      <div class="page-header result-header polished-result-header">
        <div>
          <span>Screening Report</span>
          <h1>Result Details</h1>
          <p>Review the screening result, handwriting sample, and expert validation.</p>
        </div>

        <RouterLink class="small-action-btn" to="/admin/results">
          <ArrowLeft :size="14" :stroke-width="1.9" />
          Back
        </RouterLink>
      </div>

      <p v-if="loading" class="muted-message">Loading result details...</p>
      <p v-if="error" class="error-message">{{ error }}</p>

      <div v-if="!loading && !error && result" class="result-detail-stack">
        <section class="panel-card result-overview-card">
          <div class="result-overview-head">
            <div>
              <span>Model Screening Result</span>
              <h2>{{ result.classification || 'No classification' }}</h2>
            </div>
          </div>

          <div class="result-score-grid">
            <div class="result-score-card">
              <div class="result-score-icon">
                <Percent :size="18" :stroke-width="1.8" />
              </div>

              <span>High Potential model score</span>
              <strong>{{ formatPercent(result.dysgraphia_probability) }}</strong>

              <div class="result-score-track">
                <div
                  class="result-score-fill probability"
                  :style="{ width: `${normalizePercent(result.dysgraphia_probability)}%` }"
                ></div>
              </div>
            </div>

            <div class="result-score-card">
              <div class="result-score-icon">
                <Gauge :size="18" :stroke-width="1.8" />
              </div>

              <span>Predicted-class score</span>
              <strong>{{ formatPercent(result.confidence_score) }}</strong>

              <div class="result-score-track">
                <div
                  class="result-score-fill confidence"
                  :style="{ width: `${normalizePercent(result.confidence_score)}%` }"
                ></div>
              </div>
            </div>

            <div class="result-score-card">
              <div class="result-score-icon">
                <CalendarDays :size="18" :stroke-width="1.8" />
              </div>

              <span>Date Generated</span>
              <strong>{{ result.date_generated || 'N/A' }}</strong>
            </div>
          </div>

          <p>Model scores are screening outputs, not a diagnosis.</p>

        </section>

        <section class="result-content-grid">
          <section class="panel-card result-image-card">
            <div class="result-section-head">
              <div>
                <span>Handwriting Sample</span>
                <h2>Uploaded Image</h2>
                <p>Image submitted for this screening.</p>
              </div>
            </div>

            <div class="result-image-preview">
              <img
                v-if="result.image_url"
                :src="result.image_url"
                alt="Handwriting Sample"
              />

              <div v-else class="clean-empty-state small">
                <ImageOff :size="30" :stroke-width="1.7" />
                <h3>No image available</h3>
                <p>The handwriting image path was not found.</p>
              </div>
            </div>
          </section>

          <section class="panel-card result-side-card student-context-card">
            <div class="result-section-head compact">
              <div>
                <span>Student</span>
                <h2>Student Context</h2>
              </div>
            </div>

            <div class="result-info-list compact-info-list">
              <div>
                <span>Name</span>
                <strong>{{ result.student_name || 'N/A' }}</strong>
              </div>

              <div>
                <span>Age</span>
                <strong>{{ result.age || 'N/A' }}</strong>
              </div>

              <div>
                <span>Grade Level</span>
                <strong>{{ result.grade_level || 'N/A' }}</strong>
              </div>

              <div>
                <span>Teacher</span>
                <strong>{{ result.teacher_name || 'N/A' }}</strong>
              </div>

              <div class="wide-info">
                <span>Parent / Guardian</span>
                <strong>{{ result.parent_name || 'Not assigned' }}</strong>
              </div>

            </div>

            <RouterLink
              v-if="result.student_id"
              class="result-side-link"
              :to="`/admin/progress/${result.student_id}`"
            >
              <TrendingUp :size="15" :stroke-width="1.9" />
              View Student Progress
            </RouterLink>
          </section>
        </section>

        <section class="panel-card expert-review-card">
          <div class="result-section-head compact with-badge">
            <div>
              <span>Validation</span>
              <h2>Expert Review</h2>
            </div>

            <span class="result-badge" :class="validationClass(result.validation_status)">
              {{ result.validation_status || 'Pending' }}
            </span>
          </div>

          <div class="result-info-list expert-review-list">
            <div>
              <span>Expert / SPED Coordinator</span>
              <strong>{{ result.expert_name || 'Not yet validated' }}</strong>
            </div>

            <div>
              <span>Validation Date</span>
              <strong>{{ result.validation_date || 'Not yet validated' }}</strong>
            </div>

            <div>
              <span>Follow-up Needed</span>
              <strong :class="followUpClass">
                {{ result.follow_up_needed || 'No' }}
              </strong>
            </div>

            <div class="wide-info">
              <span>Expert Remarks</span>
              <strong>{{ result.remarks || 'No remarks yet.' }}</strong>
            </div>

            <div class="wide-info">
              <span>Expert Recommendation</span>
              <strong>{{ result.expert_recommendation || 'No expert recommendation yet.' }}</strong>
            </div>
          </div>
        </section>
      </div>

      <div v-if="!loading && !error && !result" class="clean-empty-state">
        <ImageOff :size="34" :stroke-width="1.7" />
        <h3>No result details found</h3>
        <p>The selected screening result could not be loaded.</p>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  ArrowLeft,
  CalendarDays,
  Gauge,
  ImageOff,
  Percent,
  TrendingUp
} from 'lucide-vue-next'

const route = useRoute()

const result = ref(null)
const loading = ref(true)
const error = ref('')

const followUpClass = computed(() => {
  return String(result.value?.follow_up_needed || '').toLowerCase() === 'yes'
    ? 'follow-up-yes'
    : 'follow-up-no'
})

onMounted(() => {
  loadResultDetails()
})

async function loadResultDetails() {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await adminApi.get(`/results/${route.params.id}`)

    if (response.data.success) {
      result.value = response.data.result
    } else {
      error.value = response.data.message || 'Unable to load result details.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to connect. Check your connection and try again.'
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

function validationClass(status) {
  if (status === 'Validated') return 'success'
  if (status === 'Flagged') return 'danger'
  return 'secondary'
}
</script>
