import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchRiskSummary, RiskSummaryResponse } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, AlertTriangle, TrendingUp, XCircle, Activity, Users } from 'lucide-react'

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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-gray-500 mx-auto mb-4" />
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

  const overallStatus = highRisk > 0 ? 'concerning' : moderateRisk > 3 ? 'moderate' : 'good'

  const summary = highRisk > 0
    ? `Risk analysis identified ${highRisk} high-risk patient(s) requiring immediate attention. ${moderateRisk} patients have moderate risk and ${lowRisk} are low risk. Mean risk score across population: ${(data.mean_risk_score * 100).toFixed(1)}%.`
    : `No high-risk patients identified. ${moderateRisk} patient(s) have moderate risk factors and ${lowRisk} are low risk. Mean risk score across population: ${(data.mean_risk_score * 100).toFixed(1)}%.`

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Patient Risk Stratification</h1>
        <p className="text-gray-500 mt-1">ML-powered risk assessment for revision prediction</p>
      </div>

      <Card className="bg-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-800 mb-2">AI Assessment</h3>
            <p className="text-gray-600 leading-relaxed">{summary}</p>
            <p className="text-xs text-gray-400 mt-2">
              Assessment Date: {new Date(data.assessment_date).toLocaleString()}
            </p>
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

      <Card>
        <CardHeader title="Risk Metrics" subtitle="Population-level risk statistics" />
        <div className="grid grid-cols-3 gap-6 mt-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Mean Risk Score</p>
            <p className="text-2xl font-semibold text-gray-800 mt-1">{(data.mean_risk_score * 100).toFixed(1)}%</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Overall Status</p>
            <div className="mt-1">
              <Badge variant={overallStatus === 'good' ? 'success' : overallStatus === 'moderate' ? 'warning' : 'danger'}>
                {overallStatus === 'good' ? 'Low Risk Population' : overallStatus === 'moderate' ? 'Moderate Concern' : 'Action Required'}
              </Badge>
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">High Risk Patients</p>
            <p className="text-2xl font-semibold text-gray-800 mt-1">
              {data.high_risk_patients.length > 0 ? data.high_risk_patients.join(', ') : 'None'}
            </p>
          </div>
        </div>
      </Card>

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
