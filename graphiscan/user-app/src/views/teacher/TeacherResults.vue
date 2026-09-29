<template>
  <UserLayout title="Results">
    <section class="teacher-results-page teacher-results-clean">
      <section class="results-hero-card results-hero-clean">
        <div>
          <span>Screening Records</span>
          <h2>Result History</h2>
          <p>View each screening result and its expert review status.</p>
        </div>

        <div class="results-hero-icon">
          <FileText :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="results-overview-grid results-stats-clean">
        <div class="results-overview-card results-stat-card-clean">
          <div class="results-overview-icon">
            <FileText :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Total Results</span>
            <strong>{{ loading ? '...' : results.length }}</strong>
          </div>
        </div>

        <div class="results-overview-card results-stat-card-clean">
          <div class="results-overview-icon" :class="{ warning: pendingResults > 0 }">
            <Clock3 :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Pending Review</span>
            <strong>{{ loading ? '...' : pendingResults }}</strong>
          </div>
        </div>
      </section>

      <section class="results-list-panel results-list-clean">
        <div class="results-panel-head results-panel-head-clean">
          <div>
            <span>Directory</span>
            <h3>Screening Results</h3>
            <p>Showing {{ filteredResults.length }} of {{ results.length }}</p>
          </div>

          <button
            class="results-refresh-btn results-refresh-clean"
            type="button"
            :disabled="loading"
            @click="loadResults"
          >
            <RefreshCw :size="15" :stroke-width="2" />
          </button>
        </div>

        <div class="results-search-box results-search-clean">
          <Search :size="17" :stroke-width="2" />

          <input
            v-model="search"
            type="text"
            placeholder="Search results"
          />
        </div>

        <div v-if="results.length > 0" class="filter-row results-filter-row-clean">
          <button
            v-for="filter in filters"
            :key="filter.value"
            class="filter-pill results-filter-pill-clean"
            :class="{ active: activeFilter === filter.value }"
            type="button"
            @click="activeFilter = filter.value"
          >
            {{ filter.label }}
            <strong>{{ filter.count }}</strong>
          </button>
        </div>

        <div class="results-status-area">
          <p v-if="loading" class="mobile-muted">Loading results...</p>
          <p v-else-if="error" class="error-message">{{ error }}</p>
        </div>

        <section
          v-if="!loading && !error && filteredResults.length > 0"
          class="modern-results-list results-modern-list-clean"
        >
          <article
            v-for="result in filteredResults"
            :key="result.result_id"
            class="modern-result-card result-card-clean"
          >
            <div class="modern-result-top result-card-top-clean">
              <div class="student-avatar">
                {{ getInitial(result.student_name) }}
              </div>

              <div class="modern-result-main result-main-clean">
                <h3>{{ result.student_name || 'Unknown Student' }}</h3>
                <p>{{ result.grade_level || 'Grade not set' }}</p>
              </div>
            </div>

            <div class="result-badge-row result-badge-row-clean">
              <span class="mobile-badge" :class="getClassificationClass(result.classification)">
                {{ result.classification || 'No classification' }}
              </span>

              <span class="mobile-badge" :class="getValidationClass(result.validation_status)">
                {{ formatValidationStatus(result.validation_status) }}
              </span>
            </div>

            <div class="modern-result-details result-details-clean screening-result-meta">
              <div>
                <span>Model score</span>
                <strong>{{ formatPercent(result.confidence_score) }}</strong>
              </div>

              <div>
                <span>Screened on</span>
                <strong>{{ result.date_generated || 'N/A' }}</strong>
              </div>
            </div>

            <RouterLink
              class="result-view-btn result-view-clean"
              :to="`/teacher/results/${result.result_id}`"
            >
              View Details
            </RouterLink>
          </article>
        </section>

        <section
          v-if="!loading && !error && results.length > 0 && filteredResults.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <Search :size="26" :stroke-width="1.8" />
          </div>

          <h3>No matching results</h3>
          <p>Try another student name, classification, status, or date.</p>
        </section>

        <section
          v-if="!loading && !error && results.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <FileQuestion :size="28" :stroke-width="1.8" />
          </div>

          <h3>No screening results yet</h3>
          <p>Upload a handwriting sample first. Generated results will appear here.</p>

          <RouterLink class="mobile-empty-link" to="/teacher/upload">
            Upload New Sample
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
  Clock3,
  FileQuestion,
  FileText,
  RefreshCw,
  Search
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const search = ref('')
const activeFilter = ref('all')
const results = ref([])
const loading = ref(true)
const error = ref('')

const filters = computed(() => {
  return [
    {
      label: 'All',
      value: 'all',
      count: results.value.length
    },
    {
      label: 'Pending',
      value: 'pending',
      count: countByValidation('pending')
    },
    {
      label: 'Validated',
      value: 'validated',
      count: countByValidation('validated')
    },
    {
      label: 'Flagged',
      value: 'flagged',
      count: countByValidation('flagged')
    },
    {
  label: 'High Potential',
  value: 'high_potential',
  count: highPotentialResults.value
}
  ]
})

onMounted(() => {
  loadResults()
})

async function loadResults() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get('/teacher/results')

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      error.value = response.data.message || 'Unable to load results.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load results. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

const pendingResults = computed(() => {
  return results.value.filter((result) => {
    const status = normalizeText(result.validation_status)
    return !status || status === 'pending'
  }).length
})

const highPotentialResults = computed(() => {
  return results.value.filter((result) => isHighPotentialResult(result)).length
})

const filteredResults = computed(() => {
  const keyword = search.value.toLowerCase().trim()

  return results.value
    .filter((result) => {
      const validationStatus = normalizeText(result.validation_status || 'pending')

      const matchesSearch =
        !keyword ||
        String(result.student_name || '').toLowerCase().includes(keyword) ||
        String(result.grade_level || '').toLowerCase().includes(keyword) ||
        String(result.classification || '').toLowerCase().includes(keyword) ||
        String(result.validation_status || '').toLowerCase().includes(keyword) ||
        String(result.confidence_score || '').toLowerCase().includes(keyword) ||
        String(result.date_generated || '').toLowerCase().includes(keyword)

      const matchesFilter =
        activeFilter.value === 'all' ||
        validationStatus === activeFilter.value ||
        (activeFilter.value === 'high_potential' && isHighPotentialResult(result))

      return matchesSearch && matchesFilter
    })
    .sort((a, b) => {
      return getDateValue(b.date_generated) - getDateValue(a.date_generated)
    })
})

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function countByValidation(status) {
  return results.value.filter((result) => {
    const validationStatus = normalizeText(result.validation_status || 'pending')
    return validationStatus === status
  }).length
}

function isHighPotentialResult(result) {
  const classification = normalizeText(result.classification)

  return (
    classification.includes('high potential') ||
    classification.includes('potential dysgraphia')
  )
}

function getDateValue(value) {
  const dateValue = new Date(value).getTime()

  if (Number.isNaN(dateValue)) {
    return 0
  }

  return dateValue
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

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'R'
}

function getClassificationClass(classification) {
  const text = normalizeText(classification)

  if (text.includes('high potential') || text.includes('potential dysgraphia')) {
    return 'danger'
  }

  if (text.includes('normal')) {
    return 'success'
  }

  return 'secondary'
}

function getValidationClass(status) {
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
</script>
