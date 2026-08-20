import { PageHeader } from '../components/ui/PageHeader';
import { NotYetImplemented } from '../components/ui/QueryStates';

export function InsightsPage() {
  return (
    <div>
      <PageHeader
        title="Insights"
        description="Legal Change & Impact Radar, timeline, and document comparison."
      />
      <NotYetImplemented
        title="Insights not yet built"
        description="The Change Radar, Timeline, and Comparison views are specified in docs/API_CONTRACT.md (/insights/*) but not yet implemented in this session. Building this against real data is the next step."
      />
    </div>
  );
}
