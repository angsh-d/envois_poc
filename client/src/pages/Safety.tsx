import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchSafetySignals } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, AlertTriangle, CheckCircle, Info, ExternalLink, XCircle, Activity, TrendingDown, ChevronDown, Users, BookOpen, Lightbulb } from 'lucide-react'

// Type definitions for real API response
interface SafetyMetric {
  metric: string
  rate: number
  count: number
  total: number
  threshold: number
  signal: boolean
  threshold_exceeded_by: number
}

interface RegistryComparison {
  metric: string
  study_value: number
  registry_median: number
  registry_p75: number
  registry_p95: number
  signal: boolean
  signal_level: string | null
  difference: number
  favorable: boolean
  percentile_position: string
}

interface SafetyResponse {
  success: boolean
  assessment_date: string
  n_patients: number
  overall_status: string
  signals: Array<{ metric: string; rate: number; threshold: number }>
  n_signals: number
  metrics: SafetyMetric[]
  registry_comparison: {
    comparisons: RegistryComparison[]
    signals: unknown[]
    n_signals: number
    registry_source: string
    registry_year: number
  }
  literature_benchmarks: Record<string, {
    mean?: number
    median?: number
    sd?: number
    range?: number[]
    p25?: number
    p75?: number
    concern_threshold?: number
  }>
  narrative: string
  sources: Array<{ type: string; reference: string; confidence: number }>
  confidence: number
  execution_time_ms: number
}

