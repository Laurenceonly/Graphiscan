<template>
  <AdminLayout title="Student Progress">
    <div class="compact-page admin-progress-page-clean">
      <div class="page-header compact-header">
        <div>
          <span>Progress Monitoring</span>
          <h1>Student Progress</h1>
          <p>Monitor student screening progress, probability trends, validation status, and follow-up needs.</p>
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
              <h2>Progress Records</h2>
              <p>{{ filteredStudents.length }} of {{ students.length }} student/s shown.</p>
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
            <div class="filter-chip-row">
              <button
                v-for="filter in trendFilters"
                :key="filter.value"
                class="filter-chip"
                :class="{ active: trendFilter === filter.value }"
                type="button"
                @click="trendFilter = filter.value"
              >
                {{ filter.label }}
                <strong>{{ filter.count }}</strong>
              </button>
            </div>

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
          >
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Student</th>
                  <th>Teacher</th>
                  <th>Parent</th>
                  <th>Latest Result</th>
                  <th>Probability</th>
                  <th>Screenings</th>
                  <th>Trend</th>
                  <th>Validation</th>
                  <th>Follow-up</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="(student, index) in filteredStudents" :key="student.student_id">
                  <td>{{ index + 1 }}</td>

                  <td>
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

                  <td>{{ student.teacher_name || 'N/A' }}</td>
                  <td>{{ student.parent_name || 'Not assigned' }}</td>

                  <td>
                    <span class="result-badge" :class="classificationClass(getClassification(student))">
                      {{ getClassification(student) }}
                    </span>
                  </td>

                  <td>
                    <div class="probability-cell">
                      <strong>{{ formatPercent(getProbability(student)) }}</strong>

                      <div class="mini-progress">
                        <div
                          class="mini-progress-fill"
                          :style="{ width: `${progressWidth(getProbability(student))}%` }"
                        ></div>
                      </div>
                    </div>
                  </td>

                  <td>
                    <strong>{{ getTotalScreenings(student) }}</strong>
                  </td>

                  <td>
                    <span class="result-badge" :class="trendClass(getTrend(student))">
                      {{ getTrend(student) }}
                    </span>

                    <small v-if="getProbabilityChange(student) !== null" class="table-subtext">
                      {{ signedChange(getProbabilityChange(student)) }} pts
                    </small>
                  </td>

                  <td>
                    <span class="result-badge" :class="validationClass(getValidationStatus(student))">
                      {{ getValidationStatus(student) }}
                    </span>
                  </td>

                  <td>
                    <span class="result-badge" :class="followUpClass(getFollowUpNeeded(student))">
                      {{ getFollowUpNeeded(student) }}
                    </span>
                  </td>

                  <td>
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
const trendFilter = ref('all')
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

const trendCounts = computed(() => {
  return {
    all: students.value.length,
    improving: countByTrend('improving'),
    needsAttention: countByTrend('needs attention'),
    noMajorChange: countByTrend('no major change'),
    notEnoughData: countByTrend('not enough data yet')
  }
})

const trendFilters = computed(() => {
  return [
    {
      label: 'All',
      value: 'all',
      count: trendCounts.value.all
    },
    {
      label: 'Improving',
      value: 'improving',
      count: trendCounts.value.improving
    },
    {
      label: 'Needs Attention',
      value: 'needs attention',
      count: trendCounts.value.needsAttention
    },
    {
      label: 'No Major Change',
      value: 'no major change',
      count: trendCounts.value.noMajorChange
    },
    {
      label: 'Not Enough Data',
      value: 'not enough data yet',
      count: trendCounts.value.notEnoughData
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
        getTrend(student),
        getValidationStatus(student),
        getFollowUpNeeded(student)
      ]
        .join(' ')
        .toLowerCase()

      const matchesSearch = !keyword || searchableText.includes(keyword)

      const matchesTrend =
        trendFilter.value === 'all' ||
        normalizeTrend(getTrend(student)) === trendFilter.value

      const matchesValidation =
        validationFilter.value === 'all' ||
        normalizeText(getValidationStatus(student)) === validationFilter.value

      return matchesSearch && matchesTrend && matchesValidation
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
      error.value = 'Unable to load student progress. Please refresh or log in again.'
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

function getProbability(student) {
  const latest = getLatestResult(student)

  return (
    student.latest_probability ??
    student.dysgraphia_probability ??
    latest.dysgraphia_probability ??
    null
  )
}

function getTotalScreenings(student) {
  return Number(student.total_screenings ?? student.screening_count ?? student.result_count ?? 0)
}

function getTrend(student) {
  return student.trend_label || student.progress_trend || 'Not enough data yet'
}

function getProbabilityChange(student) {
  if (student.probability_change === null || student.probability_change === undefined) {
    return null
  }

  return Number(student.probability_change)
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

function normalizeTrend(value) {
  const text = normalizeText(value)

  if (text.includes('improving')) return 'improving'
  if (text.includes('needs attention')) return 'needs attention'
  if (text.includes('no major change') || text.includes('stable')) return 'no major change'

  return 'not enough data yet'
}

function countByTrend(trend) {
  return students.value.filter((student) => {
    return normalizeTrend(getTrend(student)) === trend
  }).length
}

function countByValidation(status) {
  return students.value.filter((student) => {
    return normalizeText(getValidationStatus(student)) === status
  }).length
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
  const normalized = normalizePercent(value)

  if (normalized === null) {
    return 'N/A'
  }

  return `${normalized}%`
}

function progressWidth(value) {
  const normalized = normalizePercent(value)

  if (normalized === null) {
    return 0
  }

  return Math.max(0, Math.min(100, normalized))
}

function signedChange(value) {
  const numberValue = Number(value || 0)

  if (numberValue > 0) {
    return `+${numberValue}`
  }

  return String(numberValue)
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
  trendFilter.value = 'all'
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

function trendClass(trend) {
  const text = normalizeTrend(trend)

  if (text === 'improving') return 'success'
  if (text === 'needs attention') return 'danger'
  if (text === 'no major change') return 'warning'

  return 'secondary'
}

function followUpClass(value) {
  return normalizeText(value) === 'yes' ? 'danger' : 'success'
}
</script>