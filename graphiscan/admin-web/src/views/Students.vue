<template>
  <AdminLayout title="Student Management">
    <div class="compact-page student-management-page">
      <div class="page-header compact-header">
        <div>
          <h1>Students</h1>
          <p>Manage student records, assigned teachers, and linked parents.</p>
        </div>
      </div>

      <section class="user-summary-grid">
        <article
          v-for="item in studentStatCards"
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
            <h2>Student records</h2>
            <p>View assignments and linked guardians.</p>
          </div>

          <div class="user-toolbar">
            <button class="primary-action-btn" type="button" @click="openAddModal">
              <Plus :size="16" :stroke-width="1.9" />
              Add Student
            </button>

            <button class="soft-action-btn" type="button" @click="loadPageData">
              <RefreshCw :size="15" :stroke-width="1.8" />
              Refresh
            </button>

            <div class="search-field">
              <Search :size="16" :stroke-width="1.8" />
              <input
                v-model="search"
                type="text"
                placeholder="Search students"
              />
            </div>
          </div>
        </div>

        <p v-if="loading" class="muted-message">Loading students...</p>
        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <div
          v-if="!loading && !error && filteredStudents.length > 0"
          class="table-wrapper compact-table-scroll admin-students-table"
        >
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Teacher</th>
                <th>Parent / Guardian</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="student in filteredStudents"
                :key="student.student_id"
              >
                <td>
                  <div class="user-cell">
                    <div class="user-avatar">
                      {{ getInitial(student.fullname) }}
                    </div>

                    <div>
                      <strong>{{ student.fullname || 'Unknown Student' }}</strong>
                      <small class="table-subtext">
                        {{ student.grade_level || 'Grade not set' }}
                        <template v-if="student.age"> · Age {{ student.age }}</template>
                      </small>
                    </div>
                  </div>
                </td>

                <td>
                  <div class="user-cell compact-user-cell">
                    <div class="mini-user-icon">
                      <UserRound :size="15" :stroke-width="1.8" />
                    </div>

                    <div>
                      <strong>{{ getDisplayName(student.teacher_name, 'Not assigned') }}</strong>
                      <small class="table-subtext">{{ getDisplayName(student.teacher_email, 'N/A') }}</small>
                    </div>
                  </div>
                </td>

                <td>
                  <div class="guardian-cell">
                    <div class="user-cell compact-user-cell">
                      <div class="mini-user-icon">
                        <UsersRound :size="15" :stroke-width="1.8" />
                      </div>

                      <div>
                        <strong>{{ getDisplayName(student.parent_name, 'Not assigned') }}</strong>
                        <small class="table-subtext">{{ getDisplayName(student.parent_email, 'N/A') }}</small>
                      </div>
                    </div>

                    <button
                      class="guardian-link-btn"
                      type="button"
                      @click="openGuardianModal(student)"
                    >
                      {{ hasLinkedParent(student) ? 'Change' : 'Link' }}
                    </button>
                  </div>
                </td>

                <td>
                  <div class="table-actions">
                    <button
                      class="small-action-btn"
                      type="button"
                      @click="openViewModal(student)"
                    >
                      <Eye :size="14" :stroke-width="1.9" />
                      View
                    </button>

                    <button
                      class="danger-action-btn"
                      type="button"
                      @click="openDeleteModal(student)"
                    >
                      <Trash2 :size="14" :stroke-width="1.9" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="!loading && !error && filteredStudents.length === 0"
          class="clean-empty-state"
        >
          <GraduationCap :size="34" :stroke-width="1.7" />
          <h3>No students found</h3>
          <p>Try another search keyword or add a student record.</p>
        </div>
      </div>

      <div v-if="showViewModal" class="modal-backdrop">
        <section class="standard-modal">
          <div class="standard-modal-head">
            <div>
              <span>Student Details</span>
              <h2>{{ selectedViewStudent?.fullname || 'Student Record' }}</h2>
              <p>View student profile, assigned teacher, and linked parent.</p>
            </div>

            <button class="modal-close-btn" type="button" @click="closeViewModal">
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <div class="student-view-body">
            <div class="detail-list">
              <div>
                <span>Full Name</span>
                <strong>{{ selectedViewStudent?.fullname || 'N/A' }}</strong>
              </div>

              <div>
                <span>Age</span>
                <strong>{{ selectedViewStudent?.age || 'N/A' }}</strong>
              </div>

              <div>
                <span>Grade Level</span>
                <strong>{{ selectedViewStudent?.grade_level || 'N/A' }}</strong>
              </div>

              <div>
                <span>Assigned Teacher</span>
                <strong>{{ getDisplayName(selectedViewStudent?.teacher_name, 'Not assigned') }}</strong>
                <small class="table-subtext">{{ getDisplayName(selectedViewStudent?.teacher_email, 'N/A') }}</small>
              </div>

              <div>
                <span>Parent / Guardian</span>
                <strong>{{ getDisplayName(selectedViewStudent?.parent_name, 'Not assigned') }}</strong>
                <small class="table-subtext">{{ getDisplayName(selectedViewStudent?.parent_email, 'N/A') }}</small>
              </div>

              <div>
                <span>Date Added</span>
                <strong>{{ selectedViewStudent?.created_at || 'N/A' }}</strong>
              </div>
            </div>

            <div class="modal-actions">
              <button class="cancel-btn" type="button" @click="closeViewModal">
                Close
              </button>

              <RouterLink
                v-if="selectedViewStudent?.student_id"
                class="primary-modal-btn"
                :to="`/admin/progress/${selectedViewStudent.student_id}`"
              >
                View Progress
              </RouterLink>
            </div>
          </div>
        </section>
      </div>

      <div v-if="showAddModal" class="modal-backdrop">
        <section class="standard-modal">
          <div class="standard-modal-head">
            <div>
              <span>Create Student</span>
              <h2>Add student</h2>
              <p>Create a student record and assign a teacher.</p>
            </div>

            <button class="modal-close-btn" type="button" @click="closeAddModal">
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <form class="admin-form-grid" @submit.prevent="createStudent">
            <div class="form-group">
              <label>Student Full Name</label>
              <input
                v-model="newStudent.fullname"
                type="text"
                placeholder="Enter student full name"
              />
            </div>

            <div class="form-group">
              <label>Age</label>
              <input
                v-model="newStudent.age"
                type="number"
                min="1"
                placeholder="Enter age"
              />
            </div>

            <div class="form-group">
              <label>Grade Level</label>
              <input
                v-model="newStudent.grade_level"
                type="text"
                placeholder="Example: Grade 3"
              />
            </div>

            <div class="form-group">
              <label>Assigned Teacher</label>
              <select v-model="newStudent.teacher_id">
                <option value="">Select teacher</option>
                <option
                  v-for="teacher in activeTeachers"
                  :key="teacher.user_id"
                  :value="teacher.user_id"
                >
                  {{ teacher.fullname }} - {{ teacher.email }}
                </option>
              </select>
            </div>

            <div class="form-group full-field">
              <label>Parent / Guardian</label>
              <select v-model="newStudent.parent_id">
                <option value="">No parent assigned</option>
                <option
                  v-for="parent in activeParents"
                  :key="parent.user_id"
                  :value="parent.user_id"
                >
                  {{ parent.fullname }} - {{ parent.email }}
                </option>
              </select>
            </div>

            <p v-if="addError" class="error-message full-field">{{ addError }}</p>

            <div class="modal-actions full-field">
              <button class="cancel-btn" type="button" @click="closeAddModal">
                Cancel
              </button>

              <button class="primary-modal-btn" type="submit" :disabled="addLoading">
                {{ addLoading ? 'Creating...' : 'Create Student' }}
              </button>
            </div>
          </form>
        </section>
      </div>

      <div v-if="showGuardianModal" class="modal-backdrop">
        <section class="standard-modal">
          <div class="standard-modal-head">
            <div>
              <span>Guardian Assignment</span>
              <h2>Update guardian</h2>
              <p>Link, change, or remove the parent connected to this student.</p>
            </div>

            <button class="modal-close-btn" type="button" @click="closeGuardianModal">
              <X :size="18" :stroke-width="1.8" />
            </button>
          </div>

          <form class="admin-form-grid" @submit.prevent="updateStudentGuardian">
            <div class="form-group full-field">
              <label>Student</label>
              <input
                type="text"
                :value="selectedGuardianStudent?.fullname || 'Unknown Student'"
                disabled
              />
            </div>

            <div class="form-group full-field">
              <label>Parent / Guardian</label>
              <select v-model="selectedGuardianId">
                <option value="">No parent assigned</option>
                <option
                  v-for="parent in activeParents"
                  :key="parent.user_id"
                  :value="parent.user_id"
                >
                  {{ parent.fullname }} - {{ parent.email }}
                </option>
              </select>
            </div>

            <p v-if="guardianError" class="error-message full-field">
              {{ guardianError }}
            </p>

            <div class="modal-actions full-field">
              <button class="cancel-btn" type="button" @click="closeGuardianModal">
                Cancel
              </button>

              <button class="primary-modal-btn" type="submit" :disabled="guardianLoading">
                {{ guardianLoading ? 'Saving...' : 'Save Guardian' }}
              </button>
            </div>
          </form>
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
            <h2>Delete student record?</h2>

            <p>This action is permanent. Connected records may be affected.</p>

            <div class="delete-target-card">
              <strong>{{ selectedStudent?.fullname || 'Unknown Student' }}</strong>
              <small>Grade Level: {{ selectedStudent?.grade_level || 'N/A' }}</small>
              <em>Teacher: {{ getDisplayName(selectedStudent?.teacher_name, 'Not assigned') }}</em>
            </div>

            <div class="warning-box">
              <ShieldAlert :size="18" :stroke-width="1.8" />
              <p>Continue only if you are sure this student record should be removed.</p>
            </div>
          </div>

          <form class="delete-form" @submit.prevent="deleteStudentPermanently">
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
import { RouterLink } from 'vue-router'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  AlertTriangle,
  Eye,
  GraduationCap,
  Link2Off,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Trash2,
  UserRound,
  UsersRound,
  X
} from 'lucide-vue-next'

