import { ReactNode } from 'react'

type BadgeVariant = 'success' | 'warning' | 'danger' | 'neutral' | 'info'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  className?: string
}

export function Badge({ children, variant = 'neutral', size = 'md', className = '' }: BadgeProps) {
  const variants = {
    success: 'bg-green-100 text-green-700 border-green-200',
    warning: 'bg-amber-100 text-amber-700 border-amber-200',
    danger: 'bg-red-100 text-red-700 border-red-200',
    neutral: 'bg-gray-100 text-gray-600 border-gray-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  }

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full border
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {children}
    </span>
  )
}
