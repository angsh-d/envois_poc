import React from 'react'
import {
  TrendingUp, TrendingDown, Minus,
  CheckCircle2, AlertCircle, AlertTriangle, XCircle,
  Users, UserCheck, Activity, BarChart3, Shield, Bell, List
} from 'lucide-react'
import { MetricGridItem } from '../lib/api'

interface ChatMetricGridProps {
  metrics: MetricGridItem[]
}

// Extended metric with status/icon from backend
interface ExtendedMetric extends MetricGridItem {
  status?: 'success' | 'warning' | 'danger' | 'neutral'
  icon?: string
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  'check': CheckCircle2,
  'check-circle': CheckCircle2,
  'x': XCircle,
  'alert-triangle': AlertTriangle,
  'alert-circle': AlertCircle,
  'users': Users,
  'user-check': UserCheck,
  'activity': Activity,
  'bar-chart': BarChart3,
  'shield': Shield,
  'bell': Bell,
  'list': List,
  'trending-up': TrendingUp,
}

function getStatusColor(status?: string, trend?: string): {
  bg: string
  text: string
  border: string
} {
  // Use status if provided (from backend)
  if (status) {
    switch (status) {
      case 'success':
        return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' }
      case 'danger':
        return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' }
      case 'warning':
        return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' }
      default:
        return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' }
    }
  }

  // Fall back to trend
  if (trend === 'up') {
    return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' }
  } else if (trend === 'down') {
    return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' }
  }

  return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' }
}

function getTrendIcon(trend?: string) {
  switch (trend) {
    case 'up':
      return TrendingUp
    case 'down':
      return TrendingDown
    default:
      return Minus
  }
}

function MetricCard({ metric }: { metric: ExtendedMetric }) {
  const { label, value, trend, delta, status, icon } = metric
  const colors = getStatusColor(status, trend)
  const TrendIcon = getTrendIcon(trend)
  const IconComponent = icon ? iconMap[icon] : null

  return (
    <div className={`flex flex-col p-3 rounded-lg border ${colors.border} ${colors.bg}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wide">
          {label}
        </span>
        {IconComponent && (
          <IconComponent className={`w-4 h-4 ${colors.text} opacity-60`} />
        )}
      </div>
      <div className="flex items-end justify-between">
        <span className={`text-[20px] font-bold ${colors.text}`}>
          {value}
        </span>
        <div className="flex items-center gap-1">
          {delta && (
            <span className={`text-[11px] ${colors.text}`}>
              {delta}
            </span>
          )}
          {trend && (
            <TrendIcon className={`w-4 h-4 ${colors.text}`} />
          )}
        </div>
      </div>
    </div>
  )
}

export function ChatMetricGrid({ metrics }: ChatMetricGridProps) {
  if (!metrics || metrics.length === 0) {
    return null
  }

  // Determine grid columns based on metric count
  const gridCols = metrics.length <= 2
    ? 'grid-cols-2'
    : metrics.length === 3
    ? 'grid-cols-3'
    : 'grid-cols-2 sm:grid-cols-4'

  return (
    <div className={`grid ${gridCols} gap-3`}>
      {metrics.map((metric, index) => (
        <MetricCard key={index} metric={metric as ExtendedMetric} />
      ))}
    </div>
  )
}
