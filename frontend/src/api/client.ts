import axios, { AxiosError } from 'axios'
import { API_BASE_URL } from '@/lib/env'
import { useAuthStore } from '@/store/authStore'

export const apiClient = axios.create({ baseURL: API_BASE_URL })

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken
  if (!refreshToken) return null
  try {
    const resp = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
    const { access_token, refresh_token } = resp.data
    const user = useAuthStore.getState().user
    if (user) useAuthStore.getState().setSession(access_token, refresh_token, user)
    return access_token
  } catch {
    useAuthStore.getState().clearSession()
    return null
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config
    if (error.response?.status === 401 && original && !(original as { _retry?: boolean })._retry) {
      ;(original as { _retry?: boolean })._retry = true
      refreshInFlight ??= refreshAccessToken()
      const newToken = await refreshInFlight
      refreshInFlight = null
      if (newToken) {
        original.headers = original.headers ?? {}
        original.headers.Authorization = `Bearer ${newToken}`
        return apiClient(original)
      }
    }
    return Promise.reject(error)
  },
)

export interface ApiErrorBody {
  error: { code: string; message: string }
}

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined
    if (body?.error?.message) return body.error.message
  }
  return 'Something went wrong. Please try again.'
}
