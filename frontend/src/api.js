import axios from 'axios'
import { authStore } from './stores/auth'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // update/backup/restore can legitimately take a while
})

api.interceptors.request.use((config) => {
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      authStore.logout()
    }
    return Promise.reject(error)
  },
)

export default api
