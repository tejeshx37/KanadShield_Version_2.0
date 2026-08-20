import { PageHeader } from '../components/ui/PageHeader';
import { NotYetImplemented } from '../components/ui/QueryStates';

export function LibraryPage() {
  return (
    <div>
      <PageHeader title="Library" description="Bookmarks, saved searches, alerts, and offline access." />
      <NotYetImplemented
        title="Library not yet built"
        description="Bookmarks/saved-search/alert CRUD and the offline download manager are specified in docs/API_CONTRACT.md but not yet implemented in this session."
      />
    </div>
  );
}
