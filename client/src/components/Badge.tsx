import { cn } from '../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'sm' | 'md'
}

export function Badge({ children, variant = 'default', size = 'md' }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        size === 'sm' && 'px-2.5 py-0.5 text-[11px]',
        size === 'md' && 'px-3 py-1 text-[12px]',
        variant === 'default' && 'bg-neutral-100 text-neutral-600',
        variant === 'success' && 'bg-[#34c759]/10 text-[#248a3d]',
        variant === 'warning' && 'bg-[#ff9500]/10 text-[#c77700]',
        variant === 'danger' && 'bg-[#ff3b30]/10 text-[#d70015]',
        variant === 'info' && 'bg-[#0071e3]/10 text-[#0071e3]'
      )}
    >
      {children}
    </span>
  )
}
