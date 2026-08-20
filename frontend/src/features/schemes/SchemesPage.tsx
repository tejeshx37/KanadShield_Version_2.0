import { Link } from 'react-router-dom'
import { Card, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export function SchemesPage() {
  return (
    <div className="mx-auto max-w-xl space-y-4 py-8 text-center">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Government Schemes</h1>
      <Card>
        <CardBody className="space-y-3">
          <p className="text-sm text-ink-700">
            Check which government schemes you may be eligible for, based on the information you provide.
            This is not a final eligibility determination — always verify with the official source.
          </p>
          <Link to="/schemes/match">
            <Button className="w-full">Check my eligibility</Button>
          </Link>
        </CardBody>
      </Card>
    </div>
  )
}
