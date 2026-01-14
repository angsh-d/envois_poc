import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { 
  fetchSafetySignals, 
  SafetyResponse, 
  SafetyMetric
} from '@/lib/api'
import { useRoute } from 'wouter'
import { 
  AlertTriangle, CheckCircle, XCircle, 
  Activity, ChevronRight, Users, BookOpen, 
  Database, Clock, ChevronDown
} from 'lucide-react'

function formatMetricName(metric: string): string {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

export default function Safety() {
  const [, params] = useRoute('/study/:studyId/safety')
  const studyId = params?.studyId || 'h34-delta'
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null)
  const [expandedProvenance, setExpandedProvenance] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery<SafetyResponse>({
    queryKey: ['safety-signals'],
    queryFn: fetchSafetySignals,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 60,
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

  const getOverallStatus = () => {
    if (data.requires_dsmb_review) return 'concern'
    if (data.high_priority.length > 0) return 'monitor'
    if (data.n_signals > 0) return 'monitor'
    return 'acceptable'
  }

  const overallStatus = getOverallStatus()

  const getStatusColor = () => {
    switch (overallStatus) {
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
        <p className="text-gray-500 mt-1">Cross-source contextualization of adverse events with full data provenance</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Signals Detected</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{data.n_signals}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">High Priority</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{data.high_priority.length}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">DSMB Review</p>
          <div className="mt-2">
            <Badge variant={data.requires_dsmb_review ? 'danger' : 'success'}>
              {data.requires_dsmb_review ? 'Required' : 'Not Required'}
            </Badge>
          </div>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Status</p>
          <div className="mt-2">
            <Badge variant={getStatusColor() as 'success' | 'warning' | 'danger' | 'neutral'} className="text-lg px-3 py-1">
              {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
            </Badge>
          </div>
        </Card>
      </div>

      {/* Safety Metrics Table with Provenance */}
      <Card>
        <CardHeader 
          title="Safety Metrics" 
          subtitle="Adverse event rates vs protocol thresholds with full data provenance" 
        />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Events</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Rate</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Threshold</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Details</th>
            </tr>
          </thead>
          <tbody>
            {data.signals.map((metric, i) => {
              const isExpanded = expandedMetric === metric.metric
              const provenance = metric.provenance
              const affectedPatients = metric.affected_patients || []
              const citations = metric.literature_citations || []
              
              return (
                <React.Fragment key={i}>
                  <tr 
                    className={`border-b border-gray-50 last:border-0 transition-colors hover:bg-gray-50 ${isExpanded ? 'bg-gray-50' : ''}`}
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <Activity className={`w-4 h-4 ${metric.signal ? 'text-gray-700' : 'text-gray-400'}`} />
                        <span className="font-medium text-gray-800">{formatMetricName(metric.metric)}</span>
                        {metric.signal_level && (
                          <Badge variant={metric.signal_level === 'high' ? 'danger' : 'warning'} className="text-xs">
                            {metric.signal_level}
                          </Badge>
                        )}
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
                    <td className="py-4 px-4 text-center">
                      <button
                        onClick={() => setExpandedMetric(isExpanded ? null : metric.metric)}
                        className={`inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          isExpanded 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        <ChevronDown className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                        {isExpanded ? 'Hide' : 'Show'}
                      </button>
                    </td>
                  </tr>
                  
                  {/* Expanded Detail Row */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={6} className="bg-gray-50 px-4 pb-4">
                        <div className="grid grid-cols-3 gap-4 pt-2">
                          {/* Provenance Panel */}
                          <div className="bg-white rounded-xl border border-blue-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Database className="w-4 h-4 text-blue-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Data Provenance</h4>
                                <p className="text-xs text-blue-600">Source transparency</p>
                              </div>
                            </div>
                            {provenance ? (
                              <div className="space-y-2 text-xs">
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="text-blue-800 font-medium">Event Count</p>
                                  <p className="text-blue-600 font-mono text-xs">{provenance.data_sources?.event_count}</p>
                                </div>
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="text-blue-800 font-medium">Patient Count</p>
                                  <p className="text-blue-600 font-mono text-xs">{provenance.data_sources?.patient_count}</p>
                                </div>
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="text-blue-800 font-medium">Threshold Source</p>
                                  <p className="text-blue-600 font-mono text-xs">{provenance.data_sources?.threshold}</p>
                                </div>
                                <div className="p-2 bg-gray-50 rounded-lg mt-2">
                                  <p className="text-gray-700 font-medium">Methodology</p>
                                  <p className="text-gray-600">{provenance.methodology}</p>
                                </div>
                                <div className="p-2 bg-gray-50 rounded-lg">
                                  <p className="text-gray-700 font-medium">Calculation</p>
                                  <p className="text-gray-600 font-mono">{provenance.calculation}</p>
                                </div>
                              </div>
                            ) : (
                              <p className="text-xs text-gray-400">No provenance data available</p>
                            )}
                          </div>

                          {/* Affected Patients */}
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <Users className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Affected Patients</h4>
                                <p className="text-xs text-gray-500">{affectedPatients.length} patients</p>
                              </div>
                            </div>
                            {affectedPatients.length > 0 ? (
                              <div className="space-y-2 max-h-48 overflow-y-auto">
                                {affectedPatients.slice(0, 5).map((patient, idx) => (
                                  <div key={idx} className="p-2 bg-gray-50 rounded-lg text-xs">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="font-medium text-gray-800">{patient.patient_id}</span>
                                      <span className="text-gray-500">{patient.ae_date}</span>
                                    </div>
                                    <p className="text-gray-600">{patient.ae_title}</p>
                                    {patient.demographics && (
                                      <div className="flex gap-2 mt-1 text-gray-400">
                                        <span>{patient.demographics.gender}</span>
                                        {patient.demographics.age && <span>Age {patient.demographics.age}</span>}
                                        {patient.demographics.bmi && <span>BMI {patient.demographics.bmi}</span>}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-xs text-gray-400">No affected patients data</p>
                            )}
                          </div>

                          {/* Literature Citations */}
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <BookOpen className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Literature Context</h4>
                                <p className="text-xs text-gray-500">{citations.length} publications</p>
                              </div>
                            </div>
                            {citations.length > 0 ? (
                              <div className="space-y-2 max-h-48 overflow-y-auto">
                                {citations.map((citation, idx) => (
                                  <div key={idx} className="p-2 bg-gray-50 rounded-lg text-xs">
                                    <p className="font-medium text-gray-800">{citation.title}</p>
                                    <p className="text-gray-500">{citation.journal} ({citation.year})</p>
                                    <p className="text-gray-600 mt-1">
                                      n={citation.n_patients}, Rate: {(citation.reported_rate * 100).toFixed(1)}%
                                    </p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-xs text-gray-400">No literature citations available</p>
                            )}
                          </div>
                        </div>

                        {/* Recommended Action */}
                        {metric.recommended_action && (
                          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                            <div className="flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4 text-amber-600" />
                              <span className="font-medium text-amber-800 text-sm">Recommended Action</span>
                            </div>
                            <p className="text-amber-700 text-sm mt-1">{metric.recommended_action}</p>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </Card>

      {/* Summary Section */}
      <Card>
        <div className="flex items-start gap-4">
          {data.n_signals === 0 ? (
            <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0" />
          )}
          <div>
            <h3 className="font-semibold text-gray-800">
              {data.n_signals === 0 ? 'No Active Safety Signals' : 'Safety Signals Detected'}
            </h3>
            <p className="text-gray-600 text-sm mt-1">
              {data.n_signals === 0
                ? 'All monitored safety metrics are within acceptable thresholds.'
                : `${data.n_signals} safety signal(s) detected that require monitoring and potential intervention.`}
            </p>
          </div>
        </div>
      </Card>

      {/* Data Sources */}
      <Card>
        <CardHeader title="Data Sources" subtitle={`${data.sources.length} sources used for this assessment`} />
        <div className="grid grid-cols-2 gap-3 mt-4">
          {data.sources.map((source, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Database className="w-4 h-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-700">{source.type}</p>
                <p className="text-xs text-gray-500">{source.reference}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
          <Clock className="w-3 h-3" />
          Analysis completed in {data.execution_time_ms.toFixed(0)}ms | Detection: {new Date(data.detection_date).toLocaleString()}
        </div>
      </Card>
    </div>
  )
}
