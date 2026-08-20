export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api/v1'
export const SUPPORTED_LANGUAGES = ((import.meta.env.VITE_SUPPORTED_LANGUAGES as string | undefined) ?? 'en,gu,hi')
  .split(',')
  .map((l) => l.trim())
  .filter(Boolean)
