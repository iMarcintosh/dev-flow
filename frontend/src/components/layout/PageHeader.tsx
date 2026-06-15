import { ReactNode } from 'react'

interface PageHeaderProps {
  children: ReactNode
  className?: string
}

export function PageHeader({ children, className = '' }: PageHeaderProps) {
  return (
    <div
      className={`sticky top-0 z-30 border-b border-border backdrop-blur-md ${className}`}
      style={{ backgroundColor: 'rgba(17, 17, 17, 0.75)' }}
    >
      {children}
    </div>
  )
}
