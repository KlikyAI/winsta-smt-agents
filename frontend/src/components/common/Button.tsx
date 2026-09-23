import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'lime' | 'danger' | 'ghost' | 'light';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses = {
    sm: 'px-3.5 py-1.5 text-xs gap-1.5 min-h-[36px]',
    md: 'px-5 py-2 text-sm gap-2 min-h-[42px]',
    lg: 'px-6 py-3 text-base gap-2.5 min-h-[48px]',
  }[size];

  const variantClasses = {
    primary:
      'bg-[#0f172a] text-[#ffffff] border border-[#0f172a] hover:bg-[#1e293b] shadow-[2px_2px_0px_#0f172a]',
    secondary:
      'bg-slate-100 text-slate-900 border border-slate-300 hover:bg-slate-200 shadow-[2px_2px_0px_#cbd5e1]',
    lime:
      'bg-[#8b5cf6] text-[#ffffff] border border-[#7c3aed] hover:bg-[#7c3aed] shadow-[2px_2px_0px_#6d28d9] font-extrabold',
    danger:
      'bg-rose-600 text-white border border-rose-700 hover:bg-rose-700 shadow-[2px_2px_0px_#be123c]',
    light:
      'bg-white text-slate-900 border border-slate-300 hover:bg-slate-50 shadow-[2px_2px_0px_#e2e8f0]',
    ghost:
      'bg-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent',
  }[variant];

  return (
    <button
      className={`clova-pill inline-flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};
