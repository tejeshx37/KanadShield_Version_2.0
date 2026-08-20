import { PageHeader } from '../components/ui/PageHeader';
import { NotYetImplemented } from '../components/ui/QueryStates';

export function PublicServicePage() {
  return (
    <div>
      <PageHeader
        title="Public Service"
        description="Scheme discovery and citizen entitlement matching."
      />
      <NotYetImplemented
        title="Public Service not yet built"
        description="Scheme discovery, the manual profile form, and the DigiLocker verification flow are specified in docs/API_CONTRACT.md (/schemes, /entitlement/*) but not yet implemented in this session."
      />
    </div>
  );
}
