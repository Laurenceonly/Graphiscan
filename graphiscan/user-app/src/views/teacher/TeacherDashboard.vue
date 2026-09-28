<template>
  <UserLayout title="Teacher Dashboard">
    <section class="teacher-dashboard-stack teacher-dashboard-clean">
      <section class="teacher-hero-card teacher-hero-clean">
        <div class="teacher-hero-copy">
          <span>Teacher Workspace</span>
          <h2>Welcome, {{ firstName }}</h2>
          <p>Manage students, upload handwriting samples, and review screening progress.</p>
        </div>

        <div class="teacher-hero-icon">
          <PenLine :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <p v-if="loading" class="mobile-muted">Loading dashboard...</p>
      <p v-if="error" class="error-message">{{ error }}</p>

      <section class="teacher-stats-grid-clean">
        <RouterLink
          v-for="item in statCards"
          :key="item.label"
          class="teacher-stat-card-clean"
          :to="item.to"
        >
          <div class="teacher-stat-icon-clean" :class="item.tone">
            <component :is="item.icon" :size="21" :stroke-width="1.9" />
          </div>

          <div>
            <span>{{ item.label }}</span>
            <strong>{{ loading ? '...' : item.value }}</strong>
          </div>
        </RouterLink>
      </section>

      <section class="teacher-action-panel-clean">
        <div class="teacher-panel-head-clean">
          <div>
            <span>Quick Actions</span>
            <h3>Teacher Tools</h3>
          </div>

          <button class="teacher-refresh-btn-clean" type="button" @click="loadDashboardData">
            <RefreshCw :size="16" :stroke-width="1.9" />
          </button>
        </div>

        <div class="teacher-action-list-clean">
          <RouterLink class="teacher-action-card-clean" to="/teacher/students">
            <div class="teacher-action-icon-clean">
              <UsersRound :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Students</strong>
              <p>View and add student records.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>

          <RouterLink class="teacher-action-card-clean" to="/teacher/upload">
            <div class="teacher-action-icon-clean">
              <UploadCloud :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Upload Sample</strong>
              <p>Submit handwriting for screening.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>

          <RouterLink class="teacher-action-card-clean" to="/teacher/results">
            <div class="teacher-action-icon-clean">
              <FileText :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <strong>Results</strong>
              <p>Review screening and validation records.</p>
            </div>

            <ChevronRight :size="18" :stroke-width="1.9" />
          </RouterLink>
        </div>
      </section>

      <section class="teacher-note-card teacher-note-clean">
        <div class="teacher-note-icon">
          <ClipboardCheck :size="22" :stroke-width="1.9" />
        </div>

        <div>
          <strong>Reminder</strong>
          <p>Use clear handwriting images and check student details before upload.</p>
        </div>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertTriangle,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  FileText,
  PenLine,
  RefreshCw,
  UploadCloud,
  UsersRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const students = ref([])
const results = ref([])
const loading = ref(true)
const error = ref('')

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

const userData = getStoredUserData()

const firstName = computed(() => {
  const fullname = userData.fullname || 'Teacher'
  return fullname.split(' ')[0]
})

const totalStudents = computed(() => {
  return students.value.length
})

const totalScreenings = computed(() => {
  return results.value.length
})

const pendingValidations = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.validation_status) === 'pending' ||
      !result.validation_status
  }).length
})

const followUpNeeded = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.follow_up_needed) === 'yes'
  }).length
})

const statCards = computed(() => {
  return [
    {
      label: 'Students',
      value: totalStudents.value,
      icon: UsersRound,
      to: '/teacher/students',
      tone: ''
    },
    {
      label: 'Screenings',
      value: totalScreenings.value,
      icon: FileText,
      to: '/teacher/results',
      tone: ''
    },
    {
      label: 'Pending Reviews',
      value: pendingValidations.value,
      icon: Clock3,
      to: '/teacher/results',
      tone: pendingValidations.value > 0 ? 'warning' : 'success'
    },
    {
      label: 'Follow-up Needed',
      value: followUpNeeded.value,
      icon: AlertTriangle,
      to: '/teacher/results',
      tone: followUpNeeded.value > 0 ? 'danger' : 'success'
    }
  ]
})

onMounted(() => {
  loadDashboardData()
})

async function loadDashboardData() {
  loading.value = true
  error.value = ''

  try {
    const [studentResponse, resultResponse] = await Promise.allSettled([
      userApi.get('/teacher/students'),
      userApi.get('/teacher/results')
    ])

    if (studentResponse.status === 'fulfilled' && studentResponse.value.data.success) {
      students.value = studentResponse.value.data.students || []
    } else {
      students.value = []
    }

    if (resultResponse.status === 'fulfilled' && resultResponse.value.data.success) {
      results.value = resultResponse.value.data.results || []
    } else {
      results.value = []
    }

    if (studentResponse.status === 'rejected' && resultResponse.status === 'rejected') {
      error.value = 'Unable to load dashboard data.'
    }
  } catch (err) {
    error.value = 'Unable to load dashboard data.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}
</script>