import { cn } from '../lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'link'
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
        'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200',
        variant === 'primary' && 'bg-neutral-900 text-white hover:bg-neutral-800 active:scale-[0.98]',
        variant === 'secondary' && 'bg-white border border-neutral-300 text-neutral-900 hover:bg-neutral-50 hover:border-neutral-400 active:scale-[0.98]',
        variant === 'ghost' && 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100',
        variant === 'link' && 'text-[#0071e3] hover:underline underline-offset-2 p-0',
        size === 'sm' && variant !== 'link' && 'px-4 py-2 text-[13px]',
        size === 'md' && variant !== 'link' && 'px-5 py-2.5 text-[15px]',
        size === 'lg' && variant !== 'link' && 'px-8 py-3.5 text-[17px]',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
