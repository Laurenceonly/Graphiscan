<template>
  <UserLayout title="Students">
    <section class="teacher-students-page teacher-students-clean">
      <section class="students-header-card students-header-clean students-header-blue teacher-standard-hero">
  <div class="teacher-standard-hero-copy">
    <span>Student Records</span>
    <h2>My Students</h2>
    <p>Manage assigned students and prepare records for screening.</p>
  </div>

  <div class="teacher-standard-hero-side">
    <div class="teacher-standard-hero-icon">
      <UsersRound :size="28" :stroke-width="1.9" />
    </div>

    <RouterLink class="students-add-btn students-add-clean students-add-on-blue" to="/teacher/students/add">
      <UserPlus :size="17" :stroke-width="2" />
      Add Student
    </RouterLink>
  </div>
</section>
      <section class="students-stats-grid-clean">
        <article
          v-for="item in studentStatCards"
          :key="item.label"
          class="students-stat-card-clean"
        >
          <div class="students-stat-icon-clean" :class="item.tone">
            <component :is="item.icon" :size="20" :stroke-width="1.9" />
          </div>

          <div>
            <span>{{ item.label }}</span>
            <strong>{{ loading ? '...' : item.value }}</strong>
          </div>
        </article>
      </section>

      <section class="students-list-card students-list-clean">
        <div class="students-list-head students-list-head-clean">
          <div>
            <span>Directory</span>
            <h3>Student List</h3>
            <p>Showing {{ filteredStudents.length }} of {{ students.length }}</p>
          </div>

          <button
            class="students-refresh-btn students-refresh-clean"
            type="button"
            :disabled="loading"
            @click="loadStudents"
          >
            <RefreshCw :size="15" :stroke-width="2" />
          </button>
        </div>

        <div class="students-search-box students-search-clean">
          <Search :size="17" :stroke-width="2" />

          <input
            v-model="search"
            type="text"
            placeholder="Search students"
          />
        </div>

        <div class="students-filter-row-clean">
          <button
            v-for="filter in guardianFilters"
            :key="filter.value"
            class="students-filter-chip-clean"
            :class="{ active: guardianFilter === filter.value }"
            type="button"
            @click="guardianFilter = filter.value"
          >
            {{ filter.label }}
            <strong>{{ filter.count }}</strong>
          </button>
        </div>

        <div class="students-status-area">
          <p v-if="loading" class="mobile-muted">Loading students...</p>
          <p v-else-if="error" class="error-message">{{ error }}</p>
        </div>

        <section
          v-if="!loading && !error && filteredStudents.length > 0"
          class="modern-student-list students-modern-list-clean"
        >
          <article
            v-for="student in filteredStudents"
            :key="student.student_id"
            class="modern-student-card student-card-clean"
          >
            <div class="modern-student-top student-card-top-clean">
              <div class="student-avatar student-avatar-clean">
                {{ getInitial(student.fullname) }}
              </div>

              <div class="modern-student-main student-main-clean">
                <h3>{{ student.fullname || 'Unknown Student' }}</h3>
                <p>{{ student.grade_level || 'Grade not set' }}</p>
              </div>
            </div>

            <div class="modern-student-details student-details-clean">
              <div>
                <span>Age</span>
                <strong>{{ student.age || 'N/A' }}</strong>
              </div>

              <div>
                <span>Parent / Guardian</span>
                <strong>{{ displayGuardian(student) }}</strong>
              </div>

              <div>
                <span>Date Added</span>
                <strong>{{ student.created_at || 'N/A' }}</strong>
              </div>
            </div>

            <div class="student-card-actions student-actions-clean">
              <RouterLink
                class="student-progress-btn student-action-primary"
                :to="`/teacher/students/${student.student_id}/progress`"
              >
                <TrendingUp :size="16" :stroke-width="2" />
                Progress
              </RouterLink>

              <RouterLink
                class="student-upload-btn student-action-secondary"
                to="/teacher/upload"
              >
                <UploadCloud :size="16" :stroke-width="2" />
                Upload
              </RouterLink>
            </div>
          </article>
        </section>

        <section
          v-if="!loading && !error && students.length > 0 && filteredStudents.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <Search :size="26" :stroke-width="1.8" />
          </div>

          <h3>No matching students</h3>
          <p>Try another keyword or guardian filter.</p>
        </section>

        <section
          v-if="!loading && !error && students.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <UsersRound :size="28" :stroke-width="1.8" />
          </div>

          <h3>No students yet</h3>
          <p>Add your first student record to start screening.</p>

          <RouterLink class="mobile-empty-link" to="/teacher/students/add">
            Add Student
          </RouterLink>
        </section>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertCircle,
  RefreshCw,
  Search,
  TrendingUp,
  UploadCloud,
  UserPlus,
  UsersRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const search = ref('')
const guardianFilter = ref('all')
const students = ref([])
const loading = ref(true)
const error = ref('')

onMounted(() => {
  loadStudents()
})

async function loadStudents() {
  loading.value = true
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
      error.value = 'Unable to load students. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

const studentsWithGuardian = computed(() => {
  return students.value.filter((student) => hasGuardian(student)).length
})

const studentsWithoutGuardian = computed(() => {
  return students.value.length - studentsWithGuardian.value
})

const studentStatCards = computed(() => {
  return [
    {
      label: 'Total Students',
      value: students.value.length,
      icon: UsersRound,
      tone: ''
    },
    {
      label: 'No Guardian',
      value: studentsWithoutGuardian.value,
      icon: AlertCircle,
      tone: studentsWithoutGuardian.value > 0 ? 'warning' : 'success'
    }
  ]
})

const guardianFilters = computed(() => {
  return [
    {
      label: 'All',
      value: 'all',
      count: students.value.length
    },
    {
      label: 'With Guardian',
      value: 'with',
      count: studentsWithGuardian.value
    },
    {
      label: 'No Guardian',
      value: 'without',
      count: studentsWithoutGuardian.value
    }
  ]
})

const filteredStudents = computed(() => {
  const keyword = search.value.toLowerCase().trim()

  return students.value
    .filter((student) => {
      const matchesGuardian =
        guardianFilter.value === 'all' ||
        (guardianFilter.value === 'with' && hasGuardian(student)) ||
        (guardianFilter.value === 'without' && !hasGuardian(student))

      const matchesSearch =
        !keyword ||
        String(student.fullname || '').toLowerCase().includes(keyword) ||
        String(student.grade_level || '').toLowerCase().includes(keyword) ||
        String(student.parent_name || '').toLowerCase().includes(keyword) ||
        String(student.age || '').toLowerCase().includes(keyword) ||
        String(student.created_at || '').toLowerCase().includes(keyword)

      return matchesGuardian && matchesSearch
    })
    .sort((a, b) => {
      return String(a.fullname || '').localeCompare(String(b.fullname || ''))
    })
})

function hasGuardian(student) {
  const parentName = String(student.parent_name || '').trim().toLowerCase()

  return Boolean(
    parentName &&
    parentName !== 'not assigned' &&
    parentName !== 'n/a' &&
    parentName !== 'none'
  )
}

function displayGuardian(student) {
  return hasGuardian(student) ? student.parent_name : 'Not assigned'
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'S'
}
</script>
