/**
 * Onboarding API Client for Product Data Steward Configuration
 */
const API_BASE = '/api/v1/onboarding'

// Request Types
export interface StartOnboardingRequest {
  product_name: string
  category?: string
  indication?: string
  study_phase?: string
  protocol_id: string  // Required - no default
  technologies?: string[]
}

export interface AcceptRecommendationsRequest {
  accepted_sources?: string[]
  custom_settings?: Record<string, unknown>
}

// Response Types
export interface PhaseProgress {
  completed: boolean
  progress: number
}

export interface OnboardingSessionResponse {
  session_id: string
  product_name?: string
  current_phase: string
  phase_progress: Record<string, PhaseProgress>
  message: string
  success: boolean
  analysis?: ContextAnalysis
  discovery_results?: DiscoveryResults
  recommendations?: Recommendations
  research_status?: ResearchStatus
  intelligence_brief?: IntelligenceBrief
  configuration_complete?: boolean
}

export interface ContextAnalysis {
  phase: string
  product_info: ProductInfo
  analysis: {
    product_understanding?: {
      clinical_context: string
      key_characteristics: string[]
      data_requirements: string[]
    }
    recommended_data_sources?: DataSourceRecommendation[]
    recommended_registries?: RegistryRecommendation[]
    search_terms?: string[]
    competitive_products?: CompetitorProduct[]
  }
  recommended_data_sources: DataSourceRecommendation[]
  recommended_registries: RegistryRecommendation[]
  search_terms: string[]
  competitive_products: CompetitorProduct[]
  next_phase: string
  message: string
}

export interface ProductInfo {
  product_name: string
  category: string
  indication: string
  study_phase: string
  protocol_id: string
  technologies: string[]
}

export interface DataSourceRecommendation {
  type: string
  name: string
  priority: 'high' | 'medium' | 'low'
  rationale: string
}

export interface RegistryRecommendation {
  name: string
  region: string
  relevance: string
  selected?: boolean
  data_years?: string
  exclusion_reason?: string
}

export interface CompetitorProduct {
  manufacturer: string
  product: string
  relevance?: string
}

export interface DiscoveryResults {
  phase: string
  overall_progress: number
  discovery_results: {
    literature_discovery?: LiteratureDiscovery
    registry_discovery?: RegistryDiscovery
    fda_discovery?: FDADiscovery
    competitive_discovery?: CompetitiveDiscovery
  }
  next_phase?: string
  message: string
}

export interface LiteratureDiscovery {
  status: string
  progress: number
  papers_found: number
  top_papers: TopPaper[]
}

export interface TopPaper {
  title: string
  journal: string
  year: number
  relevance_score: number
  insight: string
  pmid?: string
}

export interface RegistryDiscovery {
  status: string
  progress: number
  registries_found: number
  recommended: RegistryRecommendation[]
}

export interface FDADiscovery {
  status: string
  progress: number
  maude_events: number
  clearances: number
  recalls: number
  summary: {
    similar_devices_analyzed: number
    time_range: string
    event_trend: string
  }
}

export interface CompetitiveDiscovery {
  status: string
  progress: number
  competitors_identified: number
  products: CompetitorProduct[]
}

export interface Recommendations {
  phase: string
  recommendations: {
    clinical_study?: ClinicalStudyRecommendation
    registries?: RegistryRecommendation[]
    literature?: LiteratureRecommendation
    fda_surveillance?: FDASurveillanceRecommendation
  }
  ai_narrative: string
  next_phase: string
  message: string
}

export interface ClinicalStudyRecommendation {
  source: string
  selected: boolean
  enabled_insights: string[]
  data_preview: string
}

export interface LiteratureRecommendation {
  total_papers: number
  selected_papers: number
  top_papers: TopPaper[]
  enabled_insights: string[]
}

export interface FDASurveillanceRecommendation {
  sources: string[]
  selected: boolean
  enabled_insights: string[]
  preview: string
}

