import { Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useUiStore, type LanguageCode } from '../../store/uiStore';
import { languageLabels, t } from '../../i18n/strings';
import { useDepartments } from '../../api/hooks';

export function Topbar() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const language = useUiStore((s) => s.language);
  const setLanguage = useUiStore((s) => s.setLanguage);
  const activeDepartmentId = useUiStore((s) => s.activeDepartmentId);
  const setActiveDepartment = useUiStore((s) => s.setActiveDepartment);
  const { data: departments } = useDepartments();

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/research?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <header className="flex items-center gap-4 border-b border-card-border bg-canvas-bg px-8 py-4">
      <form onSubmit={handleSearchSubmit} className="flex-1">
        <div className="flex items-center gap-2 rounded-full border border-card-border bg-card-bg px-4 py-2">
          <Search size={16} className="text-ink-muted" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('search_placeholder', language)}
            aria-label="Global search"
            className="w-full bg-transparent text-sm text-ink placeholder:text-ink-muted focus:outline-none"
          />
        </div>
      </form>

      <label className="sr-only" htmlFor="department-switcher">
        Department context
      </label>
      <select
        id="department-switcher"
        value={activeDepartmentId ?? ''}
        onChange={(e) => setActiveDepartment(e.target.value || null)}
        className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm text-ink"
      >
        <option value="">All departments</option>
        {departments?.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name}
          </option>
        ))}
      </select>

      <label className="sr-only" htmlFor="language-switcher">
        Language
      </label>
      <select
        id="language-switcher"
        value={language}
        onChange={(e) => setLanguage(e.target.value as LanguageCode)}
        className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm text-ink"
      >
        {(Object.keys(languageLabels) as LanguageCode[]).map((code) => (
          <option key={code} value={code}>
            {languageLabels[code]}
          </option>
        ))}
      </select>
    </header>
  );
}
