import { cn } from '../lib/utils'

interface ProgressBarProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  color?: 'default' | 'success' | 'warning' | 'danger'
  showLabel?: boolean
  label?: string
}

export function ProgressBar({ 
  value, 
  max = 100, 
  size = 'md', 
  color = 'default',
  showLabel = true,
  label
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100)
  
  return (
    <div className="w-full">
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm text-gray-600">{label}</span>}
          {showLabel && <span className="text-sm font-medium text-gray-900">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className={cn(
        'w-full bg-gray-200 rounded-full overflow-hidden',
        size === 'sm' && 'h-1.5',
        size === 'md' && 'h-2.5',
        size === 'lg' && 'h-4'
      )}>
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            color === 'default' && 'bg-black',
            color === 'success' && 'bg-green-500',
            color === 'warning' && 'bg-yellow-500',
            color === 'danger' && 'bg-red-500'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
