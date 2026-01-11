import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchSafetySignals } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, AlertTriangle, CheckCircle, Info, ExternalLink } from 'lucide-react'

const mockData = {
  summary: "Fracture rate of 13% exceeds the 8% protocol threshold. However, cross-referencing with literature and registry data shows this is explained by the high osteoporosis prevalence (32%) in the study population. All 5 fracture events occurred in osteoporotic patients.",
  signals: [
    {
      event: 'Periprosthetic Fracture',
      h34Rate: '13%',
      threshold: '8%',
      status: 'monitored',
      conclusion: 'Explained by population',
    },
    {
      event: 'Dislocation',
      h34Rate: '5%',
      threshold: '6%',
      status: 'ok',
      conclusion: 'Within expected range',
    },
    {
      event: 'Infection',
      h34Rate: '3%',
      threshold: '4%',
      status: 'ok',
      conclusion: 'Below threshold',
    },
  ],
  crossSourceAnalysis: {
    studyData: {
      title: 'Study Data Analysis',
      findings: [
        '5/37 patients (13%) experienced periprosthetic fracture',
        '5/5 fracture patients had documented osteoporosis (100%)',
        '4/5 fractures occurred within 90 days post-surgery',
        'No fractures in non-osteoporotic patients (0/25)',
      ],
    },
    literature: {
      title: 'Literature Context',
      findings: [
        'Dixon et al 2025: Osteoporosis primary risk factor for fracture',
        'Expected fracture rate in osteoporotic cohorts: 15-20%',
        'Expected fracture rate in non-osteoporotic: 4-8%',
        'Hazard ratio for osteoporosis: 2.4 (95% CI: 1.8-3.2)',
      ],
      source: 'Dixon et al 2025, Harris et al 2025',
    },
    registry: {
      title: 'Registry Benchmark',
      findings: [
        'AOANJRR threshold for concern: >10%',
        'Risk-adjusted expectation for 32% osteoporosis: 10-15%',
        'H-34 rate of 13% is WITHIN risk-adjusted expectation',
      ],
      source: 'AOANJRR 2024',
    },
    protocol: {
      title: 'Protocol Context',
      findings: [
        'Section 5.2: Osteoporosis is NOT an exclusion criterion',
        'Section 9.1: Safety threshold set at 8% (general population)',
        'Protocol does not specify risk-adjusted thresholds',
      ],
      source: 'CIP v2.0 Section 5.2, 9.1',
    },
  },
  conclusion: {
    status: 'explained',
    text: 'The elevated fracture rate does NOT indicate a device safety issue. The rate is fully explained by the high prevalence of osteoporosis in the study population and is within literature-predicted ranges for this risk profile.',
    recommendation: 'Document this analysis in the safety section of the CSR. Consider adding enhanced bone quality screening to future protocol versions.',
  },
}

export default function Safety() {
  const [, params] = useRoute('/study/:studyId/safety')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading } = useQuery({
    queryKey: ['safety', studyId],
    queryFn: () => fetchSafetySignals(studyId),
    retry: false,
  })

  const safety = data || mockData

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Safety Signals</h1>
        <p className="text-gray-500 mt-1">Cross-source contextualization of adverse events</p>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Analysis</h3>
            <p className="text-gray-600 leading-relaxed">{safety.summary}</p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Signal Detection" subtitle="Adverse event rates vs protocol thresholds" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Event Type</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">H-34 Rate</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Threshold</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Conclusion</th>
            </tr>
          </thead>
          <tbody>
            {safety.signals.map((signal, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0">
                <td className="py-4 px-4 font-medium text-gray-800">{signal.event}</td>
                <td className="py-4 px-4 text-center">
                  <span className={`font-semibold ${
                    signal.status === 'monitored' ? 'text-amber-600' : 'text-gray-800'
                  }`}>
                    {signal.h34Rate}
                  </span>
                </td>
                <td className="py-4 px-4 text-center text-gray-500">{signal.threshold}</td>
                <td className="py-4 px-4 text-center">
                  {signal.status === 'ok' ? (
                    <Badge variant="success">OK</Badge>
                  ) : (
                    <Badge variant="warning">Monitored</Badge>
                  )}
                </td>
                <td className="py-4 px-4 text-sm text-gray-600">{signal.conclusion}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {Object.values(safety.crossSourceAnalysis).map((source, i) => (
          <Card key={i}>
            <CardHeader
              title={source.title}
              action={
                'source' in source ? (
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    {source.source}
                  </span>
                ) : null
              }
            />
            <ul className="space-y-2 mt-3">
              {source.findings.map((finding, j) => (
                <li key={j} className="flex items-start gap-2 text-sm text-gray-600">
                  <Info className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                  {finding}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>

      <Card className={`border-l-4 ${
        safety.conclusion.status === 'explained' ? 'border-green-500 bg-green-50/50' : 'border-amber-500 bg-amber-50/50'
      }`}>
        <div className="flex items-start gap-4">
          {safety.conclusion.status === 'explained' ? (
            <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0" />
          )}
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">Conclusion</h3>
            <p className="text-gray-600 leading-relaxed">{safety.conclusion.text}</p>
            <p className="text-sm font-medium text-gray-700 mt-3">
              Recommendation: {safety.conclusion.recommendation}
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
