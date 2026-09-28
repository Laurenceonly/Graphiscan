<template>
  <main class="modern-login-page">
    <section class="login-shell">
      <div class="login-left">
        <div class="login-brand-row">
          <div class="login-brand-mark">G</div>

          <div>
            <h1>GRAPHI<span>SCAN</span></h1>
            <p>Admin Web Panel</p>
          </div>
        </div>

        <div class="login-copy">
          <span class="login-kicker">Administrator Access</span>
          <h2>Welcome back</h2>
          <p>
            Sign in to manage users, students, screening results, progress records,
            audit logs, and system settings.
          </p>
        </div>

        <form class="modern-login-form" @submit.prevent="loginAdmin">
          <div class="form-group">
            <label>Email Address</label>

            <div class="input-wrap">
              <Mail :size="18" :stroke-width="1.8" />
              <input
                v-model="email"
                type="email"
                placeholder="Enter admin email"
                autocomplete="email"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Password</label>

            <div class="input-wrap login-password-wrap">
              <LockKeyhole :size="18" :stroke-width="1.8" />

              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter password"
                autocomplete="current-password"
                required
              />

              <button
                class="login-password-toggle"
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
            <ShieldCheck :size="18" :stroke-width="1.8" />
            <span>Administrator accounts only.</span>
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
        </form>
      </div>

      <div class="login-right">
        <div class="hero-panel">
          <div class="hero-bg-shape one"></div>
          <div class="hero-bg-shape two"></div>

          <div class="hero-logo">G</div>

          <div class="hero-content">
            <span>GRAPHISCAN</span>
            <h2>Dysgraphia Detection and Management System</h2>
            <p>
              A centralized admin workspace for user management, student records,
              AI screening results, expert validation, and audit monitoring.
            </p>
          </div>

          <div class="hero-floating-card">
            <div>
              <strong>Admin Monitoring</strong>
              <p>Track screening activity, validation status, progress, and system records.</p>
            </div>

            <div class="mini-avatars">
              <span>T</span>
              <span>P</span>
              <span>E</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  LogIn,
  Mail,
  ShieldCheck
} from 'lucide-vue-next'
import adminApi from '../api/adminApi'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const success = ref('')
const loading = ref(false)

onMounted(() => {
  if (route.query.session === 'expired') {
    error.value = 'Your admin session expired. Please log in again.'
  }
})

async function loginAdmin() {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    const response = await adminApi.post('/login', {
      email: email.value.trim(),
      password: password.value
    })

    if (response.data.success) {
      if (!response.data.token) {
        error.value = 'Login succeeded but no admin token was returned.'
        return
      }

      localStorage.setItem('graphiscan_admin_auth', 'true')
      localStorage.setItem('graphiscan_admin_token', response.data.token)
      localStorage.setItem('graphiscan_admin_user', JSON.stringify(response.data.user))

      success.value = 'Login successful.'
      router.replace('/admin/dashboard')
    } else {
      error.value = response.data.message || 'Login failed.'
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message
    } else {
      error.value = 'Failed to connect to Flask API.'
    }

    console.error(err)
  } finally {
    loading.value = false
  }
}
</script>