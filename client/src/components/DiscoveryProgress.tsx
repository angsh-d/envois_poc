import { BookOpen, Building2, Shield, Users, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import { ConfidenceBadge, ConfidenceLevel } from './ConfidenceBadge'

interface ConfidenceData {
  overall_score: number
  level: ConfidenceLevel
  factors?: Record<string, number>
  explanation?: string
}

interface AgentStatus {
  name: string
  icon: React.ComponentType<{ className?: string }>
  status: 'queued' | 'running' | 'completed' | 'error'
  progress: number
  detail?: string
  error?: string
  confidence?: ConfidenceData
}

interface AgentData {
  status: string
  progress: number
  papers_found?: number
  registries_found?: number
  maude_events?: number
  competitors_identified?: number
  error?: string
  confidence?: ConfidenceData
}

interface DiscoveryProgressProps {
  overallProgress: number
  agents: {
    literature?: AgentData
    registry?: AgentData
    fda?: AgentData
    competitive?: AgentData
  }
  overallConfidence?: ConfidenceData
  error?: string
  onRetry?: () => void
}

export function DiscoveryProgress({ overallProgress, agents, overallConfidence, error, onRetry }: DiscoveryProgressProps) {
  const getAgentStatus = (status?: string, hasError?: string): AgentStatus['status'] => {
    if (hasError) return 'error'
    if (status === 'completed') return 'completed'
    if (status === 'running') return 'running'
    return 'queued'
  }

  const agentList: AgentStatus[] = [
    {
      name: 'Literature Agent',
      icon: BookOpen,
      status: getAgentStatus(agents.literature?.status, agents.literature?.error),
      progress: agents.literature?.progress || 0,
      detail: agents.literature?.papers_found ? `${agents.literature.papers_found} papers` : undefined,
      error: agents.literature?.error,
      confidence: agents.literature?.confidence,
    },
    {
      name: 'Registry Agent',
      icon: Building2,
      status: getAgentStatus(agents.registry?.status, agents.registry?.error),
      progress: agents.registry?.progress || 0,
      detail: agents.registry?.registries_found ? `${agents.registry.registries_found} registries` : undefined,
      error: agents.registry?.error,
      confidence: agents.registry?.confidence,
    },
    {
      name: 'FDA Agent',
      icon: Shield,
      status: getAgentStatus(agents.fda?.status, agents.fda?.error),
      progress: agents.fda?.progress || 0,
      detail: agents.fda?.maude_events ? `${agents.fda.maude_events} events` : undefined,
      error: agents.fda?.error,
      confidence: agents.fda?.confidence,
    },
    {
      name: 'Competitive Agent',
      icon: Users,
      status: getAgentStatus(agents.competitive?.status, agents.competitive?.error),
      progress: agents.competitive?.progress || 0,
      detail: agents.competitive?.competitors_identified ? `${agents.competitive.competitors_identified} competitors` : undefined,
      error: agents.competitive?.error,
      confidence: agents.competitive?.confidence,
    },
  ]

  const hasErrors = agentList.some(a => a.status === 'error') || !!error

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
          <span className="text-sm font-medium text-gray-700">Discovery Progress</span>
          <div className="flex items-center gap-2">
            {overallConfidence && overallProgress >= 100 && (
              <ConfidenceBadge confidence={overallConfidence} size="sm" />
            )}
            <span className={`text-sm font-semibold ${hasErrors ? 'text-gray-500' : 'text-gray-900'}`}>
              {hasErrors ? 'Error' : `${Math.round(overallProgress)}%`}
            </span>
          </div>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              hasErrors ? 'bg-gray-400' : 'bg-gray-900'
            }`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        {overallConfidence && overallProgress >= 100 && overallConfidence.explanation && (
          <p className="mt-2 text-xs text-gray-500">{overallConfidence.explanation}</p>
        )}
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-2 gap-3">
        {agentList.map((agent) => {
          const Icon = agent.icon
          const isComplete = agent.status === 'completed'
          const isRunning = agent.status === 'running'
          const isError = agent.status === 'error'

          return (
            <div
              key={agent.name}
              className={`
                border rounded-xl p-3 transition-all duration-200
                ${isComplete ? 'bg-gray-50 border-gray-300' :
                  isError ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-200'}
                ${isRunning ? 'ring-2 ring-gray-300' : ''}
              `}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center
                  ${isComplete ? 'bg-gray-900' :
                    isError ? 'bg-gray-200' :
                    isRunning ? 'bg-gray-700' : 'bg-gray-100'}
                `}>
                  {isComplete ? (
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  ) : isError ? (
                    <AlertCircle className="w-4 h-4 text-gray-500" />
                  ) : isRunning ? (
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className={`text-xs font-medium truncate ${
                      isError ? 'text-red-700' : 'text-gray-700'
                    }`}>{agent.name}</div>
                    {isComplete && agent.confidence && (
                      <ConfidenceBadge confidence={agent.confidence} size="sm" showScore />
                    )}
                  </div>
                  {isError && agent.error ? (
                    <div className="text-xs text-red-500 truncate">{agent.error}</div>
                  ) : agent.detail && (
                    <div className="text-xs text-gray-500">{agent.detail}</div>
                  )}
                </div>
              </div>
              <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`
                    h-full rounded-full transition-all duration-300
                    ${isComplete ? 'bg-gray-900' : isError ? 'bg-gray-400' : 'bg-gray-700'}
                  `}
                  style={{ width: `${agent.progress}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