export interface ResearchStatus {
  phase: string
  overall_progress: number
  research_status: {
    competitive_landscape?: ResearchReport
    state_of_the_art?: ResearchReport
    regulatory_precedents?: ResearchReport
  }
  next_phase?: string
  message: string
}

export interface ResearchReport {
  status: 'queued' | 'running' | 'completed'
  progress: number
  analyzing?: string[]
  will_analyze?: string[]
  sources?: string[]
  report?: {
    pages: number
    sections: string[]
    generated_at: string
  }
}

export interface IntelligenceBrief {
  phase: string
  intelligence_brief: {
    product_name: string
    protocol_id: string
    category: string
    indication: string
    data_sources: {
      clinical_db: { patients: number; configured: boolean }
      registries: { count: number; configured: boolean }
      fda_surveillance: { configured: boolean }
    }
    knowledge_base: {
      publications: number
      ifu_labeling: boolean
      protocol: boolean
    }
    generated_reports: GeneratedReport[]
    enabled_modules: string[]
  }
  configuration_complete: boolean
  message: string
}

export interface GeneratedReport {
  name: string
  pages: number
  status: string
}

export interface SessionSummary {
  session_id: string
  product_name: string
  current_phase: string
  created_at: string
  completed_at?: string
}

export interface SessionListResponse {
  sessions: SessionSummary[]
  total: number
}

// API Functions
export async function startOnboarding(request: StartOnboardingRequest): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Failed to start onboarding: ${response.statusText}`)
  }

  return response.json()
}

export async function getSessionStatus(sessionId: string): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/status`)

  if (!response.ok) {
    throw new Error(`Failed to get session status: ${response.statusText}`)
  }

  return response.json()
}

export async function runDiscovery(sessionId: string): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/discovery`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to run discovery: ${response.statusText}`)
  }

  return response.json()
}

export async function generateRecommendations(sessionId: string): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/recommendations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to generate recommendations: ${response.statusText}`)
  }

  return response.json()
}

export async function acceptRecommendations(
  sessionId: string,
  request: AcceptRecommendationsRequest = {}
): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/recommendations/accept`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Failed to accept recommendations: ${response.statusText}`)
  }

  return response.json()
}

export async function runDeepResearch(sessionId: string): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to run deep research: ${response.statusText}`)
  }

  return response.json()
}

export async function completeOnboarding(sessionId: string): Promise<OnboardingSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to complete onboarding: ${response.statusText}`)
  }

  return response.json()
}

export async function listSessions(): Promise<SessionListResponse> {
  const response = await fetch(`${API_BASE}/sessions`)

  if (!response.ok) {
    throw new Error(`Failed to list sessions: ${response.statusText}`)
  }

  return response.json()
}

// Phase constants
export const ONBOARDING_PHASES = {
  CONTEXT_CAPTURE: 'context_capture',
  DISCOVERY: 'discovery',
  RECOMMENDATIONS: 'recommendations',
  DEEP_RESEARCH: 'deep_research',
  COMPLETE: 'complete'
} as const

export type OnboardingPhase = typeof ONBOARDING_PHASES[keyof typeof ONBOARDING_PHASES]

// Helper to get phase display name
export function getPhaseDisplayName(phase: string): string {
  const names: Record<string, string> = {
    context_capture: 'Analyzing Product Context',
    discovery: 'Discovering Data Sources',
    recommendations: 'Generating Recommendations',
    deep_research: 'Running Deep Research',
    complete: 'Configuration Complete'
  }
  return names[phase] || phase
}

// Helper to get phase icon
export function getPhaseIcon(phase: string): string {
  const icons: Record<string, string> = {
    context_capture: '1',
    discovery: '2',
    recommendations: '3',
    deep_research: '4',
    complete: '5'
  }
  return icons[phase] || '?'
}

// Conversation History Types
export interface ChatMessage {
  id: string | number
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, unknown>
  created_at?: string
}

export interface AddMessageRequest {
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, unknown>
}

export interface AddMessageResponse {
  session_id: string
  message_id: number
  success: boolean
}

export interface ConversationHistoryResponse {
  session_id: string
  messages: ChatMessage[]
  total: number
}

// Conversation History API Functions
export async function addMessage(
  sessionId: string,
  request: AddMessageRequest
): Promise<AddMessageResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Failed to add message: ${response.statusText}`)
  }

  return response.json()
}

