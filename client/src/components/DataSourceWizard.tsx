import { useState } from 'react'
import {
  ChevronRight,
  Check,
  X,
  BookOpen,
  Shield,
  BarChart3,
  Building2,
  Sparkles,
  Info,
  AlertCircle,
  FlaskConical,
  FileText,
  Search,
  Edit3,
  Plus,
  Trash2,
  FolderOpen,
  Database,
  Loader2,
} from 'lucide-react'
import { ApprovalStatus } from '../lib/onboardingApi'
import {
  FolderContents,
  StudyDataAnalysis,
  ProtocolAnalysis,
  LiteratureAnalysis,
  ExtractedJsonAnalysis
} from './LocalDataConfig'

// Step definition
interface WizardStep {
  id: string
  title: string
  subtitle: string
  icon: React.ReactNode
  type: 'local_data' | 'clinical' | 'registry' | 'literature' | 'fda' | 'competitive' | 'clinical_trials_search' | 'fda_submissions_search'
  isSearchPanel?: boolean
  isLocalDataPanel?: boolean
}

const WIZARD_STEPS: WizardStep[] = [
  {
    id: 'local_data',
    title: 'Local Data',
    subtitle: 'Study files & protocol',
    icon: <FolderOpen className="w-4 h-4" />,
    type: 'local_data',
    isLocalDataPanel: true,
  },
  {
    id: 'registries',
    title: 'Registries',
    subtitle: 'External benchmarks',
    icon: <BarChart3 className="w-4 h-4" />,
    type: 'registry',
  },
  {
    id: 'literature',
    title: 'Literature',
    subtitle: 'Published evidence',
    icon: <BookOpen className="w-4 h-4" />,
    type: 'literature',
  },
  {
    id: 'competitive',
    title: 'Competitive',
    subtitle: 'Market landscape',
    icon: <Building2 className="w-4 h-4" />,
    type: 'competitive',
  },
  {
    id: 'fda',
    title: 'FDA Surveillance',
    subtitle: 'Regulatory data',
    icon: <Shield className="w-4 h-4" />,
    type: 'fda',
  },
  {
    id: 'clinical_trials_search',
    title: 'ClinicalTrials.gov',
    subtitle: 'Trial registry',
    icon: <FlaskConical className="w-4 h-4" />,
    type: 'clinical_trials_search',
    isSearchPanel: true,
  },
  {
    id: 'fda_submissions_search',
    title: 'FDA Submissions',
    subtitle: '510(k) & MAUDE',
    icon: <FileText className="w-4 h-4" />,
    type: 'fda_submissions_search',
    isSearchPanel: true,
  },
]

// Search parameter types
interface CTSearchParams {
  ownTrials: {
    sponsor: string
    condition: string
    intervention: string
    phases: string[]
    status: string[]
    dateRange: { start: string; end: string }
  }
  competitorTrials: {
    sponsors: string[]
    condition: string
    intervention: string
    phases: string[]
    dateRange: { start: string; end: string }
  }
}

interface FDASearchParams {
  ownSubmissions: {
    applicant: string
    productCodes: string[]
    decisionDateRange: { start: string; end: string }
  }
  competitorSubmissions: {
    applicants: string[]
    productCodes: string[]
    decisionDateRange: { start: string; end: string }
  }
}

interface SourceRecommendation {
  id: string
  name: string
  type: 'local_data' | 'local_study_data' | 'local_protocol' | 'local_literature' | 'local_extracted' | 'clinical' | 'registry' | 'literature' | 'fda' | 'competitive' | 'clinical_trials' | 'earlier_phase_fda' | 'competitor_trials' | 'competitor_fda'
  status: ApprovalStatus
  description: string
  preview?: string
  confidence: number
  whyRecommended: string
  keyReasons: string[]
  enabledInsights: string[]
  aiRecommended: boolean
  rejectionReason?: string
  metadata?: Record<string, unknown>
}

interface SearchResults {
  ctOwnTrials: { count: number; trials: Array<{ nctId: string; title: string; phase: string; status: string }> }
  ctCompetitorTrials: { count: number; trials: Array<{ nctId: string; title: string; sponsor: string; phase: string }> }
  fdaOwnSubmissions: { count: number; submissions: Array<{ kNumber: string; deviceName: string; decisionDate: string }> }
  fdaCompetitorSubmissions: { count: number; submissions: Array<{ kNumber: string; applicant: string; deviceName: string }> }
}

interface DataSourceWizardProps {
  recommendations: SourceRecommendation[]
  onApprove: (sourceId: string, sourceType: string) => void
  onReject: (sourceId: string, sourceType: string, name: string) => void
  onComplete: () => void
  isLoading?: boolean
  approvalSummary?: {
    approved: number
    rejected: number
    pending: number
    total: number
    canProceed: boolean
  }
  folderContents?: FolderContents | null
  folderPath?: string
  productContext?: {
    productName: string
    manufacturer: string
    category: string
    indication: string
    studyPhase: string
    competitors: string[]
    fdaProductCodes: string[]
  }
  onSearchClinicalTrials?: (params: CTSearchParams) => Promise<SearchResults['ctOwnTrials'] | SearchResults['ctCompetitorTrials']>
  onSearchFDASubmissions?: (params: FDASearchParams) => Promise<SearchResults['fdaOwnSubmissions'] | SearchResults['fdaCompetitorSubmissions']>
}

