<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">G</div>

        <div>
          <h1>GRAPHI<span>SCAN</span></h1>
          <p>Admin Workspace</p>
        </div>
      </div>

      <div
        v-for="section in navigationSections"
        :key="section.label"
        class="sidebar-section"
      >
        <p class="sidebar-label">{{ section.label }}</p>

        <nav class="nav-menu">
          <RouterLink
            v-for="item in section.links"
            :key="item.to"
            class="nav-link"
            :to="item.to"
          >
            <span class="nav-icon">
              <component :is="item.icon" :size="17" :stroke-width="1.8" />
            </span>

            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>

      <button class="logout-btn" type="button" @click="openLogoutModal">
        <LogOut :size="16" :stroke-width="1.8" />
        <span>Logout</span>
      </button>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <h2>{{ title }}</h2>
        </div>

        <div class="topbar-actions">
          <div class="admin-profile admin-profile-static">
            <div class="avatar">{{ adminInitial }}</div>

            <div>
              <strong>{{ adminName }}</strong>
              <small>System Administrator</small>
            </div>
          </div>
        </div>
      </header>

      <section class="content">
        <slot />
      </section>
    </main>

    <div v-if="showLogoutModal" class="modal-backdrop">
      <section class="logout-confirm-modal">
        <div class="danger-modal-head">
          <div class="danger-icon">
            <AlertTriangle :size="26" :stroke-width="1.8" />
          </div>

          <button
            class="modal-close-btn"
            type="button"
            :disabled="logoutLoading"
            @click="closeLogoutModal"
          >
            <X :size="18" :stroke-width="1.8" />
          </button>
        </div>

        <div class="danger-modal-copy">
          <span>Confirm Logout</span>
          <h2>Log out?</h2>
          <p>You will need to sign in again to access the admin workspace.</p>
        </div>

        <div class="logout-modal-actions">
          <button
            class="cancel-btn"
            type="button"
            :disabled="logoutLoading"
            @click="closeLogoutModal"
          >
            Cancel
          </button>

          <button
            class="confirm-delete-btn"
            type="button"
            :disabled="logoutLoading"
            @click="logoutAdmin"
          >
            {{ logoutLoading ? 'Logging out...' : 'Logout' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import adminApi from '../api/adminApi'
import {
  AlertTriangle,
  FileText,
  GraduationCap,
  History,
  LayoutDashboard,
  LogOut,
  Settings,
  TrendingUp,
  Users,
  X
} from 'lucide-vue-next'

defineProps({
  title: {
    type: String,
    default: 'Admin Dashboard'
  }
})

const router = useRouter()

const showLogoutModal = ref(false)
const logoutLoading = ref(false)

function getStoredAdminUser() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_admin_user') || '{}')
  } catch {
    return {}
  }
}

const adminUser = getStoredAdminUser()

const navigationSections = [
  {
    label: 'Overview',
    links: [
      {
        label: 'Dashboard',
        to: '/admin/dashboard',
        icon: LayoutDashboard
      }
    ]
  },
  {
    label: 'Management',
    links: [
      {
        label: 'Users',
        to: '/admin/users',
        icon: Users
      },
      {
        label: 'Students',
        to: '/admin/students',
        icon: GraduationCap
      }
    ]
  },
  {
    label: 'Screening',
    links: [
      {
        label: 'Results',
        to: '/admin/results',
        icon: FileText
      },
      {
        label: 'Progress',
        to: '/admin/progress',
        icon: TrendingUp
      }
    ]
  },
  {
    label: 'System',
    links: [
      {
        label: 'Audit Logs',
        to: '/admin/audit-logs',
        icon: History
      },
      {
        label: 'Settings',
        to: '/admin/settings',
        icon: Settings
      }
    ]
  }
]

const adminName = computed(() => {
  return adminUser.fullname || 'Admin'
})

const adminInitial = computed(() => {
  return adminName.value ? adminName.value.charAt(0).toUpperCase() : 'A'
})

function openLogoutModal() {
  showLogoutModal.value = true
}

function closeLogoutModal() {
  if (logoutLoading.value) return

  showLogoutModal.value = false
}

function clearAdminSession() {
  localStorage.removeItem('graphiscan_admin_auth')
  localStorage.removeItem('graphiscan_admin_token')
  localStorage.removeItem('graphiscan_admin_user')
}

async function logoutAdmin() {
  logoutLoading.value = true

  try {
    await adminApi.post('/logout')
  } catch (err) {
    console.error(err)
  } finally {
    clearAdminSession()

    showLogoutModal.value = false
    logoutLoading.value = false

    router.replace('/login')
  }
}
</script>