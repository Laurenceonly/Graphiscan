import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserManagement from '../views/UserManagement.vue'
import AllResults from '../views/AllResults.vue'
import AuditLogs from '../views/AuditLogs.vue'
import ResultDetails from '../views/ResultDetails.vue'
import Students from '../views/Students.vue'
import AdminProgress from '../views/AdminProgress.vue'
import AdminProgressDetails from '../views/AdminProgressDetails.vue'
import AdminSettings from '../views/AdminSettings.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    component: Login
  },
  {
    path: '/admin/dashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/users',
    component: UserManagement,
    meta: { requiresAuth: true }
  },
  {
  path: '/admin/students',
  component: Students,
  meta: {
    requiresAuth: true
  } 
  },
  {
  path: '/admin/progress',
  component: AdminProgress,
  meta: {
    requiresAuth: true
  }
  },
  {
  path: '/admin/progress/:id',
  component: AdminProgressDetails,
  meta: {
    requiresAuth: true
  }
  },
  {
    path: '/admin/results',
    component: AllResults,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/results/:id',
    component: ResultDetails,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/audit-logs',
    component: AuditLogs,
    meta: { requiresAuth: true }
  },
  {
  path: '/admin/settings',
  name: 'AdminSettings',
  component: AdminSettings,
  meta: {
    requiresAdmin: true
  }
}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function clearAdminSession() {
  localStorage.removeItem('graphiscan_admin_auth')
  localStorage.removeItem('graphiscan_admin_token')
  localStorage.removeItem('graphiscan_admin_user')
}

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('graphiscan_admin_auth') === 'true'
  const token = localStorage.getItem('graphiscan_admin_token')

  if (to.meta.requiresAuth) {
    if (isAuthenticated && !token) {
      clearAdminSession()

      next({
        path: '/login',
        query: { session: 'expired' }
      })

      return
    }

    if (!isAuthenticated || !token) {
      clearAdminSession()
      next('/login')
      return
    }
  }

  if (to.path === '/login' && isAuthenticated && token) {
    next('/admin/dashboard')
    return
  }

  next()
})

export default router