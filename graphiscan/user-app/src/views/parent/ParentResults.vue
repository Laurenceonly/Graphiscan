<template>
  <UserLayout title="Child Results">
    <section class="parent-results-page parent-results-clean">
      <section class="parent-results-hero parent-results-hero-clean">
        <div class="parent-results-hero-copy">
          <span>Screening Records</span>
          <h2>Child Results</h2>
          <p>View screening reports, validation status, teacher details, and expert remarks.</p>
        </div>

        <div class="parent-results-hero-icon">
          <FileText :size="28" :stroke-width="1.9" />
        </div>
      </section>

      <section class="parent-results-overview parent-results-stats-clean">
        <article class="parent-results-card parent-results-stat-card-clean">
          <div class="parent-results-icon">
            <FileText :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Reviewed Results</span>
            <strong>{{ loading ? '...' : results.length }}</strong>
          </div>
        </article>

        <article class="parent-results-card parent-results-stat-card-clean">
          <div class="parent-results-icon">
            <UsersRound :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Children With Reports</span>
            <strong>{{ loading ? '...' : childrenWithReports }}</strong>
          </div>
        </article>

        <article class="parent-results-card parent-results-stat-card-clean">
          <div class="parent-results-icon success">
            <ClipboardList :size="20" :stroke-width="2" />
          </div>

          <div>
            <span>Follow-up Needed</span>
            <strong>{{ loading ? '...' : followUpCount }}</strong>
          </div>
        </article>
      </section>

      <section class="parent-results-panel parent-results-panel-clean">
        <div class="parent-results-head parent-results-head-clean">
          <div>
            <span>Report Directory</span>
            <h3>Screening Reports</h3>
            <p>Showing {{ filteredResults.length }} of {{ results.length }}</p>
          </div>

          <button
            class="parent-refresh-btn parent-refresh-clean"
            type="button"
            :disabled="loading"
            @click="loadResults"
          >
            <RefreshCw :size="15" :stroke-width="2" />
          </button>
        </div>

        <div class="parent-search-box parent-search-clean">
          <Search :size="17" :stroke-width="2" />

          <input
            v-model="search"
            type="text"
            placeholder="Search reports"
          />
        </div>

        <div v-if="loading || error" class="parent-results-status-area">
          <p v-if="loading" class="mobile-muted">Loading child results...</p>
          <p v-else-if="error" class="error-message">{{ error }}</p>
        </div>

        <section
          v-if="!loading && !error && filteredResults.length > 0"
          class="parent-result-list parent-result-list-clean"
        >
          <article
            v-for="result in filteredResults"
            :key="result.result_id"
            class="parent-result-card parent-result-card-clean"
          >
            <div class="parent-result-top parent-result-top-clean">
              <div class="student-avatar">
                {{ getInitial(result.student_name) }}
              </div>

              <div class="parent-result-main parent-result-main-clean">
                <h3>{{ result.student_name || 'Unknown Student' }}</h3>
                <p>
                  {{ result.grade_level || 'Grade not set' }}
                  ·
                  Teacher: {{ result.teacher_name || 'N/A' }}
                </p>
              </div>
            </div>

            <div class="result-badge-row parent-result-badge-row-clean">
              <span class="mobile-badge" :class="classificationClass(result.classification)">
                {{ result.classification || 'No classification' }}
              </span>

              <span class="mobile-badge" :class="validationClass(result.validation_status)">
                {{ formatValidationStatus(result.validation_status) }}
              </span>
            </div>

            <div class="parent-result-details parent-result-details-clean screening-result-meta">
              <div>
                <span>Model score</span>
                <strong>{{ formatPercent(result.confidence_score) }}</strong>
              </div>

              <div>
                <span>Screened on</span>
                <strong>{{ result.date_generated || 'N/A' }}</strong>
              </div>
            </div>

            <div class="parent-remarks-box">
              <span>Expert Remarks</span>
              <p>{{ result.remarks || 'No remarks yet.' }}</p>
            </div>

            <div class="parent-result-actions parent-result-actions-clean">
              <RouterLink
                v-if="result.student_id"
                class="parent-progress-btn parent-progress-clean"
                :to="`/parent/students/${result.student_id}/progress`"
              >
                <TrendingUp :size="16" :stroke-width="2" />
                Progress
              </RouterLink>

              <RouterLink
                class="parent-view-btn parent-view-clean"
                :to="`/parent/results/${result.result_id}`"
              >
                <Eye :size="16" :stroke-width="2" />
                Details
              </RouterLink>
            </div>
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
          <p>Try another keyword or filter.</p>
        </section>

        <section
          v-if="!loading && !error && results.length === 0"
          class="mobile-empty-state compact"
        >
          <div>
            <FileQuestion :size="28" :stroke-width="1.8" />
          </div>

          <h3>No results yet</h3>
          <p>Expert-reviewed results connected to your child will appear here.</p>
        </section>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ClipboardList,
  Eye,
  FileQuestion,
  FileText,
  RefreshCw,
  Search,
  TrendingUp,
  UsersRound
} from 'lucide-vue-next'
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

const search = ref('')
const results = ref([])
const loading = ref(true)
const error = ref('')

onMounted(() => {
  loadResults()
})

async function loadResults() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get('/parent/results')

    if (response.data.success) {
      results.value = response.data.results || []
    } else {
      results.value = []
      error.value = response.data.message || 'Unable to load child results.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load child results. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

const childrenWithReports = computed(() => {
  return new Set(results.value.map((result) => result.student_id)).size
})

const followUpCount = computed(() => {
  return results.value.filter((result) => normalizeText(result.follow_up_needed) === 'yes').length
})

const filteredResults = computed(() => {
  const keyword = search.value.toLowerCase().trim()

  return results.value
    .filter((result) => {
      const matchesSearch =
        !keyword ||
        String(result.student_name || '').toLowerCase().includes(keyword) ||
        String(result.grade_level || '').toLowerCase().includes(keyword) ||
        String(result.teacher_name || '').toLowerCase().includes(keyword) ||
        String(result.classification || '').toLowerCase().includes(keyword) ||
        String(result.validation_status || '').toLowerCase().includes(keyword) ||
        String(result.confidence_score || '').toLowerCase().includes(keyword) ||
        String(result.date_generated || '').toLowerCase().includes(keyword)

      return matchesSearch
    })
    .sort((a, b) => {
      return getDateValue(b.date_generated) - getDateValue(a.date_generated)
    })
})

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
