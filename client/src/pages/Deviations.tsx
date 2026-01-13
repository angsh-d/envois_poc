import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchDeviations } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, FileWarning, CheckCircle, XCircle, AlertTriangle, Clock, UserX, ClipboardList, FileText, Shield } from 'lucide-react'

// Type definitions for real API response
interface DeviationRecord {
  patient_id: string
  deviation_type: string
  severity: string
  classification: string
  description: string
  visit?: string
  visit_id?: string
  expected_day?: number
  actual_day?: number
  deviation_days?: number
  window?: string
  missing_assessment?: string
  violated_criterion?: string
  criterion_type?: string
  actual_value?: unknown
  required_value?: string
  ae_id?: string
  onset_date?: string
  report_date?: string
  days_delayed?: number
  is_sae?: boolean
  consent_date?: string
  surgery_date?: string
  action: string
  requires_explanation: boolean
  affects_evaluability: boolean
}

// Deviation type configuration
const DEVIATION_TYPES = {
  visit_timing: { label: 'Visit Timing', icon: Clock, color: 'text-gray-600', bgColor: 'bg-gray-100' },
  missing_assessment: { label: 'Missing Assessment', icon: ClipboardList, color: 'text-gray-600', bgColor: 'bg-gray-100' },
  ie_violation: { label: 'IE Violation', icon: UserX, color: 'text-gray-700', bgColor: 'bg-gray-100' },
  ae_reporting: { label: 'AE Reporting', icon: FileText, color: 'text-gray-600', bgColor: 'bg-gray-100' },
  consent_timing: { label: 'Consent Timing', icon: Shield, color: 'text-gray-600', bgColor: 'bg-gray-100' },
}

interface DeviationsResponse {
  success: boolean
  assessment_date: string
  total_visits: number
  total_deviations: number
  deviation_rate: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  by_visit: Record<string, number>
  deviations: DeviationRecord[]
  detector_results: Array<{ detector_name: string; deviation_type: string; n_deviations: number; patients_checked?: number; visits_checked?: number }>
  protocol_version: string
  sources: Array<{ type: string; reference: string; confidence: number; details?: Record<string, unknown> }>
  execution_time_ms: number
}

