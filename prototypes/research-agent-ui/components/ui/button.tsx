// ═══════════════════════════════════════════════════════════════
// Button 组件
// ═══════════════════════════════════════════════════════════════

import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'primary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-all',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            // Variants
            'bg-slate-700 text-white hover:bg-slate-600 focus:ring-slate-500': variant === 'default',
            'bg-indigo-600 text-white hover:bg-indigo-500 focus:ring-indigo-500': variant === 'primary',
            'border border-slate-600 text-slate-300 hover:bg-slate-800 focus:ring-slate-500': variant === 'outline',
            'text-slate-300 hover:bg-slate-800 focus:ring-slate-500': variant === 'ghost',
            'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500': variant === 'danger',
            // Sizes
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-sm': size === 'md',
            'px-6 py-3 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'

export { Button }

