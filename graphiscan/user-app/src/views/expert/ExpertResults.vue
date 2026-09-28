<template>
  <UserLayout title="Validation Queue">
    <section class="expert-results-page expert-results-clean">
      <section class="expert-results-hero expert-results-hero-clean">
        <div class="expert-results-hero-copy">
          <span>Expert Review</span>
          <h2>Validation Queue</h2>
          <p>Review AI screening records, confidence scores, probability, and validation status.</p>
        </div>

        <div class="expert-results-hero-icon">
          <ClipboardCheck :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="expert-queue-overview expert-queue-stats-clean">
        <article class="expert-queue-card expert-queue-card-clean">
          <div class="expert-queue-icon warning">
            <Clock3 :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Pending</span>
            <strong>{{ loading ? '...' : pendingCount }}</strong>
          </div>
        </article>

        <article class="expert-queue-card expert-queue-card-clean">
          <div class="expert-queue-icon success">
            <CheckCircle2 :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Validated</span>
            <strong>{{ loading ? '...' : validatedCount }}</strong>
          </div>
        </article>

        <article class="expert-queue-card expert-queue-card-clean">
          <div class="expert-queue-icon danger">
            <Flag :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Flagged</span>
            <strong>{{ loading ? '...' : flaggedCount }}</strong>
          </div>
        </article>
      </section>

      <section class="expert-queue-panel expert-queue-panel-clean">
        <div class="expert-queue-head expert-queue-head-clean">
          <div>
            <span>Review Directory</span>
            <h3>Screening Records</h3>
            <p>{{ filteredResults.length }} of {{ results.length }} record/s shown.</p>
          </div>

          <button
            class="expert-refresh-btn expert-refresh-clean"
            type="button"
            :disabled="loading"
            @click="loadResults"
          >
            <RefreshCw :size="15" :stroke-width="2" />
          </button>
        </div>

        <div class="expert-search-box expert-search-clean">
          <Search :size="17" :stroke-width="2" />

          <input
            v-model="search"
            type="text"
            placeholder="Search records"
          />
        </div>

        <div v-if="results.length > 0" class="filter-row expert-filter-row-clean">
          <button
            v-for="filter in filters"
            :key="filter.value"
            type="button"
            class="filter-pill expert-filter-pill-clean"
            :class="{ active: selectedFilter === filter.value }"
            @click="selectedFilter = filter.value"
          >
            {{ filter.label }}
            <strong>{{ filter.count }}</strong>
          </button>
        </div>

        <div v-if="loading || error" class="expert-results-status-area">
          <p v-if="loading" class="mobile-muted">Loading validation queue...</p>
          <p v-else-if="error" class="error-message">{{ error }}</p>
        </div>

        <section
          v-if="!loading && !error && filteredResults.length > 0"
          class="expert-result-list expert-result-list-clean"
        >
          <article
            v-for="result in filteredResults"
            :key="result.result_id"
            class="expert-result-card expert-result-card-clean"
          >
            <div class="expert-result-top expert-result-top-clean">
              <div class="student-avatar">
                {{ getInitial(result.student_name) }}
              </div>

              <div class="expert-result-main expert-result-main-clean">
                <h3>{{ result.student_name || 'Unknown Student' }}</h3>
                <p>
                  {{ result.grade_level || 'Grade not set' }}
                  ·
                  Teacher: {{ result.teacher_name || 'N/A' }}
                </p>
              </div>
            </div>

            <div class="result-badge-row expert-result-badge-row-clean">
              <span class="mobile-badge" :class="classificationClass(result.classification)">
                {{ result.classification || 'No classification' }}
              </span>

              <span class="mobile-badge" :class="validationClass(result.validation_status)">
                {{ formatValidationStatus(result.validation_status) }}
              </span>
            </div>

            <div class="expert-result-details expert-result-details-clean">
              <div>
                <span>Probability</span>
                <strong>{{ formatPercent(result.dysgraphia_probability) }}</strong>
              </div>

              <div>
                <span>Confidence</span>
                <strong>{{ formatPercent(result.confidence_score) }}</strong>
              </div>

              <div>
                <span>Date Generated</span>
                <strong>{{ result.date_generated || 'N/A' }}</strong>
              </div>
            </div>

            <RouterLink
              class="expert-review-btn expert-review-clean"
              :to="`/expert/validate/${result.result_id}`"
            >
              <ClipboardCheck :size="16" :stroke-width="2" />
              Review Result
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

          <h3>No matching records</h3>
          <p>Try another keyword or filter.</p>
        </section>

        <section
          v-if="!loading && !error && results.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <ClipboardCheck :size="28" :stroke-width="1.8" />
          </div>

          <h3>No records found</h3>
          <p>Screening results waiting for expert validation will appear here.</p>
        </section>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Flag,
  RefreshCw,
  Search
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const search = ref('')
const selectedFilter = ref('pending')
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
      count: pendingCount.value
    },
    {
      label: 'Validated',
      value: 'validated',
      count: validatedCount.value
    },
    {
      label: 'Flagged',
      value: 'flagged',
      count: flaggedCount.value
    }
  ]
})

const pendingCount = computed(() => {
  return results.value.filter((result) => {
    const status = normalizeText(result.validation_status || 'pending')
    return status === 'pending' || !status
  }).length
})

const validatedCount = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.validation_status) === 'validated'
  }).length
})

const flaggedCount = computed(() => {
  return results.value.filter((result) => {
    return normalizeText(result.validation_status) === 'flagged'
  }).length
})

const filteredResults = computed(() => {
  const keyword = search.value.toLowerCase().trim()

  return results.value
    .filter((result) => {
      const status = normalizeText(result.validation_status || 'pending')

      const matchesFilter =
        selectedFilter.value === 'all' || status === selectedFilter.value

      const matchesSearch =
        !keyword ||
        String(result.student_name || '').toLowerCase().includes(keyword) ||
        String(result.grade_level || '').toLowerCase().includes(keyword) ||
        String(result.teacher_name || '').toLowerCase().includes(keyword) ||
        String(result.classification || '').toLowerCase().includes(keyword) ||
        String(result.validation_status || '').toLowerCase().includes(keyword) ||
        String(result.dysgraphia_probability || '').toLowerCase().includes(keyword) ||
        String(result.confidence_score || '').toLowerCase().includes(keyword) ||
        String(result.date_generated || '').toLowerCase().includes(keyword)

      return matchesFilter && matchesSearch
    })
    .sort((a, b) => {
      return getStatusWeight(a.validation_status) - getStatusWeight(b.validation_status) ||
        getDateValue(b.date_generated) - getDateValue(a.date_generated)
    })
})

onMounted(() => {
  loadResults()
})

async function loadResults() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get('/expert/results', {
      timeout: 15000
    })

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      results.value = []
      error.value = response.data.message || 'Unable to load validation queue.'
    }
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      error.value = 'Loading took too long. Please check if Flask is running, then refresh.'
    } else if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load validation queue. Please refresh or log in again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
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

function getStatusWeight(status) {
  const text = normalizeText(status || 'pending')

  if (text === 'pending') return 1
  if (text === 'flagged') return 2
  if (text === 'validated') return 3

  return 4
}

function getDateValue(value) {
  const dateValue = new Date(value).getTime()

  if (Number.isNaN(dateValue)) {
    return 0
  }

  return dateValue
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'S'
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