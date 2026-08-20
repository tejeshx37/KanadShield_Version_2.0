import { PageHeader } from '../components/ui/PageHeader';
import { NotYetImplemented } from '../components/ui/QueryStates';

export function SupportPage() {
  return (
    <div>
      <PageHeader title="Support" description="AI Ask assistant and help resources." />
      <NotYetImplemented
        title="Support not yet built"
        description="The grounded AI Ask panel (POST /ask) with citations and an insufficient-evidence state is specified in docs/API_CONTRACT.md but not yet implemented in this session."
      />
    </div>
  );
}
