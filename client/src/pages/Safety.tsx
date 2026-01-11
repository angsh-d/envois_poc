import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle, CheckCircle2, BookOpen, Database, FileText, Stethoscope } from 'lucide-react'
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
  const { data, isLoading } = useQuery({
    queryKey: ['safety'],
    queryFn: () => fetchAPI<SafetyData>('/api/v1/safety'),
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
        '100% (5/5) occurred in patients with osteoporosis diagnosis',
      ],
      literatureCorrelation: [
        'Osteoporosis identified as primary risk factor (Dixon et al 2025, Harris et al 2025)',
        'Expected rate in osteoporotic patients: 15-20% (vs 4% in non-osteoporotic)',
        'H-34 osteoporosis prevalence: 32% (12/37)—higher than typical study population',
      ],
      registryContext: [
        'Overall fracture rate threshold for concern: >10% (AOANJRR 2024)',
        'Risk-adjusted expectation for high-osteoporosis cohort: 10-15%',
        'H-34 rate (13%) is WITHIN risk-adjusted expectation',
      ],
      protocolCheck: [
        'Osteoporosis is NOT an exclusion criterion (CIP v2.0 Section 5.2)',
        'No enhanced monitoring protocol specified for bone quality',
      ],
    },
    interpretation: {
      confidence: 'HIGH (3 corroborating sources)',
      conclusion: 'Elevated fracture rate is EXPLAINED by patient population characteristics (high osteoporosis prevalence), NOT implant failure. Rate is within literature-predicted range for this risk profile.',
      regulatoryImplication: 'Signal requires documentation but does not indicate device defect. Recommend enhanced labeling for osteoporotic patients.',
    },
    recommendedActions: [
      'Generate Safety Narrative for regulatory submission',
      'Draft Protocol Amendment for enhanced bone density screening',
      'Create IFU Update with osteoporosis precaution language',
      'Flag 7 remaining patients with osteoporosis for enhanced monitoring',
    ],
    provenance: [
      'Study AEs (Sheet 17)',
      'Patient diagnoses (Sheet 2)',
      'Literature (Dixon 2025, Harris 2025)',
      'Registry (AOANJRR 2024)',
      'Protocol (CIP v2.0 Section 5.2)',
    ],
  }

  const displayData = data || mockData

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'elevated':
        return 'text-red-600 bg-red-50'
      case 'watch':
        return 'text-yellow-600 bg-yellow-50'
      default:
        return 'text-green-600 bg-green-50'
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="info">UC2</Badge>
            <Badge>Cross-Source Analysis</Badge>
          </div>
          <h1 className="text-5xl font-semibold text-black tracking-tight mb-3">
            Safety Signal Detection
          </h1>
          <p className="text-xl text-gray-500 font-light max-w-3xl">
            Proactive safety monitoring with cross-source contextualization. AI agents correlate study data 
            with literature and registry benchmarks to interpret signals with full provenance.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <Card className="mb-8 border-l-4 border-l-red-500">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <Badge variant="danger">Safety Signal Detected</Badge>
              <h2 className="text-xl font-semibold text-black mt-1">{displayData.analysis.title}</h2>
            </div>
          </div>
        </Card>

        <Card className="mb-8">
          <h2 className="text-xl font-semibold text-black mb-6">Signal Comparison Matrix</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">H-34 Study</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Literature</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Registry</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody>
                {displayData.signals.map((signal, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-4 px-4 font-medium text-black">{signal.name}</td>
                    <td className="py-4 px-4 text-sm text-gray-600">{signal.studyRate}</td>
                    <td className="py-4 px-4 text-sm text-gray-600">{signal.literatureRate}</td>
                    <td className="py-4 px-4 text-sm text-gray-600">{signal.registryRate}</td>
                    <td className="py-4 px-4">
                      <span className={cn('px-3 py-1 rounded-full text-xs font-medium uppercase', getStatusColor(signal.status))}>
                        {signal.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <div className="flex items-center gap-2 mb-6">
              <Stethoscope className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-semibold text-black">Study Data Analysis</h2>
            </div>
            <ul className="space-y-3">
              {displayData.analysis.studyFindings.map((finding, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-gray-700">{finding}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-6">
              <BookOpen className="w-5 h-5 text-purple-600" />
              <h2 className="text-xl font-semibold text-black">Literature Correlation</h2>
            </div>
            <ul className="space-y-3">
              {displayData.analysis.literatureCorrelation.map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-6">
              <Database className="w-5 h-5 text-green-600" />
              <h2 className="text-xl font-semibold text-black">Registry Context</h2>
            </div>
            <ul className="space-y-3">
              {displayData.analysis.registryContext.map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-6">
              <FileText className="w-5 h-5 text-orange-600" />
              <h2 className="text-xl font-semibold text-black">Protocol Check</h2>
            </div>
            <ul className="space-y-3">
              {displayData.analysis.protocolCheck.map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <Card className="mb-8 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200">
          <h2 className="text-xl font-semibold text-black mb-6">Signal Interpretation</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-2">Confidence Level</p>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-black">{displayData.interpretation.confidence}</span>
              </div>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-2">Conclusion</p>
              <p className="text-gray-700">{displayData.interpretation.conclusion}</p>
            </div>
          </div>
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
            <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-2">Regulatory Implication</p>
            <p className="text-blue-800">{displayData.interpretation.regulatoryImplication}</p>
          </div>
        </Card>

        <Card className="mb-8">
          <h2 className="text-xl font-semibold text-black mb-6">Recommended Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {displayData.recommendedActions.map((action, index) => (
              <button
                key={index}
                className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left"
              >
                <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-sm">{index + 1}</span>
                </div>
                <span className="text-gray-700">{action}</span>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-black mb-4">Provenance</h2>
          <div className="flex flex-wrap gap-2">
            {displayData.provenance.map((source, index) => (
              <Badge key={index} variant="default">{source}</Badge>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
