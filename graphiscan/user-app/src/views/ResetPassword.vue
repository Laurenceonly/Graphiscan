<template>
  <main class="mobile-login-page reset-mobile-page">
    <section class="mobile-login-card reset-card-clean">
      <div class="mobile-brand">
        <div class="mobile-brand-mark">G</div>

        <div>
          <h1>GRAPHI<span>SCAN</span></h1>
          <p>Create a new password</p>
        </div>
      </div>

      <div class="mobile-login-copy compact reset-copy">
        <span>Password Reset</span>
        <h2>Reset password</h2>
        <p>Create a strong password for your GRAPHISCAN account.</p>
      </div>

      <form class="mobile-login-form reset-clean-form" @submit.prevent="resetPassword">
        <div v-if="!token" class="reset-token-warning">
          <AlertCircle :size="18" :stroke-width="1.9" />
          <span>Reset token is missing. Please request a new password reset link.</span>
        </div>

        <div class="form-group">
          <label>New Password</label>

          <div class="input-wrap clean-reset-input">
            <LockKeyhole :size="18" :stroke-width="1.9" />

            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter new password"
              autocomplete="new-password"
              required
            />

            <button
              class="password-toggle-btn clean-password-toggle"
              type="button"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" :size="15" :stroke-width="1.8" />
              <Eye v-else :size="15" :stroke-width="1.8" />
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>

          <div class="password-strength clean-reset-strength">
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

            <ul class="password-rules clean-reset-rules">
              <li :class="{ passed: passwordRules.length }">
                At least 8 characters
              </li>
              <li :class="{ passed: passwordRules.uppercase }">
                One uppercase letter
              </li>
              <li :class="{ passed: passwordRules.lowercase }">
                One lowercase letter
              </li>
              <li :class="{ passed: passwordRules.number }">
                One number
              </li>
              <li :class="{ passed: passwordRules.symbol }">
                One symbol
              </li>
            </ul>
          </div>
        </div>

        <div class="form-group">
          <label>Confirm Password</label>

          <div class="input-wrap clean-reset-input">
            <KeyRound :size="18" :stroke-width="1.9" />

            <input
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="Re-enter new password"
              autocomplete="new-password"
              required
            />

            <button
              class="password-toggle-btn clean-password-toggle"
              type="button"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <EyeOff v-if="showConfirmPassword" :size="15" :stroke-width="1.8" />
              <Eye v-else :size="15" :stroke-width="1.8" />
              {{ showConfirmPassword ? 'Hide' : 'Show' }}
            </button>
          </div>

          <p
            v-if="confirmPassword && password !== confirmPassword"
            class="field-warning"
          >
            Passwords do not match.
          </p>
        </div>

        <div class="reset-info-note">
          <ShieldCheck :size="18" :stroke-width="1.9" />
          <span>Use uppercase, lowercase, number, and symbol characters.</span>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <button
          class="login-submit-btn reset-submit-btn"
          type="submit"
          :disabled="loading || !token"
        >
          <LoaderCircle
            v-if="loading"
            class="loading-icon"
            :size="18"
            :stroke-width="1.9"
          />

          <RotateCcwKey
            v-else
            :size="18"
            :stroke-width="1.9"
          />

          {{ loading ? 'Resetting...' : 'Reset Password' }}
        </button>

        <p class="auth-switch reset-switch">
          Remembered your password?
          <RouterLink to="/login">Back to login</RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  AlertCircle,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  RotateCcwKey,
  ShieldCheck
} from 'lucide-vue-next'
import userApi from '../api/userApi'

const route = useRoute()
const router = useRouter()

const token = String(route.query.token || '')

const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const error = ref('')
const success = ref('')
const loading = ref(false)

const passwordRules = computed(() => {
  return {
    length: password.value.length >= 8,
    uppercase: /[A-Z]/.test(password.value),
    lowercase: /[a-z]/.test(password.value),
    number: /[0-9]/.test(password.value),
    symbol: /[^A-Za-z0-9]/.test(password.value)
  }
})

const strengthScore = computed(() => {
  return Object.values(passwordRules.value).filter(Boolean).length
})

const strengthLabel = computed(() => {
  if (!password.value) return 'None'
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

function clearMessages() {
  error.value = ''
  success.value = ''
}

function validateForm() {
  if (!token) {
    return 'Invalid or missing reset token.'
  }

  if (strengthScore.value < 5) {
    return 'Please create a stronger password.'
  }

  if (password.value !== confirmPassword.value) {
    return 'Passwords do not match.'
  }

  return ''
}

async function resetPassword() {
  clearMessages()

  const validationMessage = validateForm()

  if (validationMessage) {
    error.value = validationMessage
    return
  }

  loading.value = true

  try {
    const response = await userApi.post('/reset-password', {
      token,
      password: password.value,
      confirm_password: confirmPassword.value
    })

    if (response.data.success) {
      success.value = response.data.message || 'Password reset successfully.'

      setTimeout(() => {
        router.push({
          path: '/login',
          query: {
            reset: 'success'
          }
        })
      }, 900)
    } else {
      error.value = response.data.message || 'Password reset failed.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Unable to connect to the server.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}
</script>