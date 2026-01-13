import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchRiskSummary } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, AlertTriangle, TrendingUp, XCircle, Activity, BookOpen } from 'lucide-react'

// Type definitions for real API response
interface RiskSummaryResponse {
  generated_at: string
  model_version: string
  n_risk_factors: number
  risk_thresholds: {
    high: string
    moderate: string
    low: string
  }
  hazard_ratios: Record<string, number>
  literature_sources: string[]
}

// Format factor name for display
function formatFactorName(factor: string): string {
  return factor
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

// Get priority level based on hazard ratio
function getPriority(hr: number): 'high' | 'medium' | 'low' {
  if (hr >= 2.0) return 'high'
  if (hr >= 1.5) return 'medium'
  return 'low'
}

export default function Risk() {
  const [, params] = useRoute('/study/:studyId/risk')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading, error } = useQuery<RiskSummaryResponse>({
    queryKey: ['risk', studyId],
    queryFn: () => fetchRiskSummary(studyId),
    retry: false,
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
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Failed to load risk data</p>
        </div>
      </div>
    )
  }

  // Sort hazard ratios by value (descending)
  const sortedFactors = Object.entries(data.hazard_ratios)
    .sort(([, a], [, b]) => b - a)
    .map(([factor, hr]) => ({
      factor,
      hr,
      priority: getPriority(hr),
    }))

  // Count factors by priority
  const highPriorityCount = sortedFactors.filter(f => f.priority === 'high').length
  const mediumPriorityCount = sortedFactors.filter(f => f.priority === 'medium').length
  const lowPriorityCount = sortedFactors.filter(f => f.priority === 'low').length

  // Generate summary based on data
  const topFactors = sortedFactors.slice(0, 3)
  const summary = `Risk model identifies ${data.n_risk_factors} risk factors for revision prediction. ` +
    `Top risk factors are ${topFactors.map(f => `${formatFactorName(f.factor)} (HR ${f.hr.toFixed(2)})`).join(', ')}. ` +
    `Model version: ${data.model_version}.`

  const getPriorityBadge = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high': return <Badge variant="danger">High</Badge>
      case 'medium': return <Badge variant="warning">Medium</Badge>
      case 'low': return <Badge variant="success">Low</Badge>
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Risk Factor Analysis</h1>
        <p className="text-gray-500 mt-1">Literature-derived hazard ratios for patient risk stratification</p>
      </div>

      {/* AI Summary */}
      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-800 mb-2">AI Assessment</h3>
            <p className="text-gray-600 leading-relaxed">{summary}</p>
            <p className="text-xs text-gray-400 mt-2">
              Generated: {new Date(data.generated_at).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      {/* Risk Factor Distribution */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="text-center border-l-4 border-red-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">High Priority</p>
          <p className="text-4xl font-semibold text-red-600 mt-2">{highPriorityCount}</p>
          <p className="text-sm text-gray-500 mt-1">HR ≥ 2.0</p>
        </Card>
        <Card className="text-center border-l-4 border-amber-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Medium Priority</p>
          <p className="text-4xl font-semibold text-amber-600 mt-2">{mediumPriorityCount}</p>
          <p className="text-sm text-gray-500 mt-1">HR 1.5 - 2.0</p>
        </Card>
        <Card className="text-center border-l-4 border-green-500">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Lower Priority</p>
          <p className="text-4xl font-semibold text-green-600 mt-2">{lowPriorityCount}</p>
          <p className="text-sm text-gray-500 mt-1">HR &lt; 1.5</p>
        </Card>
      </div>

      {/* Risk Thresholds */}
      <Card>
        <CardHeader title="Risk Stratification Thresholds" subtitle="Model-defined risk categories" />
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="p-4 bg-red-50 rounded-lg border border-red-100">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="font-medium text-red-800">High Risk</span>
            </div>
            <p className="text-sm text-red-700">{data.risk_thresholds.high}</p>
          </div>
          <div className="p-4 bg-amber-50 rounded-lg border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-amber-600" />
              <span className="font-medium text-amber-800">Moderate Risk</span>
            </div>
            <p className="text-sm text-amber-700">{data.risk_thresholds.moderate}</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-100">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="font-medium text-green-800">Low Risk</span>
            </div>
            <p className="text-sm text-green-700">{data.risk_thresholds.low}</p>
          </div>
        </div>
      </Card>

      {/* Hazard Ratios Table */}
      <Card>
        <CardHeader
          title="Risk Factors & Hazard Ratios"
          subtitle="Literature-derived hazard ratios for revision prediction"
          action={<Badge variant="neutral">{data.n_risk_factors} factors</Badge>}
        />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Risk Factor</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Hazard Ratio</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Relative Risk</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Priority</th>
            </tr>
          </thead>
          <tbody>
            {sortedFactors.map((item, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                <td className="py-4 px-4">
                  <span className="font-medium text-gray-800">{formatFactorName(item.factor)}</span>
                </td>
                <td className="py-4 px-4 text-center">
                  <span className={`font-semibold ${
                    item.hr >= 2.0 ? 'text-red-600' :
                    item.hr >= 1.5 ? 'text-amber-600' :
                    item.hr < 1 ? 'text-green-600' : 'text-gray-800'
                  }`}>
                    {item.hr.toFixed(2)}
                  </span>
                </td>
                <td className="py-4 px-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          item.hr >= 2.0 ? 'bg-red-500' :
                          item.hr >= 1.5 ? 'bg-amber-500' :
                          item.hr < 1 ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                        style={{ width: `${Math.min(100, (item.hr / 4.5) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {item.hr >= 1 ? `+${((item.hr - 1) * 100).toFixed(0)}%` : `${((item.hr - 1) * 100).toFixed(0)}%`}
                    </span>
                  </div>
                </td>
                <td className="py-4 px-4 text-center">
                  {getPriorityBadge(item.priority)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Model Information */}
      <Card>
        <CardHeader title="Model Information" />
        <div className="grid grid-cols-3 gap-6 mt-4">
          <div>
            <p className="text-sm text-gray-500">Model Version</p>
            <p className="font-medium text-gray-800 mt-1">{data.model_version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Risk Factors</p>
            <p className="font-medium text-gray-800 mt-1">{data.n_risk_factors}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="font-medium text-gray-800 mt-1">{new Date(data.generated_at).toLocaleDateString()}</p>
          </div>
        </div>
      </Card>

      {/* Literature Sources */}
      <Card>
        <CardHeader
          title="Literature Sources"
          subtitle="Publications used to derive hazard ratios"
          action={<Badge variant="neutral">{data.literature_sources.length} sources</Badge>}
        />
        <div className="mt-4 flex flex-wrap gap-2">
          {data.literature_sources.map((source, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
              <BookOpen className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-700">{source}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
