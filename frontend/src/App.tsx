import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ResearchPage } from './pages/ResearchPage';
import { ArchivesPage } from './pages/ArchivesPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';
import { InsightsPage } from './pages/InsightsPage';
import { PublicServicePage } from './pages/PublicServicePage';
import { LibraryPage } from './pages/LibraryPage';
import { SupportPage } from './pages/SupportPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/archives" element={<ArchivesPage />} />
            <Route path="/archives/documents/:id" element={<DocumentDetailPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/public-service" element={<PublicServicePage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/support" element={<SupportPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
