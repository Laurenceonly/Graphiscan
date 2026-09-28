<template>
  <main class="mobile-login-page recovery-mobile-page">
    <section class="mobile-login-card recovery-card-clean">
      <div class="mobile-brand">
        <div class="mobile-brand-mark">G</div>

        <div>
          <h1>GRAPHI<span>SCAN</span></h1>
          <p>Account Recovery</p>
        </div>
      </div>

      <div class="mobile-login-copy compact recovery-copy">
        <span>Password Reset</span>
        <h2>Forgot password?</h2>
        <p>Enter your email to request password reset instructions.</p>
      </div>

      <form class="mobile-login-form recovery-clean-form" @submit.prevent="requestReset">
        <div class="form-group">
          <label>Email Address</label>

          <div class="input-wrap clean-recovery-input">
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

        <div class="recovery-info-note">
          <ShieldCheck :size="18" :stroke-width="1.9" />
          <span>
            If the email exists, reset instructions will be sent.
          </span>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <button class="login-submit-btn recovery-submit-btn" type="submit" :disabled="loading">
          <LoaderCircle
            v-if="loading"
            class="loading-icon"
            :size="18"
            :stroke-width="1.9"
          />

          <Send
            v-else
            :size="18"
            :stroke-width="1.9"
          />

          {{ loading ? 'Submitting...' : 'Send Reset Instructions' }}
        </button>

        <p class="auth-switch recovery-switch">
          Remembered your password?
          <RouterLink to="/login">Back to login</RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LoaderCircle,
  Mail,
  Send,
  ShieldCheck
} from 'lucide-vue-next'
import userApi from '../api/userApi'

const email = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

function clearMessages() {
  error.value = ''
  success.value = ''
}

function getResetMessage() {
  return 'If this email is registered, password reset instructions will be sent.'
}

async function requestReset() {
  clearMessages()

  const cleanEmail = email.value.trim().toLowerCase()

  if (!emailPattern.test(cleanEmail)) {
    error.value = 'Please enter a valid email address.'
    return
  }

  loading.value = true

  try {
    const response = await userApi.post('/forgot-password', {
      email: cleanEmail
    })

    success.value = response.data.message || getResetMessage()
    email.value = ''
  } catch (err) {
    success.value = getResetMessage()
    console.error(err)
  } finally {
    loading.value = false
  }
}
</script>