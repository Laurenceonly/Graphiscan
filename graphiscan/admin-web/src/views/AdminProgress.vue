<template>
  <AdminLayout>
    <div class="compact-page admin-progress-page-clean">
      <div class="page-header compact-header">
        <div>
          <h1>Student Progress</h1>
          <p>Review assessment history, expert decisions, and follow-up needs.</p>
        </div>
      </div>

      <p v-if="loading" class="muted-message">Loading student progress...</p>
      <p v-if="error" class="error-message">{{ error }}</p>

      <template v-if="!loading && !error">
        <section class="user-summary-grid admin-progress-stat-grid">
          <article
            v-for="item in progressStatCards"
            :key="item.label"
            class="user-summary-card"
          >
            <div class="user-summary-icon" :class="item.tone">
              <component :is="item.icon" :size="19" :stroke-width="1.9" />
            </div>

            <div>
              <span>{{ item.label }}</span>
              <strong>{{ displayNumber(item.value) }}</strong>
            </div>
          </article>
        </section>

        <div class="panel-card compact-panel">
          <div class="table-header compact-table-header">
            <div>
              <h2>Students</h2>
              <p>{{ filteredStudents.length }} of {{ students.length }} students shown.</p>
            </div>

            <div class="user-toolbar">
              <button class="soft-action-btn" type="button" @click="loadProgress">
                <RefreshCw :size="15" :stroke-width="1.8" />
                Refresh
              </button>

              <div class="search-field">
                <Search :size="16" :stroke-width="1.8" />
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Search progress"
                />
              </div>
            </div>
          </div>

          <div class="admin-progress-filter-panel">
            <div class="user-filter-controls">
              <select v-model="validationFilter" class="user-filter-select">
                <option value="all">All validations</option>
                <option value="pending">Pending ({{ validationCounts.pending }})</option>
                <option value="validated">Validated ({{ validationCounts.validated }})</option>
                <option value="flagged">Flagged ({{ validationCounts.flagged }})</option>
              </select>

              <button class="clear-filter-btn" type="button" @click="clearFilters">
                Clear filters
              </button>
            </div>
          </div>

          <div
            v-if="filteredStudents.length > 0"
            class="table-wrapper compact-table-scroll admin-progress-table"
            role="region"
            aria-label="Student progress"
            tabindex="0"
          >
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Teacher</th>
                  <th>Latest Result</th>
                  <th>Assessments</th>
                  <th>Validation</th>
                  <th>Follow-up</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="student in filteredStudents" :key="student.student_id">
                  <td data-label="Student">
                    <div class="user-cell">
                      <div class="user-avatar">
                        {{ getInitial(student.fullname || student.student_name) }}
                      </div>

                      <div>
                        <strong>{{ student.fullname || student.student_name || 'Unnamed Student' }}</strong>
                        <small class="table-subtext">
                          {{ student.grade_level || 'No grade level' }}
                          <template v-if="student.age"> · Age {{ student.age }}</template>
                        </small>
                      </div>
                    </div>
                  </td>

                  <td data-label="Teacher">{{ student.teacher_name || 'N/A' }}</td>
                  <td data-label="Latest Result">
                    <span class="result-badge" :class="classificationClass(getClassification(student))">
                      {{ getClassification(student) }}
                    </span>
                  </td>

                  <td data-label="Assessments">
                    <strong>{{ getTotalScreenings(student) }}</strong>
                  </td>

                  <td data-label="Validation">
                    <span class="result-badge" :class="validationClass(getValidationStatus(student))">
                      {{ getValidationStatus(student) }}
                    </span>
                  </td>

                  <td data-label="Follow-up">
                    <span class="result-badge" :class="followUpClass(getFollowUpNeeded(student))">
                      {{ getFollowUpNeeded(student) }}
                    </span>
                  </td>

                  <td data-label="Action">
                    <RouterLink
                      class="small-action-btn"
                      :to="`/admin/progress/${student.student_id}`"
                    >
                      <Eye :size="14" :stroke-width="1.9" />
                      View
                    </RouterLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="clean-empty-state">
            <FileQuestion :size="34" :stroke-width="1.7" />
            <h3>No progress records found</h3>
            <p>Try another search keyword or filter.</p>
          </div>
        </div>
      </template>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertCircle,
  ClipboardCheck,
  Eye,
  FileQuestion,
  FileText,
  RefreshCw,
  Search,
  Users
} from 'lucide-vue-next'
import AdminLayout from '../layouts/AdminLayout.vue'
import adminApi from '../api/adminApi'

