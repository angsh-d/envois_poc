import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/Card'
import { ProgressBar } from '../components/ProgressBar'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { fetchAPI } from '../lib/utils'
import { Link } from 'wouter'

interface HealthResponse {
  status: string
  study_name: string
  version: string
}

export default function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetchAPI<HealthResponse>('/health'),
  })

  const metrics = {
    enrolled: 37,
    target: 50,
    evaluable: 8,
    readiness: 72,
    signals: 2,
    deviations: 4,
    atRisk: 7,
  }

  return (
    <div className="min-h-screen">
      <section className="pt-24 pb-20 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto text-center">
          <div className="animate-fade-in-up opacity-0">
            <Badge variant="success" size="sm">Active Study</Badge>
          </div>
          <h1 className="text-display-lg mt-4 animate-fade-in-up opacity-0 stagger-1">
            H-34 DELTA Revision Cup
          </h1>
          <p className="text-body-lg text-neutral-500 mt-4 max-w-[600px] mx-auto animate-fade-in-up opacity-0 stagger-2">
            Clinical Intelligence Dashboard powered by Multi-Agent AI. 
            Real-time regulatory readiness, safety monitoring, and patient risk stratification.
          </p>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 animate-fade-in-up opacity-0 stagger-3">
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Enrolled</p>
              <p className="text-display-md mt-1">{metrics.enrolled}</p>
              <p className="text-body-sm text-neutral-400 mt-1">of {metrics.target} target</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Evaluable</p>
              <p className="text-display-md mt-1">{metrics.evaluable}</p>
              <p className="text-body-sm text-neutral-400 mt-1">at 2-year endpoint</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Signals</p>
              <p className="text-display-md mt-1 text-[#ff9500]">{metrics.signals}</p>
              <p className="text-body-sm text-neutral-400 mt-1">requiring attention</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">At Risk</p>
              <p className="text-display-md mt-1 text-[#ff3b30]">{metrics.atRisk}</p>
              <p className="text-body-sm text-neutral-400 mt-1">enhanced monitoring</p>
            </Card>
          </div>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 animate-fade-in-up opacity-0 stagger-4">
              <Card className="p-8" variant="elevated">
                <div className="flex items-start justify-between mb-8">
                  <div>
                    <p className="text-caption text-neutral-500 uppercase tracking-wider">Submission Readiness</p>
                    <p className="text-headline text-neutral-900 mt-1">Gap analysis across 4 sources</p>
                  </div>
                  <Link href="/readiness">
                    <Button variant="link" size="sm">View Details →</Button>
                  </Link>
                </div>
                
                <div className="flex items-end gap-6 mb-8">
                  <span className="text-display-xl text-neutral-900">{metrics.readiness}%</span>
                  <span className="text-body text-neutral-500 pb-4">Target: 90%</span>
                </div>
                
                <ProgressBar 
                  value={metrics.readiness} 
                  size="lg" 
                  variant={metrics.readiness >= 90 ? 'success' : metrics.readiness >= 70 ? 'warning' : 'danger'}
                  showLabel={false}
                />

                <div className="grid grid-cols-2 gap-6 mt-8">
                  <div className="p-4 rounded-xl bg-[#ff3b30]/5 border border-[#ff3b30]/10">
                    <p className="text-body-sm font-medium text-[#d70015] mb-2">Blockers</p>
                    <p className="text-body-sm text-neutral-600">17 patients need 2-year follow-up</p>
                    <p className="text-body-sm text-neutral-600 mt-1">3 patients missing imaging</p>
                  </div>
                  <div className="p-4 rounded-xl bg-neutral-100/60 border border-neutral-200/60">
                    <p className="text-body-sm font-medium text-neutral-700 mb-2">Timeline</p>
                    <p className="text-body-sm text-neutral-600">+30 days → 78% ready</p>
                    <p className="text-body-sm text-neutral-600 mt-1">+180 days → 92% ready</p>
                  </div>
                </div>
              </Card>
            </div>

            <div className="lg:col-span-2 animate-fade-in-up opacity-0 stagger-5">
              <Card className="p-8 h-full" variant="elevated">
                <p className="text-headline text-neutral-900 mb-6">Quick Actions</p>
                <div className="space-y-3">
                  <Link href="/readiness">
                    <div className="group p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all cursor-pointer">
                      <p className="text-body font-medium text-neutral-900 group-hover:text-[#0071e3] transition-colors">Regulatory Readiness</p>
                      <p className="text-body-sm text-neutral-500">Full gap analysis</p>
                    </div>
                  </Link>
                  <Link href="/safety">
                    <div className="group p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all cursor-pointer">
                      <p className="text-body font-medium text-neutral-900 group-hover:text-[#0071e3] transition-colors">Safety Signals</p>
                      <p className="text-body-sm text-neutral-500">Cross-source analysis</p>
                    </div>
                  </Link>
                  <Link href="/deviations">
                    <div className="group p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all cursor-pointer">
                      <p className="text-body font-medium text-neutral-900 group-hover:text-[#0071e3] transition-colors">Protocol Deviations</p>
                      <p className="text-body-sm text-neutral-500">Automated detection</p>
                    </div>
                  </Link>
                  <Link href="/risk">
                    <div className="group p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all cursor-pointer">
                      <p className="text-body font-medium text-neutral-900 group-hover:text-[#0071e3] transition-colors">Patient Risk</p>
                      <p className="text-body-sm text-neutral-500">ML-powered stratification</p>
                    </div>
                  </Link>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Active Safety Signals</p>
              <div className="space-y-4">
                <div className="p-5 rounded-xl bg-[#ff3b30]/5 border border-[#ff3b30]/10">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="danger" size="sm">Elevated</Badge>
                    <span className="text-caption text-neutral-400">2 days ago</span>
                  </div>
                  <p className="text-body font-medium text-neutral-900">Periprosthetic Fracture Rate: 13%</p>
                  <p className="text-body-sm text-neutral-600 mt-2">
                    Exceeds literature benchmark (4-8%). Cross-source analysis indicates 
                    correlation with high osteoporosis prevalence.
                  </p>
                  <Link href="/safety">
                    <Button variant="link" size="sm" className="mt-3">View Analysis →</Button>
                  </Link>
                </div>
                <div className="p-5 rounded-xl bg-[#ff9500]/5 border border-[#ff9500]/10">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="warning" size="sm">Watch</Badge>
                    <span className="text-caption text-neutral-400">Monitoring</span>
                  </div>
                  <p className="text-body font-medium text-neutral-900">Revision Rate: 8.1%</p>
                  <p className="text-body-sm text-neutral-600 mt-2">
                    At upper boundary of registry benchmark (6.2%). Early failure cluster identified.
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Outcome Metrics</p>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-body-sm text-neutral-600">MCID Achievement (HHS ≥20pt)</span>
                    <span className="text-body-sm font-medium text-neutral-900">62%</span>
                  </div>
                  <ProgressBar value={62} size="sm" variant="success" showLabel={false} />
                  <p className="text-caption text-neutral-400 mt-1">Literature benchmark: 72%</p>
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-body-sm text-neutral-600">2-Year Survival</span>
                    <span className="text-body-sm font-medium text-neutral-900">92%</span>
                  </div>
                  <ProgressBar value={92} size="sm" variant="success" showLabel={false} />
                  <p className="text-caption text-neutral-400 mt-1">Registry benchmark: 94%</p>
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-body-sm text-neutral-600">SAE Documentation</span>
                    <span className="text-body-sm font-medium text-neutral-900">100%</span>
                  </div>
                  <ProgressBar value={100} size="sm" variant="success" showLabel={false} />
                  <p className="text-caption text-neutral-400 mt-1">12/12 SAEs with narratives</p>
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-body-sm text-neutral-600">Visit Completion</span>
                    <span className="text-body-sm font-medium text-neutral-900">85%</span>
                  </div>
                  <ProgressBar value={85} size="sm" showLabel={false} />
                  <p className="text-caption text-neutral-400 mt-1">Protocol requirement: 80%</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <footer className="pb-16 text-center">
        <p className="text-caption text-neutral-400">
          Powered by Multi-Agent AI with Document-as-Code Intelligence
        </p>
        <p className="text-caption text-neutral-400 mt-1">
          Protocol + Study Data + Literature + Registry — 4 Sources, 1 Intelligence Layer
        </p>
      </footer>
    </div>
  )
}
