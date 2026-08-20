import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Archive,
  Landmark,
  Radar,
  LifeBuoy,
  BookMarked,
} from 'lucide-react';
import { useUiStore } from '../../store/uiStore';
import { t } from '../../i18n/strings';

const primaryNav = [
  { to: '/dashboard', icon: LayoutDashboard, key: 'nav_dashboard' },
  { to: '/research', icon: Search, key: 'nav_research' },
  { to: '/archives', icon: Archive, key: 'nav_archives' },
  { to: '/public-service', icon: Landmark, key: 'nav_public_service' },
  { to: '/insights', icon: Radar, key: 'nav_insights' },
];

const secondaryNav = [
  { to: '/support', icon: LifeBuoy, key: 'nav_support' },
  { to: '/library', icon: BookMarked, key: 'nav_library' },
];

function NavItem({ to, icon: Icon, label }: { to: string; icon: typeof LayoutDashboard; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-full px-4 py-2.5 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent-gold text-sidebar-text-active'
            : 'text-sidebar-text hover:bg-white/5 hover:text-sidebar-text-active'
        }`
      }
    >
      <Icon size={18} aria-hidden="true" />
      <span>{label}</span>
    </NavLink>
  );
}

export function Sidebar() {
  const language = useUiStore((s) => s.language);

  return (
    <aside className="flex h-full w-[220px] shrink-0 flex-col bg-sidebar-bg px-3 py-5">
      <div className="px-3 pb-5">
        <p className="font-serif text-lg font-bold text-sidebar-text-active">KanadShield</p>
        <p className="mt-0.5 text-xs text-sidebar-text">Legal &amp; Government Intelligence</p>
      </div>

      <button
        type="button"
        className="mb-6 w-full rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-sidebar-bg hover:bg-white/90"
      >
        {t('new_research', language)}
      </button>

      <nav className="flex flex-col gap-1" aria-label="Primary">
        {primaryNav.map((item) => (
          <NavItem key={item.to} to={item.to} icon={item.icon} label={t(item.key, language)} />
        ))}
      </nav>

      <div className="mt-6 border-t border-white/10 pt-4">
        <nav className="flex flex-col gap-1" aria-label="Secondary">
          {secondaryNav.map((item) => (
            <NavItem key={item.to} to={item.to} icon={item.icon} label={t(item.key, language)} />
          ))}
        </nav>
      </div>
    </aside>
  );
}
