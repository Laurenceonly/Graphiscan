<template>
  <main class="mobile-login-page">
    <section class="mobile-login-card user-login-card-clean">
      <div class="mobile-brand">
        <div class="mobile-brand-mark">G</div>

        <div>
          <h1>GRAPHI<span>SCAN</span></h1>
          <p>Teacher • Parent • Expert • Guest</p>
        </div>
      </div>

      <div class="mobile-login-copy">
        <span>User Access</span>
        <h2>Welcome back</h2>
        <p>
          Sign in to view your assigned records, screening results, progress,
          and validation tasks.
        </p>
      </div>

      <form class="mobile-login-form" @submit.prevent="loginUser">
        <div class="form-group">
          <label>Email Address</label>

          <div class="input-wrap clean-login-input">
            <Mail :size="18" :stroke-width="1.9" />

            <input
              v-model="email"
              type="email"
              placeholder="Enter your email"
              autocomplete="email"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label>Password</label>

          <div class="input-wrap clean-login-input">
            <LockKeyhole :size="18" :stroke-width="1.9" />

            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter your password"
              autocomplete="current-password"
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
        </div>

        <div class="login-access-note">
          <ShieldCheck :size="18" :stroke-width="1.9" />
          <span>Use the account approved for your role.</span>
        </div>

        <div class="login-options-row clean-login-link-row">
          <RouterLink to="/forgot-password">Forgot password?</RouterLink>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <button class="login-submit-btn" type="submit" :disabled="loading">
          <LoaderCircle
            v-if="loading"
            class="loading-icon"
            :size="18"
            :stroke-width="1.9"
          />
          <LogIn
            v-else
            :size="18"
            :stroke-width="1.9"
          />

          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>

        <p class="auth-switch">
          Don’t have an account?
          <RouterLink to="/register">Create account</RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  LogIn,
  Mail,
  ShieldCheck
} from 'lucide-vue-next'
import userApi from '../api/userApi'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)

const error = ref('')
const success = ref('')
const loading = ref(false)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

onMounted(() => {
  clearMessages()

  if (route.query.session === 'expired') {
    clearUserSession()
    error.value = 'Your session expired. Please log in again.'
  }

  if (route.query.session === 'inactive') {
    clearUserSession()
    error.value = 'Your account is no longer active. Please contact the administrator.'
  }

  if (route.query.session === 'unauthorized') {
    clearUserSession()
    error.value = 'You are not authorized to access that page.'
  }

  if (route.query.reset === 'success') {
    success.value = 'Password reset successfully. You may now log in.'
  }

  if (route.query.registered === 'success') {
    success.value = 'Account registered successfully. You may now log in.'
  }

  if (route.query.registered === 'pending') {
    success.value = 'Registration submitted. Please wait for account approval.'
  }
})

function clearUserSession() {
  localStorage.removeItem('graphiscan_user_auth')
  localStorage.removeItem('graphiscan_user_token')
  localStorage.removeItem('graphiscan_user_data')
}

function clearMessages() {
  error.value = ''
  success.value = ''
}

function validateLoginForm() {
  const cleanEmail = email.value.trim().toLowerCase()

  if (!cleanEmail || !password.value) {
    return 'Email and password are required.'
  }

  if (!emailPattern.test(cleanEmail)) {
    return 'Please enter a valid email address.'
  }

  return ''
}

async function loginUser() {
  clearMessages()

  const validationMessage = validateLoginForm()

  if (validationMessage) {
    error.value = validationMessage
    return
  }

  loading.value = true

  try {
    const response = await userApi.post('/login', {
      email: email.value.trim().toLowerCase(),
      password: password.value
    })

    if (response.data.success) {
      if (!response.data.token) {
        error.value = 'Login succeeded but no user token was returned.'
        return
      }

      localStorage.setItem('graphiscan_user_auth', 'true')
      localStorage.setItem('graphiscan_user_token', response.data.token)
      localStorage.setItem('graphiscan_user_data', JSON.stringify(response.data.user))

      success.value = 'Login successful.'

      router.replace(response.data.redirect_path)
    } else {
      error.value = response.data.message || 'Invalid email or password.'
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