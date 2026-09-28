<template>
  <AdminLayout title="Student Progress">
    <div class="compact-page admin-progress-detail-clean-page">
      <div class="page-header compact-header">
        <div>
          <span>Individual Progress</span>
          <h1>{{ student?.fullname || 'Student Progress' }}</h1>
          <p>Review screening history, probability trend, validation records, and follow-up status.</p>
        </div>

        <RouterLink class="small-action-btn admin-back-btn" to="/admin/progress">
  <ArrowLeft :size="16" :stroke-width="2" />
  Back to Progress
</RouterLink>
      </div>

      <p v-if="loading" class="muted-message">Loading student progress...</p>
      <p v-if="error" class="error-message">{{ error }}</p>

      <template v-if="!loading && !error && student">
        <section class="user-summary-grid admin-progress-summary-grid-clean">
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
              <strong>{{ item.value }}</strong>
            </div>
          </article>
        </section>

        <section class="admin-progress-main-grid">
          <section class="panel-card admin-progress-profile-panel">
            <div class="admin-progress-panel-head">
              <div>
                <span>Student Profile</span>
                <h2>Screening Context</h2>
              </div>
            </div>

            <div class="admin-progress-info-list">
              <div>
                <span>Age</span>
                <strong>{{ student.age || 'N/A' }}</strong>
              </div>

              <div>
                <span>Grade Level</span>
                <strong>{{ student.grade_level || 'N/A' }}</strong>
              </div>

              <div>
                <span>Teacher</span>
                <strong>{{ student.teacher_name || 'N/A' }}</strong>
              </div>

              <div>
                <span>Parent / Guardian</span>
                <strong>{{ student.parent_name || 'Not assigned' }}</strong>
              </div>
            </div>
          </section>

          <section class="panel-card admin-progress-interpret-panel">
            <div class="admin-progress-interpret-head">
              <div class="admin-progress-interpret-icon">
                <BrainCircuit :size="22" :stroke-width="1.9" />
              </div>

              <div>
                <span>Interpretation Guide</span>
                <h2>Progress Reading</h2>
              </div>
            </div>

            <p>{{ progressInterpretation }}</p>
          </section>
        </section>

        <section class="panel-card admin-progress-chart-panel">
          <div class="admin-progress-panel-head split-head">
            <div>
              <span>Progress Graph</span>
              <h2>Dysgraphia Probability Over Time</h2>
            </div>

            <span class="result-badge" :class="trendClass">
              {{ summary.trend_label || 'Not enough data yet' }}
            </span>
          </div>

          <div v-if="progress.length >= 1" class="admin-progress-chart-wrap-clean">
            <Line :data="chartData" :options="chartOptions" />
          </div>

          <div v-else class="clean-empty-state">
            <LineChart :size="30" :stroke-width="1.8" />
            <h3>No graph data yet</h3>
            <p>No screening records are available for this student yet.</p>
          </div>
        </section>

        <section class="panel-card admin-progress-timeline-panel">
          <div class="admin-progress-panel-head split-head">
            <div>
              <span>Screening Timeline</span>
              <h2>Screening and Validation History</h2>
            </div>

            <small class="admin-progress-record-count">
              {{ progress.length }} record/s
            </small>
          </div>

          <div v-if="progress.length > 0" class="admin-progress-timeline-list-clean">
            <article
              v-for="(item, index) in progress"
              :key="item.result_id"
              class="admin-progress-timeline-item-clean"
            >
              <div class="admin-progress-timeline-number">
                {{ index + 1 }}
              </div>

              <div class="admin-progress-timeline-content-clean">
                <div class="admin-progress-timeline-top-clean">
                  <div>
                    <h3>{{ item.classification || 'Screening Result' }}</h3>
                    <p>{{ item.date_generated || 'No date available' }}</p>
                  </div>

                  <span class="result-badge" :class="validationClass(item.validation_status)">
                    {{ item.validation_status || 'Pending' }}
                  </span>
                </div>

                <div class="admin-progress-timeline-metrics-clean">
                  <div>
                    <span>Probability</span>
                    <strong>{{ formatPercent(item.dysgraphia_probability) }}</strong>
                  </div>

                  <div>
                    <span>Follow-up</span>
                    <strong :class="followUpClass(item.follow_up_needed)">
                      {{ item.follow_up_needed || 'No' }}
                    </strong>
                  </div>

                  <div>
                    <span>Expert Reviewer</span>
                    <strong>{{ item.expert_name || 'Not yet reviewed' }}</strong>
                  </div>
                </div>

                <div class="admin-progress-note-grid">
                  <div>
                    <span>Expert Remarks</span>
                    <p>{{ item.remarks || 'No remarks yet.' }}</p>
                  </div>

                  <div>
                    <span>Expert Recommendation</span>
                    <p>{{ item.expert_recommendation || 'No expert recommendation yet.' }}</p>
                  </div>
                </div>

                <RouterLink
                  class="small-action-btn admin-progress-result-link"
                  :to="`/admin/results/${item.result_id}`"
                >
                  <Eye :size="15" :stroke-width="2" />
                  View Result
                </RouterLink>
              </div>
            </article>
          </div>

          <div v-else class="clean-empty-state">
            <FileQuestion :size="30" :stroke-width="1.8" />
            <h3>No screenings yet</h3>
            <p>This student has no recorded handwriting screening results yet.</p>
          </div>
        </section>
      </template>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  AlertTriangle,
  ArrowLeft,
  BrainCircuit,
  Eye,
  FileQuestion,
  LineChart,
  ListChecks,
  Percent,
  TrendingUp
} from 'lucide-vue-next'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import AdminLayout from '../layouts/AdminLayout.vue'
import adminApi from '../api/adminApi'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
)

