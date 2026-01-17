import { Info, CheckCircle, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react'
import { useState } from 'react'

export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW' | 'INSUFFICIENT'

interface ConfidenceData {
  overall_score: number
  level: ConfidenceLevel
  factors?: Record<string, number>
  explanation?: string
  methodology?: string
}

interface ConfidenceBadgeProps {
  confidence: ConfidenceData
  showScore?: boolean
  showTooltip?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const levelConfig = {
  HIGH: {
    icon: CheckCircle,
    bg: 'bg-gray-900',
    border: 'border-gray-900',
    text: 'text-white',
    iconColor: 'text-white',
    label: 'High Confidence',
    description: 'Strong evidence from multiple recent sources',
  },
  MODERATE: {
    icon: Info,
    bg: 'bg-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-700',
    iconColor: 'text-gray-500',
    label: 'Moderate Confidence',
    description: 'Good evidence with some limitations',
  },
  LOW: {
    icon: AlertTriangle,
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-600',
    iconColor: 'text-gray-400',
    label: 'Low Confidence',
    description: 'Limited evidence, use with caution',
  },
  INSUFFICIENT: {
    icon: AlertCircle,
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-500',
    iconColor: 'text-gray-400',
    label: 'Insufficient Data',
    description: 'Not enough data for reliable conclusions',
  },
}

const sizeConfig = {
  sm: {
    badge: 'px-1.5 py-0.5 text-xs',
    icon: 'w-3 h-3',
  },
  md: {
    badge: 'px-2 py-1 text-sm',
    icon: 'w-4 h-4',
  },
  lg: {
    badge: 'px-3 py-1.5 text-base',
    icon: 'w-5 h-5',
  },
}

export function ConfidenceBadge({
  confidence,
  showScore = false,
  showTooltip = true,
  size = 'md',
  className = '',
}: ConfidenceBadgeProps) {
  const [isTooltipVisible, setIsTooltipVisible] = useState(false)
  const config = levelConfig[confidence.level] || levelConfig.MODERATE
  const sizeStyles = sizeConfig[size]
  const Icon = config.icon

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        className={`
          inline-flex items-center gap-1 rounded-full border
          ${config.bg} ${config.border} ${config.text} ${sizeStyles.badge}
          ${showTooltip ? 'cursor-help' : ''}
        `}
        onMouseEnter={() => showTooltip && setIsTooltipVisible(true)}
        onMouseLeave={() => showTooltip && setIsTooltipVisible(false)}
      >
        <Icon className={`${sizeStyles.icon} ${config.iconColor}`} />
        <span className="font-medium">
          {showScore ? `${Math.round(confidence.overall_score * 100)}%` : confidence.level}
        </span>
      </div>

      {/* Tooltip */}
      {showTooltip && isTooltipVisible && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-white rounded-lg shadow-lg border border-gray-200 text-left">
          <div className="flex items-center gap-2 mb-2">
            <Icon className={`w-4 h-4 ${config.iconColor}`} />
            <span className={`font-medium ${config.text}`}>{config.label}</span>
            <span className="ml-auto text-sm font-semibold text-gray-900">
              {Math.round(confidence.overall_score * 100)}%
            </span>
          </div>

          <p className="text-xs text-gray-600 mb-2">{config.description}</p>

          {confidence.explanation && (
            <p className="text-xs text-gray-700 mb-2">{confidence.explanation}</p>
          )}

          {confidence.factors && Object.keys(confidence.factors).length > 0 && (
            <div className="space-y-1 pt-2 border-t border-gray-100">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Factors</p>
              {Object.entries(confidence.factors).map(([factor, score]) => (
                <div key={factor} className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 capitalize flex-1">{factor.replace(/_/g, ' ')}</span>
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${getFactorColor(score)}`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{Math.round(score * 100)}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Arrow */}
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-gray-200 transform rotate-45" />
        </div>
      )}
    </div>
  )
}

function getFactorColor(score: number): string {
  if (score >= 0.8) return 'bg-gray-900'
  if (score >= 0.6) return 'bg-gray-600'
  if (score >= 0.4) return 'bg-gray-400'
  return 'bg-gray-300'
}

// Compact inline confidence indicator
interface ConfidenceIndicatorProps {
  score: number
  label?: string
  className?: string
}

export function ConfidenceIndicator({ score, label, className = '' }: ConfidenceIndicatorProps) {
  const level = getLevel(score)
  const config = levelConfig[level]

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {label && <span className="text-xs text-gray-500">{label}</span>}
      <div className="flex items-center gap-1">
        <div className={`w-2 h-2 rounded-full ${config.bg.replace('50', '500')}`} />
        <span className="text-xs font-medium text-gray-700">{Math.round(score * 100)}%</span>
      </div>
    </div>
  )
}

function getLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return 'HIGH'
  if (score >= 0.6) return 'MODERATE'
  if (score >= 0.4) return 'LOW'
  return 'INSUFFICIENT'
}

// Confidence score bar for detailed view
interface ConfidenceBarProps {
  confidence: ConfidenceData
  showFactors?: boolean
  className?: string
}

export function ConfidenceBar({ confidence, showFactors = false, className = '' }: ConfidenceBarProps) {
  const config = levelConfig[confidence.level] || levelConfig.MODERATE

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">Confidence</span>
          <HelpCircle className="w-3.5 h-3.5 text-gray-400" />
        </div>
        <ConfidenceBadge confidence={confidence} showScore size="sm" />
      </div>

      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${config.bg.replace('50', '500')}`}
          style={{ width: `${confidence.overall_score * 100}%` }}
        />
      </div>

      {confidence.explanation && (
        <p className="text-xs text-gray-600">{confidence.explanation}</p>
      )}

      {showFactors && confidence.factors && (
        <div className="grid grid-cols-2 gap-2 pt-2">
          {Object.entries(confidence.factors).map(([factor, score]) => (
            <div key={factor} className="flex items-center gap-2">
              <span className="text-xs text-gray-500 capitalize">{factor.replace(/_/g, ' ')}</span>
              <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${getFactorColor(score)}`}
                  style={{ width: `${score * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
