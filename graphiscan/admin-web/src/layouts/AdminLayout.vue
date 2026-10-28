<template>
  <div class="admin-shell">
    <Transition name="sidebar-scrim">
    <button
      v-if="isMenuOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Close navigation"
      @click="closeMenu"
    ></button>
    </Transition>

    <aside id="admin-navigation" ref="sidebarRef" class="sidebar" :class="{ 'is-open': isMenuOpen }" aria-label="Admin navigation">
      <div class="brand">
        <slot name="brand">
        <div>
          <h1>Graphi<span>Scan</span></h1>
          <p>Admin Workspace</p>
        </div>
        </slot>
        <button class="sidebar-close-btn" type="button" aria-label="Close navigation" @click="closeMenu">
          <X :size="20" :stroke-width="1.8" />
        </button>
      </div>

      <slot name="navigation" :close-menu="closeMenu">
      <div
        v-for="section in navigationSections"
        :key="section.label"
        class="sidebar-section"
      >
        <p class="sidebar-label">{{ section.label }}</p>

        <nav class="nav-menu" :aria-label="section.label">
          <RouterLink
            v-for="item in section.links"
            :key="item.to"
            class="nav-link"
            :to="item.to"
            @click="closeMenu"
          >
            <span class="nav-icon">
              <component :is="item.icon" :size="17" :stroke-width="1.8" />
            </span>

            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>

      </slot>
      <button class="logout-btn" type="button" @click="openLogoutModal">
        <LogOut :size="16" :stroke-width="1.8" />
        <span>Logout</span>
      </button>
    </aside>

    <main class="main-panel" :inert="isNarrow && isMenuOpen ? '' : null">
      <header class="topbar">
        <button
          ref="menuButtonRef"
          class="mobile-nav-toggle"
          type="button"
          aria-label="Open navigation"
          aria-controls="admin-navigation"
          :aria-expanded="isMenuOpen"
          @click="openMenu"
        >
          <Menu :size="21" :stroke-width="1.8" />
        </button>
        <slot name="topbar"><span class="mobile-header-brand">GraphiScan</span></slot>
      </header>

      <section class="content">
        <slot />
      </section>
    </main>

    <div v-if="showLogoutModal" v-dialog="closeLogoutModal" class="modal-backdrop">
      <section class="logout-confirm-modal">
        <div class="standard-modal-head">
          <h2>Log out?</h2>
          <button
            class="modal-close-btn"
            aria-label="Close logout confirmation"
            type="button"
            :disabled="logoutLoading"
            @click="closeLogoutModal"
          >
            <X :size="18" :stroke-width="1.8" />
          </button>
        </div>

        <div class="danger-modal-copy">
          <p>You will need to sign in again to access the workspace.</p>
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
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import adminApi from '../api/adminApi'
import {
  FileText,
  GraduationCap,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  TrendingUp,
  Users,
  X
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const props = defineProps({ signOut: { type: Function, default: null } })

const showLogoutModal = ref(false)
const logoutLoading = ref(false)
const isMenuOpen = ref(false)
const isNarrow = ref(false)
const sidebarRef = ref(null)
const menuButtonRef = ref(null)
let navMedia

function syncNavWidth(event) {
  isNarrow.value = event.matches
  if (!event.matches) closeMenu()
}

function closeMenu() {
  isMenuOpen.value = false
}

async function openMenu() {
  isMenuOpen.value = true
  await nextTick()
  sidebarRef.value?.querySelector('.nav-link')?.focus()
}

function onKeydown(event) {
  if (event.key === 'Escape' && isMenuOpen.value) {
    closeMenu()
    nextTick(() => menuButtonRef.value?.focus())
  } else if (event.key === 'Tab' && isMenuOpen.value) {
    const controls = [...sidebarRef.value.querySelectorAll('a[href], button')]
      .filter(element => !element.disabled && element.getClientRects().length)
    const first = controls[0]
    const last = controls.at(-1)
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last?.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first?.focus()
    }
  }
}

watch(() => route.fullPath, closeMenu)
watch(isMenuOpen, (open) => {
  document.body.classList.toggle('admin-nav-open', open)
})

onMounted(() => {
  navMedia = window.matchMedia('(max-width: 1100px)')
  syncNavWidth(navMedia)
  navMedia.addEventListener('change', syncNavWidth)
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  navMedia?.removeEventListener('change', syncNavWidth)
  window.removeEventListener('keydown', onKeydown)
  document.body.classList.remove('admin-nav-open')
})

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

  if (props.signOut) {
    try { await props.signOut() }
    finally { logoutLoading.value = false; showLogoutModal.value = false }
    return
  }

  try {
    await adminApi.post('/logout')
  } catch (err) {
    console.error(err)
  } finally {
    clearAdminSession()

    showLogoutModal.value = false
    logoutLoading.value = false

    router.replace('/legacy-login')
  }
}
</script>