const route = useRoute()

const student = ref(null)
const summary = ref({})
const progress = ref([])
const loading = ref(true)
const error = ref('')

const latestResult = computed(() => {
  return summary.value.latest_result || progress.value[progress.value.length - 1] || null
})

const progressStatCards = computed(() => {
  return [
    {
      label: 'Total Screenings',
      value: displayValue(summary.value.total_screenings || progress.value.length || 0),
      icon: ListChecks,
      tone: ''
    },
    {
      label: 'Latest Probability',
      value: formatPercent(latestResult.value?.dysgraphia_probability),
      icon: Percent,
      tone: probabilityTone(latestResult.value?.dysgraphia_probability)
    },
    {
      label: 'Progress Trend',
      value: summary.value.trend_label || 'Not enough data',
      icon: TrendingUp,
      tone: trendTone.value
    },
    {
      label: 'Follow-up Needed',
      value: latestResult.value?.follow_up_needed || 'No',
      icon: AlertTriangle,
      tone: followUpTone.value
    }
  ]
})

const trendTone = computed(() => {
  const text = String(summary.value.trend_label || '').toLowerCase()

  if (text.includes('improving')) return 'success'
  if (text.includes('increasing') || text.includes('declining')) return 'danger'
  if (text.includes('stable')) return 'warning'

  return ''
})

const trendClass = computed(() => {
  if (trendTone.value === 'success') return 'success'
  if (trendTone.value === 'danger') return 'danger'
  if (trendTone.value === 'warning') return 'warning'

  return 'secondary'
})

const followUpTone = computed(() => {
  return String(latestResult.value?.follow_up_needed || '').toLowerCase() === 'yes'
    ? 'danger'
    : 'success'
})

const chartData = computed(() => {
  return {
    labels: progress.value.map((item, index) => {
      return item.date_generated || `Screening ${index + 1}`
    }),
    datasets: [
      {
        label: 'Dysgraphia Probability',
        data: progress.value.map((item) => normalizePercent(item.dysgraphia_probability)),
        borderColor: '#2f80b9',
        backgroundColor: 'rgba(47, 128, 185, 0.1)',
        pointBackgroundColor: '#2f80b9',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 3,
        tension: 0.38,
        fill: true
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        usePointStyle: true,
        boxWidth: 8,
        boxHeight: 8,
        padding: 18,
        color: '#475467',
        font: {
          family: 'Inter',
          size: 12,
          weight: '500'
        }
      }
    },
    tooltip: {
      backgroundColor: '#1f2a37',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      padding: 12,
      cornerRadius: 12,
      displayColors: true,
      callbacks: {
        label(context) {
          return `${context.dataset.label}: ${context.raw}%`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#667085',
        maxRotation: 0,
        autoSkip: true,
        font: {
          family: 'Inter',
          size: 11
        }
      }
    },
    y: {
      beginAtZero: true,
      suggestedMax: 100,
      grid: {
        color: 'rgba(102, 112, 133, 0.12)'
      },
      ticks: {
        color: '#667085',
        callback(value) {
          return `${value}%`
        },
        font: {
          family: 'Inter',
          size: 11
        }
      }
    }
  }
}

const progressInterpretation = computed(() => {
  if (!progress.value.length) {
    return 'No screening result has been recorded yet. Progress monitoring will appear after a handwriting sample is screened.'
  }

  if (progress.value.length === 1) {
    return 'Only one screening result is available. More records are needed to identify whether the probability is improving, stable, or increasing.'
  }

  const change = Number(summary.value.probability_change || 0)

  if (change < 0) {
    return `The dysgraphia probability decreased by ${Math.abs(change)} points from the first to the latest screening. This may indicate improvement, with expert review still needed for context.`
  }

  if (change > 0) {
    return `The dysgraphia probability increased by ${change} points from the first to the latest screening. This may require closer monitoring or follow-up support.`
  }

  return 'The dysgraphia probability shows no major change across screenings. Continued monitoring may be recommended.'
})

onMounted(() => {
  loadProgress()
})

async function loadProgress() {
  loading.value = true
  error.value = ''

  try {
    const response = await adminApi.get(`/students/${route.params.id}/progress`)

    if (response.data.success) {
      student.value = response.data.student
      summary.value = response.data.summary || {}
      progress.value = response.data.progress || []
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

function normalizePercent(value) {
  if (value === null || value === undefined || value === '') {
    return 0
  }

  const cleanedValue = String(value).replace('%', '').trim()
  const numberValue = Number(cleanedValue)

  if (Number.isNaN(numberValue)) {
    return 0
  }

  if (numberValue > 0 && numberValue <= 1) {
    return Number((numberValue * 100).toFixed(2))
  }

  return Math.min(100, Number(numberValue.toFixed(2)))
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  return `${normalizePercent(value)}%`
}

function displayValue(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function probabilityTone(value) {
  const percent = normalizePercent(value)

  if (!percent) return ''
  if (percent >= 70) return 'danger'
  if (percent >= 50) return 'warning'

  return 'success'
}

function followUpClass(value) {
  return String(value || '').toLowerCase() === 'yes'
    ? 'follow-up-yes'
    : 'follow-up-no'
}

function validationClass(status) {
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}
</script>