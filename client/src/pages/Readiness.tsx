import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchReadiness } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, CheckCircle, AlertTriangle, XCircle, Users, Shield, Activity, Database, ChevronDown, ChevronRight } from 'lucide-react'

// Helper to safely render values that might be code objects
const isCodeObject = (value: unknown): value is { code: string; decode: string; codeSystem?: string } => {
  return typeof value === 'object' && value !== null && 'code' in value && 'decode' in value
}

const safeRenderValue = (value: unknown): string => {
  if (value === null || value === undefined) return 'N/A'
  if (isCodeObject(value)) {
    return `${value.decode} (${value.code})`
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

// Type definitions for real API response
interface SafetySignalDetail {
  metric: string
  observed_rate: string
  threshold: string
  calculation: string
  exceeded_by: string
}

interface BlockingIssueProvenance {
  calculation?: string
  values?: Record<string, number | string>
  threshold?: string
  thresholds?: Record<string, string>
  signals_detected?: SafetySignalDetail[]
  current_status?: string
  source?: string
  regulatory_reference?: string
  classification_rules?: Record<string, string>
  definitions?: Record<string, string>
  determination?: string
}

interface BlockingIssue {
  category: string
  issue: string
  provenance?: BlockingIssueProvenance
}

interface EnrollmentData {
  enrolled: number
  target: number
  interim_target: number
  percent_complete: number
  status: string
  is_ready: boolean
}

interface ComplianceData {
  deviation_rate: number
  by_severity: Record<string, number>
  status: string
  is_ready: boolean
}

interface SafetyData {
  n_signals: number
  overall_status: string
  is_ready: boolean
}

interface DataCompletenessData {
  enrolled: number
  completed: number
  withdrawn: number
  evaluable: number
  completion_rate: number
  is_ready: boolean
}

interface SourceDetails {
  data_source?: string
  data_fields?: string[]
  query_types?: string[]
  protocol_id?: string
  sample_size_target?: number
  primary_endpoint?: string
  regulatory_reference?: string
  calculation?: string
  protocol_reference?: string
  thresholds_source?: string
  metrics_evaluated?: string[]
}

interface Source {
  type: string
  reference: string
  confidence: number
  details?: SourceDetails
}

interface ReadinessResponse {
  success: boolean
  assessment_date: string
  protocol_id: string
  protocol_version: string
  is_ready: boolean
  blocking_issues: BlockingIssue[]
  enrollment: EnrollmentData
  compliance: ComplianceData
  safety: SafetyData
  data_completeness: DataCompletenessData
  narrative: string
  sources: Source[]
}

// Helper to calculate overall readiness score
function calculateReadinessScore(data: ReadinessResponse): number {
  let score = 0
  let total = 0

  // Enrollment contribution (40% weight)
  total += 40
  if (data.enrollment.is_ready) {
    score += 40
  } else {
    score += Math.min(40, (data.enrollment.percent_complete / 100) * 40)
  }

  // Compliance contribution (20% weight)
  // Note: deviation_rate is now returned as decimal (0.0-1.0) for API consistency
  total += 20
  if (data.compliance.is_ready) {
    score += 20
  } else {
    score += data.compliance.deviation_rate < 0.05 ? 15 : data.compliance.deviation_rate < 0.10 ? 10 : 5
  }

  // Safety contribution (20% weight)
  total += 20
  if (data.safety.is_ready) {
    score += 20
  } else {
    score += data.safety.n_signals === 0 ? 15 : data.safety.n_signals < 3 ? 10 : 5
  }

  // Data completeness contribution (20% weight)
  total += 20
  if (data.data_completeness.is_ready) {
    score += 20
  } else {
    score += Math.min(20, (data.data_completeness.completion_rate / 100) * 20)
  }

  return Math.round((score / total) * 100)
}

// Helper to build category rows from API data
function buildCategories(data: ReadinessResponse) {
  return [
    {
      name: 'Enrollment Progress',
      status: data.enrollment.is_ready ? 'pass' : data.enrollment.percent_complete >= 70 ? 'watch' : 'gap',
      detail: `${data.enrollment.enrolled}/${data.enrollment.target} enrolled (${data.enrollment.percent_complete.toFixed(0)}%)`,
      source: 'Study Database',
      icon: Users,
    },
    {
      name: 'Protocol Compliance',
      status: data.compliance.is_ready ? 'pass' : data.compliance.deviation_rate < 0.05 ? 'watch' : 'gap',
      detail: `Deviation rate: ${(data.compliance.deviation_rate * 100).toFixed(1)}% - ${data.compliance.status}`,
      source: 'Deviation Tracker',
      icon: Shield,
    },
    {
      name: 'Safety Status',
      status: data.safety.is_ready ? 'pass' : data.safety.n_signals === 0 ? 'pass' : 'watch',
      detail: `${data.safety.n_signals} active signal(s) - ${data.safety.overall_status}`,
      source: 'Safety Database',
      icon: Activity,
    },
    {
      name: 'Data Completeness',
      status: data.data_completeness.is_ready ? 'pass' : data.data_completeness.completion_rate >= 80 ? 'watch' : 'blocker',
      detail: `${data.data_completeness.evaluable} evaluable, ${data.data_completeness.completion_rate.toFixed(0)}% complete`,
      source: 'Study Database',
      icon: Database,
    },
  ]
}

// Helper to build blockers from API data with full provenance
function buildBlockers(data: ReadinessResponse) {
  return data.blocking_issues.map(issue => ({
    title: issue.category.charAt(0).toUpperCase() + issue.category.slice(1).replace('_', ' '),
    description: issue.issue,
    action: getActionForCategory(issue.category),
    provenance: issue.provenance,
  }))
}

function getActionForCategory(category: string): string {
  switch (category) {
    case 'enrollment':
      return 'Continue enrollment activities and site engagement'
    case 'data_completeness':
      return 'Issue data queries and follow up on missing data'
    case 'compliance':
      return 'Review deviations and implement corrective actions'
    case 'safety':
      return 'Review safety signals with medical monitor'
    default:
      return 'Review and address identified issues'
  }
}

export default function Readiness() {
  const [, params] = useRoute('/study/:studyId/readiness')
  const studyId = params?.studyId || 'h34-delta'
  const [expandedProvenance, setExpandedProvenance] = useState<number[]>([])

  const toggleProvenance = (index: number) => {
    setExpandedProvenance(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  const { data, isLoading, error } = useQuery<ReadinessResponse>({
    queryKey: ['readiness', studyId],
    queryFn: () => fetchReadiness(studyId),
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
          <p className="text-gray-600">Failed to load readiness data</p>
        </div>
      </div>
    )
  }

  // Transform API data for display
  const score = calculateReadinessScore(data)
  const categories = buildCategories(data)
  const blockers = buildBlockers(data)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass': return <CheckCircle className="w-5 h-5 text-gray-600" />
      case 'watch': return <AlertTriangle className="w-5 h-5 text-gray-500" />
      case 'gap': return <AlertTriangle className="w-5 h-5 text-gray-500" />
      case 'blocker': return <XCircle className="w-5 h-5 text-gray-700" />
      default: return null
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pass': return <Badge variant="success">Pass</Badge>
      case 'watch': return <Badge variant="warning">Watch</Badge>
      case 'gap': return <Badge variant="danger">Gap</Badge>
      case 'blocker': return <Badge variant="danger">Blocker</Badge>
      default: return <Badge variant="neutral">{status}</Badge>
    }
  }

  // Build timeline from enrollment data
  const timeline = {
    current: new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    projected: data.enrollment.percent_complete >= 100 ? 'Ready' : 'TBD',
    milestones: [
      {
        label: 'Interim Target',
        value: `${data.enrollment.interim_target}`,
        completed: data.enrollment.enrolled >= data.enrollment.interim_target
      },
      {
        label: 'Current Enrollment',
        value: `${data.enrollment.enrolled}`,
        completed: true
      },
      {
        label: 'Target Enrollment',
        value: `${data.enrollment.target}`,
        completed: data.enrollment.enrolled >= data.enrollment.target
      },
    ],
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Regulatory Readiness</h1>
        <p className="text-gray-500 mt-1">Submission readiness assessment for {data.protocol_id} v{data.protocol_version}</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-1 flex flex-col items-center justify-center py-8">
          <div className="relative w-40 h-40">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="80" cy="80" r="70" stroke="#e5e7eb" strokeWidth="12" fill="none" />
              <circle
                cx="80" cy="80" r="70"
                stroke={score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444'}
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(score / 100) * 440} 440`}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-semibold text-gray-900">{score}%</span>
              <span className="text-sm text-gray-500">Readiness</span>
            </div>
          </div>
          <Badge
            variant={data.is_ready ? 'success' : 'warning'}
            className="mt-4"
          >
            {data.is_ready ? 'Ready for Submission' : 'Not Ready'}
          </Badge>
        </Card>

        <Card className="col-span-2">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">AI Assessment</h3>
              <p className="text-gray-600 leading-relaxed">{data.narrative}</p>
              <p className="text-xs text-gray-400 mt-3">
                Assessment Date: {new Date(data.assessment_date).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Category Status" subtitle="Requirement-by-requirement assessment" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Category</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Detail</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Source</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(cat.status)}
                    <span className="font-medium text-gray-800">{cat.name}</span>
                  </div>
                </td>
                <td className="py-4 px-4 text-center">{getStatusBadge(cat.status)}</td>
                <td className="py-4 px-4 text-sm text-gray-600">{cat.detail}</td>
                <td className="py-4 px-4 text-xs text-gray-400">{cat.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {blockers.length > 0 && (
        <Card className="border-l-4 border-gray-600">
          <CardHeader title="Critical Blockers" subtitle="Full transparency with calculation provenance" action={<Badge variant="danger">{blockers.length}</Badge>} />
          <div className="space-y-4 mt-4">
            {blockers.map((blocker, i) => (
              <div key={i} className="p-4 bg-gray-100 rounded-xl">
                <div className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{blocker.title}</p>
                    <p className="text-sm text-gray-600 mt-1">{blocker.description}</p>

                    {/* Provenance Details - Collapsible */}
                    {blocker.provenance && (
                      <div className="mt-3">
                        <button
                          onClick={() => toggleProvenance(i)}
                          className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors"
                        >
                          {expandedProvenance.includes(i) ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                          <span className="uppercase tracking-wide">View Calculation Provenance</span>
                        </button>

                        {expandedProvenance.includes(i) && (
                      <div className="mt-2 p-3 bg-white rounded-lg border border-gray-200">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Calculation Provenance</p>

                        {/* Calculation formula */}
                        {blocker.provenance.calculation && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Formula:</span>
                            <p className="text-sm font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded mt-0.5">
                              {blocker.provenance.calculation}
                            </p>
                          </div>
                        )}

                        {/* Data values used */}
                        {blocker.provenance.values && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Data Values:</span>
                            <div className="grid grid-cols-2 gap-1 mt-1">
                              {Object.entries(blocker.provenance.values).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="text-gray-500">{key.replace(/_/g, ' ')}:</span>
                                  <span className="ml-1 font-medium text-gray-700">{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Threshold */}
                        {blocker.provenance.threshold && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Threshold:</span>
                            <p className="text-xs text-gray-600 mt-0.5">{blocker.provenance.threshold}</p>
                          </div>
                        )}

                        {/* Safety signals detected - CRITICAL */}
                        {blocker.provenance.signals_detected && blocker.provenance.signals_detected.length > 0 && (
                          <div className="mb-3">
                            <span className="text-xs text-gray-400">Signals Exceeding Thresholds:</span>
                            <div className="mt-1 space-y-2">
                              {blocker.provenance.signals_detected.map((signal, idx) => (
                                <div key={idx} className="p-2 bg-gray-50 border border-gray-200 rounded">
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold text-gray-700">{signal.metric}</span>
                                    <span className="text-xs font-mono text-gray-700">{signal.exceeded_by} over threshold</span>
                                  </div>
                                  <div className="text-xs text-gray-600 mt-1">
                                    <span className="font-mono">{signal.calculation}</span>
                                  </div>
                                  <div className="flex gap-4 mt-1 text-xs">
                                    <span>Observed: <span className="font-semibold text-gray-700">{signal.observed_rate}</span></span>
                                    <span>Threshold: <span className="font-semibold text-gray-600">{signal.threshold}</span></span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Thresholds for safety */}
                        {blocker.provenance.thresholds && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Protocol Safety Thresholds:</span>
                            <div className="grid grid-cols-2 gap-1 mt-1">
                              {Object.entries(blocker.provenance.thresholds).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="text-gray-500">{key.replace(/_/g, ' ')}:</span>
                                  <span className="ml-1 font-medium text-gray-700">{safeRenderValue(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Classification rules */}
                        {blocker.provenance.classification_rules && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Classification Rules:</span>
                            <div className="mt-1 space-y-0.5">
                              {Object.entries(blocker.provenance.classification_rules).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="font-medium text-gray-600 capitalize">{key}:</span>
                                  <span className="ml-1 text-gray-500">{safeRenderValue(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Definitions */}
                        {blocker.provenance.definitions && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-400">Definitions:</span>
                            <div className="mt-1 space-y-0.5">
                              {Object.entries(blocker.provenance.definitions).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="font-medium text-gray-600 capitalize">{key}:</span>
                                  <span className="ml-1 text-gray-500">{safeRenderValue(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Source and regulatory reference */}
                        <div className="flex flex-wrap gap-4 mt-2 pt-2 border-t border-gray-100">
                          {blocker.provenance.source && (
                            <div className="text-xs">
                              <span className="text-gray-400">Source:</span>
                              <span className="ml-1 text-gray-600">{blocker.provenance.source}</span>
                            </div>
                          )}
                          {blocker.provenance.regulatory_reference && (
                            <div className="text-xs">
                              <span className="text-gray-400">Regulatory:</span>
                              <span className="ml-1 text-purple-600">{blocker.provenance.regulatory_reference}</span>
                            </div>
                          )}
                        </div>
                      </div>
                        )}
                      </div>
                    )}

                    <p className="text-sm text-gray-700 font-medium mt-3">Action: {blocker.action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Enrollment Progress" subtitle={`${data.enrollment.enrolled} of ${data.enrollment.target} patients enrolled`} />
        <div className="mt-6">
          {/* Progress bar */}
          <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="absolute h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(100, data.enrollment.percent_complete)}%` }}
            />
            {/* Interim target marker */}
            <div
              className="absolute top-0 h-full w-0.5 bg-gray-500"
              style={{ left: `${(data.enrollment.interim_target / data.enrollment.target) * 100}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>0</span>
            <span className="text-gray-600">Interim: {data.enrollment.interim_target}</span>
            <span>Target: {data.enrollment.target}</span>
          </div>

          {/* Milestones */}
          <div className="mt-6 flex items-center justify-between">
            {timeline.milestones.map((milestone, i) => (
              <div key={i} className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${milestone.completed ? 'bg-gray-100' : 'bg-gray-100'}`}>
                  {milestone.completed ? (
                    <CheckCircle className="w-5 h-5 text-gray-600" />
                  ) : (
                    <span className="text-sm font-medium text-gray-400">{milestone.value}</span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-800 mt-2">{milestone.label}</p>
                <p className="text-xs text-gray-500">n={milestone.value}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Data Sources with Provenance */}
      <Card>
        <CardHeader title="Data Sources & Provenance" subtitle={`${data.sources.length} sources with full traceability`} />
        <div className="mt-4 space-y-3">
          {data.sources.map((source, i) => (
            <div key={i} className="p-4 bg-gray-50 rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant="neutral" className="text-xs capitalize">{source.type.replace('_', ' ')}</Badge>
                  <span className="font-medium text-gray-800">{source.reference}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${source.confidence >= 0.95 ? 'bg-gray-400' : source.confidence >= 0.8 ? 'bg-gray-500' : 'bg-gray-600'}`} />
                  <span className="text-xs text-gray-500">
                    {(source.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              </div>
              {source.details && (
                <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-2 text-xs">
                  {source.details.regulatory_reference && (
                    <div>
                      <span className="text-gray-400">Regulatory:</span>
                      <span className="ml-1 text-gray-600">{source.details.regulatory_reference}</span>
                    </div>
                  )}
                  {source.details.data_source && (
                    <div>
                      <span className="text-gray-400">Data Source:</span>
                      <span className="ml-1 text-gray-600">{source.details.data_source}</span>
                    </div>
                  )}
                  {source.details.calculation && (
                    <div className="col-span-2">
                      <span className="text-gray-400">Calculation:</span>
                      <span className="ml-1 text-gray-600">{source.details.calculation}</span>
                    </div>
                  )}
                  {source.details.metrics_evaluated && (
                    <div className="col-span-2">
                      <span className="text-gray-400">Metrics:</span>
                      <span className="ml-1 text-gray-600">{source.details.metrics_evaluated.join(', ')}</span>
                    </div>
                  )}
                  {source.details.data_fields && (
                    <div className="col-span-2">
                      <span className="text-gray-400">Data Fields:</span>
                      <span className="ml-1 text-gray-600">{source.details.data_fields.join(', ')}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
