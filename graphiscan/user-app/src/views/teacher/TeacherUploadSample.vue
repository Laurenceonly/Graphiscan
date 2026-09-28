<template>
  <UserLayout title="Upload Sample">
    <section class="teacher-upload-page upload-page-clean">
      <section class="upload-hero-card upload-hero-clean">
        <div>
          <span>AI Screening</span>
          <h2>Upload handwriting</h2>
          <p>Select a student, attach a clear handwriting image, and generate a screening result.</p>
        </div>

        <div class="upload-hero-icon">
          <UploadCloud :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="upload-guide-card upload-guide-clean">
        <div class="upload-guide-head">
          <ClipboardCheck :size="20" :stroke-width="1.9" />

          <div>
            <strong>Before Uploading</strong>
            <p>Use a clear handwriting image with readable writing and minimal shadows.</p>
          </div>
        </div>

        <div class="upload-tips-grid upload-tips-clean">
          <div>
            <span>1</span>
            <p>Select the correct student.</p>
          </div>

          <div>
            <span>2</span>
            <p>Use PNG, JPG, or JPEG only.</p>
          </div>

          <div>
            <span>3</span>
            <p>Review the screening result after upload.</p>
          </div>
        </div>
      </section>

      <form class="upload-form-panel upload-form-clean" @submit.prevent="uploadSample">
        <div class="upload-panel-head upload-panel-head-clean">
          <div>
            <span>Screening Setup</span>
            <h3>Student and image</h3>
          </div>

          <button
            class="upload-refresh-btn upload-refresh-clean"
            type="button"
            :disabled="loadingStudents || uploading"
            @click="loadStudents"
          >
            <RefreshCw :size="15" :stroke-width="2" />
          </button>
        </div>

        <div class="form-group">
          <label>Student</label>

          <div class="modern-select-wrap clean-upload-select">
            <UserRound :size="18" :stroke-width="1.9" />

            <select v-model="studentId" required>
              <option value="">Select student</option>

              <option
                v-for="student in students"
                :key="student.student_id"
                :value="student.student_id"
              >
                {{ student.fullname }} · {{ student.grade_level || 'Grade N/A' }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="selectedStudent" class="selected-student-card selected-student-clean">
          <div class="student-avatar">
            {{ getInitial(selectedStudent.fullname) }}
          </div>

          <div>
            <strong>{{ selectedStudent.fullname }}</strong>
            <small>
              {{ selectedStudent.grade_level || 'Grade not set' }}
              ·
              Age {{ selectedStudent.age || 'N/A' }}
            </small>
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

          <div class="capture-action-grid capture-action-grid-clean">
            <button
              class="capture-action-card capture-action-clean"
              type="button"
              :disabled="uploading"
              @click="openCamera"
            >
              <div class="capture-action-icon">
                <Camera :size="24" :stroke-width="1.9" />
              </div>

              <div>
                <strong>Take Photo</strong>
                <p>Capture handwriting using your camera.</p>
              </div>
            </button>

            <button
              class="capture-action-card capture-action-clean"
              type="button"
              :disabled="uploading"
              @click="openGallery"
            >
              <div class="capture-action-icon">
                <ImagePlus :size="24" :stroke-width="1.9" />
              </div>

              <div>
                <strong>Choose Image</strong>
                <p>Select a handwriting image from your device.</p>
              </div>
            </button>
          </div>
        </div>

        <div v-if="previewUrl" class="modern-preview-card preview-card-clean">
          <div class="preview-card-head">
            <div>
              <span>Selected Image</span>
              <strong>{{ selectedFileName }}</strong>
              <small>{{ selectedFileSize }}</small>
            </div>

            <button type="button" :disabled="uploading" @click="clearSelectedFile">
              <X :size="14" :stroke-width="2" />
              Remove
            </button>
          </div>

          <img :src="previewUrl" alt="Handwriting preview" />
        </div>

        <div class="upload-status-area">
          <p v-if="loadingStudents" class="mobile-muted">Loading students...</p>
          <p v-else-if="error" class="error-message">{{ error }}</p>
          <p v-else-if="success" class="success-message">{{ success }}</p>
        </div>

        <section v-if="screeningResult" class="modern-screening-result-card screening-result-clean">
          <div class="result-card-head">
            <div>
              <span>Screening Result</span>
              <h3>{{ screeningResult.classification || 'Screening Complete' }}</h3>
            </div>

            <CheckCircle2 :size="26" :stroke-width="1.9" />
          </div>

          <div class="screening-result-grid screening-result-grid-clean">
            <div>
              <small>High Potential Probability</small>
              <strong>{{ formatPercent(screeningResult.dysgraphia_probability) }}</strong>
            </div>

            <div>
              <small>Confidence</small>
              <strong>{{ formatPercent(screeningResult.confidence_score) }}</strong>
            </div>
          </div>

          <RouterLink
            v-if="screeningResult.result_id"
            class="upload-result-link upload-result-link-clean"
            :to="`/teacher/results/${screeningResult.result_id}`"
          >
            View Full Result
          </RouterLink>
        </section>

        <button
          class="upload-submit-btn upload-submit-clean"
          type="submit"
          :disabled="isSubmitDisabled"
        >
          <LoaderCircle
            v-if="uploading"
            :size="17"
            :stroke-width="2"
          />

          <ScanLine
            v-else
            :size="17"
            :stroke-width="2"
          />

          {{ uploading ? 'Screening handwriting...' : 'Upload and Screen' }}
        </button>
      </form>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  Camera,
  CheckCircle2,
  ClipboardCheck,
  ImagePlus,
  LoaderCircle,
  RefreshCw,
  ScanLine,
  UploadCloud,
  UserRound,
  X
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const studentId = ref('')
const students = ref([])

const galleryInput = ref(null)
const cameraInput = ref(null)

const selectedFile = ref(null)
const selectedFileName = ref('')
const selectedFileSize = ref('')
const previewUrl = ref('')

const loadingStudents = ref(true)
const uploading = ref(false)
const error = ref('')
const success = ref('')
const screeningResult = ref(null)

const selectedStudent = computed(() => {
  return students.value.find((student) => {
    return String(student.student_id) === String(studentId.value)
  })
})

const isSubmitDisabled = computed(() => {
  return uploading.value || loadingStudents.value || !studentId.value || !selectedFile.value
})

onMounted(() => {
  loadStudents()
})

onBeforeUnmount(() => {
  clearSelectedFile()
})

async function loadStudents() {
  loadingStudents.value = true
  error.value = ''

  try {
    const response = await userApi.get('/teacher/students')

    if (response.data.success) {
      students.value = response.data.students || []
    } else {
      error.value = response.data.message || 'Unable to load students.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load students. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    loadingStudents.value = false
  }
}

function openCamera() {
  cameraInput.value?.click()
}

function openGallery() {
  galleryInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files?.[0]

  clearSelectedFile()
  error.value = ''
  success.value = ''
  screeningResult.value = null

  if (!file) {
    return
  }

  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg']
  const maxSizeInMb = 10
  const maxSizeInBytes = maxSizeInMb * 1024 * 1024

  if (!allowedTypes.includes(file.type)) {
    error.value = 'Please select a PNG, JPG, or JPEG image.'
    resetFileInputs()
    return
  }

  if (file.size > maxSizeInBytes) {
    error.value = `Image file must be ${maxSizeInMb}MB or smaller.`
    resetFileInputs()
    return
  }

  selectedFile.value = file
  selectedFileName.value = file.name
  selectedFileSize.value = formatFileSize(file.size)
  previewUrl.value = URL.createObjectURL(file)
}

function clearSelectedFile() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }

  selectedFile.value = null
  selectedFileName.value = ''
  selectedFileSize.value = ''
  previewUrl.value = ''

  resetFileInputs()
}

