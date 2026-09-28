<template>
  <UserLayout title="Add Student">
    <section class="teacher-add-student-page">
      <section class="add-student-hero-card">
        <div>
          <span>Student Registration</span>
          <h2>Add student profile</h2>
          <p>
            Create a student record under your teacher account and optionally
            link a parent or guardian.
          </p>
        </div>

        <div class="add-student-hero-icon">
          <UserPlus :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <form class="add-student-form-panel" @submit.prevent="addStudent">
        <div class="add-student-panel-head">
          <div>
            <span>Student Details</span>
            <h3>Basic information</h3>
          </div>

          <RouterLink class="add-student-secondary-btn" to="/teacher/students">
            <ArrowLeft :size="15" :stroke-width="2" />
            Students
          </RouterLink>
        </div>

        <div class="form-group">
          <label>Full Name</label>

          <div class="modern-input-wrap">
            <UserRound :size="18" :stroke-width="1.9" />

            <input
              v-model="fullname"
              type="text"
              placeholder="Enter student full name"
              autocomplete="off"
              required
            />
          </div>
        </div>

        <div class="add-student-two-grid">
          <div class="form-group">
            <label>Age</label>

            <div class="modern-input-wrap">
              <CalendarDays :size="18" :stroke-width="1.9" />

              <input
                v-model="age"
                type="number"
                min="1"
                max="30"
                placeholder="Age"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Grade Level</label>

            <div class="modern-input-wrap">
              <GraduationCap :size="18" :stroke-width="1.9" />

              <input
                v-model="gradeLevel"
                type="text"
                placeholder="Example: Grade 3"
                autocomplete="off"
                required
              />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Parent / Guardian</label>

          <div class="modern-select-wrap">
            <UsersRound :size="18" :stroke-width="1.9" />

            <select v-model="parentId">
              <option value="">Not assigned</option>
              <option
                v-for="parent in parents"
                :key="parent.user_id"
                :value="parent.user_id"
              >
                {{ parent.fullname }} — {{ parent.email }}
              </option>
            </select>
          </div>

          <p class="add-student-field-note">
            You can leave this blank and link a guardian later.
          </p>
        </div>

        <div v-if="selectedParent" class="selected-parent-card">
          <div class="selected-parent-icon">
            <UserRound :size="18" :stroke-width="1.9" />
          </div>

          <div>
            <strong>{{ selectedParent.fullname }}</strong>
            <small>{{ selectedParent.email }}</small>
          </div>
        </div>

        <p v-if="loadingParents" class="mobile-muted">Loading parent accounts...</p>
        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <button class="add-student-submit-btn" type="submit" :disabled="saving">
          <LoaderCircle v-if="saving" :size="17" :stroke-width="2" />
          <Save v-else :size="17" :stroke-width="2" />

          {{ saving ? 'Saving student...' : 'Save Student' }}
        </button>
      </form>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  ArrowLeft,
  CalendarDays,
  GraduationCap,
  LoaderCircle,
  Save,
  UserPlus,
  UserRound,
  UsersRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const router = useRouter()

const fullname = ref('')
const age = ref('')
const gradeLevel = ref('')
const parentId = ref('')

const parents = ref([])
const loadingParents = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

const selectedParent = computed(() => {
  return parents.value.find((parent) => {
    return String(parent.user_id) === String(parentId.value)
  })
})

onMounted(() => {
  loadParents()
})

async function loadParents() {
  loadingParents.value = true

  try {
    const response = await userApi.get('/teacher/parents')

    if (response.data.success) {
      parents.value = response.data.parents
    }
  } catch (err) {
    console.error(err)
  } finally {
    loadingParents.value = false
  }
}

function validateStudentForm() {
  const cleanFullname = fullname.value.trim()
  const cleanGradeLevel = gradeLevel.value.trim()
  const numericAge = Number(age.value)

  if (!cleanFullname || !age.value || !cleanGradeLevel) {
    return 'Please complete the required student fields.'
  }

  if (cleanFullname.length < 2) {
    return 'Student full name must be at least 2 characters.'
  }

  if (!Number.isFinite(numericAge) || numericAge < 1 || numericAge > 30) {
    return 'Please enter a valid student age.'
  }

  return ''
}

async function addStudent() {
  error.value = ''
  success.value = ''

  const validationMessage = validateStudentForm()

  if (validationMessage) {
    error.value = validationMessage
    return
  }

  saving.value = true

  try {
    const response = await userApi.post('/teacher/students/add', {
      fullname: fullname.value.trim(),
      age: age.value,
      grade_level: gradeLevel.value.trim(),
      parent_id: parentId.value
    })

    if (response.data.success) {
      success.value = response.data.message || 'Student added successfully.'

      setTimeout(() => {
        router.push('/teacher/students')
      }, 700)
    } else {
      error.value = response.data.message || 'Unable to add student.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to add student. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    saving.value = false
  }
}
</script>