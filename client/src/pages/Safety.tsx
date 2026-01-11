import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { fetchAPI, cn } from '../lib/utils'

interface SafetySignal {
  name: string
  studyRate: string
  literatureRate: string
  registryRate: string
  status: 'elevated' | 'normal' | 'watch'
}

interface SafetyData {
  signals: SafetySignal[]
  analysis: {
    title: string
    studyFindings: string[]
    literatureCorrelation: string[]
    registryContext: string[]
    protocolCheck: string[]
  }
  interpretation: {
    confidence: string
    conclusion: string
    regulatoryImplication: string
  }
  recommendedActions: string[]
  provenance: string[]
}

export default function Safety() {
  const { data } = useQuery({
    queryKey: ['safety'],
    queryFn: () => fetchAPI<SafetyData>('/api/v1/uc2/safety/overview'),
    retry: false,
  })

  const mockData: SafetyData = {
    signals: [
      { name: 'Fracture Rate', studyRate: '13% (5/37)', literatureRate: '4-8%', registryRate: '<10%', status: 'elevated' },
      { name: 'Dislocation Rate', studyRate: '5% (2/37)', literatureRate: '3-6%', registryRate: '5%', status: 'normal' },
      { name: 'Infection Rate', studyRate: '3% (1/37)', literatureRate: '2-4%', registryRate: '3%', status: 'normal' },
      { name: 'Overall AE Rate', studyRate: '35% (13/37)', literatureRate: '28-40%', registryRate: '35%', status: 'normal' },
    ],
    analysis: {
      title: 'Periprosthetic Fracture Rate Exceeds Benchmarks',
      studyFindings: [
        '5 periprosthetic fractures in 37 patients (13%)',
        '4/5 occurred within 90 days (intraop or early postop)',
        '100% (5/5) occurred in patients with osteoporosis',
      ],
      literatureCorrelation: [
        'Osteoporosis identified as primary risk factor',
        'Expected rate in osteoporotic patients: 15-20%',
        'H-34 osteoporosis prevalence: 32% (12/37)',
      ],
      registryContext: [
        'Overall fracture rate threshold: >10%',
        'Risk-adjusted expectation for cohort: 10-15%',
        'H-34 rate (13%) within risk-adjusted range',
      ],
      protocolCheck: [
        'Osteoporosis is NOT an exclusion criterion',
        'No enhanced monitoring for bone quality specified',
      ],
    },
    interpretation: {
      confidence: 'HIGH (3 corroborating sources)',
      conclusion: 'Elevated fracture rate is EXPLAINED by patient population characteristics (high osteoporosis prevalence), NOT implant failure.',
      regulatoryImplication: 'Signal requires documentation but does not indicate device defect.',
    },
    recommendedActions: [
      'Generate Safety Narrative',
      'Draft Protocol Amendment',
      'Create IFU Update',
      'Flag Similar Patients',
    ],
    provenance: [
      'Study AEs (Sheet 17)',
      'Patient Diagnoses (Sheet 2)',
      'Literature (Dixon 2025)',
      'Registry (AOANJRR 2024)',
    ],
  }

  const displayData = data || mockData

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'elevated':
        return 'bg-[#ff3b30]/10 text-[#d70015]'
      case 'watch':
        return 'bg-[#ff9500]/10 text-[#c77700]'
      default:
        return 'bg-[#34c759]/10 text-[#248a3d]'
    }
  }

  return (
    <div className="min-h-screen">
      <section className="pt-24 pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto text-center">
          <div className="animate-fade-in-up opacity-0">
            <Badge variant="info" size="sm">UC2 · Cross-Source Analysis</Badge>
          </div>
          <h1 className="text-display-lg mt-4 animate-fade-in-up opacity-0 stagger-1">
            Safety Signal Detection
          </h1>
          <p className="text-body-lg text-neutral-500 mt-4 max-w-[700px] mx-auto animate-fade-in-up opacity-0 stagger-2">
            Proactive safety monitoring with cross-source contextualization. 
            AI correlates study data with literature and registry benchmarks.
          </p>
        </div>
      </section>

      <section className="pb-12 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto">
          <Card className="p-6 border-l-4 border-l-[#ff3b30] animate-fade-in-up opacity-0 stagger-3" variant="elevated">
            <div className="flex items-center gap-3">
              <Badge variant="danger" size="sm">Signal Detected</Badge>
              <p className="text-headline text-neutral-900">{displayData.analysis.title}</p>
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card variant="elevated" className="overflow-hidden">
            <div className="p-6 border-b border-neutral-100">
              <p className="text-headline text-neutral-900">Signal Comparison</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-neutral-50">
                    <th className="text-left py-4 px-6 text-caption text-neutral-500 uppercase tracking-wider font-medium">Metric</th>
                    <th className="text-left py-4 px-6 text-caption text-neutral-500 uppercase tracking-wider font-medium">H-34 Study</th>
                    <th className="text-left py-4 px-6 text-caption text-neutral-500 uppercase tracking-wider font-medium">Literature</th>
                    <th className="text-left py-4 px-6 text-caption text-neutral-500 uppercase tracking-wider font-medium">Registry</th>
                    <th className="text-left py-4 px-6 text-caption text-neutral-500 uppercase tracking-wider font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {displayData.signals.map((s, i) => (
                    <tr key={i} className="hover:bg-neutral-50 transition-colors">
                      <td className="py-4 px-6 text-body font-medium text-neutral-900">{s.name}</td>
                      <td className="py-4 px-6 text-body-sm text-neutral-600">{s.studyRate}</td>
                      <td className="py-4 px-6 text-body-sm text-neutral-600">{s.literatureRate}</td>
                      <td className="py-4 px-6 text-body-sm text-neutral-600">{s.registryRate}</td>
                      <td className="py-4 px-6">
                        <span className={cn('px-3 py-1 rounded-full text-[11px] font-semibold uppercase', getStatusStyles(s.status))}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6" variant="elevated">
              <p className="text-body font-semibold text-[#0071e3] mb-4">Study Data Analysis</p>
              <ul className="space-y-3">
                {displayData.analysis.studyFindings.map((f, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-[#0071e3] rounded-full mt-2 flex-shrink-0" />
                    <span className="text-body-sm text-neutral-700">{f}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-6" variant="elevated">
              <p className="text-body font-semibold text-purple-600 mb-4">Literature Correlation</p>
              <ul className="space-y-3">
                {displayData.analysis.literatureCorrelation.map((l, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-body-sm text-neutral-700">{l}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-6" variant="elevated">
              <p className="text-body font-semibold text-[#34c759] mb-4">Registry Context</p>
              <ul className="space-y-3">
                {displayData.analysis.registryContext.map((r, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-[#34c759] rounded-full mt-2 flex-shrink-0" />
                    <span className="text-body-sm text-neutral-700">{r}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-6" variant="elevated">
              <p className="text-body font-semibold text-[#ff9500] mb-4">Protocol Check</p>
              <ul className="space-y-3">
                {displayData.analysis.protocolCheck.map((p, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-[#ff9500] rounded-full mt-2 flex-shrink-0" />
                    <span className="text-body-sm text-neutral-700">{p}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card className="p-8" variant="elevated">
            <p className="text-headline text-neutral-900 mb-6">Signal Interpretation</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-caption text-neutral-500 uppercase tracking-wider mb-2">Confidence</p>
                <p className="text-body font-medium text-[#248a3d]">{displayData.interpretation.confidence}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-caption text-neutral-500 uppercase tracking-wider mb-2">Conclusion</p>
                <p className="text-body text-neutral-700">{displayData.interpretation.conclusion}</p>
              </div>
            </div>
            <div className="mt-6 p-4 rounded-xl bg-[#0071e3]/5 border border-[#0071e3]/10">
              <p className="text-caption text-neutral-500 uppercase tracking-wider mb-2">Regulatory Implication</p>
              <p className="text-body text-[#0071e3]">{displayData.interpretation.regulatoryImplication}</p>
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card className="p-8" variant="elevated">
            <p className="text-headline text-neutral-900 mb-6">Recommended Actions</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {displayData.recommendedActions.map((a, i) => (
                <button key={i} className="p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-all text-left group">
                  <div className="w-8 h-8 rounded-lg bg-neutral-900 flex items-center justify-center mb-3">
                    <span className="text-white text-body-sm font-semibold">{i + 1}</span>
                  </div>
                  <p className="text-body-sm text-neutral-900">{a}</p>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
