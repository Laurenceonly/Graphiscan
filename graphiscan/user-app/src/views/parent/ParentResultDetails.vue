<template>
  <UserLayout title="Result Details">
    <section class="parent-result-details-page">
      <div v-if="loading || error" class="parent-result-details-status">
        <p v-if="loading" class="mobile-muted">Loading result details...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section v-if="!loading && !error && result" class="parent-report-stack">
        <section class="parent-report-hero">
          <div>
            <span>Child Screening Report</span>
            <h2>{{ result.classification || 'Screening Result' }}</h2>
            <p>
              Review screening output, expert validation, recommendations, and handwriting sample.
            </p>
          </div>

          <div class="parent-report-hero-icon">
            <FileText :size="28" :stroke-width="1.9" />
          </div>
        </section>

        <section class="parent-report-status-card">
          <div class="parent-report-status-head">
            <div>
              <span>AI Screening Output</span>
              <h3>{{ result.classification || 'No classification available' }}</h3>
            </div>

            <span class="mobile-badge" :class="classificationClass(result.classification)">
              {{ result.classification || 'N/A' }}
            </span>
          </div>

          <div class="parent-report-score-grid">
            <div>
              <small>High Potential Probability</small>
              <strong>{{ formatPercent(result.dysgraphia_probability) }}</strong>
            </div>

            <div>
              <small>Confidence Score</small>
              <strong>{{ formatPercent(result.confidence_score) }}</strong>
            </div>
          </div>
        </section>

        <section class="parent-report-card">
          <div class="parent-report-section-head">
            <span>Student Information</span>
            <h3>{{ result.student_name || 'Unknown Student' }}</h3>
          </div>

          <div class="parent-report-info-grid">
            <div>
              <small>Age</small>
              <strong>{{ result.age || 'N/A' }}</strong>
            </div>

            <div>
              <small>Grade Level</small>
              <strong>{{ result.grade_level || 'N/A' }}</strong>
            </div>

            <div>
              <small>Teacher</small>
              <strong>{{ result.teacher_name || 'N/A' }}</strong>
            </div>

            <div>
              <small>Date Generated</small>
              <strong>{{ result.date_generated || 'N/A' }}</strong>
            </div>
          </div>
        </section>

        <section class="parent-report-card">
          <div class="parent-report-section-head">
            <span>Handwriting Sample</span>
            <h3>Uploaded Image</h3>
          </div>

          <div v-if="result.image_url" class="parent-report-image-preview">
            <img
              v-if="!imageError"
              :src="result.image_url"
              alt="Handwriting sample"
              @load="imageError = false"
              @error="imageError = true"
            />

            <div v-else class="image-error-box">
              <ImageOff :size="28" :stroke-width="1.8" />
              <h3>Image preview failed</h3>
              <p>You can still open the handwriting image using the buttons below.</p>
            </div>

            <div class="image-action-row">
              <button
                type="button"
                class="image-action-btn"
                @click="viewImage(result.image_url)"
              >
                View Image
              </button>

              <button
                type="button"
                class="image-action-btn secondary"
                @click="downloadImage"
              >
                Download Image
              </button>
            </div>
          </div>

          <div v-else class="mobile-empty-state compact">
            <div>
              <ImageOff :size="28" :stroke-width="1.8" />
            </div>

            <h3>No image available</h3>
            <p>The handwriting sample image was not found.</p>
          </div>
        </section>

        <section class="parent-report-card">
          <div class="parent-report-section-head">
            <span>AI Recommendation</span>
            <h3>System Suggested Action</h3>
          </div>

          <p class="parent-report-text">
            {{ result.recommendation || 'No AI recommendation available.' }}
          </p>
        </section>

        <section class="parent-report-card">
          <div class="parent-report-section-head">
            <span>Analysis</span>
            <h3>Analysis Summary</h3>
          </div>

          <p class="parent-report-text">
            {{ result.analysis_summary || 'No analysis summary available.' }}
          </p>
        </section>

        <section class="parent-validation-card">
          <div class="parent-report-section-head">
            <span>Expert Validation</span>
            <h3>Review Status</h3>
          </div>

          <div class="parent-validation-row">
            <span class="mobile-badge" :class="validationClass(result.validation_status)">
              {{ formatValidationStatus(result.validation_status) }}
            </span>
          </div>

          <div class="parent-report-info-grid">
            <div>
              <small>Expert / SPED</small>
              <strong>{{ result.expert_name || 'Not yet validated' }}</strong>
            </div>

            <div>
              <small>Validation Date</small>
              <strong>{{ result.validation_date || 'Not yet validated' }}</strong>
            </div>

            <div>
              <small>Follow-up Needed</small>
              <strong>{{ result.follow_up_needed || 'No' }}</strong>
            </div>
          </div>

          <div class="parent-remarks-box">
            <small>Expert Remarks</small>
            <p>{{ result.remarks || 'No remarks yet.' }}</p>
          </div>

          <div class="parent-remarks-box">
            <small>Expert Recommendation</small>
            <p>{{ result.expert_recommendation || 'No expert recommendation yet.' }}</p>
          </div>
        </section>

        <RouterLink class="parent-back-link" to="/parent/results">
          <ArrowLeft :size="17" :stroke-width="2" />
          Back to Child Results
        </RouterLink>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  ArrowLeft,
  FileText,
  ImageOff
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const route = useRoute()

const result = ref(null)
const loading = ref(true)
const error = ref('')
const imageError = ref(false)

onMounted(() => {
  loadResultDetails()
})

async function loadResultDetails() {
  loading.value = true
  error.value = ''
  imageError.value = false

  try {
    const response = await userApi.get(`/parent/results/${route.params.id}`)

    if (response.data.success) {
      result.value = response.data.result
    } else {
      error.value = response.data.message || 'Unable to load result details.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load result details. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  const numberValue = Number(String(value).replace('%', '').trim())

  if (Number.isNaN(numberValue)) {
    return 'N/A'
  }

  return `${Number(numberValue.toFixed(2))}%`
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

function validationClass(status) {
  const text = normalizeText(status)

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'
  if (text === 'pending' || !text) return 'secondary'

  return 'secondary'
}

function formatValidationStatus(status) {
  const text = normalizeText(status)

  if (text === 'validated') return 'Validated'
  if (text === 'flagged') return 'Flagged'

  return 'Pending'
}

function viewImage(imageUrl) {
  if (!imageUrl) return

  window.open(imageUrl, '_blank')
}

async function downloadImage() {
  if (!result.value?.result_id) return

  try {
    const response = await userApi.get(
      `/results/${result.value.result_id}/download-image`,
      {
        responseType: 'blob'
      }
    )

    const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')

    link.href = blobUrl
    link.download = getImageFileName(result.value.image_url)

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    window.URL.revokeObjectURL(blobUrl)
  } catch (err) {
    console.error(err)
    viewImage(result.value?.image_url)
  }
}

function getImageFileName(imageUrl) {
  try {
    const url = new URL(imageUrl)
    const filename = url.pathname.split('/').pop()

    return filename || 'handwriting-sample.jpg'
  } catch {
    return 'handwriting-sample.jpg'
  }
}
</script>