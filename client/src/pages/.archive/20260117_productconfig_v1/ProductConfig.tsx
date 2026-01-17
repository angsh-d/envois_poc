import { useReducer, useEffect, useCallback, useState } from 'react'
import { Link, useParams } from 'wouter'
import {
  ArrowLeft,
  Settings,
  Play,
  RotateCcw,
} from 'lucide-react'
import { Card } from '@/components/Card'
import { Navbar } from '@/components/Navbar'
import { OnboardingChat, useOnboardingChat } from '@/components/OnboardingChat'
import { DiscoveryProgress } from '@/components/DiscoveryProgress'
import { ResearchProgress } from '@/components/ResearchProgress'
import { IntelligenceBrief } from '@/components/IntelligenceBrief'
import { ApiError } from '@/components/ErrorAlert'
import { ApprovalCard, RegistryItem, PaperItem } from '@/components/RecommendationCard'
import { ApprovalSummary } from '@/components/ApprovalSummary'
import { FeedbackPanel, RejectionModal, AuditTrailModal } from '@/components/FeedbackPanel'
import {
  startOnboarding,
  runDiscovery,
  generateRecommendations,
  runDeepResearch,
  completeOnboarding,
  updateSourceApproval,
  submitFeedback,
  getApprovalAudit,
  finalizeApprovals,
  initializeApprovals,
  ONBOARDING_PHASES,
  type OnboardingSessionResponse,
  type ApprovalStatus,
  type ApprovalSummary as ApprovalSummaryType,
  type SourceApproval,
  type ApprovalAuditEntry,
} from '@/lib/onboardingApi'

// Product data type
interface Product {
  id: string
  name: string
  category: string
  indication: string
  technologies: string[]
  protocolId: string
}

// Error state type
interface ErrorState {
  message: string
  phase: string
  statusCode?: number
  retryAction?: () => void
}

// Onboarding state shape
interface OnboardingState {
  // Session management
  sessionId: string | null
  currentPhase: string
  started: boolean
  isLoading: boolean
  message: string

  // Phase data
  sessionData: OnboardingSessionResponse | null
  discoveryResults: Record<string, unknown> | null
  recommendations: Record<string, unknown> | null
  researchStatus: Record<string, unknown> | null
  intelligenceBrief: Record<string, unknown> | null

  // Interactive Approval state
  sourceApprovals: Record<string, SourceApproval>
  approvalSummary: ApprovalSummaryType | null
  auditEntries: ApprovalAuditEntry[]
  stewardFeedback: string[]

  // Legacy selection state (kept for compatibility)
  selectedSources: string[]
  registrySelections: Record<string, boolean>
  paperSelections: Record<string, boolean>

  // Error handling
  error: ErrorState | null
}

// Action types
type OnboardingAction =
  | { type: 'START_LOADING'; message?: string }
  | { type: 'STOP_LOADING' }
  | { type: 'SET_STARTED' }
  | { type: 'SET_SESSION'; payload: { sessionId: string; phase: string; data: OnboardingSessionResponse; message: string } }
  | { type: 'SET_PHASE'; phase: string }
  | { type: 'SET_MESSAGE'; message: string }
  | { type: 'SET_DISCOVERY_RESULTS'; payload: Record<string, unknown> }
  | { type: 'SET_RECOMMENDATIONS'; payload: Record<string, unknown> }
  | { type: 'SET_RESEARCH_STATUS'; payload: Record<string, unknown> }
  | { type: 'SET_INTELLIGENCE_BRIEF'; payload: Record<string, unknown> }
  | { type: 'SET_SELECTED_SOURCES'; sources: string[] }
  | { type: 'SET_REGISTRY_SELECTIONS'; selections: Record<string, boolean> }
  | { type: 'SET_PAPER_SELECTIONS'; selections: Record<string, boolean> }
  // Interactive Approval actions
  | { type: 'SET_SOURCE_APPROVALS'; approvals: Record<string, SourceApproval> }
  | { type: 'UPDATE_SOURCE_APPROVAL'; sourceKey: string; approval: SourceApproval }
  | { type: 'SET_APPROVAL_SUMMARY'; summary: ApprovalSummaryType }
  | { type: 'SET_AUDIT_ENTRIES'; entries: ApprovalAuditEntry[] }
  | { type: 'SET_STEWARD_FEEDBACK'; feedback: string[] }
  | { type: 'ADD_STEWARD_FEEDBACK'; feedback: string }
  | { type: 'SET_ERROR'; error: ErrorState }
  | { type: 'CLEAR_ERROR' }
  | { type: 'RESET' }

// Initial state factory
const createInitialState = (): OnboardingState => ({
  sessionId: null,
  currentPhase: ONBOARDING_PHASES.CONTEXT_CAPTURE,
  started: false,
  isLoading: false,
  message: '',
  sessionData: null,
  discoveryResults: null,
  recommendations: null,
  researchStatus: null,
  intelligenceBrief: null,
  // Interactive Approval state
  sourceApprovals: {},
  approvalSummary: null,
  auditEntries: [],
  stewardFeedback: [],
  // Legacy selection state
  selectedSources: [],
  registrySelections: {},
  paperSelections: {},
  error: null,
})

