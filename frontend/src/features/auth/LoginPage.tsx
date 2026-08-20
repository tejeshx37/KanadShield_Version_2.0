import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { login, register, fetchMe } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { extractErrorMessage } from '@/api/client'

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const setSession = useAuthStore((s) => s.setSession)
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: async () => {
      if (mode === 'register') {
        await register(email, password, fullName || undefined)
      }
      const tokens = await login(email, password)
      const tempUser = { id: '', email, full_name: null, role: 'USER' as const }
      setSession(tokens.access_token, tokens.refresh_token, tempUser)
      const user = await fetchMe()
      setSession(tokens.access_token, tokens.refresh_token, user)
      navigate('/')
    },
  })

  return (
    <div className="mx-auto max-w-sm py-12">
      <Card>
        <CardBody className="space-y-4">
          <h1 className="text-lg font-semibold text-ink-950">{mode === 'login' ? 'Sign in' : 'Create account'}</h1>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate()
            }}
          >
            {mode === 'register' && (
              <Input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            )}
            <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
            {mutation.isError && <p className="text-sm text-red-700">{extractErrorMessage(mutation.error)}</p>}
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>
          <button className="text-sm text-brand-700 hover:underline" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
          </button>
        </CardBody>
      </Card>
    </div>
  )
}
