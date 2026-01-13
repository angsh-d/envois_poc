import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchRiskSummary, RiskSummaryResponse, PatientRiskDetail, FactorPrevalence } from '@/lib/api'
import { useRoute } from 'wouter'
import { 
  Sparkles, AlertTriangle, TrendingUp, Activity, Users, 
  ChevronDown, ChevronUp, Download, ClipboardList, 
  BarChart3, Shield, Clock
} from 'lucide-react'

function formatFactorName(factor: string): string {
  return factor
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

function RiskScoreBar({ score }: { score: number }) {
  const percentage = Math.round(score * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gray-600 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-sm font-medium text-gray-600 w-12 text-right">{percentage}%</span>
    </div>
  )
}

function PatientCard({ patient, isExpanded, onToggle }: { 
  patient: PatientRiskDetail
  isExpanded: boolean
  onToggle: () => void 
}) {
  const riskLevel = patient.risk_score >= 0.6 ? 'high' : patient.risk_score >= 0.3 ? 'moderate' : 'low'
  
  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden bg-white">
      <button 
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
            <span className="text-sm font-medium text-gray-600">
              {patient.patient_id.slice(-3)}
            </span>
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-900">{patient.patient_id}</p>
            <p className="text-sm text-gray-500">
              {patient.n_risk_factors} risk factor{patient.n_risk_factors !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-32">
            <RiskScoreBar score={patient.risk_score} />
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-6 mt-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Contributing Factors
              </h4>
              {patient.contributing_factors.length > 0 ? (
                <div className="space-y-2">
                  {patient.contributing_factors.map((factor, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-700">{formatFactorName(factor.factor)}</span>
                      <span className="text-xs font-medium text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                        HR: {factor.hazard_ratio.toFixed(1)}x
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">No significant risk factors identified</p>
              )}
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <ClipboardList className="w-4 h-4" />
                Recommended Actions
              </h4>
              <div className="space-y-2">
                {patient.recommendations.map((rec, idx) => (
                  <div key={idx} className="p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Badge variant={rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'success'} className="mt-0.5 text-xs">
                        {rec.priority}
                      </Badge>
                      <div>
                        <p className="text-sm text-gray-700">{rec.action}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.rationale}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TierSection({ 
  title, 
  subtitle,
  patients, 
  tierColor,
  icon: Icon,
  defaultExpanded = false
}: { 
  title: string
  subtitle: string
  patients: PatientRiskDetail[]
  tierColor: string
  icon: typeof AlertTriangle
  defaultExpanded?: boolean
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [expandedPatients, setExpandedPatients] = useState<Set<string>>(new Set())
  
  const togglePatient = (patientId: string) => {
    setExpandedPatients(prev => {
      const next = new Set(prev)
      if (next.has(patientId)) {
        next.delete(patientId)
      } else {
        next.add(patientId)
      }
      return next
    })
  }
  
  const handleExport = () => {
    const csv = [
      ['Patient ID', 'Risk Score', 'Risk Factors', 'Top Factor', 'Recommended Action'].join(','),
      ...patients.map(p => [
        p.patient_id,
        (p.risk_score * 100).toFixed(1) + '%',
        p.n_risk_factors,
        p.contributing_factors[0]?.factor || 'None',
        p.recommendations[0]?.action || 'Standard monitoring'
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${title.toLowerCase().replace(' ', '_')}_patients.csv`
    a.click()
  }
  
  return (
    <Card className={`border-l-4 ${tierColor}`}>
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
            <Icon className="w-5 h-5 text-gray-600" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-gray-800">{title}</h3>
            <p className="text-sm text-gray-500">{subtitle}</p>
          </div>
          <Badge variant="neutral" className="ml-2">{patients.length} patients</Badge>
        </div>
        <div className="flex items-center gap-2">
          {isExpanded && patients.length > 0 && (
            <button 
              onClick={(e) => { e.stopPropagation(); handleExport(); }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Export to CSV"
            >
              <Download className="w-4 h-4 text-gray-500" />
            </button>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="mt-4 space-y-2">
          {patients.length > 0 ? (
            patients.map(patient => (
              <PatientCard 
                key={patient.patient_id}
                patient={patient}
                isExpanded={expandedPatients.has(patient.patient_id)}
                onToggle={() => togglePatient(patient.patient_id)}
              />
            ))
          ) : (
            <p className="text-gray-500 text-sm py-4 text-center">No patients in this category</p>
          )}
        </div>
      )}
    </Card>
  )
}

function FactorPrevalenceCard({ factors }: { factors: FactorPrevalence[] }) {
  if (!factors || factors.length === 0) return null
  
  const maxCount = Math.max(...factors.map(f => f.count))
  
  return (
    <Card>
      <CardHeader 
        title="Risk Factor Prevalence" 
        subtitle="Most common risk factors across the population" 
      />
      <div className="mt-4 space-y-3">
        {factors.slice(0, 6).map((factor, idx) => (
          <div key={idx} className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{formatFactorName(factor.factor)}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{factor.count} patients ({factor.percentage}%)</span>
                  <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                    HR: {factor.hazard_ratio.toFixed(1)}x
                  </span>
                </div>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gray-400 rounded-full transition-all duration-500"
                  style={{ width: `${(factor.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export default function Risk() {
  const [, params] = useRoute('/study/:studyId/risk')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading, error } = useQuery<RiskSummaryResponse>({
    queryKey: ['risk', studyId],
    queryFn: () => fetchRiskSummary(),
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-48 bg-gray-100 rounded animate-pulse mt-2" />
        </div>
        <div className="h-32 bg-gray-100 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => (
            <div key={i} className="h-28 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
        <div className="h-48 bg-gray-100 rounded-2xl animate-pulse" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Failed to load risk data</p>
        </div>
      </div>
    )
  }

  const totalPatients = data.n_patients
  const highRisk = data.risk_distribution.high || 0
  const moderateRisk = data.risk_distribution.moderate || 0
  const lowRisk = data.risk_distribution.low || 0

  const highRiskPct = totalPatients > 0 ? ((highRisk / totalPatients) * 100).toFixed(1) : '0'
  const moderateRiskPct = totalPatients > 0 ? ((moderateRisk / totalPatients) * 100).toFixed(1) : '0'
  const lowRiskPct = totalPatients > 0 ? ((lowRisk / totalPatients) * 100).toFixed(1) : '0'

  const summary = highRisk > 0
    ? `${highRisk} patient${highRisk !== 1 ? 's' : ''} require${highRisk === 1 ? 's' : ''} immediate attention with enhanced monitoring protocols. ${moderateRisk} patient${moderateRisk !== 1 ? 's' : ''} have elevated risk factors warranting proactive management. Population mean risk: ${(data.mean_risk_score * 100).toFixed(0)}%.`
    : `No high-risk patients identified. ${moderateRisk} patient${moderateRisk !== 1 ? 's' : ''} have moderate risk factors to monitor. Population is generally low risk with mean score of ${(data.mean_risk_score * 100).toFixed(0)}%.`

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Patient Risk Stratification</h1>
        <p className="text-gray-500 mt-1">ML-powered risk assessment with actionable clinical recommendations</p>
      </div>

      <Card className="bg-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-800 mb-2">AI Assessment Summary</h3>
            <p className="text-gray-600 leading-relaxed">{summary}</p>
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(data.assessment_date).toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <Shield className="w-3 h-3" />
                Literature-validated hazard ratios
              </span>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-4 gap-4">
        <Card className="text-center border-l-4 border-gray-400">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Users className="w-5 h-5 text-gray-600" />
          </div>
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Patients</p>
          <p className="text-4xl font-semibold text-gray-800 mt-2">{totalPatients}</p>
        </Card>
        <Card className="text-center border-l-4 border-gray-700">
          <div className="flex items-center justify-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-gray-600" />
          </div>
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">High Risk</p>
          <p className="text-4xl font-semibold text-gray-800 mt-2">{highRisk}</p>
          <p className="text-sm text-gray-500 mt-1">{highRiskPct}%</p>
        </Card>
        <Card className="text-center border-l-4 border-gray-500">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-gray-600" />
          </div>
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Moderate Risk</p>
          <p className="text-4xl font-semibold text-gray-700 mt-2">{moderateRisk}</p>
          <p className="text-sm text-gray-500 mt-1">{moderateRiskPct}%</p>
        </Card>
        <Card className="text-center border-l-4 border-gray-300">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-gray-600" />
          </div>
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Low Risk</p>
          <p className="text-4xl font-semibold text-gray-600 mt-2">{lowRisk}</p>
          <p className="text-sm text-gray-500 mt-1">{lowRiskPct}%</p>
        </Card>
      </div>

      <Card>
        <CardHeader title="Risk Distribution" subtitle="Patient risk stratification breakdown" />
        <div className="mt-6">
          <div className="h-8 w-full rounded-lg overflow-hidden flex">
            {highRisk > 0 && (
              <div
                className="bg-gray-800 flex items-center justify-center text-white text-xs font-medium"
                style={{ width: `${(highRisk / totalPatients) * 100}%` }}
              >
                {highRiskPct}%
              </div>
            )}
            {moderateRisk > 0 && (
              <div
                className="bg-gray-500 flex items-center justify-center text-white text-xs font-medium"
                style={{ width: `${(moderateRisk / totalPatients) * 100}%` }}
              >
                {moderateRiskPct}%
              </div>
            )}
            {lowRisk > 0 && (
              <div
                className="bg-gray-300 flex items-center justify-center text-gray-700 text-xs font-medium"
                style={{ width: `${(lowRisk / totalPatients) * 100}%` }}
              >
                {lowRiskPct}%
              </div>
            )}
          </div>
          <div className="flex justify-between mt-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-gray-800"></div>
              <span>High Risk ({highRisk})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-gray-500"></div>
              <span>Moderate ({moderateRisk})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-gray-300"></div>
              <span>Low Risk ({lowRisk})</span>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        <FactorPrevalenceCard factors={data.factor_prevalence || []} />
        
        <Card>
          <CardHeader title="Population Metrics" subtitle="Statistical overview of risk distribution" />
          <div className="mt-4 space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-gray-500" />
                <span className="text-sm text-gray-600">Mean Risk Score</span>
              </div>
              <span className="text-xl font-semibold text-gray-800">{(data.mean_risk_score * 100).toFixed(1)}%</span>
            </div>
            {data.median_risk_score !== undefined && (
              <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-gray-500" />
                  <span className="text-sm text-gray-600">Median Risk Score</span>
                </div>
                <span className="text-xl font-semibold text-gray-800">{(data.median_risk_score * 100).toFixed(1)}%</span>
              </div>
            )}
            {data.std_risk_score !== undefined && (
              <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-gray-500" />
                  <span className="text-sm text-gray-600">Standard Deviation</span>
                </div>
                <span className="text-xl font-semibold text-gray-800">{(data.std_risk_score * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Patient Cohorts</h2>
        <p className="text-sm text-gray-500">Click to expand each tier and view individual patient details, risk factors, and recommended actions</p>
        
        <TierSection 
          title="High Risk Patients"
          subtitle="Require immediate attention and enhanced monitoring"
          patients={data.high_risk_patients || []}
          tierColor="border-gray-700"
          icon={AlertTriangle}
          defaultExpanded={true}
        />
        
        <TierSection 
          title="Moderate Risk Patients"
          subtitle="Elevated risk factors warranting proactive management"
          patients={data.moderate_risk_patients || []}
          tierColor="border-gray-500"
          icon={Activity}
          defaultExpanded={false}
        />
        
        <TierSection 
          title="Low Risk Patients"
          subtitle="Standard follow-up protocol recommended"
          patients={data.low_risk_patients || []}
          tierColor="border-gray-300"
          icon={TrendingUp}
          defaultExpanded={false}
        />
      </div>

      {data.note && (
        <Card className="bg-gray-50 border-gray-200">
          <div className="flex items-start gap-3">
            <Activity className="w-5 h-5 text-gray-600 mt-0.5" />
            <div>
              <p className="font-medium text-gray-800">Note</p>
              <p className="text-sm text-gray-600 mt-1">{data.note}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
