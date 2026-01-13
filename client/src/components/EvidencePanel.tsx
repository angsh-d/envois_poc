import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  BarChart3,
  Globe,
  BookOpen,
  Database,
  Calculator,
  Info,
  TrendingUp,
  X,
  ExternalLink,
  Activity,
  AlertTriangle
} from 'lucide-react'
import { Evidence, EvidenceMetric, EvidenceDataPoint, SourceRawData } from '@/lib/api'

interface EvidencePanelProps {
  evidence: Evidence
}

// Format large numbers
function formatNumber(n?: number): string {
  if (!n) return 'N/A'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return n.toLocaleString()
}

// Format percentage
function formatPercent(n?: number): string {
  if (n === undefined || n === null) return 'N/A'
  return `${(n * 100).toFixed(1)}%`
}

// Get icon for source type
function getSourceIcon(sourceType: string) {
  switch (sourceType) {
    case 'registry':
      return Globe
    case 'literature':
      return BookOpen
    case 'study_data':
      return Database
    default:
      return BarChart3
  }
}

// Get color for source type
function getSourceColor(sourceType: string): { bg: string; text: string; border: string } {
  switch (sourceType) {
    case 'registry':
      return { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' }
    case 'literature':
      return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' }
    case 'study_data':
      return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' }
    default:
      return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' }
  }
}

// Raw Data Modal
function RawDataModal({ point, onClose }: { point: EvidenceDataPoint; onClose: () => void }) {
  const raw = point.raw_data
  if (!raw) return null

  const Icon = getSourceIcon(point.source_type)
  const colors = getSourceColor(point.source_type)

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`px-4 py-3 ${colors.bg} border-b ${colors.border} flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <Icon className={`w-5 h-5 ${colors.text}`} />
            <div>
              <h3 className={`font-semibold ${colors.text}`}>{raw.abbreviation || point.source}</h3>
              <p className="text-[11px] text-gray-600">{raw.full_name}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/50 rounded">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh] space-y-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-3 text-[12px]">
            {raw.report_year && (
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-gray-500">Report Year</div>
                <div className="font-semibold text-gray-900">{raw.report_year}</div>
              </div>
            )}
            {raw.data_years && (
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-gray-500">Data Coverage</div>
                <div className="font-semibold text-gray-900">{raw.data_years}</div>
              </div>
            )}
            {raw.n_procedures && (
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-gray-500">Procedures</div>
                <div className="font-semibold text-gray-900">{raw.n_procedures.toLocaleString()}</div>
              </div>
            )}
            {raw.n_primary && (
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-gray-500">Primary THAs</div>
                <div className="font-semibold text-gray-900">{raw.n_primary.toLocaleString()}</div>
              </div>
            )}
          </div>

          {/* Survival Rates */}
          <div>
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-medium uppercase mb-2">
              <Activity className="w-3.5 h-3.5" />
              Survival Rates
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="grid grid-cols-5 gap-2 text-center">
                {[
                  { label: '1yr', value: raw.survival_1yr },
                  { label: '2yr', value: raw.survival_2yr },
                  { label: '5yr', value: raw.survival_5yr },
                  { label: '10yr', value: raw.survival_10yr },
                  { label: '15yr', value: raw.survival_15yr },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div className="text-[10px] text-green-600 font-medium">{label}</div>
                    <div className={`text-[13px] font-bold ${value ? 'text-green-700' : 'text-gray-400'}`}>
                      {formatPercent(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Revision Rates */}
          <div>
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-medium uppercase mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              Revision Rates
            </div>
            <div className="bg-orange-50 rounded-lg p-3">
              <div className="grid grid-cols-5 gap-2 text-center">
                {[
                  { label: '1yr', value: raw.revision_rate_1yr },
                  { label: '2yr', value: raw.revision_rate_2yr },
                  { label: 'Median', value: raw.revision_rate_median },
                  { label: 'P75', value: raw.revision_rate_p75 },
                  { label: 'P95', value: raw.revision_rate_p95 },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div className="text-[10px] text-orange-600 font-medium">{label}</div>
                    <div className={`text-[13px] font-bold ${value ? 'text-orange-700' : 'text-gray-400'}`}>
                      {formatPercent(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Revision Reasons */}
          {raw.revision_reasons && raw.revision_reasons.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-medium uppercase mb-2">
                <Database className="w-3.5 h-3.5" />
                Top Revision Reasons
              </div>
              <div className="space-y-1.5">
                {raw.revision_reasons.slice(0, 5).map((reason, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="flex-1">
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${reason.percentage * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-[11px] w-10 text-right font-medium text-gray-700">
                      {(reason.percentage * 100).toFixed(0)}%
                    </div>
                    <div className="text-[11px] text-gray-600 w-32 truncate" title={reason.description}>
                      {reason.reason.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between">
          <div className="text-[10px] text-gray-500">
            Click outside or press ESC to close
          </div>
          <div className="flex items-center gap-1 text-[11px] text-indigo-600">
            <ExternalLink className="w-3 h-3" />
            <span>Raw registry data</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Individual data point row (now clickable)
function DataPointRow({
  point,
  isLast,
  onShowRaw
}: {
  point: EvidenceDataPoint
  isLast: boolean
  onShowRaw: () => void
}) {
  const Icon = getSourceIcon(point.source_type)
  const colors = getSourceColor(point.source_type)
  const hasRawData = !!point.raw_data

  return (
    <button
      onClick={hasRawData ? onShowRaw : undefined}
      disabled={!hasRawData}
      className={`w-full flex items-center gap-3 py-2 text-left transition-colors ${
        !isLast ? 'border-b border-gray-100' : ''
      } ${hasRawData ? 'hover:bg-indigo-50 cursor-pointer rounded' : ''}`}
    >
      {/* Tree connector */}
      <div className="flex items-center gap-1 text-gray-300">
        <span className="w-3 border-t border-gray-300"></span>
        <span>{isLast ? '└' : '├'}</span>
      </div>

      {/* Source icon and name */}
      <div className={`flex items-center gap-1.5 min-w-[100px] ${colors.text}`}>
        <Icon className="w-3.5 h-3.5" />
        <span className={`text-[12px] font-medium ${hasRawData ? 'underline decoration-dotted' : ''}`}>
          {point.source}
        </span>
      </div>

      {/* Value */}
      <div className="flex-1">
        <span className="text-[13px] font-semibold text-gray-900">{point.value_formatted}</span>
      </div>

      {/* Sample size */}
      {point.sample_size && (
        <div className="text-[11px] text-gray-500">
          n={formatNumber(point.sample_size)}
        </div>
      )}

      {/* Year */}
      {point.year && (
        <div className="text-[11px] text-gray-400">
          {point.year}
        </div>
      )}

      {/* Click indicator */}
      {hasRawData && (
        <ExternalLink className="w-3 h-3 text-indigo-400" />
      )}
    </button>
  )
}

// Single metric card
function MetricCard({ metric, defaultExpanded = true }: { metric: EvidenceMetric; defaultExpanded?: boolean }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [selectedPoint, setSelectedPoint] = useState<EvidenceDataPoint | null>(null)

  return (
    <>
      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
        {/* Metric header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-2 px-3 py-2.5 bg-gradient-to-r from-gray-50 to-white hover:from-gray-100 transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}

          <TrendingUp className="w-4 h-4 text-indigo-500" />

          <div className="flex-1 text-left">
            <span className="text-[13px] font-semibold text-gray-800">{metric.metric_name}</span>
          </div>

          {/* Aggregated value badge */}
          {metric.aggregated_value && (
            <div className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[12px] font-semibold">
              {metric.aggregated_value}
            </div>
          )}

          {/* Data points count */}
          <div className="text-[11px] text-gray-500">
            {metric.data_points.length} sources
          </div>
        </button>

        {/* Expanded content */}
        {isExpanded && (
          <div className="px-3 pb-3">
            {/* Claim */}
            <div className="py-2 text-[12px] text-gray-600 border-b border-gray-100">
              {metric.claim}
            </div>

            {/* Calculation method */}
            {metric.calculation_method && (
              <div className="flex items-start gap-1.5 py-2 text-[11px] text-gray-500 border-b border-gray-100">
                <Calculator className="w-3.5 h-3.5 mt-0.5 text-gray-400" />
                <span>{metric.calculation_method}</span>
              </div>
            )}

            {/* Data points */}
            <div className="mt-2">
              <div className="text-[10px] text-gray-500 uppercase font-medium mb-1 flex items-center gap-1">
                <Database className="w-3 h-3" />
                Individual Data Points
                <span className="text-indigo-500 ml-1">(click for details)</span>
              </div>
              <div className="pl-2">
                {metric.data_points.map((point, i) => (
                  <DataPointRow
                    key={`${point.source}-${i}`}
                    point={point}
                    isLast={i === metric.data_points.length - 1}
                    onShowRaw={() => setSelectedPoint(point)}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Raw Data Modal */}
      {selectedPoint && (
        <RawDataModal point={selectedPoint} onClose={() => setSelectedPoint(null)} />
      )}
    </>
  )
}

// Main Evidence Panel
export function EvidencePanel({ evidence }: EvidencePanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  if (!evidence || !evidence.metrics || evidence.metrics.length === 0) {
    return null
  }

  return (
    <div className="mt-4 border border-indigo-200 rounded-lg overflow-hidden bg-gradient-to-br from-indigo-50/50 to-white">
      {/* Panel header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-indigo-100 to-indigo-50 hover:from-indigo-150 transition-colors"
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-indigo-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-indigo-500" />
        )}

        <BarChart3 className="w-4 h-4 text-indigo-600" />

        <span className="text-[13px] font-semibold text-indigo-800">Key Evidence</span>

        <div className="flex-1" />

        {/* Summary stats */}
        <div className="flex items-center gap-3 text-[11px]">
          <span className="text-indigo-600">
            {evidence.total_sources} sources
          </span>
          {evidence.total_sample_size && (
            <span className="text-indigo-500">
              n={formatNumber(evidence.total_sample_size)}
            </span>
          )}
        </div>

        <Info className="w-3.5 h-3.5 text-indigo-400" />
      </button>

      {/* Panel content */}
      {!isCollapsed && (
        <div className="p-3 space-y-2">
          {/* Summary */}
          <div className="text-[11px] text-gray-600 pb-2 border-b border-indigo-100">
            {evidence.summary}
          </div>

          {/* Metrics */}
          {evidence.metrics.map((metric, i) => (
            <MetricCard
              key={`${metric.metric_name}-${i}`}
              metric={metric}
              defaultExpanded={i === 0} // First metric expanded by default
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default EvidencePanel