export async function getConversationHistory(
  sessionId: string,
  limit: number = 50
): Promise<ConversationHistoryResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/messages?limit=${limit}`)

  if (!response.ok) {
    throw new Error(`Failed to get conversation history: ${response.statusText}`)
  }

  return response.json()
}

// Cancel/Resume Session Types
export type SessionStatus = 'active' | 'cancelled' | 'resumed' | 'completed'

export interface CancelSessionResponse {
  session_id: string
  status: 'cancelled'
  previous_phase: string
  message: string
}

export interface ResumeSessionResponse {
  session_id: string
  status: 'resumed'
  current_phase: string
  phase_progress: Record<string, PhaseProgress>
  message: string
}

// SSE Progress Streaming Types
export type ProgressEventType =
  | 'progress'
  | 'phase_change'
  | 'complete'
  | 'error'
  | 'cancelled'
  | 'partial_failure'
  | 'agent_update'

export type OverallStatus = 'completed' | 'partial' | 'failed' | 'timeout' | null

export interface ProgressEvent {
  event_type: ProgressEventType
  phase: string
  overall_progress: number
  overall_status?: OverallStatus
  agent_updates?: Record<string, unknown>
  message?: string
  data?: Record<string, unknown>
  errors?: string[]
}

export type ProgressEventHandler = (event: ProgressEvent) => void
export type ProgressErrorHandler = (error: Error) => void

// Cancel/Resume API Functions
export async function cancelSession(sessionId: string): Promise<CancelSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/cancel`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to cancel session: ${response.statusText}`)
  }

  return response.json()
}

export async function resumeSession(sessionId: string): Promise<ResumeSessionResponse> {
  const response = await fetch(`${API_BASE}/${sessionId}/resume`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to resume session: ${response.statusText}`)
  }

  return response.json()
}

// SSE Progress Stream Connection
export function subscribeToProgress(
  sessionId: string,
  onEvent: ProgressEventHandler,
  onError?: ProgressErrorHandler
): () => void {
  const eventSource = new EventSource(`${API_BASE}/${sessionId}/progress/stream`)

  // Handle different event types
  const eventTypes: ProgressEventType[] = [
    'progress',
    'phase_change',
    'complete',
    'error',
    'cancelled',
    'partial_failure',
    'agent_update'
  ]

  eventTypes.forEach(eventType => {
    eventSource.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as ProgressEvent
        onEvent(data)

        // Close connection on terminal events
        if (['complete', 'error', 'cancelled'].includes(eventType)) {
          eventSource.close()
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err)
        onError?.(err instanceof Error ? err : new Error(String(err)))
      }
    })
  })

  // Handle connection errors
  eventSource.onerror = (e) => {
    console.error('SSE connection error:', e)
    onError?.(new Error('SSE connection error'))
    eventSource.close()
  }

  // Return cleanup function
  return () => {
    eventSource.close()
  }
}

// React hook for SSE progress streaming
export function useProgressStream(sessionId: string | null) {
  // This hook should be implemented in a React component file
  // as it needs React imports. See useOnboardingProgress hook.
}


// ==================== Interactive Approval Types ====================

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface SourceApproval {
  source_id: string
  source_type: string
  status: ApprovalStatus
  reason?: string
  approved_at?: string
  approved_by?: string
  settings?: Record<string, unknown>
}

export interface ApprovalAuditEntry {
  timestamp: string
  source_id: string
  source_type: string
  action: string
  reason?: string
  user_id?: string
  previous_status?: string
}

