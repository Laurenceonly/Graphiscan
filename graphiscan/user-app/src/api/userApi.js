import axios from 'axios'

export const API_ORIGIN = (import.meta.env.VITE_API_ORIGIN || 'http://localhost:5000').replace(/\/$/, '')

const userApi = axios.create({
  baseURL: `${API_ORIGIN}/api/user`
})

userApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('graphiscan_user_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

function clearUserSession() {
  localStorage.removeItem('graphiscan_user_auth')
  localStorage.removeItem('graphiscan_user_token')
  localStorage.removeItem('graphiscan_user_data')
}

userApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearUserSession()

      if (window.location.pathname !== '/login') {
        window.location.href = '/login?session=expired'
      }
    }

    return Promise.reject(error)
  }
)

export function getImageUrl(imagePath) {
  if (!imagePath) return ''

  const cleanPath = String(imagePath).replaceAll('\\', '/')

  if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
    return cleanPath
  }

  if (cleanPath.startsWith('/')) {
    return `${API_ORIGIN}${cleanPath}`
  }

  return `${API_ORIGIN}/${cleanPath}`
}

export default userApi
