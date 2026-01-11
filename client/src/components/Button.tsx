import { cn } from '../lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className, 
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        'font-semibold rounded-full transition-all duration-300',
        variant === 'primary' && 'bg-black text-white hover:bg-gray-900 shadow-none',
        variant === 'secondary' && 'bg-white border-2 border-black text-black hover:bg-black hover:text-white',
        variant === 'ghost' && 'bg-transparent text-gray-600 hover:text-black hover:bg-gray-100',
        size === 'sm' && 'px-6 py-2 text-sm',
        size === 'md' && 'px-8 py-3 text-base',
        size === 'lg' && 'px-12 py-4 text-base',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