function resetFileInputs() {
  if (cameraInput.value) {
    cameraInput.value.value = ''
  }

  if (galleryInput.value) {
    galleryInput.value.value = ''
  }
}

async function uploadSample() {
  error.value = ''
  success.value = ''
  screeningResult.value = null

  if (!studentId.value) {
    error.value = 'Please select a student.'
    return
  }

  if (!selectedFile.value) {
    error.value = 'Please select a handwriting image.'
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('student_id', studentId.value)
    formData.append('handwriting_image', selectedFile.value)

    const response = await userApi.post('/teacher/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      success.value = response.data.message || 'Sample uploaded successfully.'

      screeningResult.value = {
        result_id: response.data.result_id,
        classification: response.data.classification,
        confidence_score: response.data.confidence_score,
        dysgraphia_probability: response.data.dysgraphia_probability
      }
    } else {
      error.value = response.data.message || 'Unable to upload handwriting sample.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to upload sample. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    uploading.value = false
  }
}

function normalizePercent(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  const cleanedValue = String(value).replace('%', '').trim()
  const numberValue = Number(cleanedValue)

  if (Number.isNaN(numberValue)) {
    return null
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

  const numberValue = Number(String(value).replace('%', '').trim())

  if (Number.isNaN(numberValue)) {
    return 'N/A'
  }

  return `${Number(numberValue.toFixed(2))}%`
}

function formatFileSize(size) {
  if (!size) {
    return 'N/A'
  }

  const sizeInMb = size / (1024 * 1024)

  if (sizeInMb >= 1) {
    return `${sizeInMb.toFixed(2)} MB`
  }

  return `${(size / 1024).toFixed(1)} KB`
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'S'
}
</script>