<template>
  <UserLayout title="Child Progress">
    <section class="student-progress-page student-progress-clean">
      <div class="student-progress-status">
        <p v-if="loading" class="mobile-muted">Loading child progress...</p>
        <p v-else-if="error" class="error-message">{{ error }}</p>
      </div>

      <section v-if="!loading && !error && student" class="student-progress-stack progress-stack-clean">
        <section class="progress-hero-card progress-hero-clean">
          <div>
            <span>Child Progress</span>
            <h2>{{ student.fullname }}</h2>
            <p>Track high potential probability trend, screening history, validation status, and follow-up needs.</p>
          </div>

          <div class="progress-hero-icon">
            <TrendingUp :size="28" :stroke-width="1.9" />
          </div>
        </section>

        <section class="progress-student-card progress-card-clean">
          <div class="progress-section-head">
            <span>Student Profile</span>
            <h3>Basic Information</h3>
          </div>

          <div class="progress-info-grid progress-info-grid-clean">
            <div>
              <small>Age</small>
              <strong>{{ student.age || 'N/A' }}</strong>
            </div>

            <div>
              <small>Grade Level</small>
              <strong>{{ student.grade_level || 'N/A' }}</strong>
            </div>

            <div>
              <small>Parent / Guardian</small>
              <strong>{{ student.parent_name || 'Not assigned' }}</strong>
            </div>

            <div>
              <small>Total Screenings</small>
              <strong>{{ summary.total_screenings || 0 }}</strong>
            </div>
          </div>
        </section>

        <section class="progress-summary-grid progress-summary-clean">
          <div class="progress-summary-card">
            <small>Latest Classification</small>
            <strong>{{ latestResult?.classification || 'No result yet' }}</strong>
          </div>

          <div class="progress-summary-card">
            <small>Latest Probability</small>
            <strong>{{ formatPercent(latestResult?.dysgraphia_probability) }}</strong>
          </div>

          <div class="progress-summary-card">
            <small>Progress Trend</small>
            <strong>{{ summary.trend_label || 'Not enough data yet' }}</strong>
          </div>
        </section>

        <section class="progress-chart-card progress-card-clean">
          <div class="progress-section-head">
            <span>Progress Graph</span>
            <h3>High Potential Probability Over Time</h3>
          </div>

          <div v-if="progress.length >= 1" class="progress-chart-wrap progress-chart-wrap-clean">
            <Line :data="chartData" :options="chartOptions" />
          </div>

          <div v-else class="mobile-empty-state compact">
            <div>
              <LineChart :size="28" :stroke-width="1.8" />
            </div>

            <h3>No graph data yet</h3>
            <p>Upload at least one handwriting sample to start progress monitoring.</p>
          </div>
        </section>

        <section class="progress-interpretation-card progress-interpretation-clean">
          <div class="progress-interpretation-icon">
            <BrainCircuit :size="22" :stroke-width="1.9" />
          </div>

          <div>
            <strong>Progress Interpretation</strong>
            <p>{{ progressInterpretation }}</p>
          </div>
        </section>

        <section class="progress-timeline-card progress-card-clean">
          <div class="progress-section-head">
            <span>Screening Timeline</span>
            <h3>Previous Screening Records</h3>
          </div>

          <div v-if="progress.length > 0" class="progress-timeline-list progress-timeline-list-clean">
            <article
              v-for="(item, index) in progress"
              :key="item.result_id"
              class="progress-timeline-item progress-timeline-item-clean"
            >
              <div class="timeline-number">{{ index + 1 }}</div>

              <div class="timeline-content">
                <div class="timeline-top timeline-top-clean">
                  <div>
                    <h4>{{ item.classification || 'Screening Result' }}</h4>
                    <p>{{ item.date_generated || 'No date available' }}</p>
                  </div>

                  <span class="mobile-badge" :class="validationClass(item.validation_status)">
                    {{ formatValidationStatus(item.validation_status) }}
                  </span>
                </div>

                <div class="timeline-metrics timeline-metrics-clean">
                  <div>
                    <small>Probability</small>
                    <strong>{{ formatPercent(item.dysgraphia_probability) }}</strong>
                  </div>

                  <div>
                    <small>Follow-up</small>
                    <strong>{{ item.follow_up_needed || 'No' }}</strong>
                  </div>
                </div>

                <div class="timeline-note">
                  <small>Expert Remarks</small>
                  <p>{{ item.remarks || 'No remarks yet.' }}</p>
                </div>

                <div class="timeline-note">
                  <small>Expert Recommendation</small>
                  <p>{{ item.expert_recommendation || 'No expert recommendation yet.' }}</p>
                </div>

                <RouterLink
                  class="timeline-view-btn timeline-view-clean"
                  :to="`/teacher/results/${item.result_id}`"
                >
                  View Full Result
                </RouterLink>
              </div>
            </article>
          </div>

          <div v-else class="mobile-empty-state compact">
            <div>
              <FileQuestion :size="28" :stroke-width="1.8" />
            </div>

            <h3>No screenings yet</h3>
            <p>This child has no recorded handwriting screening results yet.</p>
          </div>
        </section>

        <RouterLink class="progress-back-link progress-back-clean" to="/teacher/students">
          <ArrowLeft :size="17" :stroke-width="2" />
          Back to Students
        </RouterLink>
      </section>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  ArrowLeft,
  BrainCircuit,
  FileQuestion,
  LineChart,
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
import UserLayout from '../../layouts/UserLayout.vue'
import userApi from '../../api/userApi'

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
  return summary.value.latest_result || null
})

const chartData = computed(() => {
  return {
    labels: progress.value.map((item, index) => {
      return item.date_generated || `Screening ${index + 1}`
    }),
    datasets: [
      {
        label: 'High Potential Probability',
        data: progress.value.map((item) => normalizePercent(item.dysgraphia_probability)),
        borderColor: '#2f80b9',
        backgroundColor: 'rgba(47, 128, 185, 0.12)',
        pointBackgroundColor: '#2f80b9',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 4,
        borderWidth: 3,
        tension: 0.25,
        fill: true
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
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
    return 'No screening result has been recorded yet. Upload a handwriting sample to begin progress monitoring.'
  }

  if (progress.value.length === 1) {
    return 'Only one screening result is available. More screenings are needed to identify a clear progress trend.'
  }

  const change = Number(summary.value.probability_change || 0)

  if (change < 0) {
    return `High potential probability decreased by ${Math.abs(change)} points from the first to the latest screening. Continue monitoring and follow expert guidance.`
  }

  if (change > 0) {
    return `High Potential probability increased by ${change} points from the first to the latest screening. Follow-up monitoring may be needed.`
  }

  return 'High Potential probability shows no major change across screenings. Continue regular monitoring.'
})

onMounted(() => {
  loadProgress()
})

async function loadProgress() {
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.get(`/teacher/students/${route.params.id}/progress`)

    if (response.data.success) {
      student.value = response.data.student
      summary.value = response.data.summary || {}
      progress.value = response.data.progress || []
    } else {
      error.value = response.data.message || 'Unable to load child progress.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to load child progress. Please refresh or log in again.'
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

  return Number(numberValue.toFixed(2))
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  return `${normalizePercent(value)}%`
}

function validationClass(status) {
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'success'
  if (text === 'flagged') return 'danger'

  return 'secondary'
}

function formatValidationStatus(status) {
  const text = String(status || '').toLowerCase()

  if (text === 'validated') return 'Validated'
  if (text === 'flagged') return 'Flagged'

  return 'Pending'
}
</script>