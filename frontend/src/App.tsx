import { Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { HomePage } from '@/pages/HomePage'
import { SearchPage } from '@/features/search/SearchPage'
import { DocumentDetailPage } from '@/features/documents/DocumentDetailPage'
import { ActDetailPage } from '@/features/acts/ActDetailPage'
import { JudgmentDetailPage } from '@/features/judgments/JudgmentDetailPage'
import { GraphPage } from '@/features/graph/GraphPage'
import { TimelinePage } from '@/features/timeline/TimelinePage'
import { ChangeRadarPage } from '@/features/changeRadar/ChangeRadarPage'
import { SchemesPage } from '@/features/schemes/SchemesPage'
import { SchemeMatchPage } from '@/features/schemes/SchemeMatchPage'
import { ResearchPage } from '@/features/research/ResearchPage'
import { AlertsPage } from '@/features/alerts/AlertsPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { SettingsPage } from '@/features/settings/SettingsPage'
import { LoginPage } from '@/features/auth/LoginPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
        <Route path="/documents/:id/timeline" element={<TimelinePage />} />
        <Route path="/acts/:id" element={<ActDetailPage />} />
        <Route path="/judgments/:id" element={<JudgmentDetailPage />} />
        <Route path="/graph" element={<GraphPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/change-radar" element={<ChangeRadarPage />} />
        <Route path="/schemes" element={<SchemesPage />} />
        <Route path="/schemes/match" element={<SchemeMatchPage />} />
        <Route path="/research" element={<ResearchPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Route>
    </Routes>
  )
}