export default function Deviations() {
  const [, params] = useRoute('/study/:studyId/deviations')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading, error } = useQuery<DeviationsResponse>({
    queryKey: ['deviations', studyId],
    queryFn: () => fetchDeviations(studyId),
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
          <XCircle className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-600">Failed to load deviations data</p>
        </div>
      </div>
    )
  }

  // Calculate derived values
  const compliantVisits = data.total_visits - data.total_deviations
  // Backend returns decimal (e.g., 0.104), convert to percentage display
  const deviationRatePercent = data.deviation_rate * 100
  const deviationRate = deviationRatePercent > 0 ? `${deviationRatePercent.toFixed(1)}%` : '0%'

  // Get severity breakdown
  const minorCount = data.by_severity['minor'] || 0
  const majorCount = data.by_severity['major'] || 0
  const criticalCount = data.by_severity['critical'] || 0

  // Get visit breakdown for display
  const visitBreakdown = Object.entries(data.by_visit).map(([visit, count]) => ({
    visit,
    count,
  }))

  // Determine primary deviation type for dynamic descriptions
  const primaryDeviationType = Object.entries(data.by_type || {})
    .sort(([, a], [, b]) => b - a)[0]?.[0] || 'visit_timing'

  // Dynamic severity descriptions based on actual deviation types
  const getSeverityDescription = (severity: 'minor' | 'major' | 'critical') => {
    if (primaryDeviationType === 'ae_reporting') {
      switch (severity) {
        case 'minor': return 'SAE reported 2-3 days late'
        case 'major': return 'SAE reported 4-8 days late'
        case 'critical': return 'SAE reported >8 days late'
      }
    } else if (primaryDeviationType === 'missing_assessment') {
      switch (severity) {
        case 'minor': return 'Missing non-primary assessment'
        case 'major': return 'Missing required assessment'
        case 'critical': return 'Missing primary endpoint data'
      }
    }
    // Default visit timing descriptions
    switch (severity) {
      case 'minor': return 'Within 1.5x window extension'
      case 'major': return 'Beyond window or missing assessment'
      case 'critical': return 'Affects endpoint evaluability'
    }
  }

  // Generate AI summary based on real data
  const generateSummary = () => {
    if (data.total_deviations === 0) {
      return `No protocol deviations detected across ${data.total_visits} visit-assessments. All visits are within protocol-defined windows. Protocol compliance rate: 100%.`
    }
    const parts = []
    parts.push(`${data.total_deviations} protocol deviation(s) detected across ${data.total_visits} visit-assessments (${deviationRate} rate).`)
    if (minorCount > 0) parts.push(`${minorCount} minor`)
    if (majorCount > 0) parts.push(`${majorCount} major`)
    if (criticalCount > 0) parts.push(`${criticalCount} critical`)
    return parts.join(', ') + ' deviation(s).'
  }

  const getStatusIcon = () => {
    if (data.total_deviations === 0) {
      return <CheckCircle className="w-5 h-5 text-gray-600" />
    } else if (criticalCount > 0) {
      return <XCircle className="w-5 h-5 text-gray-500" />
    } else {
      return <AlertTriangle className="w-5 h-5 text-gray-500" />
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Protocol Deviations</h1>
        <p className="text-gray-500 mt-1">Automated deviation detection using Document-as-Code rules (v{data.protocol_version})</p>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Summary</h3>
            <p className="text-gray-600 leading-relaxed">{generateSummary()}</p>
            <p className="text-xs text-gray-400 mt-2">
              Assessment Date: {new Date(data.assessment_date).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-4 gap-4">
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Visits</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{data.total_visits}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Compliant</p>
          <p className="text-3xl font-semibold text-gray-700 mt-2">{compliantVisits}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Deviations</p>
          <p className="text-3xl font-semibold text-gray-700 mt-2">{data.total_deviations}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Rate</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{deviationRate}</p>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span className="font-medium text-gray-800">Minor</span>
            <span className="ml-auto text-2xl font-semibold text-gray-600">{minorCount}</span>
          </div>
          <p className="text-sm text-gray-500">{getSeverityDescription('minor')}</p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-gray-500" />
            <span className="font-medium text-gray-800">Major</span>
            <span className="ml-auto text-2xl font-semibold text-gray-600">{majorCount}</span>
          </div>
          <p className="text-sm text-gray-500">{getSeverityDescription('major')}</p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-gray-700" />
            <span className="font-medium text-gray-800">Critical</span>
            <span className="ml-auto text-2xl font-semibold text-gray-700">{criticalCount}</span>
          </div>
          <p className="text-sm text-gray-500">{getSeverityDescription('critical')}</p>
        </Card>
      </div>

      {/* Deviations by Type */}
      {data.by_type && Object.keys(data.by_type).length > 0 && (
        <Card>
          <CardHeader
            title="Deviations by Type"
            subtitle="Breakdown by deviation category"
            action={<Badge variant="neutral">{Object.keys(data.by_type).length} types detected</Badge>}
          />
          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(data.by_type).map(([type, count]) => {
              const config = DEVIATION_TYPES[type as keyof typeof DEVIATION_TYPES] || {
                label: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                icon: FileWarning,
                color: 'text-gray-600',
                bgColor: 'bg-gray-100'
              }
              const Icon = config.icon
              return (
                <div key={type} className={`flex items-center gap-3 p-3 rounded-lg ${config.bgColor}`}>
                  <Icon className={`w-5 h-5 ${config.color}`} />
                  <div>
                    <p className="text-xs text-gray-500">{config.label}</p>
                    <p className={`text-lg font-semibold ${config.color}`}>{count}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Status Summary Card */}
      <Card>
        <div className="flex items-center gap-4">
          {getStatusIcon()}
          <div>
            <h3 className="font-semibold text-gray-800">
              {data.total_deviations === 0 ? 'Excellent Compliance' :
               criticalCount > 0 ? 'Critical Issues Detected' : 'Review Required'}
            </h3>
            <p className="text-sm text-gray-500">
              {data.total_deviations === 0
                ? 'All visits are within protocol-defined windows'
                : `${data.total_deviations} deviation(s) require attention`}
            </p>
          </div>
          <Badge
            variant={data.total_deviations === 0 ? 'success' : criticalCount > 0 ? 'danger' : 'warning'}
            className="ml-auto"
          >
            {data.total_deviations === 0 ? '100% Compliant' : `${(100 - deviationRatePercent).toFixed(1)}% Compliant`}
          </Badge>
        </div>
      </Card>

      {/* Visit Breakdown */}
      {visitBreakdown.length > 0 && (
        <Card>
          <CardHeader
            title="Deviations by Visit Type"
            action={<Badge variant="neutral">{visitBreakdown.length} visit types</Badge>}
          />
          <div className="mt-4 space-y-3">
            {visitBreakdown.map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileWarning className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-800">{item.visit}</span>
                </div>
                <Badge variant="warning">{item.count} deviation(s)</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Individual Deviations Table */}
      {data.deviations && data.deviations.length > 0 && (
        <Card>
          <CardHeader
            title="Deviation Details"
            subtitle="Individual deviation records with analysis"
            action={<Badge variant="neutral">{data.deviations.length} records</Badge>}
          />
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Patient</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Type</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-600">Severity</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Action</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-600">Flags</th>
                </tr>
              </thead>
              <tbody>
                {data.deviations.map((dev, i) => {
                  const typeConfig = DEVIATION_TYPES[dev.deviation_type as keyof typeof DEVIATION_TYPES] || {
                    label: dev.deviation_type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Unknown',
                    icon: FileWarning,
                    color: 'text-gray-600',
                    bgColor: 'bg-gray-100'
                  }
                  const TypeIcon = typeConfig.icon
                  return (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono text-gray-800">{dev.patient_id}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <TypeIcon className={`w-4 h-4 ${typeConfig.color}`} />
                          <span className="text-gray-700 text-xs">{typeConfig.label}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-gray-600 max-w-xs">
                        <p className="truncate" title={dev.description}>{dev.description}</p>
                        {dev.visit && (
                          <p className="text-xs text-gray-400 mt-0.5">Visit: {dev.visit}</p>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge
                          variant={
                            dev.severity?.toLowerCase() === 'critical' ? 'danger' :
                            dev.severity?.toLowerCase() === 'major' ? 'warning' : 'neutral'
                          }
                        >
                          {dev.severity || dev.classification}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-gray-500 text-xs max-w-xs">
                        <p className="truncate" title={dev.action}>{dev.action}</p>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {dev.requires_explanation && (
                            <span className="w-2 h-2 rounded-full bg-gray-500" title="Requires explanation" />
                          )}
                          {dev.affects_evaluability && (
                            <span className="w-2 h-2 rounded-full bg-gray-700" title="Affects evaluability" />
                          )}
                          {!dev.requires_explanation && !dev.affects_evaluability && (
                            <span className="text-xs text-gray-400">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 px-4">
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              <span>Requires PI Explanation</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-700" />
              <span>Affects Evaluability</span>
            </div>
          </div>
        </Card>
      )}

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
