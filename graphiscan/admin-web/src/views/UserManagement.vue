<template>
  <AdminLayout title="User Management">
    <div class="compact-page user-management-page">
      <div class="page-header compact-header">
        <div>
          <span>Accounts</span>
          <h1>Users</h1>
          <p>Manage users, roles, and account access.</p>
        </div>
      </div>

      <section class="user-summary-grid">
        <article
          v-for="item in userStatCards"
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
            <h2>System Users</h2>
            <p>Registered admin, teacher, parent, expert, and guest accounts.</p>
          </div>

          <div class="user-toolbar">
            <button class="primary-action-btn" type="button" @click="openAddModal">
              <Plus :size="16" :stroke-width="1.9" />
              Add User
            </button>

            <button class="soft-action-btn" type="button" @click="loadUsers">
              <RefreshCw :size="15" :stroke-width="1.8" />
              Refresh
            </button>

            <div class="search-field">
              <Search :size="16" :stroke-width="1.8" />
              <input
                v-model="search"
                type="text"
                placeholder="Search users"
              />
            </div>
          </div>
        </div>

        <div class="user-filter-panel">
          <div class="filter-chip-row">
            <button
              v-for="filter in statusFilters"
              :key="filter.value"
              class="filter-chip"
              :class="{ active: statusFilter === filter.value }"
              type="button"
              @click="statusFilter = filter.value"
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
            </select>

            <button class="clear-filter-btn" type="button" @click="clearFilters">
              Clear filters
            </button>
          </div>
        </div>

        <p v-if="loading" class="muted-message">Loading users...</p>
        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <div
          v-if="!loading && !error && filteredUsers.length > 0"
          class="table-wrapper compact-table-scroll admin-users-table"
        >
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Contact</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="(user, index) in filteredUsers" :key="user.user_id">
                <td>{{ index + 1 }}</td>

                <td>
                  <div class="user-cell">
                    <div class="user-avatar">
                      {{ getInitial(user.fullname) }}
                    </div>

                    <div>
                      <strong>{{ user.fullname || 'Unknown User' }}</strong>
                    </div>
                  </div>
                </td>

                <td>{{ user.email || 'N/A' }}</td>

                <td>
                  <span class="role-badge" :class="user.role || 'unknown'">
                    {{ formatRole(user.role) }}
                  </span>
                </td>

                <td>
                  <span class="status-badge" :class="getStatusClass(user.account_status)">
                    {{ formatStatus(user.account_status) }}
                  </span>
                </td>

                <td>{{ user.contact_no || 'N/A' }}</td>
                <td>{{ user.created_at || 'N/A' }}</td>

                <td>
                  <div class="table-actions user-action-stack">
                    <span v-if="isCurrentAdmin(user)" class="current-admin-pill">
                      Current Admin
                    </span>

                    <template v-else>
                      <button
                        v-if="getUserStatus(user) === 'pending'"
                        class="success-action-btn"
                        type="button"
                        :disabled="actionLoadingId === user.user_id"
                        @click="openStatusModal(user, 'approve')"
                      >
                        <CheckCircle :size="14" :stroke-width="1.9" />
                        Approve
                      </button>

                      <button
                        v-if="getUserStatus(user) === 'pending'"
                        class="warning-action-btn"
                        type="button"
                        :disabled="actionLoadingId === user.user_id"
                        @click="openStatusModal(user, 'reject')"
                      >
                        <XCircle :size="14" :stroke-width="1.9" />
                        Reject
                      </button>

                      <button
                        v-if="getUserStatus(user) === 'active'"
                        class="neutral-action-btn"
                        type="button"
                        :disabled="actionLoadingId === user.user_id"
                        @click="openStatusModal(user, 'disable')"
                      >
                        <Ban :size="14" :stroke-width="1.9" />
                        Disable
                      </button>

                      <button
                        v-if="getUserStatus(user) === 'disabled' || getUserStatus(user) === 'rejected'"
                        class="success-action-btn"
                        type="button"
                        :disabled="actionLoadingId === user.user_id"
                        @click="openStatusModal(user, 'restore')"
                      >
                        <RotateCcw :size="14" :stroke-width="1.9" />
                        Restore
                      </button>

                      <button
                        class="danger-action-btn"
                        type="button"
                        :disabled="actionLoadingId === user.user_id"
                        @click="openDeleteModal(user)"
                      >
                        <Trash2 :size="14" :stroke-width="1.9" />
                        Delete
                      </button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="!loading && !error && filteredUsers.length === 0" class="clean-empty-state">
          <Users :size="34" :stroke-width="1.7" />
          <h3>No users found</h3>
          <p>Try another search keyword or filter.</p>
        </div>
      </div>

      <div v-if="showAddModal" class="modal-backdrop">
        <section class="standard-modal">
          <div class="standard-modal-head">
            <div>
              <span>Create Account</span>
              <h2>Add user</h2>
              <p>Create an account and assign a role.</p>
            </div>

            <button class="modal-close-btn" type="button" @click="closeAddModal">
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <form class="admin-form-grid" @submit.prevent="createUser">
            <div class="form-group">
              <label>Full Name</label>
              <input
                v-model="newUser.fullname"
                type="text"
                placeholder="Enter full name"
              />
            </div>

            <div class="form-group">
              <label>Email Address</label>
              <input
                v-model="newUser.email"
                type="email"
                placeholder="Enter email address"
              />
            </div>

            <div class="form-group">
              <label>Role</label>
              <select v-model="newUser.role">
                <option value="">Select role</option>
                <option value="admin">Administrator</option>
                <option value="teacher">Teacher</option>
                <option value="parent">Parent / Guardian</option>
                <option value="expert">Expert / SPED</option>
                <option value="guest">Guest</option>
              </select>
            </div>

            <div class="form-group">
              <label>Contact Number</label>
              <input
                v-model="newUser.contact_no"
                type="text"
                placeholder="Optional contact number"
              />
            </div>

            <div class="form-group full-field">
              <label>Password</label>

              <div class="admin-password-input">
                <input
                  v-model="newUser.password"
                  :type="showAddPassword ? 'text' : 'password'"
                  placeholder="Create password"
                />

                <button type="button" @click="showAddPassword = !showAddPassword">
                  <EyeOff v-if="showAddPassword" :size="15" :stroke-width="1.8" />
                  <Eye v-else :size="15" :stroke-width="1.8" />
                  {{ showAddPassword ? 'Hide' : 'Show' }}
                </button>
              </div>

              <div class="admin-password-strength">
                <div class="strength-head">
                  <span>Password Strength</span>
                  <strong>{{ strengthLabel }}</strong>
                </div>

                <div class="strength-track">
                  <div
                    class="strength-fill"
                    :class="strengthClass"
                    :style="{ width: strengthWidth }"
                  ></div>
                </div>

                <ul class="password-rules">
                  <li :class="{ passed: passwordRules.length }">At least 8 characters</li>
                  <li :class="{ passed: passwordRules.uppercase }">One uppercase letter</li>
                  <li :class="{ passed: passwordRules.lowercase }">One lowercase letter</li>
                  <li :class="{ passed: passwordRules.number }">One number</li>
                  <li :class="{ passed: passwordRules.symbol }">One symbol</li>
                </ul>
              </div>
            </div>

            <div class="form-group full-field">
              <label>Confirm Password</label>

              <div class="admin-password-input">
                <input
                  v-model="newUser.confirm_password"
                  :type="showConfirmAddPassword ? 'text' : 'password'"
                  placeholder="Re-enter password"
                />

                <button type="button" @click="showConfirmAddPassword = !showConfirmAddPassword">
                  <EyeOff v-if="showConfirmAddPassword" :size="15" :stroke-width="1.8" />
                  <Eye v-else :size="15" :stroke-width="1.8" />
                  {{ showConfirmAddPassword ? 'Hide' : 'Show' }}
                </button>
              </div>

              <p
                v-if="newUser.confirm_password && newUser.password !== newUser.confirm_password"
                class="field-warning"
              >
                Passwords do not match.
              </p>
            </div>

            <p v-if="addError" class="error-message full-field">{{ addError }}</p>

            <div class="modal-actions full-field">
              <button class="cancel-btn" type="button" @click="closeAddModal">
                Cancel
              </button>

              <button class="primary-modal-btn" type="submit" :disabled="addLoading">
                {{ addLoading ? 'Creating...' : 'Create Account' }}
              </button>
            </div>
          </form>
        </section>
      </div>

      <div v-if="showStatusModal" class="modal-backdrop">
        <section class="standard-modal">
          <div class="standard-modal-head">
            <div>
              <span>{{ statusModalKicker }}</span>
              <h2>{{ statusModalTitle }}</h2>
              <p>{{ statusModalMessage }}</p>
            </div>

            <button
              class="modal-close-btn"
              type="button"
              :disabled="statusActionLoading"
              @click="closeStatusModal"
            >
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <div class="status-confirm-body">
            <div class="delete-target-card">
              <strong>{{ selectedStatusUser?.fullname || 'Unknown User' }}</strong>
              <small>{{ selectedStatusUser?.email || 'No email available' }}</small>
              <em>
                {{ formatRole(selectedStatusUser?.role) }}
                •
                {{ formatStatus(selectedStatusUser?.account_status) }}
              </em>
            </div>

            <div
              v-if="selectedStatusAction === 'reject' || selectedStatusAction === 'disable'"
              class="warning-box"
            >
              <ShieldAlert :size="18" :stroke-width="1.8" />
              <p>This account will lose access until restored or approved again.</p>
            </div>

            <p v-if="statusActionError" class="error-message">
              {{ statusActionError }}
            </p>

            <div class="modal-actions">
              <button
                class="cancel-btn"
                type="button"
                :disabled="statusActionLoading"
                @click="closeStatusModal"
              >
                Cancel
              </button>

              <button
                class="primary-modal-btn"
                type="button"
                :disabled="statusActionLoading"
                @click="confirmStatusAction"
              >
                {{ statusActionLoading ? 'Processing...' : statusModalButton }}
              </button>
            </div>
          </div>
        </section>
      </div>

      <div v-if="showDeleteModal" class="modal-backdrop">
        <section class="danger-modal">
          <div class="danger-modal-head">
            <div class="danger-icon">
              <AlertTriangle :size="26" :stroke-width="1.8" />
            </div>

            <button class="modal-close-btn" type="button" @click="closeDeleteModal">
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <div class="danger-modal-copy">
            <span>Permanent Delete</span>
            <h2>Delete user?</h2>

            <p>This action is permanent. Related records may be affected.</p>

            <div class="delete-target-card">
              <strong>{{ selectedUser?.fullname || 'Unknown User' }}</strong>
              <small>{{ selectedUser?.email || 'No email available' }}</small>
              <em>{{ formatRole(selectedUser?.role) }}</em>
            </div>

            <div class="warning-box">
              <ShieldAlert :size="18" :stroke-width="1.8" />
              <p>Continue only if you are sure this account should be removed.</p>
            </div>
          </div>

          <form class="delete-form" @submit.prevent="deleteUserPermanently">
            <div class="form-group">
              <label>Type DELETE to confirm</label>
              <input
                v-model="confirmationText"
                type="text"
                placeholder="DELETE"
                autocomplete="off"
              />
            </div>

            <div class="form-group">
              <label>Admin Password</label>
              <input
                v-model="adminPassword"
                type="password"
                placeholder="Enter admin password"
                autocomplete="current-password"
              />
            </div>

            <p v-if="deleteError" class="error-message">{{ deleteError }}</p>

            <div class="modal-actions">
              <button class="cancel-btn" type="button" @click="closeDeleteModal">
                Cancel
              </button>

              <button
                class="confirm-delete-btn"
                type="submit"
                :disabled="deleteLoading"
              >
                {{ deleteLoading ? 'Deleting...' : 'Delete Permanently' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  AlertTriangle,
  Ban,
  CheckCircle,
  Clock3,
  Eye,
  EyeOff,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  Trash2,
  UserCheck,
  UserX,
  Users,
  X,
  XCircle
} from 'lucide-vue-next'

const search = ref('')
const roleFilter = ref('all')
const statusFilter = ref('all')

const users = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const actionLoadingId = ref(null)

const showAddModal = ref(false)
const addLoading = ref(false)
const addError = ref('')
const showAddPassword = ref(false)
const showConfirmAddPassword = ref(false)

const newUser = reactive({
  fullname: '',
  email: '',
  role: '',
  contact_no: '',
  password: '',
  confirm_password: ''
})

const showStatusModal = ref(false)
const selectedStatusUser = ref(null)
const selectedStatusAction = ref('')
const statusActionLoading = ref(false)
const statusActionError = ref('')

const showDeleteModal = ref(false)
const selectedUser = ref(null)
const confirmationText = ref('')
const adminPassword = ref('')
const deleteLoading = ref(false)
const deleteError = ref('')

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const currentAdmin = getCurrentAdmin()
const currentAdminId = currentAdmin.user_id

onMounted(() => {
  loadUsers()
})

async function loadUsers(clearMessages = true) {
  loading.value = true

  if (clearMessages) {
    error.value = ''
    success.value = ''
  }

  try {
    const response = await adminApi.get('/users')

    if (response.data.success) {
      users.value = response.data.users || []
    } else {
      error.value = response.data.message || 'Unable to load users.'
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to connect to Flask API.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const userStats = computed(() => {
  return {
    total: users.value.length,
    active: users.value.filter((user) => getUserStatus(user) === 'active').length,
    pending: users.value.filter((user) => getUserStatus(user) === 'pending').length,
    disabled: users.value.filter((user) => getUserStatus(user) === 'disabled').length,
    rejected: users.value.filter((user) => getUserStatus(user) === 'rejected').length
  }
})

const userStatCards = computed(() => {
  return [
    {
      label: 'Total Users',
      value: userStats.value.total,
      icon: Users,
      tone: ''
    },
    {
      label: 'Active Accounts',
      value: userStats.value.active,
      icon: UserCheck,
      tone: 'success'
    },
    {
      label: 'Pending Accounts',
      value: userStats.value.pending,
      icon: Clock3,
      tone: 'warning'
    },
    {
      label: 'Restricted Accounts',
      value: userStats.value.disabled + userStats.value.rejected,
      icon: UserX,
      tone: 'danger'
    }
  ]
})

const statusFilters = computed(() => {
  return [
    {
      label: 'All',
      value: 'all',
      count: userStats.value.total
    },
    {
      label: 'Active',
      value: 'active',
      count: userStats.value.active
    },
    {
      label: 'Pending',
      value: 'pending',
      count: userStats.value.pending
    },
    {
      label: 'Disabled',
      value: 'disabled',
      count: userStats.value.disabled
    },
    {
      label: 'Rejected',
      value: 'rejected',
      count: userStats.value.rejected
    }
  ]
})

const filteredUsers = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  const filtered = users.value.filter((user) => {
    const status = getUserStatus(user)
    const role = normalizeText(user.role)

    const searchableText = [
      user.fullname,
      user.email,
      user.role,
      user.account_status,
      user.contact_no,
      user.created_at
    ]
      .join(' ')
      .toLowerCase()

    const matchesSearch = !keyword || searchableText.includes(keyword)
    const matchesRole = roleFilter.value === 'all' || role === roleFilter.value
    const matchesStatus = statusFilter.value === 'all' || status === statusFilter.value

    return matchesSearch && matchesRole && matchesStatus
  })

  return filtered.sort((a, b) => {
    const order = {
      pending: 1,
      active: 2,
      disabled: 3,
      rejected: 4
    }

    const statusA = order[getUserStatus(a)] || 5
    const statusB = order[getUserStatus(b)] || 5

    if (statusA !== statusB) {
      return statusA - statusB
    }

    return new Date(b.created_at || 0) - new Date(a.created_at || 0)
  })
})

const passwordRules = computed(() => {
  return {
    length: newUser.password.length >= 8,
    uppercase: /[A-Z]/.test(newUser.password),
    lowercase: /[a-z]/.test(newUser.password),
    number: /[0-9]/.test(newUser.password),
    symbol: /[^A-Za-z0-9]/.test(newUser.password)
  }
})

const strengthScore = computed(() => {
  return Object.values(passwordRules.value).filter(Boolean).length
})

const strengthLabel = computed(() => {
  if (!newUser.password) return 'None'
  if (strengthScore.value <= 2) return 'Weak'
  if (strengthScore.value <= 4) return 'Good'
  return 'Strong'
})

const strengthWidth = computed(() => {
  return `${(strengthScore.value / 5) * 100}%`
})

const strengthClass = computed(() => {
  if (strengthScore.value <= 2) return 'weak'
  if (strengthScore.value <= 4) return 'good'
  return 'strong'
})

const statusModalKicker = computed(() => {
  if (selectedStatusAction.value === 'approve') return 'Approve Account'
  if (selectedStatusAction.value === 'reject') return 'Reject Account'
  if (selectedStatusAction.value === 'disable') return 'Disable Account'
  if (selectedStatusAction.value === 'restore') return 'Restore Account'
  return 'Confirm Action'
})

const statusModalTitle = computed(() => {
  if (selectedStatusAction.value === 'approve') return 'Approve account?'
  if (selectedStatusAction.value === 'reject') return 'Reject account?'
  if (selectedStatusAction.value === 'disable') return 'Disable account?'
  if (selectedStatusAction.value === 'restore') return 'Restore account?'
  return 'Confirm action?'
})

const statusModalMessage = computed(() => {
  if (selectedStatusAction.value === 'approve') {
    return 'This account will become active.'
  }

  if (selectedStatusAction.value === 'reject') {
    return 'This account will be rejected and blocked from login.'
  }

  if (selectedStatusAction.value === 'disable') {
    return 'This account will be locked until restored.'
  }

  if (selectedStatusAction.value === 'restore') {
    return 'This account will regain access.'
  }

  return 'Please confirm this account action.'
})

const statusModalButton = computed(() => {
  if (selectedStatusAction.value === 'approve') return 'Approve Account'
  if (selectedStatusAction.value === 'reject') return 'Reject Account'
  if (selectedStatusAction.value === 'disable') return 'Disable Account'
  if (selectedStatusAction.value === 'restore') return 'Restore Account'
  return 'Confirm'
})

function openAddModal() {
  resetAddForm()
  showAddModal.value = true
}

function closeAddModal() {
  if (addLoading.value) return
  showAddModal.value = false
  resetAddForm()
}

function resetAddForm() {
  newUser.fullname = ''
  newUser.email = ''
  newUser.role = ''
  newUser.contact_no = ''
  newUser.password = ''
  newUser.confirm_password = ''
  addError.value = ''
  showAddPassword.value = false
  showConfirmAddPassword.value = false
}

function validateAddForm() {
  const cleanEmail = newUser.email.trim().toLowerCase()

  if (!newUser.fullname.trim() || !cleanEmail || !newUser.role || !newUser.password || !newUser.confirm_password) {
    return 'Please complete all required fields.'
  }

  if (!emailPattern.test(cleanEmail)) {
    return 'Please enter a valid email address.'
  }

  if (strengthScore.value < 5) {
    return 'Please create a stronger password.'
  }

  if (newUser.password !== newUser.confirm_password) {
    return 'Passwords do not match.'
  }

  return ''
}

async function createUser() {
  addError.value = ''
  success.value = ''

  const validationMessage = validateAddForm()

  if (validationMessage) {
    addError.value = validationMessage
    return
  }

  addLoading.value = true

  try {
    const response = await adminApi.post('/users/add', {
      fullname: newUser.fullname.trim(),
      email: newUser.email.trim().toLowerCase(),
      role: newUser.role,
      contact_no: newUser.contact_no.trim(),
      password: newUser.password,
      confirm_password: newUser.confirm_password
    })

    if (response.data.success) {
      const message = response.data.message || 'User account created successfully.'

      showAddModal.value = false
      resetAddForm()

      await loadUsers(false)

      success.value = message
    } else {
      addError.value = response.data.message || 'Unable to create user account.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      addError.value = err.response.data.message
    } else {
      addError.value = 'Failed to connect to Flask API.'
    }

    console.error(err)
  } finally {
    addLoading.value = false
  }
}

function getUserStatus(user) {
  return normalizeText(user.account_status || 'active')
}

function isCurrentAdmin(user) {
  return String(user.user_id) === String(currentAdminId)
}

function openStatusModal(user, action) {
  selectedStatusUser.value = user
  selectedStatusAction.value = action
  statusActionError.value = ''
  showStatusModal.value = true
}

function resetStatusModal() {
  showStatusModal.value = false
  selectedStatusUser.value = null
  selectedStatusAction.value = ''
  statusActionError.value = ''
}

function closeStatusModal() {
  if (statusActionLoading.value) return

  resetStatusModal()
}

async function confirmStatusAction() {
  statusActionError.value = ''
  error.value = ''
  success.value = ''

  if (!selectedStatusUser.value || !selectedStatusAction.value) {
    statusActionError.value = 'No account action selected.'
    return
  }

  const allowedActions = ['approve', 'reject', 'disable', 'restore']

  if (!allowedActions.includes(selectedStatusAction.value)) {
    statusActionError.value = 'Invalid user action.'
    return
  }

  statusActionLoading.value = true
  actionLoadingId.value = selectedStatusUser.value.user_id

  try {
    const response = await adminApi.post(
      `/users/${selectedStatusUser.value.user_id}/${selectedStatusAction.value}`
    )

    if (response.data.success) {
      const message = response.data.message || 'User account updated successfully.'

      resetStatusModal()

      await loadUsers(false)

      success.value = message
    } else {
      statusActionError.value = response.data.message || 'Unable to update user account.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      statusActionError.value = err.response.data.message
    } else {
      statusActionError.value = 'Failed to connect to Flask API.'
    }

    console.error(err)
  } finally {
    statusActionLoading.value = false
    actionLoadingId.value = null
  }
}

function openDeleteModal(user) {
  selectedUser.value = user
  confirmationText.value = ''
  adminPassword.value = ''
  deleteError.value = ''
  showDeleteModal.value = true
}

function resetDeleteModal() {
  showDeleteModal.value = false
  selectedUser.value = null
  confirmationText.value = ''
  adminPassword.value = ''
  deleteError.value = ''
}

function closeDeleteModal() {
  if (deleteLoading.value) return
  resetDeleteModal()
}

async function deleteUserPermanently() {
  deleteError.value = ''
  success.value = ''

  if (!selectedUser.value) {
    deleteError.value = 'No user selected.'
    return
  }

  if (confirmationText.value !== 'DELETE') {
    deleteError.value = 'Please type DELETE to confirm permanent deletion.'
    return
  }

  if (!adminPassword.value) {
    deleteError.value = 'Admin password is required.'
    return
  }

  deleteLoading.value = true
  actionLoadingId.value = selectedUser.value.user_id

  try {
    const response = await adminApi.post(`/users/${selectedUser.value.user_id}/delete`, {
      confirmation_text: confirmationText.value,
      admin_password: adminPassword.value
    })

    if (response.data.success) {
      const message = response.data.message || 'User account deleted successfully.'

      resetDeleteModal()

      await loadUsers(false)

      success.value = message
    } else {
      deleteError.value = response.data.message || 'Unable to delete user account.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      deleteError.value = err.response.data.message
    } else {
      deleteError.value = 'Failed to connect to Flask API.'
    }

    console.error(err)
  } finally {
    deleteLoading.value = false
    actionLoadingId.value = null
  }
}

function clearFilters() {
  search.value = ''
  roleFilter.value = 'all'
  statusFilter.value = 'all'
}

function displayNumber(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'U'
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function formatRole(role) {
  if (role === 'admin') return 'Administrator'
  if (role === 'teacher') return 'Teacher'
  if (role === 'parent') return 'Parent'
  if (role === 'expert') return 'Expert / SPED'
  if (role === 'guest') return 'Guest'
  return 'N/A'
}

function formatStatus(status) {
  if (status === 'active') return 'Active'
  if (status === 'pending') return 'Pending'
  if (status === 'rejected') return 'Rejected'
  if (status === 'disabled') return 'Disabled'
  return 'Active'
}

function getStatusClass(status) {
  if (status === 'active') return 'active'
  if (status === 'pending') return 'pending'
  if (status === 'rejected') return 'rejected'
  if (status === 'disabled') return 'disabled'
  return 'active'
}

function getCurrentAdmin() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_admin_user') || '{}')
  } catch {
    return {}
  }
}
</script>