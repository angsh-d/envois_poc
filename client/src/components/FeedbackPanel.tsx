import { useState } from 'react'
import { MessageCircle, Send, RefreshCw, X } from 'lucide-react'

interface FeedbackPanelProps {
  onSubmit: (feedback: string, requestReanalysis: boolean) => Promise<void>
  isLoading?: boolean
  existingFeedback?: string[]
}

export function FeedbackPanel({
  onSubmit,
  isLoading = false,
  existingFeedback = [],
}: FeedbackPanelProps) {
  const [feedback, setFeedback] = useState('')
  const [requestReanalysis, setRequestReanalysis] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const handleSubmit = async () => {
    if (!feedback.trim()) return

    await onSubmit(feedback.trim(), requestReanalysis)
    setFeedback('')
    setRequestReanalysis(false)
  }

  return (
    <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 border-b border-gray-200 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
            Steward Feedback
          </h3>
          {existingFeedback.length > 0 && (
            <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-700 rounded-full">
              {existingFeedback.length} comment{existingFeedback.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-500">
          {isExpanded ? 'Click to collapse' : 'Click to expand'}
        </span>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="p-4">
          {/* Existing Feedback */}
          {existingFeedback.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Previous Feedback
              </div>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {existingFeedback.map((fb, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg">
                    <MessageCircle className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-gray-700">{fb}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* New Feedback Input */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">
                Add Additional Context or Requirements
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="E.g., &quot;Please also include the CJRR (Canada) registry if available - we have Canadian sites in this study.&quot;"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                rows={3}
                disabled={isLoading}
              />
            </div>

            {/* Request Reanalysis Checkbox */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={requestReanalysis}
                onChange={(e) => setRequestReanalysis(e.target.checked)}
                disabled={isLoading}
                className="w-4 h-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
              />
              <div className="flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5 text-gray-500" />
                <span className="text-sm text-gray-700">Request AI re-analysis based on this feedback</span>
              </div>
            </label>

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                onClick={handleSubmit}
                disabled={!feedback.trim() || isLoading}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors
                  ${feedback.trim() && !isLoading
                    ? 'bg-gray-900 text-white hover:bg-gray-800'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Submit Feedback
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Rejection Reason Modal
interface RejectionModalProps {
  isOpen: boolean
  sourceType: string
  sourceName: string
  onClose: () => void
  onConfirm: (reason: string) => void
  isLoading?: boolean
}

export function RejectionModal({
  isOpen,
  sourceType,
  sourceName,
  onClose,
  onConfirm,
  isLoading = false,
}: RejectionModalProps) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleConfirm = () => {
    if (!reason.trim()) return
    onConfirm(reason.trim())
    setReason('')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Reject {sourceName}</h3>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          <p className="text-sm text-gray-600 mb-3">
            Please provide a reason for rejecting this {sourceType} source.
            This helps improve future AI recommendations.
          </p>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why are you rejecting this recommendation?"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
            rows={3}
            disabled={isLoading}
            autoFocus
          />
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!reason.trim() || isLoading}
            className={`
              px-4 py-2 text-sm font-medium rounded-lg transition-colors
              ${reason.trim() && !isLoading
                ? 'bg-gray-700 text-white hover:bg-gray-800'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? 'Rejecting...' : 'Confirm Rejection'}
          </button>
        </div>
      </div>
    </div>
  )
}

// Audit Trail Modal
interface AuditEntry {
  timestamp: string
  source_id: string
  source_type: string
  action: string
  reason?: string
  user_id?: string
  previous_status?: string
}

interface AuditTrailModalProps {
  isOpen: boolean
  entries: AuditEntry[]
  onClose: () => void
}

export function AuditTrailModal({
  isOpen,
  entries,
  onClose,
}: AuditTrailModalProps) {
  if (!isOpen) return null

  const getActionColor = (action: string) => {
    switch (action) {
      case 'approved': return 'text-white bg-gray-900'
      case 'rejected': return 'text-gray-700 bg-gray-200'
      case 'feedback': return 'text-gray-700 bg-gray-100'
      case 'finalized': return 'text-white bg-gray-700'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 flex-shrink-0">
          <h3 className="font-semibold text-gray-900">Audit Trail</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {entries.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">
              No audit entries yet. Actions will appear here as you review recommendations.
            </p>
          ) : (
            <div className="space-y-3">
              {entries.map((entry, i) => (
                <div key={i} className="flex gap-3 pb-3 border-b border-gray-100 last:border-0">
                  <div className={`px-2 py-1 rounded text-xs font-medium capitalize flex-shrink-0 ${getActionColor(entry.action)}`}>
                    {entry.action}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-900 capitalize">{entry.source_type}</span>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-600">{entry.source_id}</span>
                    </div>
                    {entry.reason && (
                      <p className="text-sm text-gray-600 mt-0.5">{entry.reason}</p>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {formatTimestamp(entry.timestamp)}
                      {entry.previous_status && (
                        <span className="ml-2">
                          (was: <span className="capitalize">{entry.previous_status}</span>)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-4 py-3 border-t border-gray-200 bg-gray-50 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium bg-gray-600 text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
