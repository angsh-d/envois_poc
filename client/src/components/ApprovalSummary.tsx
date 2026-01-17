import { CheckCircle2, XCircle, Clock, AlertCircle, ArrowRight, Save, History } from 'lucide-react'
import { ApprovalSummary as ApprovalSummaryType } from '../lib/onboardingApi'

interface ApprovalSummaryProps {
  summary: ApprovalSummaryType
  onSaveDraft?: () => void
  onViewAudit?: () => void
  onApproveAndBuild?: () => void
  isLoading?: boolean
}

export function ApprovalSummary({
  summary,
  onSaveDraft,
  onViewAudit,
  onApproveAndBuild,
  isLoading = false,
}: ApprovalSummaryProps) {
  const { approved_count, rejected_count, pending_count, total_sources, can_proceed, minimum_required, by_type } = summary

  // Calculate progress percentage
  const decided = approved_count + rejected_count
  const progressPct = total_sources > 0 ? Math.round((decided / total_sources) * 100) : 0

  return (
    <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
          Approval Summary
        </h3>
      </div>

      {/* Summary Stats */}
      <div className="p-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* Approved */}
          <div className="flex items-center gap-2 p-3 bg-gray-900 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-white" />
            <div>
              <div className="text-lg font-bold text-white">{approved_count}</div>
              <div className="text-xs text-gray-300">Approved</div>
            </div>
          </div>

          {/* Rejected */}
          <div className="flex items-center gap-2 p-3 bg-gray-200 rounded-lg">
            <XCircle className="w-5 h-5 text-gray-600" />
            <div>
              <div className="text-lg font-bold text-gray-700">{rejected_count}</div>
              <div className="text-xs text-gray-500">Rejected</div>
            </div>
          </div>

          {/* Pending */}
          <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg">
            <Clock className="w-5 h-5 text-gray-500" />
            <div>
              <div className="text-lg font-bold text-gray-600">{pending_count}</div>
              <div className="text-xs text-gray-400">Pending</div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Review Progress</span>
            <span>{decided} of {total_sources} decided</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full flex">
              <div
                className="h-full bg-gray-900 transition-all duration-300"
                style={{ width: `${total_sources > 0 ? (approved_count / total_sources) * 100 : 0}%` }}
              />
              <div
                className="h-full bg-gray-400 transition-all duration-300"
                style={{ width: `${total_sources > 0 ? (rejected_count / total_sources) * 100 : 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Breakdown by Type */}
        {Object.keys(by_type).length > 0 && (
          <div className="mb-4 border-t border-gray-100 pt-4">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              By Source Type
            </div>
            <div className="space-y-2">
              {Object.entries(by_type).map(([type, counts]) => (
                <div key={type} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-gray-700">{type}</span>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-gray-900 font-medium">{counts.approved} approved</span>
                    <span className="text-gray-500">{counts.rejected} rejected</span>
                    <span className="text-gray-400">{counts.pending} pending</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Proceed Status */}
        <div className={`flex items-center gap-2 p-3 rounded-lg ${
          can_proceed ? 'bg-gray-900 border border-gray-900' : 'bg-gray-100 border border-gray-200'
        }`}>
          {can_proceed ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-white" />
              <span className="text-sm text-white">
                Ready to proceed! Minimum requirement met ({minimum_required}+ approved).
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="w-5 h-5 text-gray-500" />
              <span className="text-sm text-gray-600">
                At least {minimum_required} source(s) must be approved to proceed.
              </span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onSaveDraft && (
            <button
              onClick={onSaveDraft}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              Save Draft
            </button>
          )}
          {onViewAudit && (
            <button
              onClick={onViewAudit}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
            >
              <History className="w-4 h-4" />
              View Audit Trail
            </button>
          )}
        </div>

        {onApproveAndBuild && (
          <button
            onClick={onApproveAndBuild}
            disabled={!can_proceed || isLoading}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
              ${can_proceed && !isLoading
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Approve & Build
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}

// Compact version for inline display
interface ApprovalBadgeProps {
  summary: ApprovalSummaryType
}

export function ApprovalBadge({ summary }: ApprovalBadgeProps) {
  const { approved_count, rejected_count, pending_count, can_proceed } = summary

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1 text-xs">
        <CheckCircle2 className="w-3.5 h-3.5 text-gray-900" />
        <span className="text-gray-900 font-medium">{approved_count}</span>
      </div>
      <div className="flex items-center gap-1 text-xs">
        <XCircle className="w-3.5 h-3.5 text-gray-500" />
        <span className="text-gray-600 font-medium">{rejected_count}</span>
      </div>
      <div className="flex items-center gap-1 text-xs">
        <Clock className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-gray-500 font-medium">{pending_count}</span>
      </div>
      <div className={`px-2 py-0.5 rounded text-xs font-medium ${
        can_proceed ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'
      }`}>
        {can_proceed ? 'Ready' : 'Pending'}
      </div>
    </div>
  )
}
