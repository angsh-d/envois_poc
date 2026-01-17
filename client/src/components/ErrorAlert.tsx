import { AlertCircle, RefreshCw, X } from 'lucide-react'

export type ErrorSeverity = 'error' | 'warning' | 'info'

interface ErrorAlertProps {
  title?: string
  message: string
  severity?: ErrorSeverity
  onRetry?: () => void
  onDismiss?: () => void
  details?: string
  className?: string
}

const severityStyles = {
  error: {
    container: 'bg-red-50 border-red-200',
    icon: 'text-red-500',
    title: 'text-red-800',
    message: 'text-red-700',
    button: 'bg-red-100 text-red-700 hover:bg-red-200',
    details: 'bg-red-100 text-red-600',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200',
    icon: 'text-amber-500',
    title: 'text-amber-800',
    message: 'text-amber-700',
    button: 'bg-amber-100 text-amber-700 hover:bg-amber-200',
    details: 'bg-amber-100 text-amber-600',
  },
  info: {
    container: 'bg-blue-50 border-blue-200',
    icon: 'text-blue-500',
    title: 'text-blue-800',
    message: 'text-blue-700',
    button: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
    details: 'bg-blue-100 text-blue-600',
  },
}

export function ErrorAlert({
  title,
  message,
  severity = 'error',
  onRetry,
  onDismiss,
  details,
  className = '',
}: ErrorAlertProps) {
  const styles = severityStyles[severity]

  return (
    <div
      className={`rounded-lg border p-4 ${styles.container} ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${styles.icon}`} />
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={`font-medium ${styles.title}`}>{title}</h4>
          )}
          <p className={`text-sm ${title ? 'mt-1' : ''} ${styles.message}`}>
            {message}
          </p>
          {details && (
            <pre className={`mt-2 p-2 rounded text-xs overflow-x-auto font-mono ${styles.details}`}>
              {details}
            </pre>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className={`mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${styles.button}`}
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className={`flex-shrink-0 p-1 rounded-md transition-colors ${styles.button}`}
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

// Connection error specific component
interface ConnectionErrorProps {
  onRetry: () => void
  className?: string
}

export function ConnectionError({ onRetry, className = '' }: ConnectionErrorProps) {
  return (
    <ErrorAlert
      severity="error"
      title="Connection Error"
      message="Unable to connect to the server. Please check your connection and try again."
      onRetry={onRetry}
      className={className}
    />
  )
}

// API error specific component
interface ApiErrorProps {
  statusCode?: number
  message?: string
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

export function ApiError({
  statusCode,
  message,
  onRetry,
  onDismiss,
  className = '',
}: ApiErrorProps) {
  const getErrorMessage = () => {
    if (message) return message

    switch (statusCode) {
      case 400:
        return 'Invalid request. Please check your input and try again.'
      case 401:
        return 'Authentication required. Please log in and try again.'
      case 403:
        return 'You do not have permission to perform this action.'
      case 404:
        return 'The requested resource was not found.'
      case 429:
        return 'Too many requests. Please wait a moment and try again.'
      case 500:
        return 'Server error. Our team has been notified.'
      case 502:
      case 503:
        return 'Service temporarily unavailable. Please try again later.'
      default:
        return 'An unexpected error occurred. Please try again.'
    }
  }

  return (
    <ErrorAlert
      severity="error"
      title={statusCode ? `Error ${statusCode}` : 'Error'}
      message={getErrorMessage()}
      onRetry={onRetry}
      onDismiss={onDismiss}
      className={className}
    />
  )
}

// Validation error component
interface ValidationErrorProps {
  errors: string[]
  onDismiss?: () => void
  className?: string
}

export function ValidationError({
  errors,
  onDismiss,
  className = '',
}: ValidationErrorProps) {
  if (errors.length === 0) return null

  return (
    <ErrorAlert
      severity="warning"
      title="Validation Error"
      message={
        errors.length === 1
          ? errors[0]
          : `Please fix the following issues:\n• ${errors.join('\n• ')}`
      }
      onDismiss={onDismiss}
      className={className}
    />
  )
}

// Empty state component (not strictly an error, but useful for error-like states)
interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  icon,
  title,
  message,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`text-center py-12 px-6 ${className}`}>
      {icon && (
        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-500 max-w-md mx-auto">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
