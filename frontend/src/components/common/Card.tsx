import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hoverable = false,
}) => {
  // If no background class is specified in className, default to bg-white
  const hasBg = className.includes('bg-');
  const bgClass = hasBg ? '' : 'bg-white';

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-slate-200 shadow-xs transition-all duration-200 ${bgClass} ${
        hoverable ? 'hover:border-[#8b5cf6] hover:shadow-md hover:-translate-y-0.5' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};
