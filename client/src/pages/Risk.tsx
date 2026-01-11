import { Users, AlertTriangle, TrendingUp, Activity, Eye, Calendar, FileText } from 'lucide-react'
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
      riskFactors: ['Osteoporosis diagnosis', 'BMI > 35', 'Prior revision', 'Age > 75'],
      lastVisit: '2025-10-15',
      nextVisit: '2026-01-15',
      recommendations: ['Enhanced bone density monitoring', 'Fall prevention counseling', 'Quarterly imaging'],
    },
    {
      id: 'H34-014',
      riskScore: 82,
      riskLevel: 'high',
      riskFactors: ['Osteoporosis diagnosis', 'Diabetes', 'Smoking history'],
      lastVisit: '2025-11-20',
      nextVisit: '2026-02-20',
      recommendations: ['HbA1c monitoring', 'Smoking cessation support', 'Enhanced wound surveillance'],
    },
    {
      id: 'H34-023',
      riskScore: 78,
      riskLevel: 'high',
      riskFactors: ['Rheumatoid arthritis', 'Immunosuppressant therapy', 'Prior infection'],
      lastVisit: '2025-12-01',
      nextVisit: '2026-03-01',
      recommendations: ['Infection screening protocol', 'Immunosuppressant review', 'Monthly labs'],
    },
    {
      id: 'H34-031',
      riskScore: 65,
      riskLevel: 'medium',
      riskFactors: ['BMI > 30', 'Hypertension'],
      lastVisit: '2025-11-05',
      nextVisit: '2026-02-05',
      recommendations: ['Weight management program', 'Blood pressure monitoring'],
    },
    {
      id: 'H34-007',
      riskScore: 58,
      riskLevel: 'medium',
      riskFactors: ['Age > 70', 'Mild bone loss'],
      lastVisit: '2025-10-28',
      nextVisit: '2026-01-28',
      recommendations: ['Standard bone health protocol', 'Annual DEXA scan'],
    },
    {
      id: 'H34-019',
      riskScore: 52,
      riskLevel: 'medium',
      riskFactors: ['Previous contralateral THA', 'Activity level concerns'],
      lastVisit: '2025-09-15',
      nextVisit: '2025-12-15',
      recommendations: ['Activity modification counseling', 'Gait analysis'],
    },
    {
      id: 'H34-002',
      riskScore: 25,
      riskLevel: 'low',
      riskFactors: ['None identified'],
      lastVisit: '2025-11-10',
      nextVisit: '2026-02-10',
      recommendations: ['Standard follow-up protocol'],
    },
  ]

  const stats = {
    high: patients.filter(p => p.riskLevel === 'high').length,
    medium: patients.filter(p => p.riskLevel === 'medium').length,
    low: patients.filter(p => p.riskLevel === 'low').length,
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-600'
      case 'medium':
        return 'text-yellow-600'
      default:
        return 'text-green-600'
    }
  }

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'high':
        return <Badge variant="danger">High Risk</Badge>
      case 'medium':
        return <Badge variant="warning">Medium Risk</Badge>
      default:
        return <Badge variant="success">Low Risk</Badge>
    }
  }

  const getProgressColor = (score: number): 'danger' | 'warning' | 'success' => {
    if (score >= 70) return 'danger'
    if (score >= 50) return 'warning'
    return 'success'
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="info">UC4</Badge>
            <Badge>ML + Literature</Badge>
          </div>
          <h1 className="text-5xl font-semibold text-black tracking-tight mb-3">
            Patient Risk Stratification
          </h1>
          <p className="text-xl text-gray-500 font-light max-w-3xl">
            ML-powered risk scoring combined with literature-grounded factors. 
            Prioritized patient lists with explainable risk factors and actionable monitoring recommendations.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Total Patients</p>
            <p className="text-4xl font-bold text-black">37</p>
          </Card>
          <Card className="p-6 border-l-4 border-l-red-500">
            <p className="text-sm text-gray-500 mb-1">High Risk</p>
            <p className="text-4xl font-bold text-red-600">{stats.high}</p>
            <p className="text-sm text-gray-500 mt-1">Enhanced monitoring</p>
          </Card>
          <Card className="p-6 border-l-4 border-l-yellow-500">
            <p className="text-sm text-gray-500 mb-1">Medium Risk</p>
            <p className="text-4xl font-bold text-yellow-600">{stats.medium}</p>
            <p className="text-sm text-gray-500 mt-1">Watch list</p>
          </Card>
          <Card className="p-6 border-l-4 border-l-green-500">
            <p className="text-sm text-gray-500 mb-1">Low Risk</p>
            <p className="text-4xl font-bold text-green-600">{stats.low}</p>
            <p className="text-sm text-gray-500 mt-1">Standard protocol</p>
          </Card>
        </div>

        <Card className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-black">Patient Risk Registry</h2>
              <p className="text-sm text-gray-500 mt-1">Sorted by risk score (highest first)</p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm">Export List</Button>
              <Button variant="primary" size="sm">Generate Reports</Button>
            </div>
          </div>

          <div className="space-y-4">
            {patients.map((patient) => (
              <div
                key={patient.id}
                className={cn(
                  'p-6 rounded-xl border-2 transition-all hover:shadow-md',
                  patient.riskLevel === 'high' && 'border-red-200 bg-red-50',
                  patient.riskLevel === 'medium' && 'border-yellow-200 bg-yellow-50',
                  patient.riskLevel === 'low' && 'border-green-200 bg-green-50'
                )}
              >
                <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      'w-14 h-14 rounded-xl flex items-center justify-center',
                      patient.riskLevel === 'high' && 'bg-red-100',
                      patient.riskLevel === 'medium' && 'bg-yellow-100',
                      patient.riskLevel === 'low' && 'bg-green-100'
                    )}>
                      <span className={cn('text-2xl font-bold', getRiskColor(patient.riskLevel))}>
                        {patient.riskScore}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-black text-lg">{patient.id}</span>
                        {getRiskBadge(patient.riskLevel)}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>Last: {patient.lastVisit}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>Next: {patient.nextVisit}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm">
                      <Eye className="w-4 h-4 mr-1" /> View Profile
                    </Button>
                    <Button variant="secondary" size="sm">
                      <FileText className="w-4 h-4 mr-1" /> Care Plan
                    </Button>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="w-full max-w-md">
                    <ProgressBar 
                      value={patient.riskScore} 
                      size="sm" 
                      color={getProgressColor(patient.riskScore)}
                      showLabel={false}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Risk Factors</p>
                    <div className="flex flex-wrap gap-2">
                      {patient.riskFactors.map((factor, index) => (
                        <Badge key={index} variant="default" size="sm">{factor}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Recommendations</p>
                    <ul className="space-y-1">
                      {patient.recommendations.map((rec, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-xl font-semibold text-black mb-6">Risk Scoring Model</h2>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-purple-600" />
                  <span className="font-medium text-black">ML Component (40%)</span>
                </div>
                <p className="text-sm text-gray-600">
                  Trained on historical revision outcomes. Features: BMI, age, bone density, 
                  comorbidity index, surgical complexity.
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-black">Literature Factors (35%)</span>
                </div>
                <p className="text-sm text-gray-600">
                  Evidence-based risk factors from Dixon 2025, Harris 2025, Meding 2025. 
                  Osteoporosis, prior revision, immunosuppression.
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-black">Registry Benchmarks (25%)</span>
                </div>
                <p className="text-sm text-gray-600">
                  Population-specific adjustments from AOANJRR 2024. Age-sex-BMI stratified 
                  revision probabilities.
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold text-black mb-6">Key Insights</h2>
            <div className="space-y-4">
              <div className="p-4 border border-red-200 bg-red-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <span className="font-medium text-red-800">High-Risk Pattern</span>
                </div>
                <p className="text-sm text-red-700">
                  100% of high-risk patients have osteoporosis. Consider enhanced bone health 
                  protocol for all osteoporotic patients.
                </p>
              </div>
              <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="font-medium text-yellow-800">Emerging Concern</span>
                </div>
                <p className="text-sm text-yellow-700">
                  3 medium-risk patients trending upward. BMI increase detected at last visit. 
                  Consider early intervention.
                </p>
              </div>
              <div className="p-4 border border-green-200 bg-green-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-800">Positive Trend</span>
                </div>
                <p className="text-sm text-green-700">
                  81% of patients (30/37) maintaining or improving risk scores. 
                  Intervention protocols showing effectiveness.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
