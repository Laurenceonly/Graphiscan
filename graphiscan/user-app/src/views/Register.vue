<template>
  <main class="mobile-login-page register-mobile-page">
    <section class="mobile-login-card register-card register-card-clean">
      <div class="mobile-brand">
        <div>
          <h1>GRAPHI<span>SCAN</span></h1>
          <p>User App Registration</p>
        </div>
      </div>

      <div class="mobile-login-copy compact">
        <span>Create Access</span>
        <h2>Create account</h2>
        <p>
          Register based on your role. Guest access starts immediately, while other roles need approval.
        </p>
      </div>

      <form class="mobile-login-form register-clean-form" @submit.prevent="registerUser">
        <div class="form-group">
          <label>Full Name</label>

          <div class="input-wrap clean-register-input">
            <UserRound :size="18" :stroke-width="1.9" />

            <input
              v-model="fullname"
              type="text"
              placeholder="Enter your full name"
              autocomplete="name"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label>Email Address</label>

          <div class="input-wrap clean-register-input">
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
          <label>Role</label>

          <div class="input-wrap clean-register-input">
            <ShieldCheck :size="18" :stroke-width="1.9" />

            <select v-model="role" required>
              <option value="">Select your role</option>
              <option value="guest">Guest</option>
              <option value="parent">Parent / Guardian</option>
              <option value="teacher">Teacher</option>
              <option value="expert">Expert</option>
            </select>
          </div>

          <div v-if="role" class="role-note-card">
            <ShieldCheck :size="17" :stroke-width="1.8" />
            <p>{{ roleNote }}</p>
          </div>
        </div>

        <div class="form-group">
          <label>Contact Number</label>

          <div class="input-wrap clean-register-input">
            <Phone :size="18" :stroke-width="1.9" />

            <input
              v-model="contactNo"
              type="text"
              placeholder="Optional contact number"
              autocomplete="tel"
            />
          </div>
        </div>

        <div class="form-group">
          <label>Password</label>

          <div class="input-wrap clean-register-input">
            <LockKeyhole :size="18" :stroke-width="1.9" />

            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Create a strong password"
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

          <div class="password-strength clean-password-strength">
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

            <ul class="password-rules clean-password-rules">
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

          <div class="input-wrap clean-register-input">
            <KeyRound :size="18" :stroke-width="1.9" />

            <input
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="Re-enter your password"
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

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="success" class="success-message">{{ success }}</p>

        <button class="login-submit-btn" type="submit" :disabled="loading">
          <LoaderCircle
            v-if="loading"
            class="loading-icon"
            :size="18"
            :stroke-width="1.9"
          />
          <UserPlus
            v-else
            :size="18"
            :stroke-width="1.9"
          />

          {{ loading ? 'Creating account...' : 'Create Account' }}
        </button>

        <p class="auth-switch">
          Already have an account?
          <RouterLink to="/login">Sign in</RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Phone,
  ShieldCheck,
  UserPlus,
  UserRound
} from 'lucide-vue-next'
import userApi from '../api/userApi'

const router = useRouter()

const fullname = ref('')
const email = ref('')
const role = ref('')
const contactNo = ref('')
const password = ref('')
const confirmPassword = ref('')

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const error = ref('')
const success = ref('')
const loading = ref(false)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

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

const roleNote = computed(() => {
  if (role.value === 'guest') {
    return 'Guest accounts can use demo screening features after registration.'
  }

  if (role.value === 'parent') {
    return 'Parent accounts need approval before viewing child records.'
  }

  if (role.value === 'teacher') {
    return 'Teacher accounts need admin approval before managing students.'
  }

  if (role.value === 'expert') {
    return 'Expert accounts need admin approval before reviewing screening results.'
  }

  return ''
})

function clearMessages() {
  error.value = ''
  success.value = ''
}

function validateForm() {
  const cleanName = fullname.value.trim()
  const cleanEmail = email.value.trim().toLowerCase()

  if (!cleanName) {
    return 'Please enter your full name.'
  }

  if (!emailPattern.test(cleanEmail)) {
    return 'Please enter a valid email address.'
  }

  if (!role.value) {
    return 'Please select your role.'
  }

  if (strengthScore.value < 5) {
    return 'Please create a stronger password.'
  }

  if (password.value !== confirmPassword.value) {
    return 'Passwords do not match.'
  }

  return ''
}

function getRegisteredQuery(data) {
  const status = String(data?.user?.account_status || data?.account_status || '').toLowerCase()

  if (role.value === 'guest' || status === 'active') {
    return 'success'
  }

  return 'pending'
}

async function registerUser() {
  clearMessages()

  const validationMessage = validateForm()

  if (validationMessage) {
    error.value = validationMessage
    return
  }

  loading.value = true

  try {
    const response = await userApi.post('/register', {
      fullname: fullname.value.trim(),
      email: email.value.trim().toLowerCase(),
      role: role.value,
      contact_no: contactNo.value.trim(),
      password: password.value,
      confirm_password: confirmPassword.value
    })

    if (response.data.success) {
      success.value = response.data.message || 'Registration submitted.'

      const registeredQuery = getRegisteredQuery(response.data)

      setTimeout(() => {
        router.push({
          path: '/login',
          query: {
            registered: registeredQuery
          }
        })
      }, 900)
    } else {
      error.value = response.data.message || 'Registration failed.'
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
