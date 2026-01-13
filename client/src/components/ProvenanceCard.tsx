import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Globe,
  BookOpen,
  FileText,
  Database,
  Sparkles,
  Calculator,
  Layers,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import { Source, SourceMetadata, ConfidenceLevel, DataLineage } from '@/lib/api'

interface ProvenanceCardProps {
  source: Source
  defaultExpanded?: boolean
}

// Confidence level colors and icons
const confidenceConfig: Record<ConfidenceLevel, { color: string; bgColor: string; icon: typeof CheckCircle2 }> = {
  high: { color: 'text-gray-600', bgColor: 'bg-gray-400', icon: CheckCircle2 },
  moderate: { color: 'text-gray-600', bgColor: 'bg-gray-500', icon: AlertCircle },
  low: { color: 'text-gray-600', bgColor: 'bg-gray-600', icon: AlertTriangle },
  insufficient: { color: 'text-gray-700', bgColor: 'bg-gray-700', icon: XCircle }
}

// Lineage badge configuration
const lineageConfig: Record<DataLineage, { label: string; icon: typeof FileCheck; color: string; bgColor: string }> = {
  raw_data: { label: 'Observed', icon: FileCheck, color: 'text-gray-700', bgColor: 'bg-gray-100' },
  calculated: { label: 'Calculated', icon: Calculator, color: 'text-gray-700', bgColor: 'bg-gray-100' },
  llm_synthesis: { label: 'AI Synthesized', icon: Sparkles, color: 'text-gray-700', bgColor: 'bg-gray-100' },
  aggregated: { label: 'Aggregated', icon: Layers, color: 'text-gray-700', bgColor: 'bg-gray-100' }
}

// Source type icons
function getSourceIcon(type: string) {
  const typeKey = type.toLowerCase()
  if (typeKey.includes('registry')) return Globe
  if (typeKey.includes('literature')) return BookOpen
  if (typeKey.includes('study') || typeKey.includes('data')) return FileText
  return Database
}

// Format large numbers
function formatNumber(n?: number): string {
  if (!n) return 'N/A'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${Math.round(n / 1000)}K`
  return n.toLocaleString()
}

// Confidence dot component
function ConfidenceDot({ level, score }: { level?: ConfidenceLevel; score?: number }) {
  const config = confidenceConfig[level || 'high']
  const displayScore = score !== undefined ? `${Math.round(score * 100)}%` : null

  return (
    <div
      className="flex items-center gap-1"
      title={`Confidence: ${level || 'high'}${displayScore ? ` (${displayScore})` : ''}`}
    >
      <div className={`w-2 h-2 rounded-full ${config.bgColor}`} />
      <span className="text-[10px] text-gray-500 capitalize">{level || 'high'}</span>
    </div>
  )
}

// Lineage badge component
function LineageBadge({ lineage }: { lineage?: DataLineage }) {
  const config = lineageConfig[lineage || 'raw_data']
  const Icon = config.icon

  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${config.bgColor} ${config.color}`}>
      <Icon className="w-2.5 h-2.5" />
      {config.label}
    </span>
  )
}

