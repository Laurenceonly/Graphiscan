<template>
  <UserLayout title="Profile">
    <section class="mobile-profile-page">
      <div class="profile-hero-card">
        <div class="profile-avatar-large">
          <UserRound :size="30" :stroke-width="1.8" aria-hidden="true" />
        </div>

        <div>
          <span>{{ readableRole }}</span>
          <h2>{{ userData.fullname || 'GRAPHISCAN User' }}</h2>
          <p>{{ userData.email || 'No email available' }}</p>
        </div>
      </div>

      <div class="profile-info-card">
        <div class="profile-section-head">
          <span>Account Details</span>
          <h3>Profile information</h3>
        </div>

        <div class="profile-detail-list">
          <div class="profile-detail-item">
            <small>Full Name</small>
            <strong>{{ userData.fullname || 'N/A' }}</strong>
          </div>

          <div class="profile-detail-item">
            <small>Email Address</small>
            <strong>{{ userData.email || 'N/A' }}</strong>
          </div>

          <div class="profile-detail-item">
            <small>Role</small>
            <strong>{{ readableRole }}</strong>
          </div>

          <div class="profile-detail-item">
            <small>Account Status</small>
            <strong class="profile-status-active">
              {{ formatStatus(userData.account_status) }}
            </strong>
          </div>
        </div>
      </div>

      <div class="profile-info-card">
        <div class="profile-section-head">
          <span>Security</span>
          <h3>Session controls</h3>
          <p>
            Use this option when you are done using GRAPHISCAN on this device.
          </p>
        </div>

        <button class="profile-logout-btn" type="button" @click="openLogoutModal">
          Logout
        </button>
      </div>

      <div v-if="showLogoutModal" class="mobile-modal-backdrop">
        <section class="mobile-confirm-modal">
          <div class="mobile-confirm-icon">
            !
          </div>

          <div class="mobile-confirm-copy">
            <span>Confirm Logout</span>
            <h2>Log out of GRAPHISCAN?</h2>

            <p>
              You are about to end your current {{ readableRole.toLowerCase() }} session.
              You will need to sign in again to continue.
            </p>
          </div>

          <div class="mobile-logout-user-card">
            <strong>{{ userData.fullname || 'GRAPHISCAN User' }}</strong>
            <small>{{ userData.email || 'No email available' }}</small>
          </div>

          <div class="mobile-confirm-actions">
            <button
              class="mobile-cancel-btn"
              type="button"
              :disabled="logoutLoading"
              @click="closeLogoutModal"
            >
              Cancel
            </button>

            <button
              class="mobile-danger-btn"
              type="button"
              :disabled="logoutLoading"
              @click="logoutUser"
            >
              {{ logoutLoading ? 'Logging out...' : 'Logout' }}
            </button>
          </div>
        </section>
      </div>
    </section>
  </UserLayout>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserRound } from 'lucide-vue-next'
import UserLayout from '../layouts/UserLayout.vue'
import userApi from '../api/userApi'

const router = useRouter()

const showLogoutModal = ref(false)
const logoutLoading = ref(false)

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

const userData = getStoredUserData()

const readableRole = computed(() => {
  if (userData.role === 'teacher') return 'Teacher'
  if (userData.role === 'parent') return 'Parent / Guardian'
  if (userData.role === 'expert') return 'Expert / SPED'
  if (userData.role === 'guest') return 'Guest'
  return 'User'
})

function formatStatus(status) {
  if (status === 'active') return 'Active'
  if (status === 'pending') return 'Pending Approval'
  if (status === 'disabled') return 'Disabled'
  if (status === 'rejected') return 'Rejected'
  return 'Active'
}

function openLogoutModal() {
  showLogoutModal.value = true
}

function closeLogoutModal() {
  if (logoutLoading.value) return

  showLogoutModal.value = false
}

function clearUserSession() {
  localStorage.removeItem('graphiscan_user_auth')
  localStorage.removeItem('graphiscan_user_token')
  localStorage.removeItem('graphiscan_user_data')
}

async function logoutUser() {
  logoutLoading.value = true

  try {
    await userApi.post('/logout')
  } catch (err) {
    console.error(err)
  } finally {
    clearUserSession()
    showLogoutModal.value = false
    logoutLoading.value = false
    router.replace('/login')
  }
}
</script>