export interface ApprovalSummary {
  total_sources: number
  approved_count: number
  rejected_count: number
  pending_count: number
  by_type: Record<string, { approved: number; rejected: number; pending: number }>
  can_proceed: boolean
  minimum_required: number
}

export interface UpdateApprovalRequest {
  status: ApprovalStatus
  reason?: string
  settings?: Record<string, unknown>
}

export interface UpdateApprovalResponse {
  success: boolean
  session_id: string
  source_type: string
  source_id: string
  status: ApprovalStatus
  approval_summary: ApprovalSummary
}

export interface SubmitFeedbackRequest {
  feedback: string
  request_reanalysis?: boolean
}

export interface SubmitFeedbackResponse {
  success: boolean
  session_id: string
  feedback_count: number
  message: string
}

export interface ApprovalAuditResponse {
  success: boolean
  session_id: string
  audit_entries: ApprovalAuditEntry[]
  total_entries: number
  approval_summary: ApprovalSummary
}

export interface FinalizeApprovalsResponse {
  success: boolean
  session_id: string
  current_phase: string
  approval_summary: ApprovalSummary
  message: string
  error?: string
}

export interface ApprovalStatusResponse {
  success: boolean
  session_id: string
  source_approvals: Record<string, SourceApproval>
  approval_summary: ApprovalSummary
  steward_feedback: string[]
}

export interface InitializeApprovalsResponse {
  success: boolean
  session_id: string
  approval_summary: ApprovalSummary
  message: string
}


// ==================== Conversational Chat Types ====================

export interface ChatRequest {
  message: string
  context?: {
    phase?: string
    focus?: string
    session_context?: string
  }
}

export interface ChatResponseData {
  session_id: string
  response: string
  suggested_actions: string[]
  follow_up_questions: string[]
  context_update?: {
    topic?: string
    key_points?: string[]
  }
}


// ==================== Conversational Chat API Functions ====================

/**
 * Send a message to the onboarding AI and receive a response.
 *
 * The steward can converse with the AI at any phase of the onboarding process:
 * - Ask questions about the configuration process
 * - Request clarification on recommendations
 * - Provide feedback or additional context
 * - Get guidance on next steps
 */
export async function chatWithAI(
  sessionId: string,
  request: ChatRequest
): Promise<ChatResponseData> {
  const response = await fetch(`${API_BASE}/${sessionId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Failed to send chat message: ${response.statusText}`)
  }

  return response.json()
}


// ==================== Interactive Approval API Functions ====================

/**
 * Update approval status for a specific data source.
 */
