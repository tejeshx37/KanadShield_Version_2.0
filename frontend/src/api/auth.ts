import { apiClient } from './client'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string | null
  role: 'USER' | 'RESEARCHER' | 'ADMIN'
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  return data
}

export async function register(email: string, password: string, fullName?: string): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/auth/register', { email, password, full_name: fullName })
  return data
}

export async function fetchMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}