const loading = ref(true)
const error = ref('')
const students = ref([])
const summary = ref({})

const searchQuery = ref('')
const validationFilter = ref('all')

const totalStudents = computed(() => {
  return Number(summary.value.total_students ?? students.value.length ?? 0)
})

const screenedStudents = computed(() => {
  const summaryCount = Number(
    summary.value.screened_students ||
    summary.value.total_screened_students ||
    0
  )

  if (summaryCount > 0) {
    return summaryCount
  }

  return students.value.filter((student) => getTotalScreenings(student) > 0).length
})

const totalScreenings = computed(() => {
  const summaryCount = Number(
    summary.value.total_screenings ||
    summary.value.total_results ||
    0
  )

  if (summaryCount > 0) {
    return summaryCount
  }

  return students.value.reduce((total, student) => {
    return total + getTotalScreenings(student)
  }, 0)
})

const followUpStudents = computed(() => {
  const summaryCount = Number(
    summary.value.follow_up_students ||
    summary.value.students_needing_follow_up ||
    0
  )

  if (summaryCount > 0) {
    return summaryCount
  }

  return students.value.filter((student) => {
    return normalizeText(getFollowUpNeeded(student)) === 'yes'
  }).length
})

const progressStatCards = computed(() => {
  return [
    {
      label: 'Total Students',
      value: totalStudents.value,
      icon: Users,
      tone: ''
    },
    {
      label: 'Screened Students',
      value: screenedStudents.value,
      icon: ClipboardCheck,
      tone: 'success'
    },
    {
      label: 'Total Screenings',
      value: totalScreenings.value,
      icon: FileText,
      tone: ''
    },
    {
      label: 'Follow-up Needed',
      value: followUpStudents.value,
      icon: AlertCircle,
      tone: followUpStudents.value > 0 ? 'danger' : 'success'
    }
  ]
})

const validationCounts = computed(() => {
  return {
    pending: countByValidation('pending'),
    validated: countByValidation('validated'),
    flagged: countByValidation('flagged')
  }
})

const filteredStudents = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()

  return students.value
    .filter((student) => {
      const searchableText = [
        student.fullname,
        student.student_name,
        student.grade_level,
        student.teacher_name,
        student.parent_name,
        getClassification(student),
        getValidationStatus(student),
        getFollowUpNeeded(student)
      ]
        .join(' ')
        .toLowerCase()

      const matchesSearch = !keyword || searchableText.includes(keyword)

      const matchesValidation =
        validationFilter.value === 'all' ||
        normalizeText(getValidationStatus(student)) === validationFilter.value

      return matchesSearch && matchesValidation
    })
    .sort((a, b) => {
      const followUpA = normalizeText(getFollowUpNeeded(a)) === 'yes' ? 1 : 0
      const followUpB = normalizeText(getFollowUpNeeded(b)) === 'yes' ? 1 : 0

      if (followUpA !== followUpB) {
        return followUpB - followUpA
      }

      return getTotalScreenings(b) - getTotalScreenings(a)
    })
})

onMounted(() => {
  loadProgress()
})

async function loadProgress() {
  loading.value = true
  error.value = ''

  try {
    const response = await adminApi.get('/students/progress')

    if (response.data.success) {
      students.value = response.data.students || response.data.progress || []
      summary.value = response.data.summary || {}
    } else {
      error.value = response.data.message || 'Unable to load student progress.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load student progress. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function getLatestResult(student) {
  return student.latest_result || student.latestResult || {}
}

function getClassification(student) {
  const latest = getLatestResult(student)

  return (
    student.latest_classification ||
    student.classification ||
    latest.classification ||
    'No result yet'
  )
}

function getTotalScreenings(student) {
  return Number(student.total_screenings ?? student.screening_count ?? student.result_count ?? 0)
}

function getValidationStatus(student) {
  const latest = getLatestResult(student)

  return (
    student.validation_status ||
    student.latest_validation_status ||
    latest.validation_status ||
    'Pending'
  )
}

function getFollowUpNeeded(student) {
  const latest = getLatestResult(student)

  return (
    student.follow_up_needed ||
    student.latest_follow_up_needed ||
    latest.follow_up_needed ||
    'No'
  )
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function countByValidation(status) {
  return students.value.filter((student) => {
    return normalizeText(getValidationStatus(student)) === status
  }).length
}

function displayNumber(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'S'
}

function clearFilters() {
  searchQuery.value = ''
  validationFilter.value = 'all'
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

  return 'secondary'
}

function followUpClass(value) {
  return normalizeText(value) === 'yes' ? 'danger' : 'success'
}
</script>