// Reducer function
function onboardingReducer(state: OnboardingState, action: OnboardingAction): OnboardingState {
  switch (action.type) {
    case 'START_LOADING':
      return {
        ...state,
        isLoading: true,
        message: action.message || state.message,
        error: null,
      }

    case 'STOP_LOADING':
      return {
        ...state,
        isLoading: false,
      }

    case 'SET_STARTED':
      return {
        ...state,
        started: true,
      }

    case 'SET_SESSION':
      return {
        ...state,
        sessionId: action.payload.sessionId,
        currentPhase: action.payload.phase,
        sessionData: action.payload.data,
        message: action.payload.message,
        isLoading: false,
      }

    case 'SET_PHASE':
      return {
        ...state,
        currentPhase: action.phase,
        // Clear error if phase changed
        error: state.error?.phase !== action.phase ? null : state.error,
      }

    case 'SET_MESSAGE':
      return {
        ...state,
        message: action.message,
      }

    case 'SET_DISCOVERY_RESULTS':
      return {
        ...state,
        discoveryResults: action.payload,
      }

    case 'SET_RECOMMENDATIONS':
      return {
        ...state,
        recommendations: action.payload,
      }

    case 'SET_RESEARCH_STATUS':
      return {
        ...state,
        researchStatus: action.payload,
      }

    case 'SET_INTELLIGENCE_BRIEF':
      return {
        ...state,
        intelligenceBrief: action.payload,
      }

    case 'SET_SELECTED_SOURCES':
      return {
        ...state,
        selectedSources: action.sources,
      }

    case 'SET_REGISTRY_SELECTIONS':
      return {
        ...state,
        registrySelections: action.selections,
      }

    case 'SET_PAPER_SELECTIONS':
      return {
        ...state,
        paperSelections: action.selections,
      }

    // Interactive Approval actions
    case 'SET_SOURCE_APPROVALS':
      return {
        ...state,
        sourceApprovals: action.approvals,
      }

    case 'UPDATE_SOURCE_APPROVAL':
      return {
        ...state,
        sourceApprovals: {
          ...state.sourceApprovals,
          [action.sourceKey]: action.approval,
        },
      }

    case 'SET_APPROVAL_SUMMARY':
      return {
        ...state,
        approvalSummary: action.summary,
      }

    case 'SET_AUDIT_ENTRIES':
      return {
        ...state,
        auditEntries: action.entries,
      }

    case 'SET_STEWARD_FEEDBACK':
      return {
        ...state,
        stewardFeedback: action.feedback,
      }

    case 'ADD_STEWARD_FEEDBACK':
      return {
        ...state,
        stewardFeedback: [...state.stewardFeedback, action.feedback],
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
        message: '',
        isLoading: false,
      }

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      }

    case 'RESET':
      return createInitialState()

    default:
      return state
  }
}

// Product data
const productData: Record<string, Product> = {
  'delta-tt': {
    id: 'delta-tt',
    name: 'DELTA TT Revision Cup',
    category: 'Hip Reconstruction',
    indication: 'Revision THA',
    technologies: ['Trabecular Titanium', 'Porous Coating', 'Uncemented'],
    protocolId: 'H-34',
  },
  'empowr-dual': {
    id: 'empowr-dual',
    name: 'EMPOWR Dual Mobility',
    category: 'Hip Reconstruction',
    indication: 'Primary THA',
    technologies: ['Dual Mobility', 'Highly Crosslinked PE'],
    protocolId: 'H-45',
  },
  'empowr-knee': {
    id: 'empowr-knee',
    name: 'EMPOWR Knee',
    category: 'Knee Reconstruction',
    indication: 'Primary TKA',
    technologies: ['Trabecular Titanium', 'Anatomic Design'],
    protocolId: 'K-12',
  },
}

const PHASE_ORDER = [
  ONBOARDING_PHASES.CONTEXT_CAPTURE,
  ONBOARDING_PHASES.DISCOVERY,
  ONBOARDING_PHASES.RECOMMENDATIONS,
  ONBOARDING_PHASES.DEEP_RESEARCH,
  ONBOARDING_PHASES.COMPLETE,
]

// Error extraction helper
const extractErrorInfo = (err: unknown): { message: string; statusCode?: number } => {
  if (err instanceof Error) {
    const statusMatch = err.message.match(/(\d{3})/)
    return {
      message: err.message,
      statusCode: statusMatch ? parseInt(statusMatch[1]) : undefined,
    }
  }
  return { message: 'An unexpected error occurred' }
}

