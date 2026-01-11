import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchRiskPatients } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, User, AlertTriangle, TrendingUp, ChevronRight } from 'lucide-react'
import { useState } from 'react'

const mockData = {
  summary: "4 patients flagged as high risk (>20% revision probability). Primary risk factors are osteoporosis (HR 2.4) and prior revision history (HR 2.1). 8 patients at moderate risk require enhanced monitoring. ML model confidence: 78%.",
  distribution: {
    high: 4,
    moderate: 8,
    low: 25,
  },
  patients: [
    {
      id: '017',
      riskScore: 82,
      tier: 'high',
      factors: [
        { name: 'Osteoporosis', contribution: 35, source: 'Dixon 2025, HR 2.4' },
        { name: 'Low baseline HHS (22)', contribution: 25, source: 'Vasios et al, HR 1.8' },
        { name: 'Age > 75', contribution: 12, source: 'Harris 2025, HR 1.4' },
        { name: 'Poor compliance', contribution: 10, source: 'UC3 Output' },
      ],
      recommendation: 'Enhanced surveillance with 3-month check-ins',
      demographics: { age: 78, gender: 'F', bmi: 24.2 },
    },
    {
      id: '031',
      riskScore: 71,
      tier: 'high',
      factors: [
        { name: 'Prior revision', contribution: 40, source: 'Meding 2025, HR 2.1' },
        { name: 'BMI > 35', contribution: 18, source: 'AOANJRR, HR 1.6' },
        { name: 'Missing imaging', contribution: 13, source: 'UC3 Output' },
      ],
      recommendation: 'Schedule additional 6-month imaging',
      demographics: { age: 65, gender: 'M', bmi: 36.8 },
    },
    {
      id: '023',
      riskScore: 68,
      tier: 'high',
      factors: [
        { name: 'Osteoporosis', contribution: 35, source: 'Dixon 2025, HR 2.4' },
        { name: 'Lost to follow-up risk', contribution: 20, source: 'UC3 Output' },
        { name: 'Low baseline HHS (28)', contribution: 13, source: 'Vasios et al' },
      ],
      recommendation: 'Urgent site contact for 2-year visit scheduling',
      demographics: { age: 72, gender: 'F', bmi: 27.1 },
    },
    {
      id: '009',
      riskScore: 55,
      tier: 'high',
      factors: [
        { name: 'Prior revision', contribution: 40, source: 'Meding 2025, HR 2.1' },
        { name: 'Slow HHS recovery', contribution: 15, source: 'Trajectory Analysis' },
      ],
      recommendation: 'Continue standard monitoring with close observation',
      demographics: { age: 68, gender: 'M', bmi: 29.4 },
    },
  ],
  modelInfo: {
    type: 'Ensemble (XGBoost + Literature HR + Registry)',
    confidence: 78,
    features: 12,
    lastUpdated: 'Jan 11, 2026',
  },
}

export default function Risk() {
  const [, params] = useRoute('/study/:studyId/risk')
  const studyId = params?.studyId || 'h34-delta'
  const [expandedPatient, setExpandedPatient] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['risk', studyId],
    queryFn: () => fetchRiskPatients(studyId),
    retry: false,
  })

  const risk = data || mockData

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'high': return 'text-red-600'
      case 'moderate': return 'text-amber-600'
      case 'low': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'high': return <Badge variant="danger">High Risk</Badge>
      case 'moderate': return <Badge variant="warning">Moderate</Badge>
      case 'low': return <Badge variant="success">Low</Badge>
      default: return <Badge variant="neutral">{tier}</Badge>
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Patient Risk Stratification</h1>
        <p className="text-gray-500 mt-1">ML-powered risk scoring with explainable factors</p>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Assessment</h3>
            <p className="text-gray-600 leading-relaxed">{risk.summary}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <Card className="text-center border-l-4 border-red-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">High Risk</p>
          <p className="text-4xl font-semibold text-red-600 mt-2">{risk.distribution.high}</p>
          <p className="text-sm text-gray-500 mt-1">&gt;20% revision risk</p>
        </Card>
        <Card className="text-center border-l-4 border-amber-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Moderate Risk</p>
          <p className="text-4xl font-semibold text-amber-600 mt-2">{risk.distribution.moderate}</p>
          <p className="text-sm text-gray-500 mt-1">10-20% revision risk</p>
        </Card>
        <Card className="text-center border-l-4 border-green-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Low Risk</p>
          <p className="text-4xl font-semibold text-green-600 mt-2">{risk.distribution.low}</p>
          <p className="text-sm text-gray-500 mt-1">&lt;10% revision risk</p>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="High-Risk Patients"
          subtitle="Patients requiring enhanced surveillance"
          action={<Badge variant="danger">{risk.patients.length} patients</Badge>}
        />
        <div className="mt-4 space-y-3">
          {risk.patients.map((patient) => (
            <div
              key={patient.id}
              className="border border-gray-100 rounded-xl overflow-hidden hover:border-gray-200 transition-colors"
            >
              <button
                onClick={() => setExpandedPatient(expandedPatient === patient.id ? null : patient.id)}
                className="w-full p-4 flex items-center gap-4 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-gray-500" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-semibold text-gray-800">Patient {patient.id}</span>
                    {getTierBadge(patient.tier)}
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {patient.demographics.age}y, {patient.demographics.gender}, BMI {patient.demographics.bmi}
                  </p>
                </div>
                <div className="text-right mr-4">
                  <span className={`text-3xl font-semibold ${getTierColor(patient.tier)}`}>
                    {patient.riskScore}%
                  </span>
                  <p className="text-xs text-gray-500">risk score</p>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedPatient === patient.id ? 'rotate-90' : ''
                }`} />
              </button>

              {expandedPatient === patient.id && (
                <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50/50 animate-fade-in">
                  <div className="py-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Risk Factor Breakdown</h4>
                    <div className="space-y-2">
                      {patient.factors.map((factor, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className="w-32 text-sm text-gray-600 truncate">{factor.name}</div>
                          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-amber-400 to-red-500 rounded-full"
                              style={{ width: `${factor.contribution}%` }}
                            />
                          </div>
                          <div className="w-12 text-sm font-medium text-gray-700 text-right">
                            +{factor.contribution}%
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-3">Sources: {patient.factors.map(f => f.source).join(', ')}</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-800">Recommendation</p>
                        <p className="text-sm text-blue-700">{patient.recommendation}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Model Information" />
        <div className="grid grid-cols-4 gap-6 mt-4">
          <div>
            <p className="text-sm text-gray-500">Model Type</p>
            <p className="font-medium text-gray-800 mt-1">{risk.modelInfo.type}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Confidence</p>
            <p className="font-medium text-gray-800 mt-1">{risk.modelInfo.confidence}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Features</p>
            <p className="font-medium text-gray-800 mt-1">{risk.modelInfo.features}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="font-medium text-gray-800 mt-1">{risk.modelInfo.lastUpdated}</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