export function DataSourceWizard({
  recommendations,
  onApprove,
  onReject,
  onComplete,
  isLoading = false,
  approvalSummary,
  folderContents,
  folderPath,
  productContext,
  onSearchClinicalTrials,
  onSearchFDASubmissions,
}: DataSourceWizardProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const currentStep = WIZARD_STEPS[currentStepIndex]

  // Search state
  const [ctSearchParams, setCtSearchParams] = useState<CTSearchParams>({
    ownTrials: {
      sponsor: productContext?.manufacturer || '',
      condition: productContext?.indication || '',
      intervention: productContext?.productName || '',
      phases: productContext?.studyPhase === 'Phase 4' ? ['Phase 1', 'Phase 2', 'Phase 3'] : [],
      status: ['Completed', 'Active, not recruiting', 'Recruiting'],
      dateRange: { start: '2015-01-01', end: new Date().toISOString().split('T')[0] },
    },
    competitorTrials: {
      sponsors: productContext?.competitors || [],
      condition: productContext?.indication || '',
      intervention: productContext?.category || '',
      phases: ['Phase 2', 'Phase 3', 'Phase 4'],
      dateRange: { start: '2015-01-01', end: new Date().toISOString().split('T')[0] },
    },
  })

  const [fdaSearchParams, setFdaSearchParams] = useState<FDASearchParams>({
    ownSubmissions: {
      applicant: productContext?.manufacturer || '',
      productCodes: productContext?.fdaProductCodes || [],
      decisionDateRange: { start: '2010-01-01', end: new Date().toISOString().split('T')[0] },
    },
    competitorSubmissions: {
      applicants: productContext?.competitors || [],
      productCodes: productContext?.fdaProductCodes || [],
      decisionDateRange: { start: '2015-01-01', end: new Date().toISOString().split('T')[0] },
    },
  })

  const [ctSearchResults, setCtSearchResults] = useState<{
    ownTrials: SearchResults['ctOwnTrials'] | null
    competitorTrials: SearchResults['ctCompetitorTrials'] | null
  }>({ ownTrials: null, competitorTrials: null })

  const [fdaSearchResults, setFdaSearchResults] = useState<{
    ownSubmissions: SearchResults['fdaOwnSubmissions'] | null
    competitorSubmissions: SearchResults['fdaCompetitorSubmissions'] | null
  }>({ ownSubmissions: null, competitorSubmissions: null })

  const [searchLoading, setSearchLoading] = useState<{
    ctOwn: boolean
    ctCompetitor: boolean
    fdaOwn: boolean
    fdaCompetitor: boolean
  }>({ ctOwn: false, ctCompetitor: false, fdaOwn: false, fdaCompetitor: false })

  // Get recommendation types for step
  const getRecommendationTypes = (stepType: string): string[] => {
    if (stepType === 'local_data') {
      return ['local_data', 'local_study_data', 'local_protocol', 'local_literature', 'local_extracted']
    }
    if (stepType === 'clinical_trials_search') {
      return ['clinical_trials', 'competitor_trials']
    }
    if (stepType === 'fda_submissions_search') {
      return ['earlier_phase_fda', 'competitor_fda']
    }
    return [stepType]
  }

  const stepRecommendationTypes = getRecommendationTypes(currentStep.type)
  const stepRecommendations = recommendations.filter(r => stepRecommendationTypes.includes(r.type))
  const recommendedSources = stepRecommendations.filter(r => r.aiRecommended)
  const alternativeSources = stepRecommendations.filter(r => !r.aiRecommended)

  // Calculate step status
  const getStepStatus = (step: WizardStep) => {
    const types = getRecommendationTypes(step.type)
    const stepRecs = recommendations.filter(r => types.includes(r.type))
    const decided = stepRecs.filter(r => r.status !== 'pending').length
    const approved = stepRecs.filter(r => r.status === 'approved').length
    if (stepRecs.length === 0) return { status: 'empty', count: 0 }
    if (decided === 0) return { status: 'pending', count: stepRecs.length }
    if (decided === stepRecs.length) return { status: 'complete', count: approved }
    return { status: 'partial', count: approved }
  }

  const isLastStep = currentStepIndex === WIZARD_STEPS.length - 1

  return (
    <div className="flex h-[calc(100vh-200px)] min-h-[600px] bg-white rounded-2xl border border-neutral-200 overflow-hidden">
      {/* Side Navigation */}
      <div className="w-64 bg-neutral-50/80 border-r border-neutral-200 flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-neutral-200">
          <h2 className="text-sm font-semibold text-neutral-900">Review Sources</h2>
          {approvalSummary && (
            <div className="flex items-center gap-3 mt-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-neutral-500">{approvalSummary.approved}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                <span className="text-xs text-neutral-500">{approvalSummary.rejected}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-neutral-300" />
                <span className="text-xs text-neutral-500">{approvalSummary.pending}</span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {WIZARD_STEPS.map((step, idx) => {
            const stepStatus = getStepStatus(step)
            const isActive = idx === currentStepIndex

            return (
              <button
                key={step.id}
                onClick={() => setCurrentStepIndex(idx)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all
                  ${isActive
                    ? 'bg-neutral-900 text-white shadow-sm'
                    : 'text-neutral-600 hover:bg-neutral-100'
                  }
                `}
              >
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                  ${isActive
                    ? 'bg-white/20'
                    : stepStatus.status === 'complete'
                      ? 'bg-emerald-100'
                      : 'bg-neutral-200/80'
                  }
                `}>
                  {stepStatus.status === 'complete' && !isActive ? (
                    <Check className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <span className={isActive ? 'text-white' : 'text-neutral-500'}>{step.icon}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${isActive ? 'text-white' : 'text-neutral-800'}`}>
                    {step.title}
                  </p>
                  <p className={`text-xs truncate ${isActive ? 'text-white/60' : 'text-neutral-400'}`}>
                    {stepStatus.status === 'complete'
                      ? `${stepStatus.count} approved`
                      : stepStatus.status === 'empty'
                        ? 'No sources'
                        : step.subtitle
                    }
                  </p>
                </div>
                {stepStatus.status === 'pending' && stepStatus.count > 0 && !isActive && (
                  <span className="w-5 h-5 rounded-full bg-neutral-200 text-neutral-600 text-xs font-medium flex items-center justify-center">
                    {stepStatus.count}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Complete Button */}
        <div className="p-4 border-t border-neutral-200">
          <button
            onClick={onComplete}
            disabled={isLoading || !approvalSummary?.canProceed}
            className={`
              w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all
              ${approvalSummary?.canProceed && !isLoading
                ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                : 'bg-neutral-100 text-neutral-400 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Start Research
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Local Data Panel */}
          {currentStep.type === 'local_data' && (
            <LocalDataPanel
              folderContents={folderContents}
              folderPath={folderPath}
              recommendations={stepRecommendations}
              onApprove={onApprove}
              onReject={onReject}
              isLoading={isLoading}
            />
          )}

          {/* ClinicalTrials Search Panel */}
          {currentStep.type === 'clinical_trials_search' && (
            <ClinicalTrialsSearchPanel
              params={ctSearchParams}
              onParamsChange={setCtSearchParams}
              results={ctSearchResults}
              loading={searchLoading}
              onSearch={async (type) => {
                if (!onSearchClinicalTrials) return
                if (type === 'own') {
                  setSearchLoading(prev => ({ ...prev, ctOwn: true }))
                  try {
                    const result = await onSearchClinicalTrials(ctSearchParams)
                    setCtSearchResults(prev => ({ ...prev, ownTrials: result as SearchResults['ctOwnTrials'] }))
                  } finally {
                    setSearchLoading(prev => ({ ...prev, ctOwn: false }))
                  }
                } else {
                  setSearchLoading(prev => ({ ...prev, ctCompetitor: true }))
                  try {
                    const result = await onSearchClinicalTrials(ctSearchParams)
                    setCtSearchResults(prev => ({ ...prev, competitorTrials: result as SearchResults['ctCompetitorTrials'] }))
                  } finally {
                    setSearchLoading(prev => ({ ...prev, ctCompetitor: false }))
                  }
                }
              }}
              recommendations={stepRecommendations}
              onApprove={onApprove}
              onReject={onReject}
              isLoading={isLoading}
            />
          )}

          {/* FDA Submissions Search Panel */}
          {currentStep.type === 'fda_submissions_search' && (
            <FDASubmissionsSearchPanel
              params={fdaSearchParams}
              onParamsChange={setFdaSearchParams}
              results={fdaSearchResults}
              loading={searchLoading}
              onSearch={async (type) => {
                if (!onSearchFDASubmissions) return
                if (type === 'own') {
                  setSearchLoading(prev => ({ ...prev, fdaOwn: true }))
                  try {
                    const result = await onSearchFDASubmissions(fdaSearchParams)
                    setFdaSearchResults(prev => ({ ...prev, ownSubmissions: result as SearchResults['fdaOwnSubmissions'] }))
                  } finally {
                    setSearchLoading(prev => ({ ...prev, fdaOwn: false }))
                  }
                } else {
                  setSearchLoading(prev => ({ ...prev, fdaCompetitor: true }))
                  try {
                    const result = await onSearchFDASubmissions(fdaSearchParams)
                    setFdaSearchResults(prev => ({ ...prev, competitorSubmissions: result as SearchResults['fdaCompetitorSubmissions'] }))
                  } finally {
                    setSearchLoading(prev => ({ ...prev, fdaCompetitor: false }))
                  }
                }
              }}
              recommendations={stepRecommendations}
              onApprove={onApprove}
              onReject={onReject}
              isLoading={isLoading}
            />
          )}

          {/* Standard Source Cards */}
          {!currentStep.isSearchPanel && !currentStep.isLocalDataPanel && (
            <div className="space-y-6">
              {/* AI Recommended */}
              {recommendedSources.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="w-4 h-4 text-neutral-400" />
                    <h3 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">AI Recommended</h3>
                  </div>
                  <div className="space-y-3">
                    {recommendedSources.map((rec) => (
                      <SourceCard
                        key={rec.id}
                        recommendation={rec}
                        onApprove={() => onApprove(rec.id, rec.type)}
                        onReject={() => onReject(rec.id, rec.type, rec.name)}
                        isLoading={isLoading}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Alternatives */}
              {alternativeSources.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <AlertCircle className="w-4 h-4 text-neutral-400" />
                    <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Alternatives</h3>
                  </div>
                  <div className="space-y-3">
                    {alternativeSources.map((rec) => (
                      <SourceCard
                        key={rec.id}
                        recommendation={rec}
                        onApprove={() => onApprove(rec.id, rec.type)}
                        onReject={() => onReject(rec.id, rec.type, rec.name)}
                        isLoading={isLoading}
                        isAlternative
                      />
                    ))}
                  </div>
                </div>
              )}

              {stepRecommendations.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-neutral-400">
                  <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mb-4">
                    <AlertCircle className="w-6 h-6" />
                  </div>
                  <p className="text-sm">No sources found for {currentStep.title.toLowerCase()}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 border-t border-neutral-100 bg-neutral-50/50 flex items-center justify-between">
          <button
            onClick={() => setCurrentStepIndex(i => Math.max(0, i - 1))}
            disabled={currentStepIndex === 0 || isLoading}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${currentStepIndex > 0 && !isLoading
                ? 'text-neutral-600 hover:bg-neutral-100'
                : 'text-neutral-300 cursor-not-allowed'
              }
            `}
          >
            Previous
          </button>

          <div className="flex items-center gap-1">
            {WIZARD_STEPS.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentStepIndex(idx)}
                className={`
                  w-2 h-2 rounded-full transition-all
                  ${idx === currentStepIndex
                    ? 'bg-neutral-900 w-6'
                    : 'bg-neutral-300 hover:bg-neutral-400'
                  }
                `}
              />
            ))}
          </div>

          <button
            onClick={() => setCurrentStepIndex(i => Math.min(WIZARD_STEPS.length - 1, i + 1))}
            disabled={isLastStep || isLoading}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${!isLastStep && !isLoading
                ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                : 'bg-neutral-100 text-neutral-400 cursor-not-allowed'
              }
            `}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Source Card Component
// ============================================================================

interface SourceCardProps {
  recommendation: SourceRecommendation
  onApprove: () => void
  onReject: () => void
  isLoading?: boolean
  isAlternative?: boolean
}

function SourceCard({ recommendation, onApprove, onReject, isLoading, isAlternative = false }: SourceCardProps) {
  const [expanded, setExpanded] = useState(recommendation.status === 'pending' && !isAlternative)

  const getStatusStyle = () => {
    if (recommendation.status === 'approved') {
      return { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700' }
    }
    if (recommendation.status === 'rejected') {
      return { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-700' }
    }
    if (isAlternative) {
      return { bg: 'bg-neutral-50', border: 'border-dashed border-neutral-300', badge: 'bg-amber-100 text-amber-700' }
    }
    return { bg: 'bg-white', border: 'border-neutral-200', badge: 'bg-neutral-100 text-neutral-600' }
  }

  const style = getStatusStyle()

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} overflow-hidden transition-all`}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold text-neutral-900 truncate">{recommendation.name}</h4>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${style.badge}`}>
                {recommendation.status === 'approved' ? 'Approved' :
                 recommendation.status === 'rejected' ? 'Rejected' :
                 isAlternative ? 'Alternative' : 'Review'}
              </span>
            </div>
            <p className="text-sm text-neutral-500 line-clamp-2">{recommendation.description}</p>
          </div>

          {/* Actions */}
          {recommendation.status === 'pending' && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={onReject}
                disabled={isLoading}
                className="w-8 h-8 rounded-lg border border-neutral-200 bg-white flex items-center justify-center text-neutral-400 hover:text-red-500 hover:border-red-200 transition-all disabled:opacity-50"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="w-8 h-8 rounded-lg bg-neutral-900 text-white flex items-center justify-center hover:bg-neutral-800 transition-all disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Confidence & Toggle */}
        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 bg-neutral-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${recommendation.confidence >= 0.8 ? 'bg-emerald-500' : recommendation.confidence >= 0.6 ? 'bg-amber-500' : 'bg-neutral-400'}`}
                style={{ width: `${recommendation.confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-neutral-400">{Math.round(recommendation.confidence * 100)}%</span>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-neutral-500 hover:text-neutral-700"
          >
            {expanded ? 'Hide details' : 'Show details'}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 pt-3 border-t border-neutral-100 space-y-4">
          {/* Why Recommended */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-neutral-400" />
              <span className="text-xs font-medium text-neutral-500 uppercase tracking-wider">
                {isAlternative ? 'Potential Value' : 'Why Recommended'}
              </span>
            </div>
            <p className="text-sm text-neutral-600">{recommendation.whyRecommended}</p>
            {recommendation.keyReasons.length > 0 && (
              <ul className="mt-2 space-y-1">
                {recommendation.keyReasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-neutral-600">
                    <Check className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Enabled Insights */}
          {recommendation.enabledInsights.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Info className="w-3.5 h-3.5 text-neutral-400" />
                <span className="text-xs font-medium text-neutral-500 uppercase tracking-wider">Enables Insights</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {recommendation.enabledInsights.map((insight, i) => (
                  <span key={i} className="px-2 py-1 bg-neutral-100 text-neutral-600 rounded text-xs">
                    {insight}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Local Data Panel
// ============================================================================

interface LocalDataPanelProps {
  folderContents?: FolderContents | null
  folderPath?: string
  recommendations: SourceRecommendation[]
  onApprove: (sourceId: string, sourceType: string) => void
  onReject: (sourceId: string, sourceType: string, name: string) => void
  isLoading: boolean
}

function LocalDataPanel({
  folderContents,
  folderPath,
  recommendations,
  onApprove,
  onReject,
  isLoading,
}: LocalDataPanelProps) {
  if (!folderContents?.validated) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-neutral-400">
        <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mb-4">
          <FolderOpen className="w-6 h-6" />
        </div>
        <p className="text-sm mb-2">No folder configured</p>
        <p className="text-xs text-neutral-400">Configure a study data folder to see local sources</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Source Path */}
      <div className="flex items-center gap-3 px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200">
        <FolderOpen className="w-5 h-5 text-neutral-400" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-neutral-400 uppercase tracking-wider">Source Folder</p>
          <p className="text-sm text-neutral-700 font-medium truncate">{folderPath}</p>
        </div>
      </div>

      {/* Study Data Files */}
      {folderContents.studyData.count > 0 && (
        <LocalSourceSection
          title="Study Data Files"
          count={folderContents.studyData.count}
          icon={<Database className="w-4 h-4" />}
        >
          {folderContents.studyData.analysis?.map((analysis, idx) => (
            <StudyDataCard key={idx} analysis={analysis} />
          )) || folderContents.studyData.files.map((file, idx) => (
            <div key={idx} className="p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm font-medium text-neutral-700">{file}</p>
            </div>
          ))}
        </LocalSourceSection>
      )}

      {/* Protocol */}
      {folderContents.protocol.found && (
        <LocalSourceSection
          title="Protocol Document"
          count={1}
          icon={<FileText className="w-4 h-4" />}
        >
          {folderContents.protocol.analysis ? (
            <ProtocolCard analysis={folderContents.protocol.analysis} />
          ) : (
            <div className="p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm font-medium text-neutral-700">{folderContents.protocol.file}</p>
            </div>
          )}
        </LocalSourceSection>
      )}

      {/* Literature */}
      {folderContents.literature.count > 0 && (
        <LocalSourceSection
          title="Literature PDFs"
          count={folderContents.literature.count}
          icon={<BookOpen className="w-4 h-4" />}
        >
          {folderContents.literature.analysis?.map((analysis, idx) => (
            <LiteratureCard key={idx} analysis={analysis} />
          )) || folderContents.literature.files.map((file, idx) => (
            <div key={idx} className="p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm font-medium text-neutral-700">{file}</p>
            </div>
          ))}
        </LocalSourceSection>
      )}

      {/* Extracted JSON */}
      {folderContents.extractedJson.count > 0 && (
        <LocalSourceSection
          title="Extracted Data"
          count={folderContents.extractedJson.count}
          icon={<FileText className="w-4 h-4" />}
        >
          {folderContents.extractedJson.analysis?.map((analysis, idx) => (
            <ExtractedJsonCard key={idx} analysis={analysis} />
          )) || folderContents.extractedJson.files.map((file, idx) => (
            <div key={idx} className="p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm font-medium text-neutral-700">{file}</p>
            </div>
          ))}
        </LocalSourceSection>
      )}
    </div>
  )
}

// Local Source Section wrapper
interface LocalSourceSectionProps {
  title: string
  count: number
  icon: React.ReactNode
  children: React.ReactNode
}

function LocalSourceSection({ title, count, icon, children }: LocalSourceSectionProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="border border-neutral-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-neutral-50/50 hover:bg-neutral-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-neutral-900 flex items-center justify-center text-white">
            {icon}
          </div>
          <div className="text-left">
            <h4 className="text-sm font-semibold text-neutral-900">{title}</h4>
            <p className="text-xs text-neutral-500">{count} {count === 1 ? 'file' : 'files'} found</p>
          </div>
        </div>
        <ChevronRight className={`w-5 h-5 text-neutral-400 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      {expanded && (
        <div className="p-4 space-y-3 border-t border-neutral-100">
          {children}
        </div>
      )}
    </div>
  )
}

// Study Data Analysis Card
function StudyDataCard({ analysis }: { analysis: StudyDataAnalysis }) {
  return (
    <div className="p-4 bg-white border border-neutral-200 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-neutral-400" />
          <h5 className="text-sm font-semibold text-neutral-900">{analysis.fileName}</h5>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-medium rounded">
            {analysis.rows} rows
          </span>
          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded">
            {analysis.columns} cols
          </span>
        </div>
      </div>

      {/* Key Insights */}
      {analysis.keyInsights && analysis.keyInsights.length > 0 && (
        <div className="space-y-1.5 mb-3">
          {analysis.keyInsights.map((insight, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-neutral-600">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
              <span>{insight}</span>
            </div>
          ))}
        </div>
      )}

      {/* Date Range */}
      {analysis.dateRange && (
        <p className="text-xs text-neutral-400 mb-3">
          Date range: {analysis.dateRange.start} to {analysis.dateRange.end}
        </p>
      )}

      {/* Column Pills */}
      <div className="flex flex-wrap gap-1.5">
        {analysis.columnNames.slice(0, 6).map((col, i) => (
          <span key={i} className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded">
            {col}
          </span>
        ))}
        {analysis.columnNames.length > 6 && (
          <span className="px-2 py-1 text-neutral-400 text-xs">
            +{analysis.columnNames.length - 6} more
          </span>
        )}
      </div>
    </div>
  )
}

// Protocol Analysis Card
function ProtocolCard({ analysis }: { analysis: ProtocolAnalysis }) {
  return (
    <div className="p-4 bg-white border border-neutral-200 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <h5 className="text-sm font-semibold text-neutral-900 mb-1">{analysis.fileName}</h5>
          <p className="text-sm text-neutral-600 line-clamp-2">{analysis.studyTitle || 'Protocol Document'}</p>
        </div>
        <span className="px-2 py-0.5 bg-neutral-100 text-neutral-600 text-xs font-medium rounded flex-shrink-0">
          {analysis.pages} pages
        </span>
      </div>

      {analysis.studyPhase && (
        <span className="inline-block px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded mb-3">
          {analysis.studyPhase}
        </span>
      )}

      {analysis.extractedSections && analysis.extractedSections.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {analysis.extractedSections.slice(0, 5).map((section, i) => (
            <span key={i} className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded">
              {section}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// Literature Analysis Card
function LiteratureCard({ analysis }: { analysis: LiteratureAnalysis }) {
  return (
    <div className="p-4 bg-white border border-neutral-200 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-2">
        <h5 className="text-sm font-semibold text-neutral-900 line-clamp-2">{analysis.title || analysis.fileName}</h5>
        <div className="flex items-center gap-2 flex-shrink-0">
          {analysis.year > 0 && (
            <span className="px-2 py-0.5 bg-neutral-100 text-neutral-600 text-xs font-medium rounded">
              {analysis.year}
            </span>
          )}
        </div>
      </div>
      {analysis.authors && (
        <p className="text-xs text-neutral-500 mb-2">{analysis.authors}</p>
      )}
      <div className="flex items-center gap-3 text-xs text-neutral-400">
        <span>{analysis.pages} pages</span>
        {analysis.relevanceScore > 0 && (
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${analysis.relevanceScore >= 0.8 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            {Math.round(analysis.relevanceScore * 100)}% relevant
          </span>
        )}
      </div>
    </div>
  )
}

// Extracted JSON Card
function ExtractedJsonCard({ analysis }: { analysis: ExtractedJsonAnalysis }) {
  return (
    <div className="p-4 bg-white border border-neutral-200 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-2">
        <h5 className="text-sm font-semibold text-neutral-900">{analysis.fileName}</h5>
        <span className="px-2 py-0.5 bg-violet-100 text-violet-700 text-xs font-medium rounded">
          {analysis.schemaType}
        </span>
      </div>
      <p className="text-xs text-neutral-500 mb-2">{analysis.recordCount} records</p>
      {analysis.keyFields.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {analysis.keyFields.slice(0, 4).map((field, i) => (
            <span key={i} className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded">
              {field}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// ClinicalTrials.gov Search Panel
// ============================================================================

interface ClinicalTrialsSearchPanelProps {
  params: CTSearchParams
  onParamsChange: (params: CTSearchParams) => void
  results: {
    ownTrials: SearchResults['ctOwnTrials'] | null
    competitorTrials: SearchResults['ctCompetitorTrials'] | null
  }
  loading: { ctOwn: boolean; ctCompetitor: boolean; fdaOwn: boolean; fdaCompetitor: boolean }
  onSearch: (type: 'own' | 'competitor') => void
  recommendations: SourceRecommendation[]
  onApprove: (sourceId: string, sourceType: string) => void
  onReject: (sourceId: string, sourceType: string, name: string) => void
  isLoading: boolean
}

function ClinicalTrialsSearchPanel({
  params,
  onParamsChange,
  results,
  loading,
  onSearch,
  recommendations,
  onApprove,
  onReject,
  isLoading,
}: ClinicalTrialsSearchPanelProps) {
  const [editingOwn, setEditingOwn] = useState(false)
  const [editingCompetitor, setEditingCompetitor] = useState(false)
  const [newCompetitor, setNewCompetitor] = useState('')

  const ownTrialsRec = recommendations.find(r => r.type === 'clinical_trials')
  const competitorTrialsRec = recommendations.find(r => r.type === 'competitor_trials')

  return (
    <div className="space-y-6">
      {/* Own Trials */}
      <SearchSection
        title="Own Prior Phase Trials"
        subtitle="Earlier phase studies from your organization"
        icon={<FlaskConical className="w-4 h-4" />}
        recommendation={ownTrialsRec}
        onApprove={() => ownTrialsRec && onApprove(ownTrialsRec.id, ownTrialsRec.type)}
        onReject={() => ownTrialsRec && onReject(ownTrialsRec.id, ownTrialsRec.type, ownTrialsRec.name)}
        isLoading={isLoading}
      >
        <div className="grid grid-cols-2 gap-4">
          <SearchField label="Sponsor" value={params.ownTrials.sponsor} editing={editingOwn}
            onChange={(v) => onParamsChange({ ...params, ownTrials: { ...params.ownTrials, sponsor: v } })} />
          <SearchField label="Condition" value={params.ownTrials.condition} editing={editingOwn}
            onChange={(v) => onParamsChange({ ...params, ownTrials: { ...params.ownTrials, condition: v } })} />
          <SearchField label="Intervention" value={params.ownTrials.intervention} editing={editingOwn}
            onChange={(v) => onParamsChange({ ...params, ownTrials: { ...params.ownTrials, intervention: v } })} />
          <div>
            <label className="text-xs text-neutral-400 block mb-1">Phases</label>
            <div className="flex flex-wrap gap-1.5">
              {['Phase 1', 'Phase 2', 'Phase 3'].map((phase) => (
                <button
                  key={phase}
                  onClick={() => {
                    if (!editingOwn) return
                    const phases = params.ownTrials.phases.includes(phase)
                      ? params.ownTrials.phases.filter(p => p !== phase)
                      : [...params.ownTrials.phases, phase]
                    onParamsChange({ ...params, ownTrials: { ...params.ownTrials, phases } })
                  }}
                  className={`px-2 py-1 text-xs rounded transition-all ${
                    params.ownTrials.phases.includes(phase)
                      ? 'bg-neutral-900 text-white'
                      : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                  } ${!editingOwn ? 'cursor-default' : ''}`}
                >
                  {phase}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setEditingOwn(!editingOwn)}
            className="text-xs text-neutral-500 hover:text-neutral-700 flex items-center gap-1"
          >
            <Edit3 className="w-3 h-3" />
            {editingOwn ? 'Done' : 'Edit Parameters'}
          </button>
          <button
            onClick={() => onSearch('own')}
            disabled={loading.ctOwn}
            className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 text-white text-xs font-medium rounded-lg hover:bg-neutral-800 disabled:opacity-50"
          >
            {loading.ctOwn ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
            {loading.ctOwn ? 'Searching...' : 'Search'}
          </button>
        </div>
        {results.ownTrials && (
          <div className="mt-4 p-3 bg-emerald-50 rounded-lg">
            <p className="text-sm font-medium text-emerald-700">{results.ownTrials.count} trials found</p>
          </div>
        )}
      </SearchSection>

      {/* Competitor Trials */}
      <SearchSection
        title="Competitor Trials"
        subtitle="Clinical trials from competitor organizations"
        icon={<Building2 className="w-4 h-4" />}
        recommendation={competitorTrialsRec}
        onApprove={() => competitorTrialsRec && onApprove(competitorTrialsRec.id, competitorTrialsRec.type)}
        onReject={() => competitorTrialsRec && onReject(competitorTrialsRec.id, competitorTrialsRec.type, competitorTrialsRec.name)}
        isLoading={isLoading}
      >
        <div className="space-y-4">
          <div>
            <label className="text-xs text-neutral-400 block mb-2">Competitor Sponsors</label>
            <div className="flex flex-wrap gap-2">
              {params.competitorTrials.sponsors.map((sponsor, idx) => (
                <span key={idx} className="flex items-center gap-1.5 px-2 py-1 bg-neutral-100 text-neutral-700 text-xs rounded">
                  {sponsor}
                  {editingCompetitor && (
                    <button
                      onClick={() => {
                        const sponsors = params.competitorTrials.sponsors.filter((_, i) => i !== idx)
                        onParamsChange({ ...params, competitorTrials: { ...params.competitorTrials, sponsors } })
                      }}
                      className="text-neutral-400 hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </span>
              ))}
              {editingCompetitor && (
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    value={newCompetitor}
                    onChange={(e) => setNewCompetitor(e.target.value)}
                    placeholder="Add competitor..."
                    className="w-32 px-2 py-1 text-xs border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-neutral-400"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newCompetitor.trim()) {
                        onParamsChange({
                          ...params,
                          competitorTrials: {
                            ...params.competitorTrials,
                            sponsors: [...params.competitorTrials.sponsors, newCompetitor.trim()]
                          }
                        })
                        setNewCompetitor('')
                      }
                    }}
                  />
                  <button
                    onClick={() => {
                      if (newCompetitor.trim()) {
                        onParamsChange({
                          ...params,
                          competitorTrials: {
                            ...params.competitorTrials,
                            sponsors: [...params.competitorTrials.sponsors, newCompetitor.trim()]
                          }
                        })
                        setNewCompetitor('')
                      }
                    }}
                    className="p-1 text-neutral-400 hover:text-neutral-600"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <SearchField label="Condition" value={params.competitorTrials.condition} editing={editingCompetitor}
              onChange={(v) => onParamsChange({ ...params, competitorTrials: { ...params.competitorTrials, condition: v } })} />
            <SearchField label="Intervention" value={params.competitorTrials.intervention} editing={editingCompetitor}
              onChange={(v) => onParamsChange({ ...params, competitorTrials: { ...params.competitorTrials, intervention: v } })} />
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setEditingCompetitor(!editingCompetitor)}
            className="text-xs text-neutral-500 hover:text-neutral-700 flex items-center gap-1"
          >
            <Edit3 className="w-3 h-3" />
            {editingCompetitor ? 'Done' : 'Edit Parameters'}
          </button>
          <button
            onClick={() => onSearch('competitor')}
            disabled={loading.ctCompetitor}
            className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 text-white text-xs font-medium rounded-lg hover:bg-neutral-800 disabled:opacity-50"
          >
            {loading.ctCompetitor ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
            {loading.ctCompetitor ? 'Searching...' : 'Search'}
          </button>
        </div>
        {results.competitorTrials && (
          <div className="mt-4 p-3 bg-emerald-50 rounded-lg">
            <p className="text-sm font-medium text-emerald-700">{results.competitorTrials.count} trials found</p>
          </div>
        )}
      </SearchSection>
    </div>
  )
}

// ============================================================================
// FDA Submissions Search Panel
// ============================================================================

interface FDASubmissionsSearchPanelProps {
  params: FDASearchParams
  onParamsChange: (params: FDASearchParams) => void
  results: {
    ownSubmissions: SearchResults['fdaOwnSubmissions'] | null
    competitorSubmissions: SearchResults['fdaCompetitorSubmissions'] | null
  }
  loading: { ctOwn: boolean; ctCompetitor: boolean; fdaOwn: boolean; fdaCompetitor: boolean }
  onSearch: (type: 'own' | 'competitor') => void
  recommendations: SourceRecommendation[]
  onApprove: (sourceId: string, sourceType: string) => void
  onReject: (sourceId: string, sourceType: string, name: string) => void
  isLoading: boolean
}

function FDASubmissionsSearchPanel({
  params,
  onParamsChange,
  results,
  loading,
  onSearch,
  recommendations,
  onApprove,
  onReject,
  isLoading,
}: FDASubmissionsSearchPanelProps) {
  const [editingOwn, setEditingOwn] = useState(false)
  const [editingCompetitor, setEditingCompetitor] = useState(false)

  const ownSubmissionsRec = recommendations.find(r => r.type === 'earlier_phase_fda')
  const competitorSubmissionsRec = recommendations.find(r => r.type === 'competitor_fda')

  return (
    <div className="space-y-6">
      {/* Own Submissions */}
      <SearchSection
        title="Own FDA Submissions"
        subtitle="Your organization's 510(k) clearances and MAUDE reports"
        icon={<Shield className="w-4 h-4" />}
        recommendation={ownSubmissionsRec}
        onApprove={() => ownSubmissionsRec && onApprove(ownSubmissionsRec.id, ownSubmissionsRec.type)}
        onReject={() => ownSubmissionsRec && onReject(ownSubmissionsRec.id, ownSubmissionsRec.type, ownSubmissionsRec.name)}
        isLoading={isLoading}
      >
        <div className="grid grid-cols-2 gap-4">
          <SearchField label="Applicant" value={params.ownSubmissions.applicant} editing={editingOwn}
            onChange={(v) => onParamsChange({ ...params, ownSubmissions: { ...params.ownSubmissions, applicant: v } })} />
          <div>
            <label className="text-xs text-neutral-400 block mb-1">Product Codes</label>
            <div className="flex flex-wrap gap-1.5">
              {params.ownSubmissions.productCodes.map((code, idx) => (
                <span key={idx} className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded">
                  {code}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setEditingOwn(!editingOwn)}
            className="text-xs text-neutral-500 hover:text-neutral-700 flex items-center gap-1"
          >
            <Edit3 className="w-3 h-3" />
            {editingOwn ? 'Done' : 'Edit Parameters'}
          </button>
          <button
            onClick={() => onSearch('own')}
            disabled={loading.fdaOwn}
            className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 text-white text-xs font-medium rounded-lg hover:bg-neutral-800 disabled:opacity-50"
          >
            {loading.fdaOwn ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
            {loading.fdaOwn ? 'Searching...' : 'Search'}
          </button>
        </div>
        {results.ownSubmissions && (
          <div className="mt-4 p-3 bg-emerald-50 rounded-lg">
            <p className="text-sm font-medium text-emerald-700">{results.ownSubmissions.count} submissions found</p>
          </div>
        )}
      </SearchSection>

      {/* Competitor Submissions */}
      <SearchSection
        title="Competitor FDA Submissions"
        subtitle="Competitor 510(k) clearances and MAUDE reports"
        icon={<Building2 className="w-4 h-4" />}
        recommendation={competitorSubmissionsRec}
        onApprove={() => competitorSubmissionsRec && onApprove(competitorSubmissionsRec.id, competitorSubmissionsRec.type)}
        onReject={() => competitorSubmissionsRec && onReject(competitorSubmissionsRec.id, competitorSubmissionsRec.type, competitorSubmissionsRec.name)}
        isLoading={isLoading}
      >
        <div className="space-y-4">
          <div>
            <label className="text-xs text-neutral-400 block mb-2">Competitor Applicants</label>
            <div className="flex flex-wrap gap-2">
              {params.competitorSubmissions.applicants.map((applicant, idx) => (
                <span key={idx} className="px-2 py-1 bg-neutral-100 text-neutral-700 text-xs rounded">
                  {applicant}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setEditingCompetitor(!editingCompetitor)}
            className="text-xs text-neutral-500 hover:text-neutral-700 flex items-center gap-1"
          >
            <Edit3 className="w-3 h-3" />
            {editingCompetitor ? 'Done' : 'Edit Parameters'}
          </button>
          <button
            onClick={() => onSearch('competitor')}
            disabled={loading.fdaCompetitor}
            className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 text-white text-xs font-medium rounded-lg hover:bg-neutral-800 disabled:opacity-50"
          >
            {loading.fdaCompetitor ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
            {loading.fdaCompetitor ? 'Searching...' : 'Search'}
          </button>
        </div>
        {results.competitorSubmissions && (
          <div className="mt-4 p-3 bg-emerald-50 rounded-lg">
            <p className="text-sm font-medium text-emerald-700">{results.competitorSubmissions.count} submissions found</p>
          </div>
        )}
      </SearchSection>
    </div>
  )
}

// ============================================================================
// Shared Components
// ============================================================================

interface SearchSectionProps {
  title: string
  subtitle: string
  icon: React.ReactNode
  recommendation?: SourceRecommendation
  onApprove: () => void
  onReject: () => void
  isLoading: boolean
  children: React.ReactNode
}

function SearchSection({ title, subtitle, icon, recommendation, onApprove, onReject, isLoading, children }: SearchSectionProps) {
  return (
    <div className="border border-neutral-200 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-4 bg-neutral-50/50 border-b border-neutral-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-neutral-900 flex items-center justify-center text-white">
            {icon}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-neutral-900">{title}</h4>
            <p className="text-xs text-neutral-500">{subtitle}</p>
          </div>
        </div>
        {recommendation && (
          <div className="flex items-center gap-2">
            {recommendation.status === 'pending' && (
              <>
                <button
                  onClick={onReject}
                  disabled={isLoading}
                  className="w-8 h-8 rounded-lg border border-neutral-200 bg-white flex items-center justify-center text-neutral-400 hover:text-red-500 hover:border-red-200 transition-all disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                </button>
                <button
                  onClick={onApprove}
                  disabled={isLoading}
                  className="w-8 h-8 rounded-lg bg-neutral-900 text-white flex items-center justify-center hover:bg-neutral-800 transition-all disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                </button>
              </>
            )}
            {recommendation.status !== 'pending' && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                recommendation.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
              }`}>
                {recommendation.status === 'approved' ? 'Approved' : 'Rejected'}
              </span>
            )}
          </div>
        )}
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  )
}

interface SearchFieldProps {
  label: string
  value: string
  editing: boolean
  onChange: (value: string) => void
}

function SearchField({ label, value, editing, onChange }: SearchFieldProps) {
  return (
    <div>
      <label className="text-xs text-neutral-400 block mb-1">{label}</label>
      {editing ? (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400"
        />
      ) : (
        <p className="text-sm text-neutral-700 bg-neutral-50 px-3 py-2 rounded-lg truncate">
          {value || 'Not specified'}
        </p>
      )}
    </div>
  )
}
