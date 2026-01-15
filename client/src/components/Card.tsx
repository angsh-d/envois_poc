import { ReactNode } from 'react'
import { HelpCircle } from 'lucide-react'

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
  hoverable?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({ children, className = '', onClick, hoverable = false, padding = 'md' }: CardProps) {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  return (
    <div
      onClick={onClick}
      className={`
        bg-white rounded-xl
        border border-gray-100
        shadow-[0_1px_3px_rgba(0,0,0,0.03)]
        ${paddingStyles[padding]}
        ${hoverable ? 'cursor-pointer transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] hover:-translate-y-0.5' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  action?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export function CardHeader({ title, subtitle, action, size = 'md' }: CardHeaderProps) {
  const titleStyles = {
    sm: 'text-sm font-semibold',
    md: 'text-base font-semibold',
    lg: 'text-lg font-semibold',
  }

  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className={`${titleStyles[size]} text-gray-900 tracking-tight`}>{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  status?: 'success' | 'warning' | 'danger' | 'neutral'
  icon?: ReactNode
  subtitle?: string
  tooltip?: string
}

export function StatCard({ label, value, status = 'neutral', icon, subtitle, tooltip }: StatCardProps) {
  const statusColors = {
    success: 'text-gray-900',
    warning: 'text-gray-900',
    danger: 'text-gray-900',
    neutral: 'text-gray-900',
  }

  const statusIndicator = {
    success: 'bg-gray-400',
    warning: 'bg-gray-500',
    danger: 'bg-gray-700',
    neutral: 'bg-gray-400',
  }

  return (
    <Card className="relative">
      <div className={`absolute top-0 left-0 w-1 h-full rounded-l-xl ${statusIndicator[status]}`} />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
            {label}
            {tooltip && (
              <span className="group relative cursor-help">
                <HelpCircle className="w-3 h-3 text-gray-400" />
                <span className="absolute top-full left-0 mt-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-64 pointer-events-none z-50 leading-relaxed text-left normal-case font-normal tracking-normal shadow-lg">
                  {tooltip}
                </span>
              </span>
            )}
          </p>
          <p className={`text-2xl font-semibold mt-1 tracking-tight ${statusColors[status]}`}>
            {value}
          </p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-gray-300">{icon}</div>}
      </div>
    </Card>
  )
}

interface DataRowProps {
  label: string
  value: ReactNode
  mono?: boolean
}

export function DataRow({ label, value, mono = false }: DataRowProps) {
  return (
    <div className="flex items-baseline justify-between py-2.5 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm text-gray-900 font-medium ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}

interface SectionProps {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
}

export function Section({ title, subtitle, children, className = '' }: SectionProps) {
  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-900 tracking-tight">{title}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}
