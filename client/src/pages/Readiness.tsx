import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/Card'
import { ProgressBar } from '../components/ProgressBar'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { fetchAPI, cn } from '../lib/utils'

interface ReadinessData {
  overall_readiness: number
  categories: Array<{
    name: string
    status: 'pass' | 'gap' | 'watch'
    finding: string
    action: string
  }>
  blockers: string[]
  warnings: string[]
  timeline: Array<{ days: number; readiness: number; milestone: string }>
  provenance: string[]
}

export default function Readiness() {
  const { data } = useQuery({
    queryKey: ['readiness'],
    queryFn: () => fetchAPI<ReadinessData>('/api/v1/uc1/readiness'),
    retry: false,
  })

  const mockData: ReadinessData = {
    overall_readiness: 72,
    categories: [
      { name: 'Primary Endpoint', status: 'pass', finding: '62% MCID (≥50% required)', action: 'None' },
      { name: 'Sample Size', status: 'gap', finding: '8/25 evaluable (32%)', action: 'Chase 17 patients' },
      { name: 'Literature Benchmark', status: 'pass', finding: 'Within published ranges', action: 'None' },
      { name: 'Registry Comparison', status: 'watch', finding: 'Revision rate at 95th %ile', action: 'Add narrative' },
      { name: 'Safety Documentation', status: 'pass', finding: 'All SAEs have narratives', action: 'None' },
      { name: 'Radiographic Data', status: 'gap', finding: '3 patients missing 1yr', action: 'Chase list below' },
      { name: 'Protocol Deviations', status: 'watch', finding: '4 timing deviations', action: 'Document in CSR' },
    ],
    blockers: [
      '17 additional patients need 2-year follow-up',
      'Patients 12, 19, 27 missing 1-year imaging',
    ],
    warnings: [
      'Revision rate narrative: Explain 8.1% vs registry 6.2%',
      'Protocol deviations: Document 4 timing deviations in CSR',
    ],
    timeline: [
      { days: 0, readiness: 72, milestone: 'Current' },
      { days: 30, readiness: 78, milestone: 'Chase radiographic' },
      { days: 90, readiness: 85, milestone: 'Additional 2yr FU' },
      { days: 180, readiness: 92, milestone: 'Target n=25' },
    ],
    provenance: [
      'Protocol (CIP v2.0)',
      'Study Data (Sheets 1, 17, 18, 20)',
      'Literature (Meding 2025)',
      'Registry (AOANJRR 2024)',
    ],
  }

  const displayData = data || mockData

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'pass':
        return { bg: 'bg-[#34c759]/10', text: 'text-[#248a3d]', label: 'Pass' }
      case 'gap':
        return { bg: 'bg-[#ff3b30]/10', text: 'text-[#d70015]', label: 'Gap' }
      case 'watch':
        return { bg: 'bg-[#ff9500]/10', text: 'text-[#c77700]', label: 'Watch' }
      default:
        return { bg: 'bg-neutral-100', text: 'text-neutral-600', label: status }
    }
  }

  return (
    <div className="min-h-screen">
      <section className="pt-24 pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto text-center">
          <div className="animate-fade-in-up opacity-0">
            <Badge variant="info" size="sm">UC1 · Multi-Agent Analysis</Badge>
          </div>
          <h1 className="text-display-lg mt-4 animate-fade-in-up opacity-0 stagger-1">
            Regulatory Readiness
          </h1>
          <p className="text-body-lg text-neutral-500 mt-4 max-w-[700px] mx-auto animate-fade-in-up opacity-0 stagger-2">
            Comprehensive gap analysis across Protocol, Study Data, Literature, and Registry. 
            5 AI agents collaborate to produce actionable remediation.
          </p>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto">
          <Card className="p-10 text-center animate-fade-in-up opacity-0 stagger-3" variant="elevated">
            <p className="text-caption text-neutral-500 uppercase tracking-wider">Overall Readiness</p>
            <p className="text-display-xl mt-2">{displayData.overall_readiness}%</p>
            <p className="text-body text-neutral-500 mt-2">Target: 90% for submission</p>
            <div className="max-w-md mx-auto mt-6">
              <ProgressBar 
                value={displayData.overall_readiness} 
                size="lg" 
                variant={displayData.overall_readiness >= 90 ? 'success' : displayData.overall_readiness >= 70 ? 'warning' : 'danger'}
                showLabel={false}
              />
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <Card className="overflow-hidden" variant="elevated">
                <div className="p-6 border-b border-neutral-100">
                  <p className="text-headline text-neutral-900">Category Status</p>
                </div>
                <div className="divide-y divide-neutral-100">
                  {displayData.categories.map((cat, i) => {
                    const styles = getStatusStyles(cat.status)
                    return (
                      <div key={i} className="p-5 flex items-center gap-4 hover:bg-neutral-50 transition-colors">
                        <div className={cn('w-16 text-center py-1 rounded-full text-[11px] font-semibold uppercase', styles.bg, styles.text)}>
                          {styles.label}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-body font-medium text-neutral-900">{cat.name}</p>
                          <p className="text-body-sm text-neutral-500 truncate">{cat.finding}</p>
                        </div>
                        <p className="text-body-sm text-neutral-400 hidden md:block">{cat.action}</p>
                      </div>
                    )
                  })}
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card className="p-6" variant="elevated">
                <p className="text-body font-semibold text-[#d70015] mb-4">Blockers</p>
                <ul className="space-y-3">
                  {displayData.blockers.map((b, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="w-1.5 h-1.5 bg-[#ff3b30] rounded-full mt-2 flex-shrink-0" />
                      <span className="text-body-sm text-neutral-700">{b}</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card className="p-6" variant="elevated">
                <p className="text-body font-semibold text-[#c77700] mb-4">Warnings</p>
                <ul className="space-y-3">
                  {displayData.warnings.map((w, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="w-1.5 h-1.5 bg-[#ff9500] rounded-full mt-2 flex-shrink-0" />
                      <span className="text-body-sm text-neutral-700">{w}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Projected Timeline</p>
              <div className="space-y-4">
                {displayData.timeline.map((t, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className={cn(
                      'w-14 text-center py-1.5 rounded-lg text-body-sm font-medium',
                      t.readiness >= 90 ? 'bg-[#34c759]/10 text-[#248a3d]' : 'bg-neutral-100 text-neutral-600'
                    )}>
                      +{t.days}d
                    </div>
                    <div className="flex-1">
                      <ProgressBar value={t.readiness} size="sm" showLabel={false} />
                    </div>
                    <span className={cn(
                      'text-body-sm font-medium w-12 text-right',
                      t.readiness >= 90 ? 'text-[#248a3d]' : 'text-neutral-900'
                    )}>
                      {t.readiness}%
                    </span>
                    <span className="text-body-sm text-neutral-500 w-32">{t.milestone}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 rounded-xl bg-[#34c759]/10 border border-[#34c759]/20">
                <p className="text-body-sm font-medium text-[#248a3d]">✓ Submission viable at +180 days</p>
              </div>
            </Card>

            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Actions</p>
              <div className="space-y-3">
                {['Download Checklist PDF', 'Generate Chase List', 'Draft CSR Section', 'Email Report'].map((action, i) => (
                  <button key={i} className="w-full flex items-center justify-between p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all text-left group">
                    <span className="text-body text-neutral-900">{action}</span>
                    <span className="text-body text-neutral-400 group-hover:text-[#0071e3] transition-colors">→</span>
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card className="p-6" variant="default">
            <p className="text-body-sm font-medium text-neutral-500 mb-3">Provenance</p>
            <div className="flex flex-wrap gap-2">
              {displayData.provenance.map((p, i) => (
                <Badge key={i} variant="default" size="sm">{p}</Badge>
              ))}
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
