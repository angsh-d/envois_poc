import { useState } from 'react'
import { HelpCircle, ChevronDown, ChevronUp, CheckCircle2, XCircle, Lightbulb, Star, Filter } from 'lucide-react'

interface InclusionExclusion {
  name: string
  reason: string
}

interface DataSource {
  name: string
  description: string
}

interface WhyExplanationData {
  summary: string
  key_reasons: string[]
  unique_value: string
  inclusions?: InclusionExclusion[]
  exclusions?: InclusionExclusion[]
  selection_criteria?: string[]
  data_sources?: DataSource[]
}

interface WhyExplanationProps {
  explanation: WhyExplanationData
  title?: string
  variant?: 'inline' | 'modal' | 'expandable'
  className?: string
}

export function WhyExplanation({
  explanation,
  title = 'Why this recommendation?',
  variant = 'expandable',
  className = '',
}: WhyExplanationProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (variant === 'inline') {
    return (
      <div className={`text-xs text-gray-600 ${className}`}>
        <p className="italic">{explanation.summary}</p>
      </div>
    )
  }

  return (
    <div className={`${className}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900 transition-colors"
      >
        <HelpCircle className="w-3.5 h-3.5" />
        <span>{isExpanded ? 'Hide explanation' : 'Why?'}</span>
        {isExpanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
          {/* Summary */}
          <p className="text-sm text-gray-700">{explanation.summary}</p>

          {/* Key Reasons */}
          {explanation.key_reasons && explanation.key_reasons.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-gray-900" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Key Reasons</span>
              </div>
              <ul className="space-y-1">
                {explanation.key_reasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                    <span className="text-gray-900 mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Unique Value */}
          {explanation.unique_value && (
            <div className="flex items-start gap-2 p-2 bg-gray-100 rounded border border-gray-200">
              <Star className="w-4 h-4 text-gray-700 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-medium text-gray-700">Unique Value:</span>
                <p className="text-xs text-gray-600">{explanation.unique_value}</p>
              </div>
            </div>
          )}

          {/* Selection Criteria (for literature) */}
          {explanation.selection_criteria && explanation.selection_criteria.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Filter className="w-3.5 h-3.5 text-gray-500" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Selection Criteria</span>
              </div>
              <ul className="space-y-1">
                {explanation.selection_criteria.map((criteria, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                    <span className="text-gray-500 mt-0.5">•</span>
                    <span>{criteria}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Data Sources (for FDA) */}
          {explanation.data_sources && explanation.data_sources.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Lightbulb className="w-3.5 h-3.5 text-gray-500" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Data Sources</span>
              </div>
              <ul className="space-y-1.5">
                {explanation.data_sources.map((source, i) => (
                  <li key={i} className="text-xs">
                    <span className="font-medium text-gray-700">{source.name}:</span>{' '}
                    <span className="text-gray-600">{source.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Inclusions */}
          {explanation.inclusions && explanation.inclusions.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-gray-900" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Included</span>
              </div>
              <ul className="space-y-1.5">
                {explanation.inclusions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5 text-gray-900 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium text-gray-700">{item.name}:</span>{' '}
                      <span className="text-gray-600">{item.reason}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Exclusions */}
          {explanation.exclusions && explanation.exclusions.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <XCircle className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Excluded</span>
              </div>
              <ul className="space-y-1.5">
                {explanation.exclusions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs">
                    <XCircle className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium text-gray-600">{item.name}:</span>{' '}
                      <span className="text-gray-500">{item.reason}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Compact why button for individual items
interface WhyButtonProps {
  reason: string
  className?: string
}

export function WhyButton({ reason, className = '' }: WhyButtonProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        onClick={() => setShowTooltip(!showTooltip)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="text-xs text-gray-600 hover:text-gray-900 hover:underline"
      >
        Why?
      </button>

      {showTooltip && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
          {reason}
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
        </div>
      )}
    </div>
  )
}

// Exclusion reason badge
interface ExclusionBadgeProps {
  reason: string
  className?: string
}

export function ExclusionBadge({ reason, className = '' }: ExclusionBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <button
        onClick={() => setShowTooltip(!showTooltip)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded hover:bg-gray-200 transition-colors"
      >
        <XCircle className="w-3 h-3" />
        <span>Excluded</span>
      </button>

      {showTooltip && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
          <span className="font-medium">Exclusion reason:</span> {reason}
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
        </div>
      )}
    </div>
  )
}
