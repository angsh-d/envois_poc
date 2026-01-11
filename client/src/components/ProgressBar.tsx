import { cn } from '../lib/utils'

interface ProgressBarProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'danger'
  showLabel?: boolean
  label?: string
  animated?: boolean
}

export function ProgressBar({ 
  value, 
  max = 100, 
  size = 'md', 
  variant = 'default',
  showLabel = false,
  label,
  animated = true
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100)
  
  return (
    <div className="w-full">
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-body-sm text-neutral-600">{label}</span>}
          {showLabel && <span className="text-body-sm font-medium text-neutral-900">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className={cn(
        'w-full bg-neutral-200/60 rounded-full overflow-hidden',
        size === 'sm' && 'h-1',
        size === 'md' && 'h-2',
        size === 'lg' && 'h-3'
      )}>
        <div
          className={cn(
            'h-full rounded-full',
            animated && 'transition-all duration-700 ease-out',
            variant === 'default' && 'bg-gradient-to-r from-neutral-700 to-neutral-900',
            variant === 'success' && 'bg-gradient-to-r from-[#30d158] to-[#34c759]',
            variant === 'warning' && 'bg-gradient-to-r from-[#ffd60a] to-[#ff9500]',
            variant === 'danger' && 'bg-gradient-to-r from-[#ff6961] to-[#ff3b30]'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
