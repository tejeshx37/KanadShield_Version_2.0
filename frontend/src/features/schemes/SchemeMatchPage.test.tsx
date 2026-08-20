import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SchemeMatchPage } from './SchemeMatchPage'
import * as personalizationApi from '@/api/personalization'

vi.mock('@/lib/useOnlineStatus', () => ({ useOnlineStatus: () => true }))

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient()
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('SchemeMatchPage', () => {
  it('submits the profile form and renders honestly-phrased eligibility results', async () => {
    vi.spyOn(personalizationApi, 'matchSchemes').mockResolvedValue({
      results: [
        {
          scheme_id: 'scheme-1',
          scheme_name: 'Senior Citizen Pension Scheme',
          matched_conditions: ['age >= 60'],
          missing_conditions: [],
          required_documents: ['Aadhaar'],
          official_source: 'https://example.test/scheme',
          explanation: "Based on the information provided, you appear potentially eligible for 'Senior Citizen Pension Scheme'.",
          is_potentially_eligible: true,
        },
      ],
    })

    renderWithClient(<SchemeMatchPage />)

    await userEvent.type(screen.getByLabelText(/age/i), '65')
    await userEvent.click(screen.getByRole('button', { name: /check eligibility/i }))

    await waitFor(() => {
      expect(screen.getByText('Senior Citizen Pension Scheme')).toBeInTheDocument()
    })

    // Never claims certainty — the whole point of this feature's safety rule.
    expect(screen.getByText(/appears potentially eligible/i)).toBeInTheDocument()
    expect(screen.queryByText(/^you are eligible/i)).not.toBeInTheDocument()
    expect(personalizationApi.matchSchemes).toHaveBeenCalledWith(
      expect.objectContaining({ age: 65 }),
    )
  })
})
