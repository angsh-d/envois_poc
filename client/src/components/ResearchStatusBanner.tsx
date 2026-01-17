import { useState, useEffect, useCallback } from 'react'
import { Loader2, CheckCircle2, AlertCircle, X, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import {
  getResearchStatus,
  ResearchStatusResponse,
  ResearchStage,
  getStageLabel,
  isResearchInProgress,
  isResearchComplete,
  isResearchFailed,
} from '@/lib/researchApi'

interface ResearchStatusBannerProps {
  sessionId: string
  productId?: string
  onComplete?: () => void
  onError?: (error: string) => void
}

export function ResearchStatusBanner({
  sessionId,
  productId,
  onComplete,
  onError,
}: ResearchStatusBannerProps) {
  const [status, setStatus] = useState<ResearchStatusResponse | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      const data = await getResearchStatus(sessionId)
      setStatus(data)
      setError(null)

      if (isResearchComplete(data.status)) {
        onComplete?.()
      } else if (isResearchFailed(data.status) && data.error_message) {
        onError?.(data.error_message)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load status'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, onComplete, onError])

  useEffect(() => {
    loadStatus()

    // Poll for status updates every 3 seconds while in progress
    const interval = setInterval(() => {
      if (status && isResearchInProgress(status.status)) {
        loadStatus()
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [loadStatus, status])

  // Don't render if loading, no status, complete, or dismissed
  if (isLoading) {
    return null
  }

  if (!status || isDismissed) {
    return null
  }

  // Don't show banner if complete (unless we want to show success briefly)
  if (isResearchComplete(status.status)) {
    return null
  }

  const isFailed = isResearchFailed(status.status)
  const inProgress = isResearchInProgress(status.status)

  const getStageStatusIcon = (stage: ResearchStage) => {
    switch (stage.status) {
      case 'complete':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
      case 'running':
        return <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
    }
  }

  return (
    <div
      className={`w-full rounded-2xl mb-6 overflow-hidden transition-all duration-300 ${
        isFailed
          ? 'bg-red-50 border border-red-200'
          : 'bg-neutral-900 text-white'
      }`}
    >
      {/* Header */}
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {inProgress ? (
              <Loader2 className={`w-5 h-5 animate-spin ${isFailed ? 'text-red-500' : 'text-white'}`} />
            ) : isFailed ? (
              <AlertCircle className="w-5 h-5 text-red-500" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            )}
            <div>
              <p className={`font-medium ${isFailed ? 'text-red-700' : ''}`}>
                {isFailed ? 'Research Failed' : 'Deep Research in Progress'}
              </p>
              <p className={`text-sm ${isFailed ? 'text-red-600' : 'text-neutral-400'}`}>
                {isFailed && status.error_message
                  ? status.error_message
                  : `${status.current_stage_label || getStageLabel(status.current_stage || '')} • ${status.progress}% complete`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                isFailed
                  ? 'text-red-700 hover:bg-red-100'
                  : 'text-neutral-300 hover:bg-neutral-800'
              }`}
            >
              {isExpanded ? 'Hide' : 'Details'}
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {productId && (
              <a
                href={`/product/${productId}/research-status`}
                className={`p-2 rounded-lg transition-colors ${
                  isFailed
                    ? 'text-red-600 hover:bg-red-100'
                    : 'text-neutral-400 hover:bg-neutral-800'
                }`}
                title="View full status"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}

            {isFailed && (
              <button
                onClick={() => setIsDismissed(true)}
                className="p-2 text-red-400 hover:bg-red-100 rounded-lg transition-colors"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        {!isFailed && (
          <div className="mt-3 h-1 bg-neutral-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-white transition-all duration-500 ease-out"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Expanded stages */}
      {isExpanded && status.stages && status.stages.length > 0 && (
        <div className={`px-6 pb-4 ${isFailed ? 'bg-red-50' : 'bg-neutral-800'}`}>
          <div className="space-y-3">
            {status.stages.map((stage, index) => (
              <div
                key={stage.name}
                className={`flex items-center gap-3 ${
                  isFailed ? 'text-gray-700' : 'text-neutral-300'
                }`}
              >
                {/* Connector line */}
                <div className="relative flex flex-col items-center">
                  {getStageStatusIcon(stage)}
                  {index < status.stages.length - 1 && (
                    <div
                      className={`absolute top-5 w-0.5 h-6 ${
                        stage.status === 'complete'
                          ? 'bg-emerald-500'
                          : isFailed
                          ? 'bg-gray-300'
                          : 'bg-neutral-600'
                      }`}
                    />
                  )}
                </div>

                {/* Stage info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-sm font-medium ${
                        stage.status === 'running'
                          ? isFailed
                            ? 'text-gray-800'
                            : 'text-white'
                          : ''
                      }`}
                    >
                      {getStageLabel(stage.name)}
                    </span>
                    <span
                      className={`text-xs ${
                        isFailed ? 'text-gray-500' : 'text-neutral-500'
                      }`}
                    >
                      {stage.status === 'complete'
                        ? '100%'
                        : stage.status === 'running'
                        ? `${stage.progress}%`
                        : stage.status === 'failed'
                        ? 'Failed'
                        : 'Pending'}
                    </span>
                  </div>

                  {/* Stage progress bar */}
                  {stage.status !== 'pending' && (
                    <div
                      className={`mt-1 h-1 rounded-full overflow-hidden ${
                        isFailed ? 'bg-gray-200' : 'bg-neutral-700'
                      }`}
                    >
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          stage.status === 'complete'
                            ? 'bg-emerald-500'
                            : stage.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-indigo-500'
                        }`}
                        style={{ width: `${stage.progress}%` }}
                      />
                    </div>
                  )}

                  {/* Error message for failed stage */}
                  {stage.status === 'failed' && stage.error && (
                    <p className="mt-1 text-xs text-red-500">{stage.error}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
