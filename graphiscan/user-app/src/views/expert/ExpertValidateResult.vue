<template>
  <UserLayout title="Validate Result">
    <section class="expert-validate-page expert-validate-clean">
      <div v-if="loading || error" class="expert-validate-status">
        <p v-if="loading" class="mobile-muted">Loading result for validation...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section v-if="!loading && !error && result" class="expert-validate-stack expert-validate-stack-clean">
        <section class="expert-validate-hero expert-validate-hero-clean">
          <div class="expert-validate-hero-copy">
            <span>Expert Review</span>
            <h2>Validate Result</h2>
            <p>Review the AI output, handwriting sample, student details, and submit your expert decision.</p>
          </div>

          <div class="expert-validate-hero-icon">
            <ClipboardCheck :size="28" :stroke-width="1.9" />
          </div>
        </section>

        <section class="expert-ai-card expert-card-clean">
          <div class="expert-ai-head expert-ai-head-clean">
            <div>
              <span>AI Screening Output</span>
              <h3>{{ result.classification || 'No classification available' }}</h3>
            </div>

            <span class="mobile-badge" :class="classificationClass(result.classification)">
              {{ result.classification || 'N/A' }}
            </span>
          </div>

          <div class="expert-score-grid expert-score-grid-clean">
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

        <section class="expert-info-card expert-card-clean">
          <div class="expert-section-head expert-section-head-clean">
            <span>Student Information</span>
            <h3>{{ result.student_name || 'Unknown Student' }}</h3>
          </div>

          <div class="expert-info-grid expert-info-grid-clean">
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

        <RouterLink
          v-if="result.student_id"
          class="expert-progress-link expert-progress-link-clean"
          :to="`/expert/students/${result.student_id}/progress`"
        >
          <TrendingUp :size="17" :stroke-width="2" />
          View Child Progress
        </RouterLink>

        <section class="expert-info-card expert-card-clean">
          <div class="expert-section-head expert-section-head-clean">
            <span>Handwriting Sample</span>
            <h3>Uploaded Image</h3>
          </div>

          <div v-if="result.image_url" class="expert-image-preview expert-image-preview-clean">
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

        <section class="expert-info-card expert-card-clean">
          <div class="expert-section-head expert-section-head-clean">
            <span>AI Recommendation</span>
            <h3>System Suggested Action</h3>
          </div>

          <p class="expert-report-text expert-report-text-clean">
            {{ result.recommendation || 'No AI recommendation available.' }}
          </p>
        </section>

        <section class="expert-info-card expert-card-clean">
          <div class="expert-section-head expert-section-head-clean">
            <span>Analysis</span>
            <h3>Analysis Summary</h3>
          </div>

          <p class="expert-report-text expert-report-text-clean">
            {{ result.analysis_summary || 'No analysis summary available.' }}
          </p>
        </section>

        <form class="expert-validation-form expert-validation-form-clean" @submit.prevent="submitValidation">
          <div class="expert-section-head expert-section-head-clean">
            <span>Validation Decision</span>
            <h3>Submit Expert Review</h3>
            <p>Select a decision, add remarks, and provide a clear recommendation.</p>
          </div>

          <div class="validation-choice-grid validation-choice-grid-clean">
            <button
              type="button"
              class="validation-choice-card validation-choice-clean"
              :class="{ active: validationStatus === 'Validated' }"
              :disabled="saving"
              @click="validationStatus = 'Validated'"
            >
              <CheckCircle2 :size="22" :stroke-width="1.9" />
              <strong>Validated</strong>
              <small>AI result is acceptable after expert review.</small>
            </button>

            <button
              type="button"
              class="validation-choice-card validation-choice-clean danger"
              :class="{ active: validationStatus === 'Flagged' }"
              :disabled="saving"
              @click="validationStatus = 'Flagged'"
            >
              <Flag :size="22" :stroke-width="1.9" />
              <strong>Flagged</strong>
              <small>Result needs attention, clarification, or follow-up.</small>
            </button>
          </div>

          <div class="form-group">
            <label>Expert Remarks</label>

            <textarea
              v-model="remarks"
              class="expert-remarks-textarea expert-remarks-clean"
              placeholder="Explain your expert judgment about the AI screening result."
              :disabled="saving"
            ></textarea>
          </div>

          <div class="form-group">
            <label>Expert Recommendation</label>

            <textarea
              v-model="expertRecommendation"
              class="expert-remarks-textarea expert-remarks-clean"
              placeholder="Enter suggested intervention, monitoring advice, or next steps."
              :disabled="saving"
            ></textarea>
          </div>

          <div class="form-group">
            <label>Follow-up Needed</label>

            <div class="validation-choice-grid validation-choice-grid-clean">
              <button
                type="button"
                class="validation-choice-card validation-choice-clean"
                :class="{ active: followUpNeeded === 'No' }"
                :disabled="saving"
                @click="followUpNeeded = 'No'"
              >
                <strong>No</strong>
                <small>No immediate follow-up is required based on this review.</small>
              </button>

              <button
                type="button"
                class="validation-choice-card validation-choice-clean danger"
                :class="{ active: followUpNeeded === 'Yes' }"
                :disabled="saving"
                @click="followUpNeeded = 'Yes'"
              >
                <strong>Yes</strong>
                <small>This student should be monitored or referred for follow-up.</small>
              </button>
            </div>
          </div>

          <div v-if="success || submitError" class="expert-submit-status">
            <p v-if="success" class="success-message">{{ success }}</p>
            <p v-else-if="submitError" class="error-message">{{ submitError }}</p>
          </div>

          <button class="expert-submit-btn expert-submit-clean" type="submit" :disabled="saving">
            <LoaderCircle v-if="saving" :size="17" :stroke-width="2" />
            <Send v-else :size="17" :stroke-width="2" />

            {{ saving ? 'Saving validation...' : 'Submit Validation' }}
          </button>

          <RouterLink class="expert-back-link expert-back-link-clean" to="/expert/results">
            <ArrowLeft :size="16" :stroke-width="2" />
            Back to Validation Queue
          </RouterLink>
        </form>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardCheck,
  Flag,
  ImageOff,
  LoaderCircle,
  Send,
  TrendingUp
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const route = useRoute()
const router = useRouter()

