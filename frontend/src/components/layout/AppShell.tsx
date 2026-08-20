import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useOnlineStatus } from '@/lib/useOnlineStatus'

const NAV_ITEMS: { to: string; label: string }[] = [
  { to: '/search', label: 'Search' },
  { to: '/graph', label: 'Graph' },
  { to: '/change-radar', label: 'Change Radar' },
  { to: '/schemes', label: 'Schemes' },
  { to: '/research', label: 'Research' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/dashboard', label: 'Dashboard' },
]

export function AppShell() {
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)
  const isOnline = useOnlineStatus()

  return (
    <div className="min-h-screen bg-ink-50">
      {!isOnline && (
        <div className="bg-amber-100 px-4 py-1.5 text-center text-xs font-medium text-amber-900">
          You are offline — showing results from your downloaded documents. Connect to search the full database.
        </div>
      )}
      <header className="border-b border-ink-300/60 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-serif-display text-lg font-semibold text-brand-700">
            KanadShield
          </Link>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm font-medium ${
                    isActive ? 'bg-brand-100 text-brand-700' : 'text-ink-700 hover:bg-ink-100'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <Link to="/profile" className="text-sm font-medium text-ink-700 hover:text-brand-700">
                  {user.email}
                </Link>
                <button onClick={clearSession} className="text-sm text-ink-500 hover:text-ink-900">
                  Sign out
                </button>
              </>
            ) : (
              <Link to="/login" className="text-sm font-medium text-brand-700 hover:text-brand-600">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
