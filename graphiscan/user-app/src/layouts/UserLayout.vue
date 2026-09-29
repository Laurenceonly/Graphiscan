<template>
  <div class="user-app-shell">
    <header class="mobile-app-header">
      <div>
        <p>{{ roleLabel }}</p>
        <h1>{{ title }}</h1>
      </div>

      <button
        class="mobile-profile-btn"
        type="button"
        title="Open profile"
        aria-label="Open profile"
        @click="goToProfile"
      >
        <UserRound :size="20" :stroke-width="1.9" aria-hidden="true" />
      </button>
    </header>

    <main class="mobile-content">
      <slot />
    </main>

    <nav v-if="navItems.length" class="mobile-bottom-nav" aria-label="App navigation">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        class="bottom-nav-item"
        :to="item.to"
      >
        <span class="bottom-nav-icon">
          <component :is="item.icon" :size="21" :stroke-width="2" />
        </span>

        <small>{{ item.label }}</small>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  ClipboardCheck,
  FileText,
  Home,
  ScanLine,
  UploadCloud,
  UserRound,
  UsersRound
} from 'lucide-vue-next'

defineProps({
  title: {
    type: String,
    default: 'Dashboard'
  }
})

const router = useRouter()

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

const userData = getStoredUserData()

const roleLabel = computed(() => {
  if (userData.role === 'teacher') return 'Teacher Workspace'
  if (userData.role === 'parent') return 'Parent Workspace'
  if (userData.role === 'expert') return 'Expert / SPED Workspace'
  if (userData.role === 'guest') return 'Guest Preview'
  return 'GRAPHISCAN App'
})

const navItems = computed(() => {
  if (userData.role === 'teacher') {
    return [
      { label: 'Home', icon: Home, to: '/teacher/dashboard' },
      { label: 'Students', icon: UsersRound, to: '/teacher/students' },
      { label: 'Upload', icon: UploadCloud, to: '/teacher/upload' },
      { label: 'Results', icon: FileText, to: '/teacher/results' },
      { label: 'Profile', icon: UserRound, to: '/profile' }
    ]
  }

  if (userData.role === 'expert') {
    return [
      { label: 'Home', icon: Home, to: '/expert/dashboard' },
      { label: 'Queue', icon: ClipboardCheck, to: '/expert/results' },
      { label: 'Profile', icon: UserRound, to: '/profile' }
    ]
  }

  if (userData.role === 'parent') {
    return [
      { label: 'Home', icon: Home, to: '/parent/dashboard' },
      { label: 'Results', icon: FileText, to: '/parent/results' },
      { label: 'Profile', icon: UserRound, to: '/profile' }
    ]
  }

  if (userData.role === 'guest') {
  return [
    { label: 'Home', icon: Home, to: '/guest/dashboard' },
    { label: 'Demo', icon: ScanLine, to: '/guest/demo' },
    { label: 'Profile', icon: UserRound, to: '/profile' }
  ]
}

  return []
})

function goToProfile() {
  router.push('/profile')
}
</script>
