import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { ProgressBar } from '../components/ProgressBar'
import { cn } from '../lib/utils'

interface Patient {
  id: string
  riskScore: number
  riskLevel: 'high' | 'medium' | 'low'
  riskFactors: string[]
  lastVisit: string
  nextVisit: string
  recommendations: string[]
}

export default function Risk() {
  const patients: Patient[] = [
    {
      id: 'H34-008',
      riskScore: 87,
      riskLevel: 'high',
      riskFactors: ['Osteoporosis', 'BMI > 35', 'Prior revision', 'Age > 75'],
      lastVisit: '2025-10-15',
      nextVisit: '2026-01-15',
      recommendations: ['Enhanced bone density monitoring', 'Fall prevention', 'Quarterly imaging'],
    },
    {
      id: 'H34-014',
      riskScore: 82,
      riskLevel: 'high',
      riskFactors: ['Osteoporosis', 'Diabetes', 'Smoking history'],
      lastVisit: '2025-11-20',
      nextVisit: '2026-02-20',
      recommendations: ['HbA1c monitoring', 'Smoking cessation', 'Enhanced wound care'],
    },
    {
      id: 'H34-023',
      riskScore: 78,
      riskLevel: 'high',
      riskFactors: ['Rheumatoid arthritis', 'Immunosuppressant', 'Prior infection'],
      lastVisit: '2025-12-01',
      nextVisit: '2026-03-01',
      recommendations: ['Infection screening', 'Immunosuppressant review', 'Monthly labs'],
    },
    {
      id: 'H34-031',
      riskScore: 65,
      riskLevel: 'medium',
      riskFactors: ['BMI > 30', 'Hypertension'],
      lastVisit: '2025-11-05',
      nextVisit: '2026-02-05',
      recommendations: ['Weight management', 'BP monitoring'],
    },
    {
      id: 'H34-007',
      riskScore: 58,
      riskLevel: 'medium',
      riskFactors: ['Age > 70', 'Mild bone loss'],
      lastVisit: '2025-10-28',
      nextVisit: '2026-01-28',
      recommendations: ['Standard bone health protocol'],
    },
  ]

  const stats = {
    total: 37,
    high: patients.filter(p => p.riskLevel === 'high').length,
    medium: patients.filter(p => p.riskLevel === 'medium').length,
    low: 37 - patients.filter(p => p.riskLevel === 'high').length - patients.filter(p => p.riskLevel === 'medium').length,
  }

  const getRiskStyles = (level: string) => {
    switch (level) {
      case 'high':
        return { text: 'text-[#ff3b30]', bg: 'bg-[#ff3b30]/10', border: 'border-[#ff3b30]/20' }
      case 'medium':
        return { text: 'text-[#ff9500]', bg: 'bg-[#ff9500]/10', border: 'border-[#ff9500]/20' }
      default:
        return { text: 'text-[#34c759]', bg: 'bg-[#34c759]/10', border: 'border-[#34c759]/20' }
    }
  }

  return (
    <div className="min-h-screen">
      <section className="pt-24 pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto text-center">
          <div className="animate-fade-in-up opacity-0">
            <Badge variant="info" size="sm">UC4 · ML + Literature</Badge>
          </div>
          <h1 className="text-display-lg mt-4 animate-fade-in-up opacity-0 stagger-1">
            Patient Risk Stratification
          </h1>
          <p className="text-body-lg text-neutral-500 mt-4 max-w-[700px] mx-auto animate-fade-in-up opacity-0 stagger-2">
            ML-powered risk scoring combined with literature-grounded factors. 
            Prioritized patient lists with explainable recommendations.
          </p>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 animate-fade-in-up opacity-0 stagger-3">
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Total</p>
              <p className="text-display-md mt-1">{stats.total}</p>
            </Card>
            <Card className="p-6 text-center border-l-4 border-l-[#ff3b30]" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">High Risk</p>
              <p className="text-display-md mt-1 text-[#ff3b30]">{stats.high}</p>
            </Card>
            <Card className="p-6 text-center border-l-4 border-l-[#ff9500]" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Medium</p>
              <p className="text-display-md mt-1 text-[#ff9500]">{stats.medium}</p>
            </Card>
            <Card className="p-6 text-center border-l-4 border-l-[#34c759]" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Low Risk</p>
              <p className="text-display-md mt-1 text-[#34c759]">{stats.low}</p>
            </Card>
          </div>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card variant="elevated" className="overflow-hidden">
            <div className="p-6 border-b border-neutral-100 flex items-center justify-between">
              <div>
                <p className="text-headline text-neutral-900">Patient Risk Registry</p>
                <p className="text-body-sm text-neutral-500 mt-1">Sorted by risk score (highest first)</p>
              </div>
              <div className="flex gap-3">
                <Button variant="secondary" size="sm">Export</Button>
                <Button variant="primary" size="sm">Generate Reports</Button>
              </div>
            </div>
            <div className="divide-y divide-neutral-100">
              {patients.map((p) => {
                const styles = getRiskStyles(p.riskLevel)
                return (
                  <div key={p.id} className={cn('p-6 hover:bg-neutral-50 transition-colors', styles.bg.replace('/10', '/[0.02]'))}>
                    <div className="flex flex-wrap items-start gap-6">
                      <div className={cn('w-16 h-16 rounded-2xl flex items-center justify-center', styles.bg)}>
                        <span className={cn('text-display-sm', styles.text)}>{p.riskScore}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-body font-semibold text-neutral-900">{p.id}</span>
                          <Badge variant={p.riskLevel === 'high' ? 'danger' : p.riskLevel === 'medium' ? 'warning' : 'success'} size="sm">
                            {p.riskLevel} risk
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-body-sm text-neutral-400 mb-3">
                          <span>Last: {p.lastVisit}</span>
                          <span>Next: {p.nextVisit}</span>
                        </div>
                        <div className="w-full max-w-xs mb-4">
                          <ProgressBar 
                            value={p.riskScore} 
                            size="sm" 
                            variant={p.riskLevel === 'high' ? 'danger' : p.riskLevel === 'medium' ? 'warning' : 'success'}
                            showLabel={false}
                          />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-caption text-neutral-500 uppercase tracking-wider mb-2">Risk Factors</p>
                            <div className="flex flex-wrap gap-1.5">
                              {p.riskFactors.map((f, i) => (
                                <Badge key={i} variant="default" size="sm">{f}</Badge>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-caption text-neutral-500 uppercase tracking-wider mb-2">Recommendations</p>
                            <ul className="space-y-1">
                              {p.recommendations.slice(0, 2).map((r, i) => (
                                <li key={i} className="text-body-sm text-neutral-600 flex items-start gap-2">
                                  <span className="w-1 h-1 bg-neutral-400 rounded-full mt-2 flex-shrink-0" />
                                  {r}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm">View</Button>
                        <Button variant="secondary" size="sm">Care Plan</Button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Risk Scoring Model</p>
              <div className="space-y-4">
                {[
                  { title: 'ML Component (40%)', desc: 'Trained on revision outcomes. BMI, age, bone density, comorbidities.', color: 'purple-500' },
                  { title: 'Literature Factors (35%)', desc: 'Evidence-based from Dixon, Harris, Meding 2025.', color: '[#0071e3]' },
                  { title: 'Registry Benchmarks (25%)', desc: 'Population-specific adjustments from AOANJRR 2024.', color: '[#34c759]' },
                ].map((item, i) => (
                  <div key={i} className="p-4 rounded-xl bg-neutral-50">
                    <p className={cn('text-body font-medium', `text-${item.color}`)}>{item.title}</p>
                    <p className="text-body-sm text-neutral-600 mt-1">{item.desc}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Key Insights</p>
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[#ff3b30]/5 border border-[#ff3b30]/10">
                  <p className="text-body font-medium text-[#d70015]">High-Risk Pattern</p>
                  <p className="text-body-sm text-neutral-600 mt-1">
                    100% of high-risk patients have osteoporosis. Consider enhanced bone health protocol.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-[#ff9500]/5 border border-[#ff9500]/10">
                  <p className="text-body font-medium text-[#c77700]">Emerging Concern</p>
                  <p className="text-body-sm text-neutral-600 mt-1">
                    3 medium-risk patients trending upward. BMI increase detected.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-[#34c759]/5 border border-[#34c759]/10">
                  <p className="text-body font-medium text-[#248a3d]">Positive Trend</p>
                  <p className="text-body-sm text-neutral-600 mt-1">
                    81% of patients (30/37) maintaining or improving scores.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