const search = ref('')
const students = ref([])
const users = ref([])

const loading = ref(true)
const error = ref('')
const success = ref('')

const showViewModal = ref(false)
const selectedViewStudent = ref(null)

const showAddModal = ref(false)
const addLoading = ref(false)
const addError = ref('')

const newStudent = reactive({
  fullname: '',
  age: '',
  grade_level: '',
  teacher_id: '',
  parent_id: ''
})

const showGuardianModal = ref(false)
const selectedGuardianStudent = ref(null)
const selectedGuardianId = ref('')
const guardianLoading = ref(false)
const guardianError = ref('')

const showDeleteModal = ref(false)
const selectedStudent = ref(null)
const confirmationText = ref('')
const adminPassword = ref('')
const deleteLoading = ref(false)
const deleteError = ref('')

onMounted(() => {
  loadPageData()
})

async function loadPageData(clearMessages = true) {
  loading.value = true

  if (clearMessages) {
    error.value = ''
    success.value = ''
  }

  try {
    const [studentsResponse, usersResponse] = await Promise.all([
      adminApi.get('/students'),
      adminApi.get('/users')
    ])

    if (studentsResponse.data.success) {
      students.value = studentsResponse.data.students || []
    } else {
      error.value = studentsResponse.data.message || 'Unable to load students.'
    }

    if (usersResponse.data.success) {
      users.value = usersResponse.data.users || []
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

const activeTeachers = computed(() => {
  return users.value.filter((user) => {
    return user.role === 'teacher' && getAccountStatus(user) === 'active'
  })
})

const activeParents = computed(() => {
  return users.value.filter((user) => {
    return user.role === 'parent' && getAccountStatus(user) === 'active'
  })
})

const filteredStudents = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  return students.value.filter((student) => {
    return (
      String(student.fullname || '').toLowerCase().includes(keyword) ||
      String(student.age || '').toLowerCase().includes(keyword) ||
      String(student.grade_level || '').toLowerCase().includes(keyword) ||
      String(student.teacher_name || '').toLowerCase().includes(keyword) ||
      String(student.teacher_email || '').toLowerCase().includes(keyword) ||
      String(student.parent_name || '').toLowerCase().includes(keyword) ||
      String(student.parent_email || '').toLowerCase().includes(keyword) ||
      String(student.created_at || '').toLowerCase().includes(keyword)
    )
  })
})

const studentStats = computed(() => {
  return {
    total: students.value.length,
    assignedTeachers: students.value.filter((student) => {
      return hasAssignedTeacher(student)
    }).length,
    linkedParents: students.value.filter((student) => {
      return hasLinkedParent(student)
    }).length,
    unlinkedParents: students.value.filter((student) => {
      return !hasLinkedParent(student)
    }).length
  }
})

const studentStatCards = computed(() => {
  return [
    {
      label: 'Total Students',
      value: studentStats.value.total,
      icon: GraduationCap,
      tone: ''
    },
    {
      label: 'Assigned Teachers',
      value: studentStats.value.assignedTeachers,
      icon: UserRound,
      tone: 'success'
    },
    {
      label: 'Linked Parents',
      value: studentStats.value.linkedParents,
      icon: UsersRound,
      tone: ''
    },
    {
      label: 'No Parent Linked',
      value: studentStats.value.unlinkedParents,
      icon: Link2Off,
      tone: 'warning'
    }
  ]
})

function getAccountStatus(user) {
  return user.account_status || 'active'
}

function openViewModal(student) {
  selectedViewStudent.value = student
  showViewModal.value = true
}

function closeViewModal() {
  showViewModal.value = false
  selectedViewStudent.value = null
}

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
  newStudent.fullname = ''
  newStudent.age = ''
  newStudent.grade_level = ''
  newStudent.teacher_id = ''
  newStudent.parent_id = ''
  addError.value = ''
}

