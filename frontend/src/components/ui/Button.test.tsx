import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders children and responds to click', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Search</Button>)
    const button = screen.getByRole('button', { name: 'Search' })
    await userEvent.click(button)
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('is disabled and does not fire onClick when disabled', async () => {
    const onClick = vi.fn()
    render(
      <Button onClick={onClick} disabled>
        Search
      </Button>,
    )
    const button = screen.getByRole('button', { name: 'Search' })
    expect(button).toBeDisabled()
    await userEvent.click(button)
    expect(onClick).not.toHaveBeenCalled()
  })
})
