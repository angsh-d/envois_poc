import { ReactNode } from 'react'

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'neutral' | 'info'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  size?: 'xs' | 'sm' | 'md'
  dot?: boolean
  className?: string
}

export function Badge({ children, variant = 'neutral', size = 'md', dot = false, className = '' }: BadgeProps) {
  const variants = {
    success: 'bg-gray-100 text-gray-700',
    warning: 'bg-gray-100 text-gray-700',
    danger: 'bg-gray-100 text-gray-700',
    neutral: 'bg-gray-100 text-gray-600',
    info: 'bg-gray-100 text-gray-700',
  }

  const dotColors = {
    success: 'bg-gray-400',
    warning: 'bg-gray-500',
    danger: 'bg-gray-700',
    neutral: 'bg-gray-400',
    info: 'bg-gray-500',
  }

  const sizes = {
    xs: 'px-1.5 py-0.5 text-[10px]',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  }

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-md
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  )
}

interface StatusDotProps {
  status: 'success' | 'warning' | 'danger' | 'neutral'
  size?: 'sm' | 'md'
}

export function StatusDot({ status, size = 'md' }: StatusDotProps) {
  const colors = {
    success: 'bg-gray-400',
    warning: 'bg-gray-500',
    danger: 'bg-gray-700',
    neutral: 'bg-gray-400',
  }

  const sizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
  }

  return <span className={`inline-block rounded-full ${colors[status]} ${sizes[size]}`} />
}
