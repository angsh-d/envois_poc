import { useState } from 'react'
import { CheckCircle2, XCircle, ChevronDown, ChevronUp, Info, Database, BookOpen, Shield, BarChart3, Clock, AlertTriangle } from 'lucide-react'
import { ConfidenceBadge, ConfidenceLevel } from './ConfidenceBadge'
import { WhyExplanation } from './WhyExplanation'
import { ApprovalStatus } from '../lib/onboardingApi'

interface ConfidenceData {
  overall_score: number
  level: ConfidenceLevel
  factors?: Record<string, number>
  explanation?: string
}

interface WhyExplanationData {
  summary: string
  key_reasons: string[]
  unique_value: string
  inclusions?: Array<{ name: string; reason: string }>
  exclusions?: Array<{ name: string; reason: string }>
  selection_criteria?: string[]
  data_sources?: Array<{ name: string; description: string }>
}

interface RecommendationCardProps {
  title: string
  type: 'clinical' | 'registry' | 'literature' | 'fda'
  selected?: boolean
  onToggle?: (selected: boolean) => void
  enabledInsights: string[]
  preview?: string
  confidence?: ConfidenceData
  whyExplanation?: WhyExplanationData
  children?: React.ReactNode
}

// New approval-based card interface
interface ApprovalCardProps {
  title: string
  sourceId: string
  type: 'clinical' | 'registry' | 'literature' | 'fda'
  approvalStatus: ApprovalStatus
  onApprove: (sourceId: string) => void
  onReject: (sourceId: string) => void
  enabledInsights: string[]
  preview?: string
  confidence?: ConfidenceData
  whyExplanation?: WhyExplanationData
  rejectionReason?: string
  isLoading?: boolean
  children?: React.ReactNode
}

const typeConfig = {
  clinical: { icon: Database, color: 'dark' },
  registry: { icon: BarChart3, color: 'medium' },
  literature: { icon: BookOpen, color: 'light' },
  fda: { icon: Shield, color: 'dark' },
}

export function RecommendationCard({
  title,
  type,
  selected = true,
  onToggle,
  enabledInsights,
  preview,
  confidence,
  whyExplanation,
  children,
}: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(false)
  const config = typeConfig[type]
  const Icon = config.icon

  const colorClasses = {
    dark: {
      bg: 'bg-gray-50',
      border: 'border-gray-300',
      icon: 'bg-gray-900 text-white',
      check: 'text-gray-900',
    },
    medium: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: 'bg-gray-700 text-white',
      check: 'text-gray-700',
    },
    light: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: 'bg-gray-500 text-white',
      check: 'text-gray-500',
    },
  }

  const colors = colorClasses[config.color as keyof typeof colorClasses]

  return (
    <div className={`border rounded-xl overflow-hidden ${selected ? colors.border : 'border-gray-200'} ${selected ? colors.bg : 'bg-white'}`}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${colors.icon}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              {onToggle && (
                <button
                  onClick={() => onToggle(!selected)}
                  className={`
                    w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
                    ${selected ? `${colors.border} ${colors.bg}` : 'border-gray-300 bg-white'}
                  `}
                >
                  {selected && <CheckCircle2 className={`w-4 h-4 ${colors.check}`} />}
                </button>
              )}
              <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
              {confidence && (
                <ConfidenceBadge confidence={confidence} size="sm" />
              )}
            </div>
            {preview && (
              <p className="text-xs text-gray-500 mt-1">{preview}</p>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded transition-colors"
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="pt-3 space-y-4">
            {/* Enabled Insights */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Info className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Enables Insights</span>
              </div>
              <ul className="space-y-1.5">
                {enabledInsights.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Why Explanation */}
            {whyExplanation && (
              <WhyExplanation explanation={whyExplanation} />
            )}

            {children}
          </div>
        </div>
      )}
    </div>
  )
}


/**
 * ApprovalCard - A recommendation card with explicit approve/reject buttons.
 *
 * Used in the Interactive Approval workflow where stewards must explicitly
 * approve or reject each data source recommendation.
 */