const result = ref(null)
const validationStatus = ref('')
const remarks = ref('')
const expertRecommendation = ref('')
const followUpNeeded = ref('No')

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const submitError = ref('')
const success = ref('')
const imageError = ref(false)

onMounted(() => {
  loadResultForValidation()
})

async function loadResultForValidation() {
  const resultId = route.params.id

  if (!resultId) {
    error.value = 'Missing result record. Please open validation from the queue.'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  result.value = null
  imageError.value = false

  try {
    const response = await userApi.get(`/expert/results/${resultId}`, {
      timeout: 15000
    })

    if (response.data.success) {
      const loadedResult = response.data.result || {}

      result.value = loadedResult

      const status = normalizeText(loadedResult.validation_status)

      if (status === 'validated') {
        validationStatus.value = 'Validated'
      } else if (status === 'flagged') {
        validationStatus.value = 'Flagged'
      } else {
        validationStatus.value = ''
      }

      remarks.value = loadedResult.remarks || ''
      expertRecommendation.value = loadedResult.expert_recommendation || ''
      followUpNeeded.value = formatFollowUpValue(loadedResult.follow_up_needed)
    } else {
      error.value = response.data.message || 'Unable to load result.'
    }
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      error.value = 'Loading took too long. Please check if Flask is running, then refresh.'
    } else if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load result. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

async function submitValidation() {
  submitError.value = ''
  success.value = ''

  if (!validationStatus.value) {
    submitError.value = 'Please select a validation status.'
    return
  }

  if (!remarks.value.trim()) {
    submitError.value = 'Please enter expert remarks before submitting.'
    return
  }

  if (!expertRecommendation.value.trim()) {
    submitError.value = 'Please enter expert recommendation before submitting.'
    return
  }

  saving.value = true

  try {
    const response = await userApi.post(
      `/expert/results/${route.params.id}/validate`,
      {
        validation_status: validationStatus.value,
        remarks: remarks.value.trim(),
        expert_recommendation: expertRecommendation.value.trim(),
        follow_up_needed: followUpNeeded.value
      },
      {
        timeout: 15000
      }
    )

    if (response.data.success) {
      success.value = response.data.message || 'Validation submitted successfully.'

      setTimeout(() => {
        router.push('/expert/results')
      }, 700)
    } else {
      submitError.value = response.data.message || 'Unable to submit validation.'
    }
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      submitError.value = 'Saving took too long. Please check if Flask is running, then try again.'
    } else if (err.response?.data?.message) {
      submitError.value = err.response.data.message
    } else {
      submitError.value = 'Unable to submit validation. Please try again.'
    }

    console.error(err)
  } finally {
    saving.value = false
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

function formatFollowUpValue(value) {
  const text = normalizeText(value)

  if (text === 'yes' || text === 'true' || text === '1') {
    return 'Yes'
  }

  return 'No'
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