export async function updateSourceApproval(
  sessionId: string,
  sourceType: string,
  sourceId: string,
  request: UpdateApprovalRequest
): Promise<UpdateApprovalResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/${sourceType}/${sourceId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to update approval: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Submit steward feedback for the recommendations.
 */
export async function submitFeedback(
  sessionId: string,
  request: SubmitFeedbackRequest
): Promise<SubmitFeedbackResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/feedback`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to submit feedback: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get the full audit trail for approval decisions.
 */
export async function getApprovalAudit(
  sessionId: string
): Promise<ApprovalAuditResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/audit`
  )

  if (!response.ok) {
    throw new Error(`Failed to get audit trail: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Finalize all approvals and proceed to deep research.
 */
export async function finalizeApprovals(
  sessionId: string
): Promise<FinalizeApprovalsResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/finalize`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to finalize approvals: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get current approval status for all sources in a session.
 */
export async function getApprovalStatus(
  sessionId: string
): Promise<ApprovalStatusResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/status`
  )

  if (!response.ok) {
    throw new Error(`Failed to get approval status: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Initialize approval status for all recommendations.
 */
export async function initializeApprovals(
  sessionId: string
): Promise<InitializeApprovalsResponse> {
  const response = await fetch(
    `${API_BASE}/${sessionId}/recommendations/initialize`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to initialize approvals: ${response.statusText}`)
  }

  return response.json()
}


// ==================== Folder Analysis Types ====================

export interface StudyDataAnalysis {
  fileName: string
  rows: number
  columns: number
  columnNames: string[]
  dataTypes: Record<string, string>
  sampleValues: Record<string, string[]>
  dateRange?: { start: string; end: string }
  keyInsights?: string[]
}

export interface ProtocolAnalysis {
  fileName: string
  pages: number
  studyTitle: string
  indication: string
  studyPhase: string
  primaryEndpoints: string[]
  secondaryEndpoints: string[]
  populationSize: string
  followUpDuration: string
  inclusionCriteriaSummary?: string
  extractedSections?: string[]
}

export interface LiteratureAnalysis {
  fileName: string
  title: string
  authors: string
  journal: string
  year: number
  pages: number
  relevanceScore: number
  keyFindings: string[]
  studyType?: string
  sampleSize?: string
}

export interface ExtractedJsonAnalysis {
  fileName: string
  schemaType: string
  recordCount: number
  keyFields: string[]
  dataPreview: Record<string, unknown>
  lastUpdated?: string
}

export interface FolderContentsResponse {
  path: string
  validated: boolean
  studyData: {
    count: number
    files: string[]
    analysis?: StudyDataAnalysis[]
  }
  protocol: {
    found: boolean
    file: string | null
    analysis?: ProtocolAnalysis
  }
  literature: {
    count: number
    files: string[]
    analysis?: LiteratureAnalysis[]
  }
  extractedJson: {
    count: number
    files: string[]
    analysis?: ExtractedJsonAnalysis[]
  }
}

// ==================== Folder Analysis API Function ====================

/**
 * Analyze a local folder for study data sources.
 * Returns detailed analysis of Excel/CSV files, protocol PDFs, literature, and JSON files.
 */
export async function analyzeFolder(folderPath: string): Promise<FolderContentsResponse> {
  const response = await fetch(`${API_BASE}/analyze-folder`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ folder_path: folderPath })
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(errorData.detail || `Failed to analyze folder: ${response.statusText}`)
  }

  return response.json()
}


// ==================== ClinicalTrials.gov Search ====================

export interface CTSearchRequest {
  sponsor?: string
  condition?: string
  intervention?: string
  phases?: string[]
  statuses?: string[]
  competitor_sponsors?: string[]
  search_type: 'own' | 'competitor'
}

export interface CTTrial {
  nctId: string
  title: string
  phase: string
  status: string
  sponsor?: string
  startDate?: string
  completionDate?: string
  enrollment?: number
}

export interface CTSearchResponse {
  count: number
  trials: CTTrial[]
}

/**
 * Search ClinicalTrials.gov for trials.
 */
export async function searchClinicalTrials(request: CTSearchRequest): Promise<CTSearchResponse> {
  const response = await fetch(`${API_BASE}/search-clinical-trials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(errorData.detail || `Clinical trials search failed: ${response.statusText}`)
  }

  return response.json()
}


// ==================== FDA 510(k) Search ====================

export interface FDASearchRequest {
  applicant?: string
  product_codes?: string[]
  competitor_applicants?: string[]
  date_start?: string
  date_end?: string
  search_type: 'own' | 'competitor'
}

export interface FDASubmission {
  kNumber: string
  deviceName: string
  applicant?: string
  decisionDate?: string
  productCode?: string
  clearanceType?: string
  reviewAdviseComm?: string
}

export interface FDASearchResponse {
  count: number
  submissions: FDASubmission[]
}

/**
 * Search FDA 510(k) database for clearances.
 */
export async function searchFDASubmissions(request: FDASearchRequest): Promise<FDASearchResponse> {
  const response = await fetch(`${API_BASE}/search-fda-submissions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(errorData.detail || `FDA search failed: ${response.statusText}`)
  }

  return response.json()
}