export function ApprovalCard({
  title,
  sourceId,
  type,
  approvalStatus,
  onApprove,
  onReject,
  enabledInsights,
  preview,
  confidence,
  whyExplanation,
  rejectionReason,
  isLoading = false,
  children,
}: ApprovalCardProps) {
  const [expanded, setExpanded] = useState(approvalStatus === 'pending')
  const config = typeConfig[type]
  const Icon = config.icon

  const colorClasses = {
    dark: {
      bg: 'bg-gray-50',
      border: 'border-gray-300',
      icon: 'bg-gray-900 text-white',
    },
    medium: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: 'bg-gray-700 text-white',
    },
    light: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: 'bg-gray-500 text-white',
    },
  }

  const colors = colorClasses[config.color as keyof typeof colorClasses]

  // Status-based styling
  const statusStyles = {
    pending: {
      border: 'border-gray-200',
      bg: 'bg-gray-50/50',
      badge: 'bg-gray-100 text-gray-600',
      icon: Clock,
    },
    approved: {
      border: 'border-gray-400',
      bg: 'bg-gray-50',
      badge: 'bg-gray-900 text-white',
      icon: CheckCircle2,
    },
    rejected: {
      border: 'border-gray-300',
      bg: 'bg-gray-50',
      badge: 'bg-gray-200 text-gray-600',
      icon: XCircle,
    },
  }

  const status = statusStyles[approvalStatus]
  const StatusIcon = status.icon

  return (
    <div className={`border-2 rounded-xl overflow-hidden transition-all ${status.border} ${status.bg}`}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${colors.icon}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
              {/* Status Badge */}
              <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${status.badge}`}>
                <StatusIcon className="w-3 h-3" />
                <span className="capitalize">{approvalStatus}</span>
              </div>
              {confidence && (
                <ConfidenceBadge confidence={confidence} size="sm" />
              )}
            </div>
            {preview && (
              <p className="text-xs text-gray-500 mt-1">{preview}</p>
            )}
            {/* Show rejection reason if rejected */}
            {approvalStatus === 'rejected' && rejectionReason && (
              <div className="flex items-start gap-1.5 mt-2 p-2 bg-gray-100 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-600">{rejectionReason}</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded transition-colors"
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>

        {/* Action Buttons - Always visible */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => onApprove(sourceId)}
            disabled={isLoading || approvalStatus === 'approved'}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
              ${approvalStatus === 'approved'
                ? 'bg-gray-900 text-white cursor-default'
                : 'bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50'
              }
            `}
          >
            <CheckCircle2 className="w-4 h-4" />
            {approvalStatus === 'approved' ? 'Approved' : 'Approve'}
          </button>
          <button
            onClick={() => onReject(sourceId)}
            disabled={isLoading || approvalStatus === 'rejected'}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
              ${approvalStatus === 'rejected'
                ? 'bg-gray-200 text-gray-600 cursor-default'
                : 'border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50'
              }
            `}
          >
            <XCircle className="w-4 h-4" />
            {approvalStatus === 'rejected' ? 'Rejected' : 'Reject'}
          </button>
          {approvalStatus !== 'pending' && (
            <button
              onClick={() => {
                // Reset to pending by calling neither approve nor reject
                // This would need to be handled by the parent
              }}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-100 transition-colors disabled:opacity-50"
            >
              <Clock className="w-4 h-4" />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="pt-3 space-y-4">
            {/* Why Recommended - Prominent */}
            {whyExplanation && (
              <div className="p-3 bg-gray-100 rounded-lg border border-gray-200">
                <div className="flex items-center gap-1.5 mb-2">
                  <Info className="w-4 h-4 text-gray-700" />
                  <span className="text-sm font-semibold text-gray-900">Why Recommended</span>
                </div>
                <p className="text-sm text-gray-700">{whyExplanation.summary}</p>
                {whyExplanation.key_reasons && whyExplanation.key_reasons.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {whyExplanation.key_reasons.map((reason, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-sm text-gray-600">
                        <CheckCircle2 className="w-3.5 h-3.5 text-gray-900 mt-0.5 flex-shrink-0" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Confidence Factors */}
            {confidence && confidence.factors && Object.keys(confidence.factors).length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Confidence Factors</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(confidence.factors).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <span className="text-xs text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className={`text-xs font-medium ${
                        value >= 0.8 ? 'text-gray-900' :
                        value >= 0.6 ? 'text-gray-700' : 'text-gray-500'
                      }`}>
                        {Math.round(value * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Enabled Insights */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Info className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Enables Insights</span>
              </div>
              <ul className="space-y-1.5">
                {enabledInsights.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-4 h-4 text-gray-900 flex-shrink-0 mt-0.5" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Alternatives Considered */}
            {whyExplanation?.exclusions && whyExplanation.exclusions.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-gray-400" />
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Alternatives Not Selected</span>
                </div>
                <ul className="space-y-1.5">
                  {whyExplanation.exclusions.map((exclusion, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <XCircle className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="text-gray-700">{exclusion.name}</span>
                        <p className="text-xs text-gray-500">{exclusion.reason}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Full Why Explanation */}
            {whyExplanation && (
              <WhyExplanation explanation={whyExplanation} />
            )}

            {children}
          </div>
        </div>
      )}
    </div>
  )
}

interface RegistryItemProps {
  name: string
  region: string
  selected: boolean
  dataYears?: string
  relevance?: string
  nProcedures?: number
  excluded?: boolean
  exclusionReason?: string
  onToggle?: (selected: boolean) => void
}

export function RegistryItem({
  name,
  region,
  selected,
  dataYears,
  relevance,
  nProcedures,
  excluded,
  exclusionReason,
  onToggle,
}: RegistryItemProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className={`
      flex items-center gap-3 p-2.5 rounded-lg transition-colors
      ${excluded ? 'bg-gray-50 opacity-60' : selected ? 'bg-white border border-gray-200' : 'bg-gray-50'}
    `}>
      <button
        onClick={() => !excluded && onToggle?.(!selected)}
        disabled={excluded}
        className={`
          w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
          ${selected && !excluded ? 'border-gray-900 bg-gray-100' : 'border-gray-300'}
          ${!excluded && 'hover:border-gray-700 cursor-pointer'}
          ${excluded && 'cursor-not-allowed'}
        `}
      >
        {selected && !excluded && <CheckCircle2 className="w-3.5 h-3.5 text-gray-900" />}
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${excluded ? 'text-gray-500' : 'text-gray-900'}`}>{name}</span>
          <span className="text-xs text-gray-400">({region})</span>
          {nProcedures && (
            <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              {nProcedures.toLocaleString()} procedures
            </span>
          )}
        </div>
        {dataYears && (
          <span className="text-xs text-gray-500">{dataYears}</span>
        )}
        {relevance && !excluded && (
          <p className="text-xs text-gray-600 mt-0.5">{relevance}</p>
        )}
        {excluded && exclusionReason && (
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-500">{exclusionReason}</span>
            <div className="relative">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                className="text-xs text-gray-600 hover:text-gray-900 hover:underline"
              >
                Why excluded?
              </button>
              {showTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
                  <span className="font-medium">Exclusion reason:</span> {exclusionReason}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface PaperItemProps {
  title: string
  journal: string
  year: number
  insight: string
  relevanceScore?: number
  pmid?: string
  url?: string
  selected?: boolean
  onToggle?: (selected: boolean) => void
}

export function PaperItem({
  title,
  journal,
  year,
  insight,
  relevanceScore,
  pmid,
  url,
  selected = true,
  onToggle,
}: PaperItemProps) {
  const [showWhyTooltip, setShowWhyTooltip] = useState(false)

  return (
    <div className={`p-3 rounded-lg border transition-colors ${
      selected ? 'bg-white border-gray-100' : 'bg-gray-50 border-gray-200 opacity-70'
    }`}>
      <div className="flex items-start gap-2">
        {onToggle && (
          <button
            onClick={() => onToggle(!selected)}
            className={`
              w-4 h-4 mt-0.5 rounded border-2 flex items-center justify-center transition-colors flex-shrink-0
              ${selected ? 'border-gray-900 bg-gray-100' : 'border-gray-300 hover:border-gray-700'}
            `}
          >
            {selected && <CheckCircle2 className="w-3 h-3 text-gray-900" />}
          </button>
        )}
        {!onToggle && (
          <CheckCircle2 className="w-4 h-4 text-gray-900 flex-shrink-0 mt-0.5" />
        )}
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium line-clamp-2 ${selected ? 'text-gray-900' : 'text-gray-600'}`}>{title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{journal}, {year}</p>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-gray-600">{insight}</p>
            <div className="relative">
              <button
                onMouseEnter={() => setShowWhyTooltip(true)}
                onMouseLeave={() => setShowWhyTooltip(false)}
                className="text-xs text-gray-400 hover:text-gray-700"
              >
                Why?
              </button>
              {showWhyTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
                  <span className="font-medium">Selected because:</span> {insight}
                  {relevanceScore && (
                    <p className="mt-1 text-gray-300">Relevance: {Math.round(relevanceScore * 100)}%</p>
                  )}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
                </div>
              )}
            </div>
          </div>
          {pmid && url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-400 hover:text-gray-700 mt-1 inline-block"
            >
              PMID: {pmid}
            </a>
          )}
        </div>
        {relevanceScore !== undefined && (
          <div className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
            relevanceScore >= 0.8 ? 'bg-gray-900 text-white' :
            relevanceScore >= 0.6 ? 'bg-gray-600 text-white' :
            'bg-gray-100 text-gray-600'
          }`}>
            {Math.round(relevanceScore * 100)}%
          </div>
        )}
      </div>
    </div>
  )
}
