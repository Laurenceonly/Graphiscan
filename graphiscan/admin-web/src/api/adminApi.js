// =========================================================
// ADMIN API HELPER
// Central Axios setup for all Vue admin API requests
// =========================================================

import axios from 'axios'

const adminApi = axios.create({
  baseURL: 'http://127.0.0.1:5000/api/admin'
})


// =========================================================
// REQUEST INTERCEPTOR
// Automatically attaches the admin token to every request
// =========================================================

adminApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('graphiscan_admin_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})


// =========================================================
// SESSION CLEANUP
// Removes stale admin login data from browser storage
// =========================================================

function clearAdminSession() {
  localStorage.removeItem('graphiscan_admin_auth')
  localStorage.removeItem('graphiscan_admin_token')
  localStorage.removeItem('graphiscan_admin_user')
}


// =========================================================
// RESPONSE INTERCEPTOR
// Handles expired/missing token errors properly
// =========================================================

adminApi.interceptors.response.use(
  (response) => response,

  (error) => {
    if (error.response && error.response.status === 401) {
      clearAdminSession()

      if (window.location.pathname !== '/login') {
        window.location.href = '/login?session=expired'
      }
    }

    return Promise.reject(error)
  }
)

export default adminApi