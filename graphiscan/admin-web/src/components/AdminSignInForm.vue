<template>
  <div class="admin-signin-form">
    <div class="admin-signin-intro">
      <h1 id="access-title">Welcome back</h1>
      <p>Sign in to your admin account.</p>
    </div>

    <form @submit.prevent="$emit('submit')">
      <div class="admin-signin-field">
        <label for="hosted-email">Email address</label>
        <div class="admin-signin-input">
          <Mail :size="18" :stroke-width="1.7" aria-hidden="true" />
          <input id="hosted-email" v-model="fields.email" type="email" autocomplete="username"
            placeholder="Enter your email" required :disabled="busy" />
        </div>
      </div>

      <div class="admin-signin-field">
        <label for="hosted-password">Password</label>
        <div class="admin-signin-input">
          <LockKeyhole :size="18" :stroke-width="1.7" aria-hidden="true" />
          <input id="hosted-password" v-model="fields.password" :type="fields.showPassword ? 'text' : 'password'"
            autocomplete="current-password" placeholder="Your password" required :disabled="busy" />
          <button class="admin-signin-toggle" type="button" :disabled="busy"
            :aria-label="fields.showPassword ? 'Hide password' : 'Show password'"
            :aria-pressed="fields.showPassword" aria-controls="hosted-password"
            @click="fields.showPassword = !fields.showPassword">
            <EyeOff v-if="fields.showPassword" :size="18" :stroke-width="1.7" aria-hidden="true" />
            <Eye v-else :size="18" :stroke-width="1.7" aria-hidden="true" />
          </button>
        </div>
      </div>

      <p v-if="error" class="admin-signin-error" role="alert">{{ error }}</p>
      <p v-if="message" class="admin-signin-message" role="status">{{ message }}</p>
      <button class="admin-signin-submit" type="submit" :disabled="busy">
        <span>{{ busy ? 'Signing in…' : 'Sign in' }}</span>
        <ArrowRight :size="18" :stroke-width="1.8" aria-hidden="true" />
      </button>
    </form>
  </div>
</template>

<script setup>
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from 'lucide-vue-next'
defineProps({
  fields: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
  message: { type: String, default: '' }
})
defineEmits(['submit'])
</script>
