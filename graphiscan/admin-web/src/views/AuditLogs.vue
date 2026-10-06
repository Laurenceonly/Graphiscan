<template>
  <AdminLayout>
    <div class="compact-page audit-logs-page">
      <div class="page-header compact-header">
        <div>
          <h1>System Logs</h1>
          <p>Review user activity, account actions, access records, and system events.</p>
        </div>
      </div>

      <section class="user-summary-grid audit-summary-grid">
        <article
          v-for="item in auditStatCards"
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
            <h2>Recorded Activities</h2>
            <p>{{ filteredLogs.length }} of {{ logs.length }} activities shown.</p>
          </div>

          <div class="user-toolbar">
            <button class="soft-action-btn" type="button" @click="loadAuditLogs">
              <RefreshCw :size="15" :stroke-width="1.8" />
              Refresh
            </button>

            <div class="search-field">
              <Search :size="16" :stroke-width="1.8" />
              <input
                v-model="search"
                type="text"
                placeholder="Search logs"
              />
            </div>
          </div>
        </div>

        <div class="audit-filter-panel-clean">
          <div class="filter-chip-row">
            <button
              v-for="filter in categoryFilters"
              :key="filter.value"
              class="filter-chip"
              :class="{ active: categoryFilter === filter.value }"
              type="button"
              @click="categoryFilter = filter.value"
            >
              {{ filter.label }}
              <strong>{{ filter.count }}</strong>
            </button>
          </div>

          <div class="user-filter-controls">
            <select v-model="roleFilter" class="user-filter-select">
              <option value="all">All roles</option>
              <option value="admin">Administrators</option>
              <option value="teacher">Teachers</option>
              <option value="parent">Parents</option>
              <option value="expert">Experts</option>
              <option value="guest">Guests</option>
              <option value="unknown">Unknown</option>
            </select>

            <button class="clear-filter-btn" type="button" @click="clearFilters">
              <FilterX :size="15" :stroke-width="1.8" />
              Clear filters
            </button>
          </div>
        </div>

        <p v-if="loading" class="muted-message">Loading audit logs...</p>
        <p v-if="error" class="error-message">{{ error }}</p>

        <div
          v-if="!loading && !error && filteredLogs.length > 0"
          class="table-wrapper compact-table-scroll audit-logs-table"
          role="region"
          aria-label="Audit logs"
          tabindex="0"
        >
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Category</th>
                <th>Action</th>
                <th>Date / Time</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="(log, index) in filteredLogs"
                :key="log.log_id || `${index}-${log.log_date}`"
              >
                <td data-label="User">
                  <div class="user-cell">
                    <div class="user-avatar">
                      {{ getInitial(log.fullname || log.email) }}
                    </div>

                    <div>
                      <strong>{{ log.fullname || 'Unknown User' }}</strong>
                      <small class="table-subtext">{{ log.email || 'No email available' }}</small>
                    </div>
                  </div>
                </td>

                <td data-label="Role">
                  <span class="role-badge" :class="log.role || 'unknown'">
                    {{ formatRole(log.role) }}
                  </span>
                </td>

                <td data-label="Category">
                  <span
                    class="action-category-badge"
                    :class="getLogCategory(log.action)"
                  >
                    {{ formatCategory(getLogCategory(log.action)) }}
                  </span>
                </td>

                <td data-label="Action">
                  <span class="audit-action-text">
                    {{ log.action || 'N/A' }}
                  </span>
                </td>

                <td data-label="Date / Time">{{ log.log_date || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="!loading && !error && filteredLogs.length === 0" class="clean-empty-state">
          <FileText :size="34" :stroke-width="1.7" />
          <h3>No audit logs found</h3>
          <p>Try another search keyword or filter.</p>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  AlertTriangle,
  FileText,
  FilterX,
  History,
  RefreshCw,
  Search,
  ShieldCheck,
  UserCog
} from 'lucide-vue-next'

const search = ref('')
const categoryFilter = ref('all')
const roleFilter = ref('all')

const logs = ref([])
const loading = ref(true)
const error = ref('')

onMounted(() => {
  loadAuditLogs()
})

async function loadAuditLogs() {
  loading.value = true
  error.value = ''

  try {
    const response = await adminApi.get('/audit-logs')

    if (response.data.success) {
      logs.value = response.data.logs || []
    } else {
      error.value = response.data.message || 'Unable to load audit logs.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to connect. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}

const auditStats = computed(() => {
  return {
    total: logs.value.length,
    access: countByCategory('login'),
    accounts: countByCategory('accounts'),
    critical: logs.value.filter((log) => isCriticalCategory(getLogCategory(log.action))).length
  }
})

const auditStatCards = computed(() => {
  return [
    {
      label: 'Total Logs',
      value: auditStats.value.total,
      icon: History,
      tone: ''
    },
    {
      label: 'Access Events',
      value: auditStats.value.access,
      icon: ShieldCheck,
      tone: 'success'
    },
    {
      label: 'Account Changes',
      value: auditStats.value.accounts,
      icon: UserCog,
      tone: ''
    },
    {
      label: 'Critical Actions',
      value: auditStats.value.critical,
      icon: AlertTriangle,
      tone: auditStats.value.critical > 0 ? 'danger' : 'success'
    }
  ]
})

const categoryFilters = computed(() => {
  return [
    {
      label: 'All',
      value: 'all',
      count: logs.value.length
    },
    {
      label: 'Access',
      value: 'login',
      count: countByCategory('login')
    },
    {
      label: 'Accounts',
      value: 'accounts',
      count: countByCategory('accounts')
    },
    {
      label: 'Students',
      value: 'students',
      count: countByCategory('students')
    },
    {
      label: 'Screening',
      value: 'screening',
      count: countByCategory('uploads') + countByCategory('results')
    },
    {
      label: 'Validation',
      value: 'validations',
      count: countByCategory('validations')
    },
    {
      label: 'Critical',
      value: 'critical',
      count: logs.value.filter((log) => isCriticalCategory(getLogCategory(log.action))).length
    },
    {
      label: 'Other',
      value: 'other',
      count: countByCategory('other') + countByCategory('guardian')
    }
  ]
})

const filteredLogs = computed(() => {
  const keyword = search.value.toLowerCase().trim()

  return logs.value
    .filter((log) => {
      const logCategory = getLogCategory(log.action)
      const logRole = String(log.role || 'unknown').toLowerCase()

      const searchableText = [
        log.fullname,
        log.email,
        log.role,
        log.action,
        log.log_date,
        formatCategory(logCategory)
      ]
        .join(' ')
        .toLowerCase()

      const matchesSearch = !keyword || searchableText.includes(keyword)
      const matchesCategory = matchesCategoryFilter(logCategory)
      const matchesRole = roleFilter.value === 'all' || logRole === roleFilter.value

      return matchesSearch && matchesCategory && matchesRole
    })
    .sort((a, b) => {
      return getTimeValue(b.log_date) - getTimeValue(a.log_date)
    })
})

function matchesCategoryFilter(category) {
  if (categoryFilter.value === 'all') {
    return true
  }

  if (categoryFilter.value === 'critical') {
    return isCriticalCategory(category)
  }

  if (categoryFilter.value === 'screening') {
    return category === 'uploads' || category === 'results'
  }

  if (categoryFilter.value === 'other') {
    return category === 'other' || category === 'guardian'
  }

  return category === categoryFilter.value
}

function countByCategory(category) {
  return logs.value.filter((log) => {
    return getLogCategory(log.action) === category
  }).length
}

function isCriticalCategory(category) {
  return category === 'delete' || category === 'password'
}

function clearFilters() {
  search.value = ''
  categoryFilter.value = 'all'
  roleFilter.value = 'all'
}

function displayNumber(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function getTimeValue(value) {
  const dateValue = new Date(value).getTime()

  if (Number.isNaN(dateValue)) {
    return 0
  }

  return dateValue
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'U'
}

function formatRole(role) {
  if (role === 'admin') return 'Administrator'
  if (role === 'teacher') return 'Teacher'
  if (role === 'parent') return 'Parent'
  if (role === 'expert') return 'Expert / SPED'
  if (role === 'guest') return 'Guest'
  return 'Unknown'
}

function getLogCategory(action) {
  const text = String(action || '').toLowerCase()

  if (text.includes('delete') || text.includes('permanent delete')) {
    return 'delete'
  }

  if (text.includes('password') || text.includes('reset')) {
    return 'password'
  }

  if (text.includes('login') || text.includes('logged in') || text.includes('logged out') || text.includes('logout')) {
    return 'login'
  }

  if (
    text.includes('account') ||
    text.includes('approved') ||
    text.includes('rejected') ||
    text.includes('disabled') ||
    text.includes('restored') ||
    text.includes('registered')
  ) {
    return 'accounts'
  }

  if (text.includes('guardian') || text.includes('linked guardian') || text.includes('removed guardian')) {
    return 'guardian'
  }

  if (text.includes('validation') || text.includes('validated') || text.includes('flagged')) {
    return 'validations'
  }

  if (text.includes('upload') || text.includes('handwriting sample')) {
    return 'uploads'
  }

  if (text.includes('result') || text.includes('screening')) {
    return 'results'
  }

  if (text.includes('student')) {
    return 'students'
  }

  return 'other'
}

function formatCategory(category) {
  if (category === 'login') return 'Access'
  if (category === 'accounts') return 'Accounts'
  if (category === 'students') return 'Students'
  if (category === 'uploads') return 'Uploads'
  if (category === 'results') return 'Results'
  if (category === 'validations') return 'Validations'
  if (category === 'password') return 'Password'
  if (category === 'delete') return 'Delete'
  if (category === 'guardian') return 'Guardian'
  return 'Other'
}
</script>
