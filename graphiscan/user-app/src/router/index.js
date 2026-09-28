import { createRouter, createWebHistory } from 'vue-router'

import userApi from '../api/userApi'

import Register from '../views/Register.vue'
import ForgotPassword from '../views/ForgotPassword.vue'
import ResetPassword from '../views/ResetPassword.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'

import TeacherDashboard from '../views/teacher/TeacherDashboard.vue'
import TeacherStudents from '../views/teacher/TeacherStudents.vue'
import TeacherAddStudent from '../views/teacher/TeacherAddStudent.vue'
import TeacherUploadSample from '../views/teacher/TeacherUploadSample.vue'
import TeacherResults from '../views/teacher/TeacherResults.vue'
import TeacherResultDetails from '../views/teacher/TeacherResultDetails.vue'
import TeacherStudentProgress from '../views/teacher/TeacherStudentProgress.vue'

import ParentDashboard from '../views/parent/ParentDashboard.vue'
import ParentResults from '../views/parent/ParentResults.vue'
import ParentResultDetails from '../views/parent/ParentResultDetails.vue'
import ParentStudentProgress from '../views/parent/ParentStudentProgress.vue'

import ExpertDashboard from '../views/expert/ExpertDashboard.vue'
import ExpertResults from '../views/expert/ExpertResults.vue'
import ExpertValidateResult from '../views/expert/ExpertValidateResult.vue'
import ExpertStudentProgress from '../views/expert/ExpertStudentProgress.vue'

import GuestDashboard from '../views/guest/GuestDashboard.vue'
import GuestDemoScreening from '../views/guest/GuestDemoScreening.vue'

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
    path: '/register',
    component: Register
  },
  {
    path: '/forgot-password',
    component: ForgotPassword
  },
  {
    path: '/reset-password',
    component: ResetPassword
  },
  {
  path: '/profile',
  component: Profile,
  meta: {
    requiresAuth: true
  }
},

  {
    path: '/teacher/dashboard',
    component: TeacherDashboard,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },
  {
    path: '/teacher/students',
    component: TeacherStudents,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },
  {
  path: '/teacher/students/:id/progress',
  component: TeacherStudentProgress,
  meta: {
    requiresAuth: true,
    role: 'teacher'
  }
  },
  {
    path: '/teacher/students/add',
    component: TeacherAddStudent,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },
  {
    path: '/teacher/upload',
    component: TeacherUploadSample,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },
  {
    path: '/teacher/results',
    component: TeacherResults,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },
  {
    path: '/teacher/results/:id',
    component: TeacherResultDetails,
    meta: {
      requiresAuth: true,
      role: 'teacher'
    }
  },

  {
    path: '/parent/dashboard',
    component: ParentDashboard,
    meta: {
      requiresAuth: true,
      role: 'parent'
    }
  },
  {
    path: '/parent/results',
    component: ParentResults,
    meta: {
      requiresAuth: true,
      role: 'parent'
    }
  },
  {
    path: '/parent/results/:id',
    component: ParentResultDetails,
    meta: {
      requiresAuth: true,
      role: 'parent'
    }
  },
  {
  path: '/parent/students/:id/progress',
  component: ParentStudentProgress,
  meta: {
    requiresAuth: true,
    role: 'parent'
  }
  },

  {
    path: '/expert/dashboard',
    component: ExpertDashboard,
    meta: {
      requiresAuth: true,
      role: 'expert'
    }
  },
  {
    path: '/expert/results',
    component: ExpertResults,
    meta: {
      requiresAuth: true,
      role: 'expert'
    }
  },
  {
  path: '/expert/students/:id/progress',
  component: ExpertStudentProgress,
  meta: {
    requiresAuth: true,
    role: 'expert'
  } 
  },
  {
    path: '/expert/validate/:id',
    component: ExpertValidateResult,
    meta: {
      requiresAuth: true,
      role: 'expert'
    }
  },

  {
    path: '/guest/dashboard',
    component: GuestDashboard,
    meta: {
      requiresAuth: true,
      role: 'guest'
    }
  },
  {
  path: '/guest/demo',
  component: GuestDemoScreening,
  meta: {
    requiresAuth: true,
    role: 'guest'
  }
}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function clearUserSession() {
  localStorage.removeItem('graphiscan_user_auth')
  localStorage.removeItem('graphiscan_user_token')
  localStorage.removeItem('graphiscan_user_data')
}

function getDashboardPath(role) {
  if (role === 'teacher') return '/teacher/dashboard'
  if (role === 'parent') return '/parent/dashboard'
  if (role === 'expert') return '/expert/dashboard'
  if (role === 'guest') return '/guest/dashboard'

  return '/login'
}

function getStoredUserData() {
  try {
    return JSON.parse(localStorage.getItem('graphiscan_user_data') || '{}')
  } catch {
    return {}
  }
}

async function verifyUserSession() {
  const response = await userApi.get('/me')

  if (!response.data.success || !response.data.user) {
    throw new Error('Invalid session.')
  }

  const freshUser = response.data.user

  if (freshUser.account_status && freshUser.account_status !== 'active') {
    throw new Error('Account is not active.')
  }

  localStorage.setItem('graphiscan_user_auth', 'true')
  localStorage.setItem('graphiscan_user_data', JSON.stringify(freshUser))

  return freshUser
}

router.beforeEach(async (to, from, next) => {
  const isAuthenticated = localStorage.getItem('graphiscan_user_auth') === 'true'
  const token = localStorage.getItem('graphiscan_user_token')

  if (to.meta.requiresAuth) {
    if (!isAuthenticated || !token) {
      clearUserSession()

      next({
        path: '/login',
        query: { session: 'expired' }
      })

      return
    }

    try {
      const freshUser = await verifyUserSession()

      if (to.meta.role && freshUser.role !== to.meta.role) {
        next(getDashboardPath(freshUser.role))
        return
      }

      next()
      return
    } catch (err) {
      console.error(err)

      clearUserSession()

      next({
        path: '/login',
        query: { session: 'inactive' }
      })

      return
    }
  }

  if (to.path === '/login' && isAuthenticated && token) {
    try {
      const freshUser = await verifyUserSession()

      next(getDashboardPath(freshUser.role))
      return
    } catch (err) {
      console.error(err)

      clearUserSession()

      next({
        path: '/login',
        query: { session: 'inactive' }
      })

      return
    }
  }

  const userData = getStoredUserData()

  if (
    (to.path === '/register' || to.path === '/forgot-password' || to.path === '/reset-password') &&
    isAuthenticated &&
    token &&
    userData.role
  ) {
    next(getDashboardPath(userData.role))
    return
  }

  next()
})

export default router