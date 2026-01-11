import { cn } from '../lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'glass' | 'elevated'
  hover?: boolean
  onClick?: () => void
}

export function Card({ children, className, variant = 'default', hover = false, onClick }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl transition-all duration-300',
        variant === 'default' && 'bg-white border border-black/[0.04] shadow-[0_2px_8px_rgba(0,0,0,0.04)]',
        variant === 'glass' && 'glass-card',
        variant === 'elevated' && 'bg-white shadow-[0_4px_16px_rgba(0,0,0,0.08),0_2px_4px_rgba(0,0,0,0.04)]',
        hover && 'hover:shadow-[0_8px_32px_rgba(0,0,0,0.12)] hover:-translate-y-0.5 cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: { value: string; positive: boolean }
  className?: string
}

export function StatCard({ title, value, subtitle, trend, className }: StatCardProps) {
  return (
    <Card className={cn('p-6', className)}>
      <p className="text-caption text-neutral-500 uppercase tracking-wide mb-2">{title}</p>
      <p className="text-display-md text-neutral-900">{value}</p>
      {subtitle && (
        <p className="text-body-sm text-neutral-500 mt-1">{subtitle}</p>
      )}
      {trend && (
        <p className={cn(
          'text-body-sm mt-2 font-medium',
          trend.positive ? 'text-[#34c759]' : 'text-[#ff3b30]'
        )}>
          {trend.positive ? '↑' : '↓'} {trend.value}
        </p>
      )}
    </Card>
  )
}