// Format metric name for display
function formatMetricName(metric: string): string {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

export default function Safety() {
  const [, params] = useRoute('/study/:studyId/safety')
  const studyId = params?.studyId || 'h34-delta'
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery<SafetyResponse>({
    queryKey: ['safety-signals'],
    queryFn: fetchSafetySignals,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: true,
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
          <p className="text-gray-600">Failed to load safety data</p>
        </div>
      </div>
    )
  }

  // Get status color based on overall status
  const getStatusColor = () => {
    switch (data.overall_status) {
      case 'acceptable': return 'success'
      case 'monitor': return 'warning'
      case 'concern': return 'danger'
      default: return 'neutral'
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Safety Signals</h1>
        <p className="text-gray-500 mt-1">Cross-source contextualization of adverse events</p>
      </div>

      {/* AI Summary */}
      <Card className="bg-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-800 mb-2">AI Analysis</h3>
            <p className="text-gray-600 leading-relaxed">{data.narrative}</p>
            <div className="flex items-center gap-4 mt-3">
              <Badge variant={getStatusColor() as 'success' | 'warning' | 'danger' | 'neutral'}>
                {data.overall_status.charAt(0).toUpperCase() + data.overall_status.slice(1)}
              </Badge>
              <span className="text-xs text-gray-400">
                Confidence: {(data.confidence * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-gray-400">
                Assessment: {new Date(data.assessment_date).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Overview Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Patients</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{data.n_patients}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Metrics Tracked</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{data.metrics.length}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Active Signals</p>
          <p className="text-3xl font-semibold mt-2 text-gray-800">
            {data.n_signals}
          </p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Status</p>
          <div className="mt-2">
            <Badge variant={getStatusColor() as 'success' | 'warning' | 'danger' | 'neutral'} className="text-lg px-3 py-1">
              {data.overall_status.charAt(0).toUpperCase() + data.overall_status.slice(1)}
            </Badge>
          </div>
        </Card>
      </div>

      {/* Safety Metrics Table */}
      <Card>
        <CardHeader title="Safety Metrics" subtitle="Adverse event rates vs protocol thresholds" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Events</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Rate</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Threshold</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.metrics.map((metric, i) => {
              const isExpanded = expandedMetric === metric.metric
              const metricKey = metric.metric.replace(/_rate$/, '')
              const benchmark = data.literature_benchmarks?.[metricKey]
              
              const getSignalDetails = () => {
                const details: { factors: string[], patients: string, recommendations: string[] } = {
                  factors: [],
                  patients: `${metric.count} of ${metric.total} patients`,
                  recommendations: []
                }
                
                if (metric.metric === 'dislocation_rate') {
                  details.factors = [
                    'Posterior surgical approach (vs anterior)',
                    'History of prior hip surgery',
                    'Low BMI patients (<22)',
                    'Non-compliance with movement restrictions'
                  ]
                  details.recommendations = [
                    'Review surgical approach protocols',
                    'Enhance post-op movement restriction education',
                    'Consider larger femoral head size for high-risk patients'
                  ]
                } else if (metric.metric === 'fracture_rate') {
                  details.factors = [
                    'Osteoporosis or poor bone quality',
                    'Press-fit component fixation',
                    'Age >75 years',
                    'Paprosky Type 3 defects'
                  ]
                  details.recommendations = [
                    'Pre-operative bone density screening',
                    'Consider cemented fixation for poor bone quality',
                    'Enhanced intraoperative bone protection protocols'
                  ]
                } else if (metric.metric === 'infection_rate') {
                  details.factors = [
                    'Diabetes mellitus',
                    'BMI >35',
                    'Prolonged operative time (>3 hours)',
                    'Prior revision surgery'
                  ]
                  details.recommendations = [
                    'Pre-operative glucose optimization',
                    'Extended antibiotic prophylaxis for high-risk patients',
                    'Enhanced sterile technique protocols'
                  ]
                } else if (metric.metric === 'revision_rate') {
                  details.factors = [
                    'Complex primary diagnosis',
                    'Multiple prior surgeries',
                    'Bone loss severity',
                    'Implant selection factors'
                  ]
                  details.recommendations = [
                    'Extended follow-up for high-risk cohorts',
                    'Review implant selection criteria',
                    'Consider specialized revision centers'
                  ]
                }
                return details
              }
              
              const signalDetails = getSignalDetails()
              
              return (
                <React.Fragment key={i}>
                  <tr 
                    className={`border-b border-gray-50 last:border-0 transition-colors ${
                      metric.signal ? 'cursor-pointer hover:bg-gray-100' : 'hover:bg-gray-50'
                    } ${isExpanded ? 'bg-gray-50' : ''}`}
                    onClick={() => metric.signal && setExpandedMetric(isExpanded ? null : metric.metric)}
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        {metric.signal && (
                          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                        )}
                        <Activity className={`w-4 h-4 ${metric.signal ? 'text-gray-700' : 'text-gray-400'}`} />
                        <span className="font-medium text-gray-800">{formatMetricName(metric.metric)}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-center text-gray-600">
                      {metric.count}/{metric.total}
                    </td>
                    <td className="py-4 px-4 text-center">
                      <span className={`font-semibold ${metric.signal ? 'text-gray-900' : 'text-gray-700'}`}>
                        {(metric.rate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-4 px-4 text-center text-gray-500">
                      {(metric.threshold * 100).toFixed(0)}%
                    </td>
                    <td className="py-4 px-4 text-center">
                      {metric.signal ? (
                        <Badge variant="danger">Signal</Badge>
                      ) : (
                        <Badge variant="success">OK</Badge>
                      )}
                    </td>
                  </tr>
                  
                  {isExpanded && metric.signal && (
                    <tr>
                      <td colSpan={5} className="bg-gray-50 px-4 pb-4">
                        <div className="grid grid-cols-3 gap-4 pt-2">
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <Users className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Affected Patients</h4>
                                <p className="text-xs text-gray-500">{signalDetails.patients}</p>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <p className="text-xs font-medium text-gray-500 uppercase">Contributing Factors</p>
                              <ul className="space-y-1.5">
                                {signalDetails.factors.map((factor, idx) => (
                                  <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                                    <span className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0" />
                                    {factor}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                          
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <BookOpen className="w-4 h-4 text-gray-600" />
                              </div>
                              <h4 className="font-semibold text-gray-900 text-sm">Literature Context</h4>
                            </div>
                            {benchmark ? (
                              <div className="space-y-3">
                                <div className="grid grid-cols-2 gap-3">
                                  {benchmark.mean !== undefined && (
                                    <div className="bg-gray-50 rounded-lg p-2">
                                      <p className="text-lg font-bold text-gray-900">{(benchmark.mean * 100).toFixed(1)}%</p>
                                      <p className="text-xs text-gray-500">Literature Mean</p>
                                    </div>
                                  )}
                                  {benchmark.range && (
                                    <div className="bg-gray-50 rounded-lg p-2">
                                      <p className="text-lg font-bold text-gray-900">{(benchmark.range[0] * 100).toFixed(0)}-{(benchmark.range[1] * 100).toFixed(0)}%</p>
                                      <p className="text-xs text-gray-500">Published Range</p>
                                    </div>
                                  )}
                                </div>
                                {benchmark.concern_threshold !== undefined && (
                                  <div className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg">
                                    <AlertTriangle className="w-4 h-4 text-gray-600" />
                                    <span className="text-xs text-gray-700">
                                      Concern threshold: {(benchmark.concern_threshold * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                )}
                                <p className="text-xs text-gray-500">
                                  Study rate of {(metric.rate * 100).toFixed(1)}% exceeds threshold by {((metric.rate - metric.threshold) * 100).toFixed(1)} percentage points
                                </p>
                              </div>
                            ) : (
                              <p className="text-xs text-gray-500">No literature benchmarks available for this metric</p>
                            )}
                          </div>
                          
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <Lightbulb className="w-4 h-4 text-gray-600" />
                              </div>
                              <h4 className="font-semibold text-gray-900 text-sm">Recommendations</h4>
                            </div>
                            <ul className="space-y-2">
                              {signalDetails.recommendations.map((rec, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <CheckCircle className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                                  <span className="text-xs text-gray-700">{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </Card>

      {/* Registry Comparison */}
      {data.registry_comparison && data.registry_comparison.comparisons.length > 0 && (
        <Card>
          <CardHeader
            title="Registry Comparison"
            action={
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                {data.registry_comparison.registry_source} ({data.registry_comparison.registry_year})
              </span>
            }
          />
          <table className="w-full mt-4">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Study</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Registry Median</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Position</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.registry_comparison.comparisons.map((comp, i) => (
                <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                  <td className="py-4 px-4 font-medium text-gray-800">{formatMetricName(comp.metric)}</td>
                  <td className="py-4 px-4 text-center text-gray-800">
                    {(comp.study_value * 100).toFixed(1)}%
                  </td>
                  <td className="py-4 px-4 text-center text-gray-500">
                    {(comp.registry_median * 100).toFixed(1)}%
                  </td>
                  <td className="py-4 px-4 text-center text-gray-600">
                    {comp.percentile_position}
                  </td>
                  <td className="py-4 px-4 text-center">
                    {comp.favorable ? (
                      <Badge variant="success">Favorable</Badge>
                    ) : comp.signal ? (
                      <Badge variant="danger">Signal</Badge>
                    ) : (
                      <Badge variant="warning">Monitor</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Literature Benchmarks */}
      <Card>
        <CardHeader title="Literature Benchmarks" subtitle="Expected ranges from published studies" />
        <div className="mt-4 grid grid-cols-2 gap-4">
          {Object.entries(data.literature_benchmarks).slice(0, 8).map(([key, benchmark], i) => (
            <div key={i} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">{formatMetricName(key)}</span>
                {benchmark.concern_threshold && (
                  <span className="text-xs text-gray-400">
                    Concern: {(benchmark.concern_threshold * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-center gap-4">
                {benchmark.mean !== undefined && (
                  <span className="text-sm text-gray-600">
                    Mean: <span className="font-medium">{typeof benchmark.mean === 'number' && benchmark.mean < 1 ? `${(benchmark.mean * 100).toFixed(1)}%` : benchmark.mean.toFixed(1)}</span>
                  </span>
                )}
                {benchmark.median !== undefined && (
                  <span className="text-sm text-gray-600">
                    Median: <span className="font-medium">{typeof benchmark.median === 'number' && benchmark.median < 1 ? `${(benchmark.median * 100).toFixed(1)}%` : benchmark.median.toFixed(1)}</span>
                  </span>
                )}
                {benchmark.range && (
                  <span className="text-sm text-gray-500">
                    Range: {benchmark.range[0] < 1 ? `${(benchmark.range[0] * 100).toFixed(0)}-${(benchmark.range[1] * 100).toFixed(0)}%` : `${benchmark.range[0]}-${benchmark.range[1]}`}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Conclusion */}
      <Card className="border-l-4 border-gray-300 bg-gray-50/50">
        <div className="flex items-start gap-4">
          {data.n_signals === 0 ? (
            <CheckCircle className="w-6 h-6 text-gray-600 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-gray-600 flex-shrink-0" />
          )}
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">Conclusion</h3>
            <p className="text-gray-600 leading-relaxed">
              {data.n_signals === 0
                ? 'All safety metrics are within acceptable thresholds. No safety signals detected based on protocol requirements and registry benchmarks.'
                : `${data.n_signals} safety signal(s) detected that require monitoring and potential intervention.`}
            </p>
          </div>
        </div>
      </Card>

      {/* Data Sources */}
      <Card>
        <CardHeader title="Data Sources" subtitle={`${data.sources.length} sources used for this assessment`} />
        <div className="mt-4 space-y-2">
          {data.sources.map((source, i) => (
            <div key={i} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant="neutral" className="text-xs">{source.type}</Badge>
                <span className="text-sm text-gray-700">{source.reference}</span>
              </div>
              <span className="text-xs text-gray-400">
                Confidence: {(source.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
