<template>
  <UserLayout title="Demo Screening">
    <section class="guest-demo-page">
      <section class="guest-demo-hero">
        <div>
          <span>Demo Screening</span>
          <h2>Try handwriting screening</h2>
          <p>
            Upload a handwriting image to preview the GRAPHISCAN AI screening flow.
            Demo results are not saved as official records.
          </p>
        </div>

        <div class="guest-demo-hero-icon">
          <ScanLine :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="guest-demo-notice">
        <div class="guest-demo-notice-icon">
          <Info :size="22" :stroke-width="1.9" />
        </div>

        <div>
          <strong>Demo only</strong>
          <p>
            This test will not be sent to experts for validation and will not appear
            in official teacher, parent, or expert records.
          </p>
        </div>
      </section>

      <form class="guest-demo-form" @submit.prevent="submitDemoScreening">
        <div class="guest-demo-form-head">
          <div>
            <span>Handwriting Sample</span>
            <h3>Upload demo image</h3>
          </div>
        </div>

        <div class="form-group">
          <label>Handwriting Image</label>

          <input
            ref="cameraInput"
            type="file"
            accept="image/*"
            capture="environment"
            class="hidden-file-input"
            @change="handleFileChange"
          />

          <input
            ref="galleryInput"
            type="file"
            accept="image/png, image/jpeg, image/jpg"
            class="hidden-file-input"
            @change="handleFileChange"
          />

          <div class="capture-action-grid">
            <button class="capture-action-card" type="button" @click="openCamera">
              <div class="capture-action-icon">
                <Camera :size="24" :stroke-width="1.9" />
              </div>

              <div>
                <strong>Take Photo</strong>
                <p>Use your phone camera to capture a demo handwriting sample.</p>
              </div>
            </button>

            <button class="capture-action-card" type="button" @click="openGallery">
              <div class="capture-action-icon">
                <ImagePlus :size="24" :stroke-width="1.9" />
              </div>

              <div>
                <strong>Choose Image</strong>
                <p>Select an existing handwriting image from your device.</p>
              </div>
            </button>
          </div>
        </div>

        <div v-if="previewUrl" class="guest-demo-preview-card">
          <div class="guest-demo-preview-head">
            <div>
              <span>Preview</span>
              <strong>{{ selectedFileName }}</strong>
            </div>

            <button type="button" @click="clearSelectedFile">
              Remove
            </button>
          </div>

          <img :src="previewUrl" alt="Demo handwriting preview" />
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <section v-if="demoResult" class="guest-demo-result-card">
          <div class="guest-demo-result-head">
            <div>
              <span>Demo AI Result</span>
              <h3>{{ demoResult.classification }}</h3>
            </div>

            <CheckCircle2 :size="26" :stroke-width="1.9" />
          </div>

          <div class="guest-demo-result-grid">
            <div>
             <small>High Potential Probability</small>
              <strong>{{ demoResult.dysgraphia_probability || 'N/A' }}</strong>
            </div>

            <div>
              <small>Confidence Score</small>
              <strong>{{ demoResult.confidence_score || 0 }}%</strong>

              <div class="guest-demo-confidence-track">
                <div
                  class="guest-demo-confidence-fill"
                  :style="{ width: `${Number(demoResult.confidence_score || 0)}%` }"
                ></div>
              </div>
            </div>
          </div>

          <div class="guest-demo-text-block">
            <small>Recommendation</small>
            <p>{{ demoResult.recommendation || 'No recommendation available.' }}</p>
          </div>

          <div class="guest-demo-text-block">
            <small>Analysis Summary</small>
            <p>{{ demoResult.analysis_summary || 'No analysis summary available.' }}</p>
          </div>

          <div class="guest-demo-warning">
            <strong>Demo result only</strong>
            <p>
              This result is not official and will not receive expert validation.
              Register as an approved user to use official GRAPHISCAN workflows.
            </p>
          </div>
        </section>

        <button class="guest-demo-submit-btn" type="submit" :disabled="screening">
          <LoaderCircle v-if="screening" :size="17" :stroke-width="2" />
          <ScanLine v-else :size="17" :stroke-width="2" />

          {{ screening ? 'Screening demo sample...' : 'Run Demo Screening' }}
        </button>
      </form>
    </section>
  </UserLayout>
</template>

<script setup>
import { ref } from 'vue'
import {
  Camera,
  CheckCircle2,
  ImagePlus,
  Info,
  LoaderCircle,
  ScanLine
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const cameraInput = ref(null)
const galleryInput = ref(null)

const selectedFile = ref(null)
const selectedFileName = ref('')
const previewUrl = ref('')

const screening = ref(false)
const error = ref('')
const success = ref('')
const demoResult = ref(null)

function openCamera() {
  cameraInput.value?.click()
}

function openGallery() {
  galleryInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files[0]

  clearSelectedFile()
  error.value = ''
  success.value = ''
  demoResult.value = null

  if (!file) return

  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg']
  const maxSizeInMb = 10
  const maxSizeInBytes = maxSizeInMb * 1024 * 1024

  if (!allowedTypes.includes(file.type)) {
    error.value = 'Please select a PNG, JPG, or JPEG image.'
    return
  }

  if (file.size > maxSizeInBytes) {
    error.value = `Image file must be ${maxSizeInMb}MB or smaller.`
    return
  }

  selectedFile.value = file
  selectedFileName.value = file.name
  previewUrl.value = URL.createObjectURL(file)
}

function clearSelectedFile() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }

  selectedFile.value = null
  selectedFileName.value = ''
  previewUrl.value = ''
}

async function submitDemoScreening() {
  error.value = ''
  success.value = ''
  demoResult.value = null

  if (!selectedFile.value) {
    error.value = 'Please select a handwriting image first.'
    return
  }

  screening.value = true

  try {
    const formData = new FormData()
    formData.append('handwriting_image', selectedFile.value)

    const response = await userApi.post('/guest/demo-screening', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      success.value = response.data.message || 'Demo screening completed.'

      demoResult.value = {
        classification: response.data.classification,
        confidence_score: response.data.confidence_score,
        dysgraphia_probability: response.data.dysgraphia_probability,
        recommendation: response.data.recommendation,
        analysis_summary: response.data.analysis_summary,
        is_demo: true
      }
    } else {
      error.value = response.data.message || 'Unable to run demo screening.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to run demo screening. Please try again.'
    }

    console.error(err)
  } finally {
    screening.value = false
  }
}
</script>