export default function ProductConfig() {
  const { productId } = useParams<{ productId: string }>()
  const product = productData[productId || '']

  const [state, dispatch] = useReducer(onboardingReducer, null, createInitialState)

  const {
    sessionId,
    currentPhase,
    started,
    isLoading,
    message,
    discoveryResults,
    recommendations,
    researchStatus,
    intelligenceBrief,
    // Interactive Approval state
    sourceApprovals,
    approvalSummary,
    auditEntries,
    stewardFeedback,
    // Legacy selection state
    selectedSources,
    registrySelections,
    paperSelections,
    error,
  } = state

  // Modal states for rejection and audit trail
  const [rejectionModal, setRejectionModal] = useState<{
    isOpen: boolean
    sourceType: string
    sourceId: string
    sourceName: string
  }>({ isOpen: false, sourceType: '', sourceId: '', sourceName: '' })

  const [auditModalOpen, setAuditModalOpen] = useState(false)

  // Conversational chat hook
  const {
    messages: chatMessages,
    isLoading: chatLoading,
    suggestedActions,
    followUpQuestions,
    sendMessage: sendChatMessage,
    handleActionClick,
    handleQuestionClick,
    addInitialMessage,
    clearMessages: clearChatMessages,
  } = useOnboardingChat(sessionId || undefined, currentPhase)

  // Add initial message when phase changes
  useEffect(() => {
    if (message && started) {
      addInitialMessage(message)
    }
  }, [message, started, addInitialMessage])

  // Clear chat when reset
  useEffect(() => {
    if (!started) {
      clearChatMessages()
    }
  }, [started, clearChatMessages])

  // Clear error when phase changes
  useEffect(() => {
    if (error && error.phase !== currentPhase) {
      dispatch({ type: 'CLEAR_ERROR' })
    }
  }, [currentPhase, error])

  const handleStartOnboarding = useCallback(async () => {
    if (!product) return

    dispatch({ type: 'SET_STARTED' })
    dispatch({ type: 'START_LOADING', message: 'Analyzing product context and identifying optimal data sources...' })

    try {
      const response = await startOnboarding({
        product_name: product.name,
        category: product.category,
        indication: product.indication,
        study_phase: 'Post-Market Surveillance',
        protocol_id: product.protocolId,
        technologies: product.technologies,
      })

      dispatch({
        type: 'SET_SESSION',
        payload: {
          sessionId: response.session_id,
          phase: response.current_phase,
          data: response,
          message: response.message,
        },
      })

      // Automatically proceed to discovery
      if (response.current_phase === ONBOARDING_PHASES.DISCOVERY) {
        await handleRunDiscovery(response.session_id)
      }
    } catch (err) {
      console.error('Failed to start onboarding:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.CONTEXT_CAPTURE,
          statusCode: errorInfo.statusCode,
          retryAction: handleStartOnboarding,
        },
      })
    }
  }, [product])

  const handleRunDiscovery = useCallback(async (sid?: string) => {
    const id = sid || sessionId
    if (!id) return

    dispatch({ type: 'START_LOADING', message: 'Running discovery agents to find relevant data sources...' })

    try {
      const response = await runDiscovery(id)
      dispatch({ type: 'SET_PHASE', phase: response.current_phase })
      dispatch({ type: 'SET_MESSAGE', message: response.message })
      dispatch({ type: 'SET_DISCOVERY_RESULTS', payload: response.discovery_results || {} })
      dispatch({ type: 'STOP_LOADING' })

      // Automatically proceed to recommendations
      if (response.current_phase === ONBOARDING_PHASES.RECOMMENDATIONS) {
        await handleGenerateRecommendations(id)
      }
    } catch (err) {
      console.error('Failed to run discovery:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.DISCOVERY,
          statusCode: errorInfo.statusCode,
          retryAction: () => handleRunDiscovery(id),
        },
      })
    }
  }, [sessionId])

  const handleGenerateRecommendations = useCallback(async (sid?: string) => {
    const id = sid || sessionId
    if (!id) return

    dispatch({ type: 'START_LOADING', message: 'Generating data source recommendations based on discovery...' })

    try {
      const response = await generateRecommendations(id)
      dispatch({ type: 'SET_PHASE', phase: response.current_phase })
      dispatch({ type: 'SET_MESSAGE', message: response.message })
      dispatch({ type: 'SET_RECOMMENDATIONS', payload: response.recommendations || {} })

      // Initialize Interactive Approval state
      try {
        const approvalResponse = await initializeApprovals(id)
        dispatch({ type: 'SET_APPROVAL_SUMMARY', summary: approvalResponse.approval_summary })
      } catch (approvalErr) {
        console.error('Failed to initialize approvals:', approvalErr)
        // Non-blocking - continue without approval initialization
      }

      dispatch({ type: 'STOP_LOADING' })
    } catch (err) {
      console.error('Failed to generate recommendations:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.RECOMMENDATIONS,
          statusCode: errorInfo.statusCode,
          retryAction: () => handleGenerateRecommendations(id),
        },
      })
    }
  }, [sessionId])

  // Interactive Approval Handlers
  const handleApproveSource = useCallback(async (sourceType: string, sourceId: string) => {
    if (!sessionId) return

    dispatch({ type: 'START_LOADING', message: 'Approving source...' })

    try {
      const response = await updateSourceApproval(sessionId, sourceType, sourceId, {
        status: 'approved',
      })

      // Update local approval state
      const sourceKey = `${sourceType}:${sourceId}`
      dispatch({
        type: 'UPDATE_SOURCE_APPROVAL',
        sourceKey,
        approval: {
          source_id: sourceId,
          source_type: sourceType,
          status: 'approved',
          approved_at: new Date().toISOString(),
        },
      })
      dispatch({ type: 'SET_APPROVAL_SUMMARY', summary: response.approval_summary })
      dispatch({ type: 'STOP_LOADING' })
    } catch (err) {
      console.error('Failed to approve source:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.RECOMMENDATIONS,
          statusCode: errorInfo.statusCode,
        },
      })
    }
  }, [sessionId])

  const handleRejectSource = useCallback(async (sourceType: string, sourceId: string, sourceName: string) => {
    // Open rejection modal to capture reason
    setRejectionModal({ isOpen: true, sourceType, sourceId, sourceName })
  }, [])

  const handleConfirmRejection = useCallback(async (reason: string) => {
    if (!sessionId) return

    const { sourceType, sourceId } = rejectionModal
    dispatch({ type: 'START_LOADING', message: 'Rejecting source...' })

    try {
      const response = await updateSourceApproval(sessionId, sourceType, sourceId, {
        status: 'rejected',
        reason,
      })

      // Update local approval state
      const sourceKey = `${sourceType}:${sourceId}`
      dispatch({
        type: 'UPDATE_SOURCE_APPROVAL',
        sourceKey,
        approval: {
          source_id: sourceId,
          source_type: sourceType,
          status: 'rejected',
          reason,
        },
      })
      dispatch({ type: 'SET_APPROVAL_SUMMARY', summary: response.approval_summary })

      // Close modal
      setRejectionModal({ isOpen: false, sourceType: '', sourceId: '', sourceName: '' })
      dispatch({ type: 'STOP_LOADING' })
    } catch (err) {
      console.error('Failed to reject source:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.RECOMMENDATIONS,
          statusCode: errorInfo.statusCode,
        },
      })
    }
  }, [sessionId, rejectionModal])

  const handleSubmitFeedback = useCallback(async (feedback: string, requestReanalysis: boolean) => {
    if (!sessionId) return

    dispatch({ type: 'START_LOADING', message: 'Submitting feedback...' })

    try {
      await submitFeedback(sessionId, { feedback, request_reanalysis: requestReanalysis })
      dispatch({ type: 'ADD_STEWARD_FEEDBACK', feedback })
      dispatch({ type: 'STOP_LOADING' })
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.RECOMMENDATIONS,
          statusCode: errorInfo.statusCode,
        },
      })
    }
  }, [sessionId])

  const handleViewAuditTrail = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await getApprovalAudit(sessionId)
      dispatch({ type: 'SET_AUDIT_ENTRIES', entries: response.audit_entries })
      setAuditModalOpen(true)
    } catch (err) {
      console.error('Failed to get audit trail:', err)
    }
  }, [sessionId])

  const handleFinalizeApprovals = useCallback(async () => {
    if (!sessionId) return

    // Validate approvals can proceed
    if (!approvalSummary?.can_proceed) {
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: `At least ${approvalSummary?.minimum_required || 1} source(s) must be approved to proceed.`,
          phase: ONBOARDING_PHASES.RECOMMENDATIONS,
        },
      })
      return
    }

    dispatch({ type: 'START_LOADING', message: 'Finalizing approvals and starting deep research...' })

    try {
      const response = await finalizeApprovals(sessionId)

      if (!response.success) {
        dispatch({
          type: 'SET_ERROR',
          error: {
            message: response.error || 'Failed to finalize approvals',
            phase: ONBOARDING_PHASES.RECOMMENDATIONS,
          },
        })
        return
      }

      dispatch({ type: 'SET_PHASE', phase: response.current_phase })
      dispatch({ type: 'SET_MESSAGE', message: response.message })
      dispatch({ type: 'STOP_LOADING' })

      // Start deep research
      pollResearchStatus()
    } catch (err) {
      console.error('Failed to finalize approvals:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.DEEP_RESEARCH,
          statusCode: errorInfo.statusCode,
          retryAction: handleFinalizeApprovals,
        },
      })
    }
  }, [sessionId, approvalSummary])

  // Helper to get approval status for a source
  const getApprovalStatus = useCallback((sourceType: string, sourceId: string): ApprovalStatus => {
    const key = `${sourceType}:${sourceId}`
    return sourceApprovals[key]?.status || 'pending'
  }, [sourceApprovals])

  const getRejectionReason = useCallback((sourceType: string, sourceId: string): string | undefined => {
    const key = `${sourceType}:${sourceId}`
    return sourceApprovals[key]?.reason
  }, [sourceApprovals])

  const pollResearchStatus = useCallback(async () => {
    if (!sessionId) return

    // Simulate progress updates
    const intervals = [
      { delay: 2000, progress: 35 },
      { delay: 4000, progress: 65 },
      { delay: 6000, progress: 100 },
    ]

    for (const { delay, progress } of intervals) {
      await new Promise(resolve => setTimeout(resolve, delay))

      try {
        const response = await runDeepResearch(sessionId)
        dispatch({ type: 'SET_RESEARCH_STATUS', payload: response.research_status || {} })
        dispatch({ type: 'SET_MESSAGE', message: response.message })

        if (response.current_phase === ONBOARDING_PHASES.COMPLETE || progress >= 100) {
          await handleComplete()
          break
        }
      } catch (err) {
        console.error('Research status poll failed:', err)
        const errorInfo = extractErrorInfo(err)
        dispatch({
          type: 'SET_ERROR',
          error: {
            message: errorInfo.message,
            phase: ONBOARDING_PHASES.DEEP_RESEARCH,
            statusCode: errorInfo.statusCode,
            retryAction: pollResearchStatus,
          },
        })
        break
      }
    }
  }, [sessionId])

  const handleComplete = useCallback(async () => {
    if (!sessionId) return

    dispatch({ type: 'START_LOADING', message: 'Finalizing configuration and generating intelligence brief...' })

    try {
      const response = await completeOnboarding(sessionId)
      dispatch({ type: 'SET_PHASE', phase: response.current_phase })
      dispatch({ type: 'SET_MESSAGE', message: response.message })
      dispatch({ type: 'SET_INTELLIGENCE_BRIEF', payload: response.intelligence_brief || {} })
      dispatch({ type: 'STOP_LOADING' })
    } catch (err) {
      console.error('Failed to complete onboarding:', err)
      const errorInfo = extractErrorInfo(err)
      dispatch({
        type: 'SET_ERROR',
        error: {
          message: errorInfo.message,
          phase: ONBOARDING_PHASES.COMPLETE,
          statusCode: errorInfo.statusCode,
          retryAction: handleComplete,
        },
      })
    }
  }, [sessionId])

  // Handler callbacks for data source selection
  const handleSelectedSourcesChange = useCallback((sources: string[]) => {
    dispatch({ type: 'SET_SELECTED_SOURCES', sources })
  }, [])

  const handleRegistrySelectionsChange = useCallback((selections: Record<string, boolean>) => {
    dispatch({ type: 'SET_REGISTRY_SELECTIONS', selections })
  }, [])

  const handlePaperSelectionsChange = useCallback((selections: Record<string, boolean>) => {
    dispatch({ type: 'SET_PAPER_SELECTIONS', selections })
  }, [])

  if (!product) {
    return (
      <div className="min-h-screen bg-[#fafafa]">
        <Navbar />
        <main className="py-16 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <h1 className="text-2xl font-semibold text-gray-900">Product Not Found</h1>
            <Link href="/" className="inline-flex items-center gap-2 mt-6 text-gray-900 hover:text-gray-600">
              <ArrowLeft className="w-4 h-4" />
              Back to Products
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const currentPhaseIndex = PHASE_ORDER.indexOf(currentPhase)

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <Navbar />

      <main>
        {/* Header Section */}
        <section className="py-12 px-6 bg-white border-b border-gray-100">
          <div className="max-w-4xl mx-auto">
            <Link
              href={`/product/${productId}`}
              className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to {product.name}
            </Link>

            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                    <Settings className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
                      Product Data Steward
                    </h1>
                    <p className="text-sm text-gray-500">{product.name}</p>
                  </div>
                </div>
              </div>

              {/* Phase Progress and Reset Button */}
              {started && (
                <div className="flex items-center gap-4">
                  {/* Phase Progress */}
                  <div className="flex items-center gap-2">
                    {PHASE_ORDER.map((phase, i) => (
                      <div key={phase} className="flex items-center">
                        <div
                          className={`
                            w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                            ${i < currentPhaseIndex ? 'bg-emerald-500 text-white' :
                              i === currentPhaseIndex ? 'bg-blue-500 text-white' :
                              'bg-gray-200 text-gray-500'}
                          `}
                        >
                          {i + 1}
                        </div>
                        {i < PHASE_ORDER.length - 1 && (
                          <div className={`w-8 h-0.5 mx-1 ${i < currentPhaseIndex ? 'bg-emerald-500' : 'bg-gray-200'}`} />
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Reset Button */}
                  <button
                    onClick={() => dispatch({ type: 'RESET' })}
                    disabled={isLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Reset Configuration"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-8 px-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Error Display */}
            {error && (
              <ApiError
                statusCode={error.statusCode}
                message={error.message}
                onRetry={error.retryAction}
                onDismiss={() => dispatch({ type: 'CLEAR_ERROR' })}
              />
            )}

            {/* AI Assistant Conversational Chat */}
            {started && !error && (
              <OnboardingChat
                messages={chatMessages}
                isLoading={isLoading || chatLoading}
                onSendMessage={sendChatMessage}
                showInput={true}
                placeholder="Ask a question about the configuration..."
                sessionId={sessionId || undefined}
                persistMessages={true}
                suggestedActions={suggestedActions}
                followUpQuestions={followUpQuestions}
                onActionClick={handleActionClick}
                onQuestionClick={handleQuestionClick}
                currentPhase={currentPhase}
              />
            )}

            {/* Start Screen */}
            {!started && (
              <Card className="text-center py-12">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Settings className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  AI-Powered Configuration
                </h2>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Our AI will automatically discover and configure the optimal data sources
                  and knowledge assets for {product.name}.
                </p>

                {/* Product Info Summary */}
                <div className="bg-gray-50 rounded-xl p-4 mb-6 max-w-md mx-auto text-left">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Category:</span>
                      <span className="ml-2 text-gray-900">{product.category}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Indication:</span>
                      <span className="ml-2 text-gray-900">{product.indication}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Protocol:</span>
                      <span className="ml-2 text-gray-900">{product.protocolId}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Technologies:</span>
                      <span className="ml-2 text-gray-900">{product.technologies.length} key</span>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {product.technologies.map((tech, i) => (
                      <span key={i} className="px-2 py-0.5 bg-white border border-gray-200 rounded text-xs text-gray-600">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleStartOnboarding}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white font-medium rounded-xl hover:bg-gray-800 transition-colors"
                >
                  <Play className="w-5 h-5" />
                  Start Autonomous Configuration
                </button>
              </Card>
            )}

            {/* Discovery Phase */}
            {started && currentPhase === ONBOARDING_PHASES.DISCOVERY && discoveryResults && (
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Discovering Intelligence Sources</h3>
                <DiscoveryProgress
                  overallProgress={
                    (((discoveryResults as Record<string, Record<string, number>>)?.literature_discovery?.progress || 0) +
                    ((discoveryResults as Record<string, Record<string, number>>)?.registry_discovery?.progress || 0) +
                    ((discoveryResults as Record<string, Record<string, number>>)?.fda_discovery?.progress || 0) +
                    ((discoveryResults as Record<string, Record<string, number>>)?.competitive_discovery?.progress || 0)) / 4
                  }
                  agents={{
                    literature: (discoveryResults as Record<string, unknown>)?.literature_discovery as { status: string; progress: number; papers_found?: number },
                    registry: (discoveryResults as Record<string, unknown>)?.registry_discovery as { status: string; progress: number; registries_found?: number },
                    fda: (discoveryResults as Record<string, unknown>)?.fda_discovery as { status: string; progress: number; maude_events?: number },
                    competitive: (discoveryResults as Record<string, unknown>)?.competitive_discovery as { status: string; progress: number; competitors_identified?: number },
                  }}
                />
              </Card>
            )}

            {/* Recommendations Phase - Interactive Approval Workflow */}
            {started && currentPhase === ONBOARDING_PHASES.RECOMMENDATIONS && recommendations && (
              <>
                <Card>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Review Recommended Data Sources</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Please review each recommendation. Approve, reject, or refine each data source
                    before proceeding to deep research. All recommendations include AI reasoning and confidence scores.
                  </p>

                  <div className="space-y-4">
                    {/* Clinical Study Data */}
                    {((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.clinical_study ||
                      (recommendations as Record<string, unknown>)?.clinical_study) && (
                      <ApprovalCard
                        title={`${product.protocolId} Protocol Database`}
                        sourceId="clinical_study"
                        type="clinical"
                        approvalStatus={getApprovalStatus('clinical', 'clinical_study')}
                        onApprove={() => handleApproveSource('clinical', 'clinical_study')}
                        onReject={() => handleRejectSource('clinical', 'clinical_study', `${product.protocolId} Protocol Database`)}
                        rejectionReason={getRejectionReason('clinical', 'clinical_study')}
                        isLoading={isLoading}
                        enabledInsights={
                          ((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.clinical_study?.enabled_insights as string[]) ||
                          ['Patient-level safety monitoring', 'Revision rate calculations', 'Risk stratification']
                        }
                        preview={
                          ((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.clinical_study?.data_preview as string) ||
                          'Primary clinical study data'
                        }
                        confidence={{
                          overall_score: 0.94,
                          level: 'high',
                          factors: {
                            data_completeness: 0.94,
                            follow_up_duration: 0.75,
                            patient_cohort_size: 0.72,
                          },
                        }}
                        whyExplanation={{
                          summary: `${product.protocolId} is your primary clinical study essential for post-market surveillance reporting.`,
                          key_reasons: [
                            'Primary source of patient-level safety data',
                            'Required for regulatory compliance',
                            'Enables risk stratification analysis',
                          ],
                          unique_value: 'Direct patient outcomes for your specific product',
                        }}
                      />
                    )}

                    {/* Registry Benchmarks */}
                    {((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.registries ||
                      (recommendations as Record<string, unknown>)?.registries) && (
                      <div className="border border-gray-200 rounded-xl p-4 bg-white">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Registry Benchmarks</h4>
                          <span className="text-xs text-gray-500">
                            Review each registry individually
                          </span>
                        </div>
                        <div className="space-y-3">
                          {(((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.registries ||
                            (recommendations as Record<string, unknown>)?.registries) as Array<{
                            name: string
                            region: string
                            relevance: string
                            data_years?: string
                            n_procedures?: number
                            selected?: boolean
                            exclusion_reason?: string
                          }>)?.filter((reg: { exclusion_reason?: string }) => !reg.exclusion_reason).map((registry, i) => (
                            <ApprovalCard
                              key={registry.name}
                              title={registry.name}
                              sourceId={registry.name.toLowerCase().replace(/\s+/g, '_')}
                              type="registry"
                              approvalStatus={getApprovalStatus('registry', registry.name.toLowerCase().replace(/\s+/g, '_'))}
                              onApprove={() => handleApproveSource('registry', registry.name.toLowerCase().replace(/\s+/g, '_'))}
                              onReject={() => handleRejectSource('registry', registry.name.toLowerCase().replace(/\s+/g, '_'), registry.name)}
                              rejectionReason={getRejectionReason('registry', registry.name.toLowerCase().replace(/\s+/g, '_'))}
                              isLoading={isLoading}
                              enabledInsights={['Long-term survival benchmarks', 'Comparative revision rates', 'Population-level outcomes']}
                              preview={`${registry.region} • ${registry.data_years || 'Multi-year data'} • ${registry.n_procedures?.toLocaleString() || 'Large'} procedures`}
                              confidence={{
                                overall_score: 0.85,
                                level: 'moderate',
                                factors: {
                                  data_coverage: 0.9,
                                  revision_specificity: 0.8,
                                  accessibility: 0.85,
                                },
                              }}
                              whyExplanation={{
                                summary: registry.relevance,
                                key_reasons: [
                                  `${registry.n_procedures?.toLocaleString() || 'Large number of'} procedures tracked`,
                                  `Covers ${registry.region} market`,
                                  registry.data_years ? `${registry.data_years} of longitudinal data` : 'Multi-year follow-up data',
                                ],
                                unique_value: 'Independent benchmark for comparative analysis',
                              }}
                            />
                          ))}
                        </div>

                        {/* Show excluded registries */}
                        {(((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.registries ||
                          (recommendations as Record<string, unknown>)?.registries) as Array<{
                          name: string
                          region: string
                          exclusion_reason?: string
                        }>)?.filter((reg: { exclusion_reason?: string }) => reg.exclusion_reason).length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-100">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Not Selected (with reasons)</p>
                            <div className="space-y-2">
                              {(((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.registries ||
                                (recommendations as Record<string, unknown>)?.registries) as Array<{
                                name: string
                                region: string
                                exclusion_reason?: string
                              }>)?.filter((reg: { exclusion_reason?: string }) => reg.exclusion_reason).map((registry) => (
                                <div key={registry.name} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                                  <div>
                                    <span className="text-sm text-gray-600">{registry.name}</span>
                                    <span className="text-xs text-gray-400 ml-2">({registry.region})</span>
                                    <p className="text-xs text-amber-600 mt-0.5">{registry.exclusion_reason}</p>
                                  </div>
                                  <button
                                    onClick={() => handleApproveSource('registry', registry.name.toLowerCase().replace(/\s+/g, '_'))}
                                    className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                                  >
                                    Override: Include Anyway
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Literature Knowledge Base */}
                    {((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.literature ||
                      (recommendations as Record<string, unknown>)?.literature) && (
                      <ApprovalCard
                        title="Literature Knowledge Base"
                        sourceId="literature"
                        type="literature"
                        approvalStatus={getApprovalStatus('literature', 'literature')}
                        onApprove={() => handleApproveSource('literature', 'literature')}
                        onReject={() => handleRejectSource('literature', 'literature', 'Literature Knowledge Base')}
                        rejectionReason={getRejectionReason('literature', 'literature')}
                        isLoading={isLoading}
                        enabledInsights={
                          ((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.literature?.enabled_insights as string[]) ||
                          ['Evidence-based clinical context', 'Comparative outcomes data', 'Risk factor identification']
                        }
                        preview={`${((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.literature?.total_papers || (recommendations as Record<string, unknown>)?.literature?.total_papers) || 0} publications discovered via PubMed search`}
                        confidence={{
                          overall_score: 0.89,
                          level: 'high',
                          factors: {
                            relevance_score: 0.92,
                            citation_quality: 0.85,
                            recency: 0.88,
                          },
                        }}
                        whyExplanation={{
                          summary: 'PubMed search for trabecular titanium revision THA outcomes with clinical study filters.',
                          key_reasons: [
                            'Peer-reviewed clinical evidence',
                            'Long-term outcome benchmarks',
                            'Hazard ratios for risk model calibration',
                          ],
                          unique_value: 'Independent validation of your clinical findings',
                        }}
                      >
                        {/* Top Papers Preview */}
                        <div className="mt-3 space-y-2">
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Top Publications</p>
                          {(((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.literature?.top_papers ||
                            (recommendations as Record<string, unknown>)?.literature?.top_papers) as Array<{
                            title: string
                            journal: string
                            year: number
                            insight: string
                            relevance_score: number
                            pmid?: string
                          }>)?.slice(0, 3).map((paper, i) => (
                            <PaperItem
                              key={i}
                              title={paper.title}
                              journal={paper.journal}
                              year={paper.year}
                              insight={paper.insight}
                              relevanceScore={paper.relevance_score}
                              pmid={paper.pmid}
                              url={paper.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}` : undefined}
                              selected={true}
                            />
                          ))}
                        </div>
                      </ApprovalCard>
                    )}

                    {/* FDA Surveillance */}
                    {((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.fda_surveillance ||
                      (recommendations as Record<string, unknown>)?.fda_surveillance) && (
                      <ApprovalCard
                        title="FDA Surveillance Sources"
                        sourceId="fda_surveillance"
                        type="fda"
                        approvalStatus={getApprovalStatus('fda', 'fda_surveillance')}
                        onApprove={() => handleApproveSource('fda', 'fda_surveillance')}
                        onReject={() => handleRejectSource('fda', 'fda_surveillance', 'FDA Surveillance Sources')}
                        rejectionReason={getRejectionReason('fda', 'fda_surveillance')}
                        isLoading={isLoading}
                        enabledInsights={
                          ((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.fda_surveillance?.enabled_insights as string[]) ||
                          ['Adverse event monitoring', 'Regulatory signal detection', 'Comparative device safety']
                        }
                        preview={
                          ((recommendations as Record<string, Record<string, unknown>>)?.recommendations?.fda_surveillance?.preview as string) ||
                          'MAUDE, 510(k), and recall databases'
                        }
                        confidence={{
                          overall_score: 0.91,
                          level: 'high',
                          factors: {
                            data_completeness: 0.95,
                            relevance: 0.88,
                            timeliness: 0.9,
                          },
                        }}
                        whyExplanation={{
                          summary: 'FDA databases provide regulatory-mandated safety surveillance data for similar devices.',
                          key_reasons: [
                            'Real-world adverse event tracking',
                            'Regulatory precedent analysis',
                            'Competitive device safety comparison',
                          ],
                          unique_value: 'Early warning system for safety signals',
                        }}
                      />
                    )}
                  </div>
                </Card>

                {/* Steward Feedback Panel */}
                <FeedbackPanel
                  onSubmit={handleSubmitFeedback}
                  isLoading={isLoading}
                  existingFeedback={stewardFeedback}
                />

                {/* Approval Summary and Actions */}
                {approvalSummary && (
                  <ApprovalSummary
                    summary={approvalSummary}
                    onSaveDraft={() => console.log('Save draft')}
                    onViewAudit={handleViewAuditTrail}
                    onApproveAndBuild={handleFinalizeApprovals}
                    isLoading={isLoading}
                  />
                )}
              </>
            )}

            {/* Deep Research Phase */}
            {started && currentPhase === ONBOARDING_PHASES.DEEP_RESEARCH && researchStatus && (
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Deep Research Agents</h3>
                <ResearchProgress
                  overallProgress={(researchStatus as Record<string, number>)?.overall_progress || 0}
                  reports={{
                    competitive_landscape: (researchStatus as Record<string, Record<string, unknown>>)?.research_status?.competitive_landscape as { status: 'queued' | 'running' | 'completed'; progress: number; pages?: number; sections?: string[]; analyzing?: string[] },
                    state_of_the_art: (researchStatus as Record<string, Record<string, unknown>>)?.research_status?.state_of_the_art as { status: 'queued' | 'running' | 'completed'; progress: number; pages?: number; sections?: string[]; analyzing?: string[] },
                    regulatory_precedents: (researchStatus as Record<string, Record<string, unknown>>)?.research_status?.regulatory_precedents as { status: 'queued' | 'running' | 'completed'; progress: number; pages?: number; sections?: string[]; analyzing?: string[] },
                  }}
                />
              </Card>
            )}

            {/* Complete Phase */}
            {started && currentPhase === ONBOARDING_PHASES.COMPLETE && intelligenceBrief && (
              <IntelligenceBrief
                productName={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.product_name as string) || product.name}
                protocolId={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.protocol_id as string) || product.protocolId}
                category={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.category as string) || product.category}
                indication={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.indication as string) || product.indication}
                dataSources={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.data_sources as {
                  clinical_db?: { patients: number; configured: boolean }
                  registries?: { count: number; configured: boolean }
                  fda_surveillance?: { configured: boolean }
                }) || {}}
                knowledgeBase={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.knowledge_base as {
                  publications: number
                  ifu_labeling: boolean
                  protocol: boolean
                }) || { publications: 0, ifu_labeling: false, protocol: false }}
                generatedReports={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.generated_reports as Array<{ name: string; pages: number; status: string }>) || []}
                enabledModules={((intelligenceBrief as Record<string, Record<string, unknown>>)?.intelligence_brief?.enabled_modules as string[]) || []}
              />
            )}
          </div>
        </section>
      </main>

      {/* Rejection Modal */}
      <RejectionModal
        isOpen={rejectionModal.isOpen}
        sourceType={rejectionModal.sourceType}
        sourceName={rejectionModal.sourceName}
        onClose={() => setRejectionModal({ isOpen: false, sourceType: '', sourceId: '', sourceName: '' })}
        onConfirm={handleConfirmRejection}
        isLoading={isLoading}
      />

      {/* Audit Trail Modal */}
      <AuditTrailModal
        isOpen={auditModalOpen}
        entries={auditEntries}
        onClose={() => setAuditModalOpen(false)}
      />
    </div>
  )
}
