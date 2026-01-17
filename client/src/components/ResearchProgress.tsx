import { FileText, Download, Eye, Loader2, CheckCircle2, Clock, AlertCircle } from 'lucide-react'

interface ResearchReport {
  name: string
  status: 'queued' | 'running' | 'completed' | 'error'
  progress: number
  pages?: number
  sections?: string[]
  analyzing?: string[]
  error?: string
}

interface ResearchProgressProps {
  overallProgress: number
  reports: {
    competitive_landscape?: ResearchReport
    state_of_the_art?: ResearchReport
    regulatory_precedents?: ResearchReport
  }
  error?: string
  onRetry?: () => void
}

export function ResearchProgress({ overallProgress, reports, error, onRetry }: ResearchProgressProps) {
  const reportList = [
    {
      key: 'competitive_landscape',
      title: 'Competitive Landscape Report',
      data: reports.competitive_landscape,
    },
    {
      key: 'state_of_the_art',
      title: 'State of the Art Report',
      data: reports.state_of_the_art,
    },
    {
      key: 'regulatory_precedents',
      title: 'Regulatory Precedents Report',
      data: reports.regulatory_precedents,
    },
  ]

  const hasErrors = reportList.some(r => r.data?.status === 'error') || !!error

  return (
    <div className="space-y-4">
      {/* Overall Error */}
      {error && (
        <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-red-700">{error}</p>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-3 py-1 text-sm font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* Overall Progress */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Deep Research Progress</span>
          <span className={`text-sm font-semibold ${hasErrors ? 'text-gray-500' : 'text-gray-900'}`}>
            {hasErrors ? 'Error' : `${Math.round(overallProgress)}%`}
          </span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              hasErrors ? 'bg-gray-400' : 'bg-gray-900'
            }`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* Report Cards */}
      <div className="space-y-3">
        {reportList.map(({ key, title, data }) => {
          const report = data || { status: 'queued' as const, progress: 0 }
          const isComplete = report.status === 'completed'
          const isRunning = report.status === 'running'
          const isError = report.status === 'error'

          return (
            <div
              key={key}
              className={`
                border rounded-xl p-4 transition-all duration-200
                ${isComplete ? 'bg-gray-50 border-gray-300' :
                  isError ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-200'}
                ${isRunning ? 'ring-2 ring-gray-300' : ''}
              `}
            >
              <div className="flex items-start gap-3">
                <div className={`
                  flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center
                  ${isComplete ? 'bg-gray-900' :
                    isError ? 'bg-gray-200' :
                    isRunning ? 'bg-gray-700' : 'bg-gray-100'}
                `}>
                  {isComplete ? (
                    <CheckCircle2 className="w-5 h-5 text-white" />
                  ) : isError ? (
                    <AlertCircle className="w-5 h-5 text-gray-500" />
                  ) : isRunning ? (
                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                  ) : (
                    <Clock className="w-5 h-5 text-gray-400" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className={`text-sm font-semibold ${isError ? 'text-gray-500' : 'text-gray-900'}`}>{title}</h4>
                    <span className={`
                      text-xs font-medium px-2 py-0.5 rounded-full
                      ${isComplete ? 'bg-gray-900 text-white' :
                        isError ? 'bg-gray-200 text-gray-500' :
                        isRunning ? 'bg-gray-700 text-white' :
                        'bg-gray-100 text-gray-500'}
                    `}>
                      {isComplete ? 'Complete' : isError ? 'Failed' : isRunning ? 'Running' : 'Queued'}
                    </span>
                  </div>

                  {/* Error message */}
                  {isError && report.error && (
                    <p className="mt-1 text-xs text-gray-500">{report.error}</p>
                  )}

                  {/* Progress bar */}
                  <div className="mt-2 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`
                        h-full rounded-full transition-all duration-300
                        ${isComplete ? 'bg-gray-900' : isError ? 'bg-gray-400' : 'bg-gray-700'}
                      `}
                      style={{ width: `${report.progress}%` }}
                    />
                  </div>

                  {/* Analyzing details */}
                  {isRunning && report.analyzing && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">Analyzing:</p>
                      <ul className="mt-1 space-y-0.5">
                        {report.analyzing.slice(0, 3).map((item, i) => (
                          <li key={i} className="text-xs text-gray-600 truncate">
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Complete details */}
                  {isComplete && report.pages && (
                    <div className="mt-2 flex items-center gap-4">
                      <span className="text-xs text-gray-500">{report.pages} pages</span>
                      {report.sections && (
                        <span className="text-xs text-gray-500">{report.sections.length} sections</span>
                      )}
                    </div>
                  )}

                  {/* Action buttons */}
                  {isComplete && (
                    <div className="mt-3 flex gap-2">
                      <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <Eye className="w-3.5 h-3.5" />
                        Preview
                      </button>
                      <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors">
                        <Download className="w-3.5 h-3.5" />
                        Download
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
