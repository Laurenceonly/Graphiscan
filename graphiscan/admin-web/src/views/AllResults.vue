<template>
  <AdminLayout>
    <div class="compact-page screening-results-page">
      <div class="page-header compact-header">
        <div>
          <h1>Screening Results</h1>
          <p>View handwriting screening results and validation status.</p>
        </div>
      </div>

      <section class="user-summary-grid">
        <article
          v-for="item in resultStatCards"
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
            <h2>Records</h2>
            <p>Showing {{ filteredResults.length }} of {{ results.length }}</p>
          </div>

          <div class="table-toolbar">
            <button
              v-for="filter in validationFilters"
              :key="filter.value"
              type="button"
              class="filter-chip"
              :class="{ active: selectedValidation === filter.value }"
              @click="setValidationFilter(filter.value)"
            >
              <component :is="filter.icon" :size="15" :stroke-width="1.8" />
              <span>{{ filter.label }}</span>
              <strong>{{ filter.count }}</strong>
            </button>

            <div class="search-field">
              <Search :size="16" :stroke-width="1.8" />
              <input
                v-model="search"
                type="text"
                placeholder="Search results"
              />
            </div>
          </div>
        </div>

        <p v-if="loading" class="muted-message">Loading screening results...</p>
        <p v-if="error" class="error-message">{{ error }}</p>

        <div
          v-if="!loading && !error && filteredResults.length > 0"
          class="table-wrapper compact-table-scroll admin-results-table"
          role="region"
          aria-label="Screening results"
          tabindex="0"
        >
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Teacher</th>
                <th>Classification</th>
                <th>Predicted-class score</th>
                <th>Validation</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="result in filteredResults" :key="result.result_id">
                <td data-label="Student">
                  <div class="user-cell">
                    <div class="user-avatar">
                      {{ getInitial(result.student_name) }}
                    </div>

                    <div>
                      <strong>{{ result.student_name || 'Unknown Student' }}</strong>
                      <small class="table-subtext">{{ result.grade_level || 'Grade not set' }}</small>
                    </div>
                  </div>
                </td>

                <td data-label="Teacher">{{ result.teacher_name || 'N/A' }}</td>

                <td data-label="Classification">
                  <span class="result-badge" :class="classificationClass(result.classification)">
                    {{ result.classification || 'N/A' }}
                  </span>
                </td>

                <td data-label="Predicted-class score">
                  <div class="confidence-cell">
                    <strong>{{ formatPercent(result.confidence_score) }}</strong>
                  </div>
                </td>

                <td data-label="Validation">
                  <span class="result-badge" :class="validationClass(result.validation_status)">
                    {{ result.validation_status || 'Pending' }}
                  </span>
                </td>

                <td data-label="Date">{{ result.date_generated || 'N/A' }}</td>

                <td data-label="Action">
                  <RouterLink
                    class="small-action-btn"
                    :to="`/admin/results/${result.result_id}`"
                  >
                    <Eye :size="14" :stroke-width="1.9" />
                    View
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="!loading && !error && filteredResults.length === 0" class="clean-empty-state">
          <FileX :size="34" :stroke-width="1.7" />
          <h3>No screening results found</h3>
          <p>Try adjusting your search keyword or validation filter.</p>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  CheckCircle2,
  Clock3,
  Eye,
  FileText,
  FileX,
  Flag,
  Search
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const search = ref('')
const results = ref([])
const loading = ref(true)
const error = ref('')

const selectedValidation = computed(() => {
  return route.query.validation || 'All'
})

const totalCounts = computed(() => {
  return {
    all: results.value.length,
    pending: countByValidation('Pending'),
    validated: countByValidation('Validated'),
    flagged: countByValidation('Flagged')
  }
})

const resultStatCards = computed(() => {
  return [
    {
      label: 'Total Results',
      value: totalCounts.value.all,
      icon: FileText,
      tone: ''
    },
    {
      label: 'Pending Review',
      value: totalCounts.value.pending,
      icon: Clock3,
      tone: 'warning'
    },
    {
      label: 'Validated Results',
      value: totalCounts.value.validated,
      icon: CheckCircle2,
      tone: 'success'
    },
    {
      label: 'Flagged Results',
      value: totalCounts.value.flagged,
      icon: Flag,
      tone: 'danger'
    }
  ]
})

const validationFilters = computed(() => [
  {
    label: 'All',
    value: 'All',
    icon: FileText,
    count: totalCounts.value.all
  },
  {
    label: 'Pending',
    value: 'Pending',
    icon: Clock3,
    count: totalCounts.value.pending
  },
  {
    label: 'Validated',
    value: 'Validated',
    icon: CheckCircle2,
    count: totalCounts.value.validated
  },
  {
    label: 'Flagged',
    value: 'Flagged',
    icon: Flag,
    count: totalCounts.value.flagged
  }
])

const filteredResults = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  const validation = selectedValidation.value

  return results.value.filter((result) => {
    const status = normalizeValidationStatus(result.validation_status)

    const matchesValidation =
      validation === 'All' || status === validation

    const matchesSearch =
      String(result.student_name || '').toLowerCase().includes(keyword) ||
      String(result.grade_level || '').toLowerCase().includes(keyword) ||
      String(result.teacher_name || '').toLowerCase().includes(keyword) ||
      String(result.parent_name || '').toLowerCase().includes(keyword) ||
      String(result.classification || '').toLowerCase().includes(keyword) ||
      String(result.validation_status || '').toLowerCase().includes(keyword) ||
      String(result.date_generated || '').toLowerCase().includes(keyword)

    return matchesValidation && matchesSearch
  })
})

onMounted(() => {
  loadResults()
})

async function loadResults() {
  loading.value = true
  error.value = ''

  try {
    const response = await adminApi.get('/results')

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      error.value = response.data.message || 'Unable to load screening results.'
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Unable to connect. Check your connection and try again.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function setValidationFilter(value) {
  if (value === 'All') {
    router.push('/admin/results')
    return
  }

  router.push({
    path: '/admin/results',
    query: {
      validation: value
    }
  })
}

function countByValidation(status) {
  return results.value.filter((result) => {
    return normalizeValidationStatus(result.validation_status) === status
  }).length
}

function normalizeValidationStatus(status) {
  if (status === 'Validated') return 'Validated'
  if (status === 'Flagged') return 'Flagged'
  return 'Pending'
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

function normalizePercent(value) {
  if (value === null || value === undefined || value === '') {
    return 0
  }

  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return 0
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

  return `${normalizePercent(value)}%`
}

function classificationClass(classification) {
  const text = String(classification || '').trim().toLowerCase()

  if (text.includes('high potential') || text.includes('potential dysgraphia')) {
    return 'danger'
  }

  if (text.includes('normal')) {
    return 'success'
  }

  return 'secondary'
}

function validationClass(status) {
  if (status === 'Validated') return 'success'
  if (status === 'Flagged') return 'danger'
  return 'secondary'
}
</script>