// Completeness bar component
function CompletenessBar({ score }: { score?: number }) {
  if (score === undefined) return null
  const percentage = Math.round(score * 100)
  const color = score >= 0.8 ? 'bg-gray-400' : score >= 0.6 ? 'bg-gray-500' : 'bg-gray-600'

  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${percentage}%` }} />
      </div>
      <span className="text-[10px] text-gray-500">{percentage}%</span>
    </div>
  )
}

// Sample size indicator
function SampleSize({ n, label = 'n' }: { n?: number; label?: string }) {
  if (!n) return null
  return (
    <div className="flex items-center gap-1 text-[11px] text-gray-600">
      <Database className="w-3 h-3" />
      <span>{label}={formatNumber(n)}</span>
    </div>
  )
}

// Metadata section based on source type
function MetadataSection({ metadata, type }: { metadata?: SourceMetadata; type: string }) {
  if (!metadata) return null

  const typeKey = type.toLowerCase()

  // Registry-specific metadata
  if (typeKey.includes('registry')) {
    return (
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
        {metadata.abbreviation && (
          <div>
            <span className="text-gray-500">Registry:</span>
            <span className="ml-1 font-medium text-gray-700">{metadata.abbreviation}</span>
          </div>
        )}
        {metadata.report_year && (
          <div>
            <span className="text-gray-500">Report Year:</span>
            <span className="ml-1 text-gray-700">{metadata.report_year}</span>
          </div>
        )}
        {metadata.data_years && (
          <div>
            <span className="text-gray-500">Data Coverage:</span>
            <span className="ml-1 text-gray-700">{metadata.data_years}</span>
          </div>
        )}
        {metadata.n_procedures && (
          <div>
            <SampleSize n={metadata.n_procedures} label="procedures" />
          </div>
        )}
        {metadata.data_completeness !== undefined && (
          <div className="col-span-2">
            <span className="text-gray-500 mr-2">Data Completeness:</span>
            <CompletenessBar score={metadata.data_completeness} />
          </div>
        )}
      </div>
    )
  }

  // Literature-specific metadata
  if (typeKey.includes('literature')) {
    return (
      <div className="space-y-2 text-[11px]">
        {metadata.publication_title && (
          <div className="font-medium text-gray-700">{metadata.publication_title}</div>
        )}
        <div className="flex flex-wrap gap-3 text-gray-600">
          {metadata.publication_year && <span>Year: {metadata.publication_year}</span>}
          {metadata.n_patients && <SampleSize n={metadata.n_patients} label="patients" />}
          {metadata.follow_up_years && <span>Follow-up: {metadata.follow_up_years}yr</span>}
          {metadata.data_years && <span>Coverage: {metadata.data_years}</span>}
        </div>
        {metadata.data_completeness !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Completeness:</span>
            <CompletenessBar score={metadata.data_completeness} />
          </div>
        )}
      </div>
    )
  }

  // Study data metadata
  return (
    <div className="space-y-2 text-[11px]">
      <div className="flex flex-wrap gap-3 text-gray-600">
        {metadata.n_patients && <SampleSize n={metadata.n_patients} label="patients" />}
        {metadata.abbreviation && <span>Study: {metadata.abbreviation}</span>}
      </div>
      {metadata.data_completeness !== undefined && (
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Completeness:</span>
          <CompletenessBar score={metadata.data_completeness} />
        </div>
      )}
    </div>
  )
}

// Quality indicators (strengths/limitations)
function QualityIndicators({ metadata }: { metadata?: SourceMetadata }) {
  if (!metadata) return null
  const { strengths, limitations } = metadata
  if (!strengths?.length && !limitations?.length) return null

  return (
    <div className="mt-2 pt-2 border-t border-gray-100 space-y-2">
      {strengths && strengths.length > 0 && (
        <div>
          <span className="text-[10px] font-medium text-gray-600 uppercase">Strengths</span>
          <ul className="mt-0.5 space-y-0.5">
            {strengths.slice(0, 2).map((s, i) => (
              <li key={i} className="text-[10px] text-gray-600 flex items-start gap-1">
                <CheckCircle2 className="w-3 h-3 text-gray-500 flex-shrink-0 mt-0.5" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
      {limitations && limitations.length > 0 && (
        <div>
          <span className="text-[10px] font-medium text-gray-600 uppercase">Limitations</span>
          <ul className="mt-0.5 space-y-0.5">
            {limitations.slice(0, 2).map((l, i) => (
              <li key={i} className="text-[10px] text-gray-600 flex items-start gap-1">
                <AlertTriangle className="w-3 h-3 text-gray-500 flex-shrink-0 mt-0.5" />
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// Main ProvenanceCard component
export function ProvenanceCard({ source, defaultExpanded = false }: ProvenanceCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const SourceIcon = getSourceIcon(source.type)
  const hasMetadata = source.metadata && Object.keys(source.metadata).length > 0

  return (
    <div className={`
      rounded-lg border transition-all duration-200
      ${isExpanded ? 'bg-white border-gray-200 shadow-sm' : 'bg-gray-50/50 border-gray-100 hover:border-gray-200'}
    `}>
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left"
        disabled={!hasMetadata}
      >
        {/* Source type icon */}
        <div className={`
          w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 bg-gray-100
        `}>
          <SourceIcon className="w-3.5 h-3.5 text-gray-600" />
        </div>

        {/* Reference text */}
        <span className="flex-1 text-[12px] text-gray-700 truncate" title={source.reference}>
          {source.reference}
        </span>

        {/* Indicators */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <ConfidenceDot level={source.confidence_level} score={source.confidence} />
          <LineageBadge lineage={source.lineage} />
          {hasMetadata && (
            isExpanded ?
              <ChevronDown className="w-4 h-4 text-gray-400" /> :
              <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expandable content */}
      {isExpanded && hasMetadata && (
        <div className="px-3 pb-3 pt-1 border-t border-gray-100">
          <MetadataSection metadata={source.metadata} type={source.type} />
          <QualityIndicators metadata={source.metadata} />
        </div>
      )}
    </div>
  )
}

export default ProvenanceCard
