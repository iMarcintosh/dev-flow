import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

interface ToastComponentProps {
  toast: Toast
  onClose: (id: string) => void
}

export function ToastComponent({ toast, onClose }: ToastComponentProps) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const colors = {
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-300',
    error: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-300',
    warning: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300',
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300',
  }

  const iconColors = {
    success: 'text-green-600 dark:text-green-400',
    error: 'text-red-600 dark:text-red-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    info: 'text-blue-600 dark:text-blue-400',
  }

  const Icon = icons[toast.type]

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg min-w-[320px] max-w-md transition-all ${colors[toast.type]}`}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColors[toast.type]}`} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{toast.title}</p>
        {toast.message && (
          <p className="mt-1 text-sm opacity-90">{toast.message}</p>
        )}
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onClose: (id: string) => void
}

export function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto animate-slide-in">
          <ToastComponent toast={toast} onClose={onClose} />
        </div>
      ))}
    </div>
  )
}