function validateAddForm() {
  if (!newStudent.fullname.trim()) {
    return 'Student full name is required.'
  }

  if (!newStudent.age) {
    return 'Student age is required.'
  }

  if (Number(newStudent.age) <= 0) {
    return 'Student age must be valid.'
  }

  if (!newStudent.grade_level.trim()) {
    return 'Grade level is required.'
  }

  if (!newStudent.teacher_id) {
    return 'Please select an assigned teacher.'
  }

  return ''
}

async function createStudent() {
  addError.value = ''
  success.value = ''

  const validationMessage = validateAddForm()

  if (validationMessage) {
    addError.value = validationMessage
    return
  }

  addLoading.value = true

  try {
    const response = await adminApi.post('/students/add', {
      fullname: newStudent.fullname.trim(),
      age: newStudent.age,
      grade_level: newStudent.grade_level.trim(),
      teacher_id: newStudent.teacher_id,
      parent_id: newStudent.parent_id || null
    })

    if (response.data.success) {
      const message = response.data.message || 'Student added successfully.'

      showAddModal.value = false
      resetAddForm()

      await loadPageData(false)

      success.value = message
    } else {
      addError.value = response.data.message || 'Unable to add student.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      addError.value = err.response.data.message
    } else {
      addError.value = 'Unable to connect. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    addLoading.value = false
  }
}

function openGuardianModal(student) {
  selectedGuardianStudent.value = student
  selectedGuardianId.value = student.parent_id || ''
  guardianError.value = ''
  showGuardianModal.value = true
}

function closeGuardianModal() {
  if (guardianLoading.value) return

  showGuardianModal.value = false
  selectedGuardianStudent.value = null
  selectedGuardianId.value = ''
  guardianError.value = ''
}

async function updateStudentGuardian() {
  guardianError.value = ''
  success.value = ''

  if (!selectedGuardianStudent.value) {
    guardianError.value = 'No student selected.'
    return
  }

  guardianLoading.value = true

  try {
    const response = await adminApi.post(
      `/students/${selectedGuardianStudent.value.student_id}/guardian`,
      {
        parent_id: selectedGuardianId.value || null
      }
    )

    if (response.data.success) {
      const message = response.data.message || 'Guardian updated successfully.'

      showGuardianModal.value = false
      selectedGuardianStudent.value = null
      selectedGuardianId.value = ''

      await loadPageData(false)

      success.value = message
    } else {
      guardianError.value = response.data.message || 'Unable to update guardian.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      guardianError.value = err.response.data.message
    } else {
      guardianError.value = 'Unable to connect. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    guardianLoading.value = false
  }
}

function openDeleteModal(student) {
  selectedStudent.value = student
  confirmationText.value = ''
  adminPassword.value = ''
  deleteError.value = ''
  showDeleteModal.value = true
}

function resetDeleteModal() {
  showDeleteModal.value = false
  selectedStudent.value = null
  confirmationText.value = ''
  adminPassword.value = ''
  deleteError.value = ''
}

function closeDeleteModal() {
  if (deleteLoading.value) return

  resetDeleteModal()
}

async function deleteStudentPermanently() {
  deleteError.value = ''
  success.value = ''

  if (!selectedStudent.value) {
    deleteError.value = 'No student selected.'
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

  try {
    const response = await adminApi.post(`/students/${selectedStudent.value.student_id}/delete`, {
      confirmation_text: confirmationText.value,
      admin_password: adminPassword.value
    })

    if (response.data.success) {
      const message = response.data.message || 'Student deleted successfully.'

      resetDeleteModal()

      await loadPageData(false)

      success.value = message
    } else {
      deleteError.value = response.data.message || 'Unable to delete student.'
    }
  } catch (err) {
    if (err.response?.data?.message) {
      deleteError.value = err.response.data.message
    } else {
      deleteError.value = 'Unable to connect. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    deleteLoading.value = false
  }
}

function displayNumber(value) {
  if (loading.value) {
    return '...'
  }

  return value
}

function hasLinkedParent(student) {
  return (
    hasRealValue(student.parent_id) ||
    hasRealValue(student.parent_name) ||
    hasRealValue(student.parent_email)
  )
}

function hasAssignedTeacher(student) {
  return (
    hasRealValue(student.teacher_id) ||
    hasRealValue(student.teacher_name) ||
    hasRealValue(student.teacher_email)
  )
}

function hasRealValue(value) {
  const text = String(value ?? '').trim().toLowerCase()

  if (!text) {
    return false
  }

  return ![
    '0',
    'n/a',
    'na',
    'none',
    'null',
    'undefined',
    'not assigned',
    'no parent assigned'
  ].includes(text)
}

function getDisplayName(value, fallback) {
  return hasRealValue(value) ? value : fallback
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : 'S'
}
</script>
