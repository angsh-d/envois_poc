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
  Database, Clock, ChevronDown, TrendingUp,
  User, FileText, Beaker, HelpCircle
} from 'lucide-react'

function formatMetricName(metric: string): string {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

function RateBar({ rate, threshold, isSignal }: { rate: number; threshold: number; isSignal: boolean }) {
  const maxValue = Math.max(rate, threshold) * 1.2
  const ratePercent = (rate / maxValue) * 100
  const thresholdPercent = (threshold / maxValue) * 100

  return (
    <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden w-24">
      <div
        className={`absolute h-full rounded-full transition-all duration-500 ${
          isSignal ? 'bg-gray-700' : 'bg-gray-400'
        }`}
        style={{ width: `${ratePercent}%` }}
      />
      <div
        className="absolute h-full w-0.5 bg-gray-500"
        style={{ left: `${thresholdPercent}%` }}
      />
    </div>
  )
}

export default function Safety() {
  const [, params] = useRoute('/study/:studyId/safety')
  const studyId = params?.studyId || 'h34-delta'
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null)
  const [expandedProvenance, setExpandedProvenance] = useState<string | null>(null)
  const [showMonitoredMetrics, setShowMonitoredMetrics] = useState(false)

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
      <Card className="overflow-hidden">
        <CardHeader 
          title="Safety Metrics" 
          subtitle="Adverse event rates vs protocol thresholds with full data provenance" 
        />
        <div className="overflow-x-auto">
          <table className="w-full mt-4">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Metric</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Events</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rate vs Threshold</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.signals.map((metric, i) => {
                const isExpanded = expandedMetric === metric.metric
                const provenance = metric.provenance
                const affectedPatients = metric.affected_patients || []
                const citations = metric.literature_citations || []
                
                return (
                  <React.Fragment key={i}>
                    <tr
                      className={`transition-all duration-200 cursor-pointer ${
                        isExpanded
                          ? 'bg-gray-100/50'
                          : metric.signal
                            ? 'hover:bg-gray-100/30'
                            : 'hover:bg-gray-50'
                      }`}
                      onClick={() => setExpandedMetric(isExpanded ? null : metric.metric)}
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            metric.signal
                              ? metric.signal_level === 'high'
                                ? 'bg-gray-800 animate-pulse'
                                : 'bg-gray-500'
                              : 'bg-gray-400'
                          }`} />
                          <div>
                            <span className="font-medium text-gray-900">{formatMetricName(metric.metric)}</span>
                            {metric.signal_level && (
                              <span className={`ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${
                                metric.signal_level === 'high'
                                  ? 'bg-gray-800 text-white'
                                  : 'bg-gray-200 text-gray-700'
                              }`}>
                                {metric.signal_level.toUpperCase()}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <div className="flex flex-col items-center">
                          <span className="text-lg font-semibold text-gray-900">{metric.count}</span>
                          <span className="text-xs text-gray-500">events in {metric.total} patients</span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex flex-col items-center gap-1">
                          <div className="flex items-center gap-3">
                            <div className="flex flex-col items-center">
                              <span className={`text-lg font-bold ${metric.signal ? 'text-gray-800' : 'text-gray-600'}`}>
                                {(metric.rate * 100).toFixed(1)}%
                              </span>
                              {metric.ci_lower !== undefined && metric.ci_upper !== undefined && (
                                <span className="text-xs text-gray-400">
                                  95% CI: {(metric.ci_lower * 100).toFixed(1)}-{(metric.ci_upper * 100).toFixed(1)}%
                                </span>
                              )}
                            </div>
                            <span className="text-gray-400">/</span>
                            <div className="flex items-center gap-1">
                              <span className="text-sm text-gray-500">{(metric.threshold * 100).toFixed(0)}%</span>
                              {metric.provenance?.threshold_source && (
                                <span className="group relative cursor-help">
                                  <HelpCircle className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 transition-colors" />
                                  <span className="absolute bottom-full right-0 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-72 pointer-events-none z-50 leading-relaxed shadow-lg text-left">
                                    <span className="font-medium text-gray-900">Source: </span>{metric.provenance.threshold_source}
                                  </span>
                                </span>
                              )}
                            </div>
                          </div>
                          <RateBar rate={metric.rate} threshold={metric.threshold} isSignal={metric.signal} />
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${
                          metric.signal
                            ? 'bg-gray-800 text-white'
                            : 'bg-gray-200 text-gray-700'
                        }`}>
                          {metric.signal ? (
                            <>
                              <AlertTriangle className="w-3 h-3" />
                              Signal Detected
                            </>
                          ) : (
                            <>
                              <CheckCircle className="w-3 h-3" />
                              Within Limits
                            </>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setExpandedMetric(isExpanded ? null : metric.metric)
                          }}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
                            isExpanded
                              ? 'bg-gray-800 text-white shadow-sm'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                          {isExpanded ? 'Hide Details' : 'View Details'}
                        </button>
                      </td>
                    </tr>
                  
                  {/* Expanded Detail Row */}
                  {isExpanded && (
                    <tr className="animate-fade-in">
                      <td colSpan={5} className="bg-gradient-to-b from-gray-100/50 to-gray-50 px-6 py-5">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                          {/* Provenance Panel */}
                          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-4">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <Database className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Data Provenance</h4>
                                <p className="text-xs text-gray-600">Full source transparency</p>
                              </div>
                            </div>
                            {provenance ? (
                              <div className="space-y-3 text-xs">
                                <div>
                                  <p className="text-gray-700 font-semibold mb-1">Methodology</p>
                                  <p className="text-gray-600 leading-relaxed">{provenance.methodology}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-2.5">
                                  <p className="text-gray-700 font-semibold mb-1">Formula</p>
                                  <p className="text-gray-800 font-mono bg-white px-2 py-1 rounded border border-gray-200">{provenance.calculation}</p>
                                </div>
                                {provenance.confidence_interval && (
                                  <div className="bg-gray-100 rounded-lg p-2.5">
                                    <p className="text-gray-700 font-semibold mb-1">Statistical Uncertainty</p>
                                    <p className="text-gray-800 font-mono text-xs">{provenance.confidence_interval}</p>
                                  </div>
                                )}
                                {provenance.signal_classification && (
                                  <div className="bg-gray-100 rounded-lg p-2.5">
                                    <p className="text-gray-700 font-semibold mb-1">Signal Classification</p>
                                    <p className="text-gray-800 text-xs">{provenance.signal_classification}</p>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <p className="text-xs text-gray-400">No provenance data available</p>
                            )}
                          </div>

                          {/* Affected Patients */}
                          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-4">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <Users className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900 text-sm">Affected Patients</h4>
                                <p className="text-xs text-gray-600">
                                  {affectedPatients.length} event{affectedPatients.length !== 1 ? 's' : ''} ({new Set(affectedPatients.map(p => p.patient_id)).size} patient{new Set(affectedPatients.map(p => p.patient_id)).size !== 1 ? 's' : ''})
                                </p>
                              </div>
                            </div>
                            {affectedPatients.length > 0 ? (
                              <div className="space-y-2 max-h-48 overflow-y-auto">
                                {affectedPatients.slice(0, 5).map((patient, idx) => (
                                  <div key={idx} className="p-2.5 bg-gray-50 rounded-lg">
                                    <div className="flex items-center justify-between mb-1.5">
                                      <span className="font-semibold text-gray-900 text-sm">{patient.patient_id}</span>
                                      {patient.event_date && (
                                        <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                                          {new Date(patient.event_date).toLocaleDateString()}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-gray-700 text-xs leading-relaxed">{patient.event_description}</p>
                                    {patient.demographics && (
                                      <div className="flex flex-wrap gap-2 mt-2">
                                        {patient.demographics.gender && (
                                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                                            {patient.demographics.gender}
                                          </span>
                                        )}
                                        {patient.demographics.age && (
                                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                                            Age {patient.demographics.age}
                                          </span>
                                        )}
                                        {patient.demographics.bmi && (
                                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                                            BMI {patient.demographics.bmi.toFixed(1)}
                                          </span>
                                        )}
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
                          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                                <BookOpen className="w-4 h-4 text-gray-600" />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-1">
                                  <h4 className="font-semibold text-gray-900 text-sm">Literature Context</h4>
                                  <span className="group relative cursor-help">
                                    <HelpCircle className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 transition-colors" />
                                    <span className="absolute bottom-full left-0 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-64 pointer-events-none z-50 leading-relaxed shadow-lg">
                                      <span className="font-medium text-gray-900">Comparison Method:</span><br/>
                                      <span className="text-gray-400">● Light</span>: Study rate ≤ literature rate (at or below benchmark)<br/>
                                      <span className="text-gray-700">● Dark</span>: Study rate &gt; literature rate (exceeds benchmark)
                                    </span>
                                  </span>
                                </div>
                                <p className="text-xs text-gray-600">{citations.length} publications</p>
                              </div>
                            </div>
                            {citations.length > 0 ? (
                              <div className="space-y-2.5 max-h-64 overflow-y-auto">
                                {citations.map((citation, idx) => (
                                  <div key={idx} className="p-3 bg-gradient-to-r from-gray-100 to-gray-50 rounded-lg border border-gray-200">
                                    <p className="font-medium text-gray-900 text-sm leading-tight">{citation.title}</p>
                                    <p className="text-gray-600 text-xs mt-1">{citation.journal} ({citation.year})</p>
                                    <div className="flex flex-wrap items-center gap-2 mt-2">
                                      {citation.n_patients && (
                                        <span className="text-xs bg-white px-2 py-0.5 rounded-full border border-gray-200 text-gray-600">
                                          n={citation.n_patients.toLocaleString()}
                                        </span>
                                      )}
                                      {citation.reported_rate != null && citation.reported_rate > 0 ? (
                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                          metric.rate <= citation.reported_rate
                                            ? 'bg-gray-200 text-gray-600'
                                            : 'bg-gray-700 text-white'
                                        }`}>
                                          {(citation.reported_rate * 100).toFixed(1)}% rate
                                        </span>
                                      ) : (
                                        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                                          Rate N/A
                                        </span>
                                      )}
                                    </div>
                                    {/* Source provenance and DOI link */}
                                    <div className="mt-2 pt-2 border-t border-gray-200">
                                      {citation.local_source && (
                                        <>
                                          <p className="text-xs text-gray-500">
                                            <span className="font-medium text-gray-700">Local:</span>{' '}
                                            <span className="font-mono text-gray-600">{citation.local_source}</span>
                                          </p>
                                          {citation.provenance?.page && (
                                            <p className="text-xs text-gray-500 mt-0.5">
                                              <span className="font-medium">Page {citation.provenance.page}</span>
                                              {citation.provenance.table && <span>, {citation.provenance.table}</span>}
                                            </p>
                                          )}
                                        </>
                                      )}
                                      {(citation.doi || citation.provenance?.doi) && (
                                        <p className="text-xs mt-1">
                                          <a
                                            href={`https://doi.org/${citation.doi || citation.provenance?.doi}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                                          >
                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                            </svg>
                                            doi.org/{citation.doi || citation.provenance?.doi}
                                          </a>
                                        </p>
                                      )}
                                    </div>
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
                          <div className="mt-5 p-4 bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-300 rounded-xl">
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                                <AlertTriangle className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <span className="font-semibold text-gray-900 text-sm">Recommended Action</span>
                                <p className="text-gray-700 text-sm mt-1 leading-relaxed">{metric.recommended_action}</p>
                              </div>
                            </div>
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
        </div>
      </Card>

      {/* Other Monitored Metrics (Below Threshold) */}
      {data.monitored_metrics && data.monitored_metrics.length > 0 && (
        <Card className="overflow-hidden">
          <button
            onClick={() => setShowMonitoredMetrics(!showMonitoredMetrics)}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-4 h-4 text-gray-600" />
              </div>
              <div className="text-left">
                <h3 className="font-semibold text-gray-800">Other Monitored Metrics</h3>
                <p className="text-sm text-gray-500">{data.n_monitored} metrics within acceptable thresholds</p>
              </div>
            </div>
            <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${showMonitoredMetrics ? 'rotate-180' : ''}`} />
          </button>

          {showMonitoredMetrics && (
            <div className="border-t border-gray-100">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50/50">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Metric</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Events</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rate vs Threshold</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.monitored_metrics.map((metric, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-gray-400" />
                          <span className="font-medium text-gray-900">{formatMetricName(metric.metric)}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="text-lg font-semibold text-gray-900">{metric.count}</span>
                        <span className="text-xs text-gray-500 ml-1">of {metric.total}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-center gap-3">
                          <div className="text-right">
                            <span className="font-semibold text-gray-900">{(metric.rate * 100).toFixed(1)}%</span>
                            <span className="text-gray-400 mx-1">/</span>
                            <span className="text-gray-500">{(metric.threshold * 100).toFixed(0)}%</span>
                          </div>
                          <RateBar rate={metric.rate} threshold={metric.threshold} isSignal={false} />
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-700">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Within Threshold
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Summary Section */}
      <Card>
        <div className="flex items-start gap-4">
          {data.n_signals === 0 ? (
            <CheckCircle className="w-6 h-6 text-gray-500 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-gray-600 flex-shrink-0" />
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
              <Database className="w-4 h-4 text-gray-500" />
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
