<template>
  <AdminLayout>
    <div class="compact-page admin-settings-page">
      <div class="page-header compact-header">
        <div>
          <h1>Settings</h1>
          <p>Manage administrator account security.</p>
        </div>
      </div>

      <section class="settings-layout">
        <section class="panel-card settings-card">
          <div class="settings-card-head">
            <div class="settings-card-icon">
              <KeyRound :size="22" :stroke-width="1.9" />
            </div>

            <div>
              <h2>Change Password</h2>
              <p>Update your password. The system will require login again after a successful change.</p>
            </div>
          </div>

          <form class="admin-form-grid settings-password-form" @submit.prevent="changeAdminPassword">
            <div class="form-group full-field">
              <label>Current Password</label>

              <div class="admin-password-input">
                <input
                  v-model="passwordForm.current_password"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  placeholder="Enter current password"
                  autocomplete="current-password"
                />

                <button
                  type="button"
                  @click="showCurrentPassword = !showCurrentPassword"
                >
                  <EyeOff v-if="showCurrentPassword" :size="15" :stroke-width="1.8" />
                  <Eye v-else :size="15" :stroke-width="1.8" />
                  {{ showCurrentPassword ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>

            <div class="form-group full-field">
              <label>New Password</label>

              <div class="admin-password-input">
                <input
                  v-model="passwordForm.new_password"
                  :type="showNewPassword ? 'text' : 'password'"
                  placeholder="Create new password"
                  autocomplete="new-password"
                />

                <button
                  type="button"
                  @click="showNewPassword = !showNewPassword"
                >
                  <EyeOff v-if="showNewPassword" :size="15" :stroke-width="1.8" />
                  <Eye v-else :size="15" :stroke-width="1.8" />
                  {{ showNewPassword ? 'Hide' : 'Show' }}
                </button>
              </div>

            </div>

            <div class="form-group full-field">
              <label>Confirm New Password</label>

              <div class="admin-password-input">
                <input
                  v-model="passwordForm.confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Re-enter new password"
                  autocomplete="new-password"
                />

                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <EyeOff v-if="showConfirmPassword" :size="15" :stroke-width="1.8" />
                  <Eye v-else :size="15" :stroke-width="1.8" />
                  {{ showConfirmPassword ? 'Hide' : 'Show' }}
                </button>
              </div>

              <p
                v-if="passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password"
                class="field-warning"
              >
                New passwords do not match.
              </p>
            </div>

            <div class="admin-password-strength">
              <div class="strength-head">
                <span>Password Strength</span>
                <strong>{{ passwordStrengthLabel }}</strong>
              </div>

              <div class="strength-track">
                <div
                  class="strength-fill"
                  :class="passwordStrengthClass"
                  :style="{ width: passwordStrengthWidth }"
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

            <p v-if="changePasswordError" class="error-message full-field">
              {{ changePasswordError }}
            </p>

            <p v-if="changePasswordSuccess" class="success-message full-field">
              {{ changePasswordSuccess }}
            </p>

            <div class="settings-actions full-field">
              <button
                class="cancel-btn"
                type="button"
                :disabled="changePasswordLoading"
                @click="resetChangePasswordForm"
              >
                Clear
              </button>

              <button
                class="primary-modal-btn"
                type="submit"
                :disabled="changePasswordLoading"
              >
                {{ changePasswordLoading ? 'Updating...' : 'Change Password' }}
              </button>
            </div>
          </form>
        </section>

      </section>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import adminApi from '../api/adminApi'
import AdminLayout from '../layouts/AdminLayout.vue'
import {
  Eye,
  EyeOff,
  KeyRound
} from 'lucide-vue-next'

const router = useRouter()

const changePasswordLoading = ref(false)
const changePasswordError = ref('')
const changePasswordSuccess = ref('')

const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules = computed(() => {
  return {
    length: passwordForm.new_password.length >= 8,
    uppercase: /[A-Z]/.test(passwordForm.new_password),
    lowercase: /[a-z]/.test(passwordForm.new_password),
    number: /[0-9]/.test(passwordForm.new_password),
    symbol: /[^A-Za-z0-9]/.test(passwordForm.new_password)
  }
})

const passwordStrengthScore = computed(() => {
  return Object.values(passwordRules.value).filter(Boolean).length
})

const passwordStrengthLabel = computed(() => {
  if (!passwordForm.new_password) return 'None'
  if (passwordStrengthScore.value <= 2) return 'Weak'
  if (passwordStrengthScore.value <= 4) return 'Good'
  return 'Strong'
})

const passwordStrengthWidth = computed(() => {
  return `${(passwordStrengthScore.value / 5) * 100}%`
})

const passwordStrengthClass = computed(() => {
  if (passwordStrengthScore.value <= 2) return 'weak'
  if (passwordStrengthScore.value <= 4) return 'good'
  return 'strong'
})

function validateChangePasswordForm() {
  if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    return 'Please complete all password fields.'
  }

  if (passwordForm.current_password === passwordForm.new_password) {
    return 'New password must be different from your current password.'
  }

  if (passwordStrengthScore.value < 5) {
    return 'Please create a stronger password.'
  }

  if (passwordForm.new_password !== passwordForm.confirm_password) {
    return 'New passwords do not match.'
  }

  return ''
}

async function changeAdminPassword() {
  changePasswordError.value = ''
  changePasswordSuccess.value = ''

  const validationMessage = validateChangePasswordForm()

  if (validationMessage) {
    changePasswordError.value = validationMessage
    return
  }

  changePasswordLoading.value = true

  try {
    const response = await adminApi.post('/change-password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
      confirm_password: passwordForm.confirm_password
    })

    if (response.data.success) {
      changePasswordSuccess.value =
        response.data.message || 'Password changed successfully. Please log in again.'

      setTimeout(() => {
        clearAdminSession()
        router.replace('/login')
      }, 900)
    } else {
      changePasswordError.value = response.data.message || 'Unable to change password.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      changePasswordError.value = err.response.data.message
    } else {
      changePasswordError.value = 'Unable to connect. Check your connection and try again.'
    }

    console.error(err)
  } finally {
    changePasswordLoading.value = false
  }
}

function resetChangePasswordForm() {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''

  changePasswordError.value = ''
  changePasswordSuccess.value = ''

  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
}

function clearAdminSession() {
  localStorage.removeItem('graphiscan_admin_auth')
  localStorage.removeItem('graphiscan_admin_token')
  localStorage.removeItem('graphiscan_admin_user')
}
</script>
