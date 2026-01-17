/**
 * ProductConfig - Apple-Inspired AI-First Onboarding Experience
 *
 * A clean, modern, step-by-step wizard for Product Data Steward configuration.
 * Uses greyscale palette with subtle accents and premium controls.
 */

import { useReducer, useEffect, useCallback, useState, useRef } from 'react'
import { Link, useParams } from 'wouter'
import {
  ArrowLeft,
  Play,
  MessageCircle,
  Send,
  Sparkles,
  ChevronRight,
  Check,
  Database,
  FileText,
  BarChart3,
  BookOpen,
  Shield,
  Loader2,
  X,
  FlaskConical,
  History,
  Users,
  ClipboardList,
  Edit3,
  Plus,
  Trash2,
  Building2,
} from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { LocalDataConfig, ConfiguredSource, type FileInfo, type FolderContents } from '@/components/LocalDataConfig'
import { analyzeFolder, searchClinicalTrials, searchFDASubmissions, type FolderContentsResponse } from '@/lib/onboardingApi'
import { DataSourceWizard } from '@/components/DataSourceWizard'
import {
  startOnboarding,
  runDiscovery,
  generateRecommendations,
  finalizeApprovals,
  updateSourceApproval,
  completeOnboarding,
  chatWithAI,
  ONBOARDING_PHASES,
  type OnboardingSessionResponse,
  type ApprovalStatus,
} from '@/lib/onboardingApi'
import { startDeepResearch } from '@/lib/researchApi'
import { useOnboardingProgress } from '@/hooks/useOnboardingProgress'

// Product data type
interface Product {
  id: string
  name: string
  category: string
  indication: string
  technologies: string[]
  protocolId: string
}

// State management
interface OnboardingState {
  phase: 'setup' | 'discovery' | 'review' | 'research' | 'complete'
  sessionId: string | null
  isLoading: boolean
  loadingMessage: string
  error: string | null

  // Setup phase - local data folder
  folderPath: string
  folderContents: FolderContents | null

  // Setup phase - editable product context
  manufacturer: string
  studyPhase: string
  competitors: string[]
  fdaProductCodes: string[]

  // Discovery results
  discoveryProgress: number
  discoveryAgents: {
    localData: { status: string; progress: number; analyzed: number; total: number }
    literature: { status: string; progress: number; count: number }
    registry: { status: string; progress: number; count: number }
    fda: { status: string; progress: number; count: number }
    competitive: { status: string; progress: number; count: number }
    clinicalTrials: { status: string; progress: number; count: number }
    earlierPhaseFda: { status: string; progress: number; count: number }
    competitorTrials: { status: string; progress: number; count: number }
    competitorFda: { status: string; progress: number; count: number }
  }

  // Recommendations
  recommendations: Array<{
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
    aiRecommended: boolean  // true if AI recommends, false if alternative
    rejectionReason?: string  // Why AI didn't initially recommend (for alternatives)
  }>

  // Chat
  chatMessages: Array<{ id: string; role: 'user' | 'assistant'; content: string }>
  chatLoading: boolean
}

type Action =
  | { type: 'SET_PHASE'; phase: OnboardingState['phase'] }
  | { type: 'SET_SESSION'; sessionId: string }
  | { type: 'SET_LOADING'; loading: boolean; message?: string }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'SET_FOLDER_PATH'; path: string }
  | { type: 'SET_FOLDER_CONTENTS'; contents: FolderContents | null }
  | { type: 'SET_MANUFACTURER'; manufacturer: string }
  | { type: 'SET_STUDY_PHASE'; studyPhase: string }
  | { type: 'SET_COMPETITORS'; competitors: string[] }
  | { type: 'SET_FDA_PRODUCT_CODES'; fdaProductCodes: string[] }
  | { type: 'SET_DISCOVERY_PROGRESS'; progress: number; agents: OnboardingState['discoveryAgents'] }
  | { type: 'SET_RECOMMENDATIONS'; recommendations: OnboardingState['recommendations'] }
  | { type: 'UPDATE_RECOMMENDATION_STATUS'; id: string; status: ApprovalStatus }
  | { type: 'ADD_CHAT_MESSAGE'; message: { role: 'user' | 'assistant'; content: string } }
  | { type: 'SET_CHAT_LOADING'; loading: boolean }
  | { type: 'RESET' }

const initialState: OnboardingState = {
  phase: 'setup',
  sessionId: null,
  isLoading: false,
  loadingMessage: '',
  error: null,
  folderPath: './demo_data',
  folderContents: null,
  // Editable product context with sensible defaults
  manufacturer: 'Lima Corporate',
  studyPhase: 'Phase 4 Post-Market Surveillance',
  competitors: ['Zimmer Biomet', 'Stryker', 'Smith+Nephew', 'DePuy Synthes', 'Medacta'],
  fdaProductCodes: ['HWC', 'HWB', 'HTO', 'MAB', 'NXG'],
  discoveryProgress: 0,
  discoveryAgents: {
    localData: { status: 'pending', progress: 0, analyzed: 0, total: 0 },
    literature: { status: 'pending', progress: 0, count: 0 },
    registry: { status: 'pending', progress: 0, count: 0 },
    fda: { status: 'pending', progress: 0, count: 0 },
    competitive: { status: 'pending', progress: 0, count: 0 },
    clinicalTrials: { status: 'pending', progress: 0, count: 0 },
    earlierPhaseFda: { status: 'pending', progress: 0, count: 0 },
    competitorTrials: { status: 'pending', progress: 0, count: 0 },
    competitorFda: { status: 'pending', progress: 0, count: 0 },
  },
  recommendations: [],
  chatMessages: [],
  chatLoading: false,
}

function reducer(state: OnboardingState, action: Action): OnboardingState {
  switch (action.type) {
    case 'SET_PHASE':
      return { ...state, phase: action.phase }
    case 'SET_SESSION':
      return { ...state, sessionId: action.sessionId }
    case 'SET_LOADING':
      return { ...state, isLoading: action.loading, loadingMessage: action.message || '', error: null }
    case 'SET_ERROR':
      return { ...state, error: action.error, isLoading: false }
    case 'SET_FOLDER_PATH':
      return { ...state, folderPath: action.path }
    case 'SET_FOLDER_CONTENTS':
      return { ...state, folderContents: action.contents }
    case 'SET_MANUFACTURER':
      return { ...state, manufacturer: action.manufacturer }
    case 'SET_STUDY_PHASE':
      return { ...state, studyPhase: action.studyPhase }
    case 'SET_COMPETITORS':
      return { ...state, competitors: action.competitors }
    case 'SET_FDA_PRODUCT_CODES':
      return { ...state, fdaProductCodes: action.fdaProductCodes }
    case 'SET_DISCOVERY_PROGRESS':
      return { ...state, discoveryProgress: action.progress, discoveryAgents: action.agents }
    case 'SET_RECOMMENDATIONS':
      return { ...state, recommendations: action.recommendations }
    case 'UPDATE_RECOMMENDATION_STATUS':
      return {
        ...state,
        recommendations: state.recommendations.map(r =>
          r.id === action.id ? { ...r, status: action.status } : r
        ),
      }
    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        chatMessages: [...state.chatMessages, { ...action.message, id: `msg-${Date.now()}` }],
      }
    case 'SET_CHAT_LOADING':
      return { ...state, chatLoading: action.loading }
    case 'RESET':
      return initialState
    default:
      return state
  }
}

// Product catalog
const products: Record<string, Product> = {
  'delta-tt': {
    id: 'delta-tt',
    name: 'DELTA TT Revision Cup',
    category: 'Hip Reconstruction',
    indication: 'Revision THA',
    technologies: ['Trabecular Titanium', 'Porous Coating'],
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
}

export default function ProductConfig() {
  const { productId } = useParams<{ productId: string }>()
  const product = products[productId || '']
  const [state, dispatch] = useReducer(reducer, initialState)
  const [chatInput, setChatInput] = useState('')
  const [chatExpanded, setChatExpanded] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const welcomeShownRef = useRef(false)

  // SSE Progress hook for real-time discovery updates
  const progressHook = useOnboardingProgress(
    state.phase === 'discovery' ? state.sessionId : null,
    {
      onError: (error) => {
        dispatch({ type: 'SET_ERROR', error })
      },
    }
  )

  // Watch SSE progress updates and sync to our state
  useEffect(() => {
    if (state.phase !== 'discovery') return

    // Map SSE agent updates to our state format
    const agents = { ...state.discoveryAgents }
    const updates = progressHook.agentUpdates

    // Literature agent
    if (updates.literature) {
      agents.literature = {
        status: updates.literature.status === 'completed' ? 'complete' : updates.literature.status,
        progress: updates.literature.progress,
        count: updates.literature.items_found || 0,
      }
    }

    // Registry agent
    if (updates.registry) {
      agents.registry = {
        status: updates.registry.status === 'completed' ? 'complete' : updates.registry.status,
        progress: updates.registry.progress,
        count: updates.registry.items_found || 0,
      }
    }

    // FDA agent
    if (updates.fda) {
      agents.fda = {
        status: updates.fda.status === 'completed' ? 'complete' : updates.fda.status,
        progress: updates.fda.progress,
        count: updates.fda.items_found || 0,
      }
    }

    // Competitive agent
    if (updates.competitive) {
      agents.competitive = {
        status: updates.competitive.status === 'completed' ? 'complete' : updates.competitive.status,
        progress: updates.competitive.progress,
        count: updates.competitive.items_found || 0,
      }
    }

    dispatch({ type: 'SET_DISCOVERY_PROGRESS', progress: progressHook.overallProgress, agents })
  }, [state.phase, progressHook.overallProgress, progressHook.agentUpdates])

  // Handle SSE completion
  useEffect(() => {
    if (progressHook.isComplete && state.sessionId && state.phase === 'discovery') {
      // Discovery complete - move to recommendations phase
      generateRecommendationsPhase(state.sessionId)
    }
  }, [progressHook.isComplete, state.sessionId, state.phase])

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.chatMessages])

  // Add welcome message on mount (only once)
  useEffect(() => {
    if (product && !welcomeShownRef.current) {
      welcomeShownRef.current = true
      dispatch({
        type: 'ADD_CHAT_MESSAGE',
        message: {
          role: 'assistant',
          content: `Hello! I'm here to help you configure ${product.name} for the intelligence platform.\n\nYou can upload your study data and protocol document on the left, then click "Start Configuration" when ready.\n\nFeel free to ask me any questions about the configuration process!`,
        },
      })
    }
  }, [product])

  // Start onboarding
  const handleStart = useCallback(async () => {
    if (!product) return

    dispatch({ type: 'SET_LOADING', loading: true, message: 'Initializing AI configuration...' })

    try {
      const response = await startOnboarding({
        product_name: product.name,
        category: product.category,
        indication: product.indication,
        protocol_id: product.protocolId,
        technologies: product.technologies,
      })

      dispatch({ type: 'SET_SESSION', sessionId: response.session_id })
      dispatch({ type: 'SET_PHASE', phase: 'discovery' })

      // Add initial AI message
      dispatch({
        type: 'ADD_CHAT_MESSAGE',
        message: {
          role: 'assistant',
          content: `I'm analyzing ${product.name} and discovering relevant data sources. This includes searching PubMed for literature, identifying registry benchmarks, and scanning FDA databases.`,
        },
      })

      // Run discovery
      await runDiscoveryPhase(response.session_id)
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to start' })
    }
  }, [product])

  // Discovery phase - now uses real SSE events for progress
  const runDiscoveryPhase = async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', loading: true, message: 'Discovering intelligence sources...' })

    // Calculate local data totals based on folder contents
    const localTotal = state.folderContents ? (
      state.folderContents.studyData.count +
      (state.folderContents.protocol.found ? 1 : 0) +
      state.folderContents.literature.count +
      state.folderContents.extractedJson.count
    ) : 0

    // Initialize with local data analysis running (local data is analyzed synchronously)
    const initialAgents: OnboardingState['discoveryAgents'] = {
      localData: { status: 'complete', progress: 100, analyzed: localTotal, total: localTotal },
      literature: { status: 'pending', progress: 0, count: 0 },
      registry: { status: 'pending', progress: 0, count: 0 },
      fda: { status: 'pending', progress: 0, count: 0 },
      competitive: { status: 'pending', progress: 0, count: 0 },
      clinicalTrials: { status: 'pending', progress: 0, count: 0 },
      earlierPhaseFda: { status: 'pending', progress: 0, count: 0 },
      competitorTrials: { status: 'pending', progress: 0, count: 0 },
      competitorFda: { status: 'pending', progress: 0, count: 0 },
    }
    dispatch({ type: 'SET_DISCOVERY_PROGRESS', progress: 5, agents: initialAgents })

    try {
      // Trigger backend discovery - SSE hook will receive real-time updates
      // The progressHook.onComplete callback will call generateRecommendationsPhase
      await runDiscovery(sessionId)
      // Note: We don't call generateRecommendationsPhase here anymore
      // The SSE onComplete callback handles the transition
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Discovery failed' })
    }
  }

  // Generate recommendations
  const generateRecommendationsPhase = async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', loading: true, message: 'Generating recommendations...' })

    try {
      const response = await generateRecommendations(sessionId)

      // Transform recommendations - includes both AI-recommended and alternatives
      // Generate local data recommendations based on folder contents
      const localDataRecs: OnboardingState['recommendations'] = []

      // Study Data Files
      if (state.folderContents?.studyData && state.folderContents.studyData.count > 0) {
        localDataRecs.push({
          id: 'local_study_data',
          name: 'Study Data Files',
          type: 'local_study_data',
          status: 'pending',
          description: `${state.folderContents.studyData.count} Excel/CSV files containing clinical study data.`,
          preview: state.folderContents.studyData.files.slice(0, 2).join(', ') + (state.folderContents.studyData.count > 2 ? ` +${state.folderContents.studyData.count - 2} more` : ''),
          confidence: 0.95,
          whyRecommended: 'Primary data source for patient-level safety monitoring and regulatory reporting.',
          keyReasons: ['Primary source of adverse events', 'Required for MDR compliance', 'Enables revision rate calculations'],
          enabledInsights: ['Safety monitoring', 'Risk stratification', 'Revision rate analysis'],
          aiRecommended: true,
        })
      }

      // Protocol Document
      if (state.folderContents?.protocol?.found) {
        localDataRecs.push({
          id: 'local_protocol',
          name: 'Protocol Document',
          type: 'local_protocol',
          status: 'pending',
          description: `Study protocol document: ${state.folderContents.protocol.file || 'protocol.pdf'}`,
          preview: 'Defines study endpoints, inclusion criteria, and analysis plan',
          confidence: 0.98,
          whyRecommended: 'Essential for understanding study design and aligning analysis with protocol requirements.',
          keyReasons: ['Defines primary endpoints', 'Specifies analysis populations', 'Required for regulatory context'],
          enabledInsights: ['Endpoint definitions', 'Analysis plan alignment', 'Protocol deviations tracking'],
          aiRecommended: true,
        })
      }

      // Licensed Literature
      if (state.folderContents?.literature && state.folderContents.literature.count > 0) {
        localDataRecs.push({
          id: 'local_literature',
          name: 'Licensed Literature',
          type: 'local_literature',
          status: 'pending',
          description: `${state.folderContents.literature.count} PDF publications from your licensed literature collection.`,
          preview: state.folderContents.literature.files.slice(0, 2).join(', ') + (state.folderContents.literature.count > 2 ? ` +${state.folderContents.literature.count - 2} more` : ''),
          confidence: 0.88,
          whyRecommended: 'Curated publications directly relevant to your product and indication.',
          keyReasons: ['Pre-screened for relevance', 'Full-text access available', 'Supports evidence synthesis'],
          enabledInsights: ['Literature review', 'Evidence comparison', 'Claims support'],
          aiRecommended: true,
        })
      }

      // Extracted JSON Data
      if (state.folderContents?.extractedJson && state.folderContents.extractedJson.count > 0) {
        localDataRecs.push({
          id: 'local_extracted',
          name: 'Extracted Data (JSON)',
          type: 'local_extracted',
          status: 'pending',
          description: `${state.folderContents.extractedJson.count} pre-extracted JSON files with structured data.`,
          preview: state.folderContents.extractedJson.files.slice(0, 2).join(', ') + (state.folderContents.extractedJson.count > 2 ? ` +${state.folderContents.extractedJson.count - 2} more` : ''),
          confidence: 0.92,
          whyRecommended: 'Pre-processed data ready for analysis and integration.',
          keyReasons: ['Already structured', 'Validated extraction', 'Faster processing'],
          enabledInsights: ['Rapid integration', 'Cross-source linking', 'Structured queries'],
          aiRecommended: true,
        })
      }

      // Build recommendations from API response
      const recs: OnboardingState['recommendations'] = [
        // Local Data recommendations (from folder)
        ...localDataRecs,
      ]

      // Map registries from API response
      const apiRecs = response.recommendations?.recommendations
      if (apiRecs?.registries) {
        apiRecs.registries.forEach((reg, idx) => {
          // Parse relevance (can be string like "high", "medium", "low" or numeric)
          const relevanceNum = typeof reg.relevance === 'number'
            ? reg.relevance
            : reg.relevance === 'high' ? 0.9 : reg.relevance === 'medium' ? 0.7 : 0.5
          const isRecommended = reg.selected !== false && relevanceNum >= 0.7
          recs.push({
            id: `registry_${idx}`,
            name: reg.name,
            type: 'registry',
            status: 'pending',
            description: `${reg.region} orthopaedic registry`,
            preview: reg.data_years ? `Data from ${reg.data_years}` : 'Registry benchmark data',
            confidence: relevanceNum,
            whyRecommended: isRecommended
              ? `High relevance for benchmarking your study outcomes.`
              : `Alternative registry for regional insights.`,
            keyReasons: isRecommended
              ? ['Population-level outcomes', 'Survival benchmarks', 'Revision rate comparison']
              : ['Regional market data', 'Alternative benchmarks'],
            enabledInsights: ['Survival benchmarks', 'Comparative analysis'],
            aiRecommended: isRecommended,
            rejectionReason: !isRecommended && reg.exclusion_reason ? reg.exclusion_reason : undefined,
          })
        })
      }

      // Map literature from API response
      if (apiRecs?.literature) {
        const lit = apiRecs.literature
        // Add main literature source
        recs.push({
          id: 'literature_pubmed',
          name: 'PubMed Literature',
          type: 'literature',
          status: 'pending',
          description: `${lit.total_papers} relevant papers found, ${lit.selected_papers} selected for analysis`,
          preview: lit.top_papers?.slice(0, 2).map(p => p.title).join('; ') || 'Published evidence',
          confidence: 0.90,
          whyRecommended: 'Peer-reviewed publications provide clinical evidence for benchmarking and claims support.',
          keyReasons: ['Published outcomes data', 'Peer-reviewed evidence', 'Systematic literature review'],
          enabledInsights: lit.enabled_insights || ['Literature synthesis', 'Evidence comparison'],
          aiRecommended: true,
        })

        // Add individual top papers as separate recommendations
        lit.top_papers?.slice(0, 5).forEach((paper, idx) => {
          recs.push({
            id: `lit_${idx + 1}`,
            name: paper.title,
            type: 'literature',
            status: 'pending',
            description: `${paper.journal || 'Journal'} (${paper.year || 'Year'})`,
            preview: paper.insight || 'Published study',
            confidence: paper.relevance_score || 0.85,
            whyRecommended: 'Highly relevant publication identified by AI literature search.',
            keyReasons: ['Direct relevance to study', 'Clinical outcomes data'],
            enabledInsights: ['Evidence synthesis', 'Benchmarking'],
            aiRecommended: true,
          })
        })
      }

      // Map FDA surveillance from API response
      if (apiRecs?.fda_surveillance) {
        const fda = apiRecs.fda_surveillance
        recs.push({
          id: 'fda_maude',
          name: 'FDA MAUDE Database',
          type: 'fda',
          status: 'pending',
          description: 'Manufacturer and User Facility Device Experience database',
          preview: fda.preview || 'Adverse events for similar devices',
          confidence: 0.92,
          whyRecommended: 'Primary source for post-market adverse event surveillance.',
          keyReasons: ['Real-world adverse events', 'Signal detection capability', 'Competitor safety comparison'],
          enabledInsights: fda.enabled_insights || ['Safety signal detection', 'Adverse event trends'],
          aiRecommended: fda.selected !== false,
        })
      }

      // Use discovery results for FDA counts if available
      const discoveryResults = response.discovery_results?.discovery_results
      if (discoveryResults?.fda_discovery) {
        const fdaDiscovery = discoveryResults.fda_discovery
        if (fdaDiscovery.recalls > 0) {
          recs.push({
            id: 'fda_recalls',
            name: 'FDA Recall Database',
            type: 'fda',
            status: 'pending',
            description: 'Medical device recalls and safety communications',
            preview: `${fdaDiscovery.recalls} recalls for similar products`,
            confidence: 0.85,
            whyRecommended: 'Historical recall data for risk mitigation and competitive intelligence.',
            keyReasons: ['Recall root cause analysis', 'Design risk identification', 'Competitor safety issues'],
            enabledInsights: ['Risk mitigation', 'Safety benchmarking'],
            aiRecommended: true,
          })
        }
      }

      // Add competitive intelligence from discovery agent results
      const competitiveCount = state.discoveryAgents.competitive?.count || 0
      if (competitiveCount > 0) {
        recs.push({
          id: 'competitive_landscape',
          name: 'Competitive Intelligence',
          type: 'competitive',
          status: 'pending',
          description: 'Market landscape analysis for revision hip implants',
          preview: `${competitiveCount} competitors identified and analyzed`,
          confidence: 0.90,
          whyRecommended: 'Strategic positioning against key market players.',
          keyReasons: ['Market share analysis', 'Product differentiation', 'Competitive benchmarking'],
          enabledInsights: ['Market positioning', 'Competitive strategy'],
          aiRecommended: true,
        })
      }

      // Add clinical trials intelligence from discovery agent results
      const clinicalTrialsCount = state.discoveryAgents.clinicalTrials?.count || 0
      if (clinicalTrialsCount > 0) {
        recs.push({
          id: 'ct_own_trials',
          name: 'ClinicalTrials.gov - Own Trials',
          type: 'clinical_trials',
          status: 'pending',
          description: 'Active and completed trials registered under your protocol',
          preview: `${clinicalTrialsCount} trials found matching your study`,
          confidence: 0.94,
          whyRecommended: 'Direct regulatory-grade documentation of your clinical program.',
          keyReasons: ['Protocol registration verification', 'Study timeline tracking', 'Enrollment status monitoring'],
          enabledInsights: ['Clinical program oversight', 'Regulatory submission support'],
          aiRecommended: true,
        })
      }

      // Add competitor trials from discovery results
      const competitorTrialsCount = state.discoveryAgents.competitorTrials?.count || 0
      if (competitorTrialsCount > 0) {
        recs.push({
          id: 'ct_competitor_trials',
          name: 'Competitor Clinical Trials',
          type: 'competitor_trials',
          status: 'pending',
          description: 'Active trials from competing manufacturers',
          preview: `${competitorTrialsCount} competitor trials identified`,
          confidence: 0.89,
          whyRecommended: 'Competitor clinical activity intelligence for strategic positioning.',
          keyReasons: ['Competitive pipeline visibility', 'Trial design benchmarking', 'Endpoint comparison'],
          enabledInsights: ['Competitive landscape analysis', 'Clinical strategy optimization'],
          aiRecommended: true,
        })
      }

      // Add competitor FDA from discovery results
      const competitorFdaCount = state.discoveryAgents.competitorFda?.count || 0
      if (competitorFdaCount > 0) {
        recs.push({
          id: 'ct_competitor_fda',
          name: 'Competitor FDA Submissions',
          type: 'competitor_fda',
          status: 'pending',
          description: 'FDA 510(k) clearances and MAUDE adverse events for competitor products',
          preview: `${competitorFdaCount} competitor submissions analyzed`,
          confidence: 0.87,
          whyRecommended: 'Competitor regulatory intelligence enables safety benchmarking.',
          keyReasons: ['Competitor safety profile comparison', 'Clearance timeline benchmarks', 'Adverse event pattern analysis'],
          enabledInsights: ['Competitive safety positioning', 'Regulatory strategy optimization'],
          aiRecommended: true,
        })
      }

      // Add earlier phase FDA from discovery results
      const earlierPhaseFdaCount = state.discoveryAgents.earlierPhaseFda?.count || 0
      if (earlierPhaseFdaCount > 0) {
        recs.push({
          id: 'ct_earlier_phase_fda',
          name: 'Earlier Phase FDA Data',
          type: 'earlier_phase_fda',
          status: 'pending',
          description: 'FDA clearances and adverse events from earlier phases',
          preview: `${earlierPhaseFdaCount} historical records`,
          confidence: 0.91,
          whyRecommended: 'Historical regulatory data provides context for post-market surveillance.',
          keyReasons: ['Pre-market safety baseline', 'Historical adverse event trends', 'Regulatory pathway precedent'],
          enabledInsights: ['Long-term safety trending', 'Regulatory strategy validation'],
          aiRecommended: true,
        })
      }

      dispatch({ type: 'SET_RECOMMENDATIONS', recommendations: recs })
      dispatch({ type: 'SET_PHASE', phase: 'review' })
      dispatch({ type: 'SET_LOADING', loading: false })

      const aiRecommendedCount = recs.filter(r => r.aiRecommended).length
      const alternativesCount = recs.filter(r => !r.aiRecommended).length

      dispatch({
        type: 'ADD_CHAT_MESSAGE',
        message: {
          role: 'assistant',
          content: `I've identified ${aiRecommendedCount} recommended data sources for your review, plus ${alternativesCount} alternatives I considered but didn't initially recommend.\n\nYou can approve my recommendations, or override my decisions to include any alternatives. I'll explain my reasoning for each.`,
        },
      })
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to generate recommendations' })
    }
  }

  // Handle source approval
  const handleApprove = useCallback(async (sourceId: string, sourceType: string) => {
    if (!state.sessionId) return

    try {
      await updateSourceApproval(state.sessionId, sourceType, sourceId, { status: 'approved' })
      dispatch({ type: 'UPDATE_RECOMMENDATION_STATUS', id: sourceId, status: 'approved' })
    } catch (err) {
      console.error('Failed to approve:', err)
    }
  }, [state.sessionId])

  // Handle source rejection
  const handleReject = useCallback(async (sourceId: string, sourceType: string) => {
    if (!state.sessionId) return

    try {
      await updateSourceApproval(state.sessionId, sourceType, sourceId, { status: 'rejected', reason: 'User rejected' })
      dispatch({ type: 'UPDATE_RECOMMENDATION_STATUS', id: sourceId, status: 'rejected' })
    } catch (err) {
      console.error('Failed to reject:', err)
    }
  }, [state.sessionId])

  // Complete review and start research
  const handleCompleteReview = useCallback(async () => {
    if (!state.sessionId) return

    const approved = state.recommendations.filter(r => r.status === 'approved').length
    if (approved === 0) {
      dispatch({ type: 'SET_ERROR', error: 'Please approve at least one data source to continue.' })
      return
    }

    dispatch({ type: 'SET_LOADING', loading: true, message: 'Finalizing approvals...' })

    try {
      // Finalize the approvals first
      await finalizeApprovals(state.sessionId)

      // Start deep research as a background job
      dispatch({ type: 'SET_LOADING', loading: true, message: 'Initiating deep research...' })
      const researchResponse = await startDeepResearch(state.sessionId)

      dispatch({ type: 'SET_PHASE', phase: 'research' })

      dispatch({
        type: 'ADD_CHAT_MESSAGE',
        message: {
          role: 'assistant',
          content: `Deep research initiated! I'll analyze your ${approved} approved sources and generate comprehensive intelligence reports. This typically takes 5-15 minutes.\n\nYou'll be notified when complete. Redirecting you to the product dashboard...`,
        },
      })

      // Redirect to the product landing page
      if (researchResponse.redirect_to) {
        window.location.href = researchResponse.redirect_to
      } else {
        window.location.href = `/product/${productId}`
      }
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to start research' })
    }
  }, [state.sessionId, state.recommendations, productId])

  // Search ClinicalTrials.gov - Real API call
  const handleSearchClinicalTrials = useCallback(async (params: {
    ownTrials: { sponsor: string; condition: string; intervention: string; phases: string[]; status: string[]; dateRange: { start: string; end: string } };
    competitorTrials: { sponsors: string[]; condition: string; intervention: string; phases: string[]; dateRange: { start: string; end: string } };
  }) => {
    const isOwnSearch = params.ownTrials.sponsor.length > 0

    const response = await searchClinicalTrials({
      search_type: isOwnSearch ? 'own' : 'competitor',
      sponsor: isOwnSearch ? params.ownTrials.sponsor : undefined,
      condition: isOwnSearch ? params.ownTrials.condition : params.competitorTrials.condition,
      intervention: isOwnSearch ? params.ownTrials.intervention : params.competitorTrials.intervention,
      phases: isOwnSearch ? params.ownTrials.phases : params.competitorTrials.phases,
      statuses: isOwnSearch ? params.ownTrials.status : undefined,
      competitor_sponsors: !isOwnSearch ? params.competitorTrials.sponsors : undefined,
    })

    return {
      count: response.count,
      trials: response.trials.map(t => ({
        nctId: t.nctId,
        title: t.title,
        phase: t.phase,
        status: t.status,
        sponsor: t.sponsor,
      }))
    }
  }, [])

  // Search FDA Submissions - Real API call
  const handleSearchFDASubmissions = useCallback(async (params: {
    ownSubmissions: { applicant: string; productCodes: string[]; decisionDateRange: { start: string; end: string } };
    competitorSubmissions: { applicants: string[]; productCodes: string[]; decisionDateRange: { start: string; end: string } };
  }) => {
    const isOwnSearch = params.ownSubmissions.applicant.length > 0

    const response = await searchFDASubmissions({
      search_type: isOwnSearch ? 'own' : 'competitor',
      applicant: isOwnSearch ? params.ownSubmissions.applicant : undefined,
      product_codes: isOwnSearch ? params.ownSubmissions.productCodes : params.competitorSubmissions.productCodes,
      competitor_applicants: !isOwnSearch ? params.competitorSubmissions.applicants : undefined,
      date_start: isOwnSearch
        ? params.ownSubmissions.decisionDateRange.start
        : params.competitorSubmissions.decisionDateRange.start,
      date_end: isOwnSearch
        ? params.ownSubmissions.decisionDateRange.end
        : params.competitorSubmissions.decisionDateRange.end,
    })

    return {
      count: response.count,
      submissions: response.submissions.map(s => ({
        kNumber: s.kNumber,
        deviceName: s.deviceName,
        applicant: s.applicant,
        decisionDate: s.decisionDate,
      }))
    }
  }, [])

  // Send chat message
  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || !product) return

    const message = chatInput.trim()
    setChatInput('')

    dispatch({ type: 'ADD_CHAT_MESSAGE', message: { role: 'user', content: message } })
    dispatch({ type: 'SET_CHAT_LOADING', loading: true })

    try {
      let sessionId = state.sessionId

      // Create session if one doesn't exist
      if (!sessionId) {
        const response = await startOnboarding({
          product_name: product.name,
          category: product.category,
          indication: product.indication,
          protocol_id: product.protocolId,
          technologies: product.technologies,
        })
        sessionId = response.session_id
        dispatch({ type: 'SET_SESSION', sessionId })
      }

      const response = await chatWithAI(sessionId, { message, context: { phase: state.phase } })
      dispatch({ type: 'ADD_CHAT_MESSAGE', message: { role: 'assistant', content: response.response } })
    } catch (err) {
      dispatch({ type: 'ADD_CHAT_MESSAGE', message: { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' } })
    } finally {
      dispatch({ type: 'SET_CHAT_LOADING', loading: false })
    }
  }, [chatInput, state.sessionId, state.phase, product])

  // Calculate approval summary
  const approvalSummary = {
    approved: state.recommendations.filter(r => r.status === 'approved').length,
    rejected: state.recommendations.filter(r => r.status === 'rejected').length,
    pending: state.recommendations.filter(r => r.status === 'pending').length,
    total: state.recommendations.length,
    canProceed: state.recommendations.filter(r => r.status === 'approved').length > 0,
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <Navbar />
        <main className="max-w-2xl mx-auto py-20 px-6 text-center">
          <h1 className="text-2xl font-semibold text-neutral-900">Product Not Found</h1>
          <Link href="/" className="inline-flex items-center gap-2 mt-6 text-neutral-500 hover:text-neutral-900">
            <ArrowLeft className="w-4 h-4" />
            Back to Products
          </Link>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <Navbar />

      {/* Minimal Header */}
      <header className="bg-white border-b border-neutral-100">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href={`/product/${productId}`}
                className="w-8 h-8 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500 hover:bg-neutral-200 hover:text-neutral-900 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-neutral-900 tracking-tight">
                  {product.name}
                </h1>
                <p className="text-xs text-neutral-400">Data Steward Configuration</p>
              </div>
            </div>

            {/* Minimal Phase indicator */}
            {state.phase !== 'setup' && (
              <div className="flex items-center gap-1">
                {['discovery', 'review', 'research', 'complete'].map((phase, i) => (
                  <div
                    key={phase}
                    className={`
                      w-2 h-2 rounded-full transition-all
                      ${state.phase === phase
                        ? 'bg-neutral-900 w-6'
                        : ['discovery', 'review', 'research', 'complete'].indexOf(state.phase) > i
                          ? 'bg-neutral-900'
                          : 'bg-neutral-200'
                      }
                    `}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content - Centered, Full Width */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Setup Phase */}
        {state.phase === 'setup' && (
          <div className="space-y-6">
            {/* Hero */}
            <div className="text-center py-8">
              <div className="w-12 h-12 bg-neutral-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-neutral-900 mb-2">
                Configure Intelligence Sources
              </h2>
              <p className="text-sm text-neutral-500 max-w-md mx-auto">
                AI will discover and recommend optimal data sources for {product.name}
              </p>
            </div>

            {/* Product Summary - Inline Pills */}
            <div className="flex flex-wrap items-center justify-center gap-2">
              <span className="px-3 py-1.5 bg-white border border-neutral-200 rounded-full text-xs text-neutral-600">
                {product.category}
              </span>
              <span className="px-3 py-1.5 bg-white border border-neutral-200 rounded-full text-xs text-neutral-600">
                {product.indication}
              </span>
              <span className="px-3 py-1.5 bg-white border border-neutral-200 rounded-full text-xs text-neutral-600">
                Protocol {product.protocolId}
              </span>
              {product.technologies.map(tech => (
                <span key={tech} className="px-3 py-1.5 bg-neutral-900 text-white rounded-full text-xs">
                  {tech}
                </span>
              ))}
            </div>

            {/* Editable Product Context */}
            <div className="bg-white rounded-2xl border border-neutral-200 p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-neutral-900">Product Context</h3>
                <span className="text-xs text-neutral-400">Used for data source discovery</span>
              </div>

              {/* Manufacturer & Study Phase */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-500 mb-1.5">Manufacturer</label>
                  <input
                    type="text"
                    value={state.manufacturer}
                    onChange={(e) => dispatch({ type: 'SET_MANUFACTURER', manufacturer: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                    placeholder="e.g., Lima Corporate"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-500 mb-1.5">Study Phase</label>
                  <select
                    value={state.studyPhase}
                    onChange={(e) => dispatch({ type: 'SET_STUDY_PHASE', studyPhase: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                  >
                    <option value="Phase 1">Phase 1</option>
                    <option value="Phase 2">Phase 2</option>
                    <option value="Phase 3">Phase 3</option>
                    <option value="Phase 4 Post-Market Surveillance">Phase 4 Post-Market Surveillance</option>
                  </select>
                </div>
              </div>

              {/* Competitors */}
              <div>
                <label className="block text-xs font-medium text-neutral-500 mb-1.5">
                  <Building2 className="w-3.5 h-3.5 inline mr-1" />
                  Competitors
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {state.competitors.map((competitor, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-purple-50 text-purple-700 rounded-lg text-xs"
                    >
                      {competitor}
                      <button
                        onClick={() => dispatch({
                          type: 'SET_COMPETITORS',
                          competitors: state.competitors.filter((_, i) => i !== idx)
                        })}
                        className="hover:text-purple-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add competitor..."
                    className="flex-1 px-3 py-1.5 bg-neutral-50 border border-neutral-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-neutral-900"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                        dispatch({
                          type: 'SET_COMPETITORS',
                          competitors: [...state.competitors, e.currentTarget.value.trim()]
                        })
                        e.currentTarget.value = ''
                      }
                    }}
                  />
                  <button
                    onClick={(e) => {
                      const input = e.currentTarget.previousElementSibling as HTMLInputElement
                      if (input.value.trim()) {
                        dispatch({
                          type: 'SET_COMPETITORS',
                          competitors: [...state.competitors, input.value.trim()]
                        })
                        input.value = ''
                      }
                    }}
                    className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-xs hover:bg-purple-200 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* FDA Product Codes */}
              <div>
                <label className="block text-xs font-medium text-neutral-500 mb-1.5">
                  <Shield className="w-3.5 h-3.5 inline mr-1" />
                  FDA Product Codes
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {state.fdaProductCodes.map((code, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-700 rounded-lg text-xs font-mono"
                    >
                      {code}
                      <button
                        onClick={() => dispatch({
                          type: 'SET_FDA_PRODUCT_CODES',
                          fdaProductCodes: state.fdaProductCodes.filter((_, i) => i !== idx)
                        })}
                        className="hover:text-amber-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add FDA code (e.g., HWC)..."
                    className="flex-1 px-3 py-1.5 bg-neutral-50 border border-neutral-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-neutral-900"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                        dispatch({
                          type: 'SET_FDA_PRODUCT_CODES',
                          fdaProductCodes: [...state.fdaProductCodes, e.currentTarget.value.trim().toUpperCase()]
                        })
                        e.currentTarget.value = ''
                      }
                    }}
                  />
                  <button
                    onClick={(e) => {
                      const input = e.currentTarget.previousElementSibling as HTMLInputElement
                      if (input.value.trim()) {
                        dispatch({
                          type: 'SET_FDA_PRODUCT_CODES',
                          fdaProductCodes: [...state.fdaProductCodes, input.value.trim().toUpperCase()]
                        })
                        input.value = ''
                      }
                    }}
                    className="px-3 py-1.5 bg-amber-100 text-amber-700 rounded-lg text-xs hover:bg-amber-200 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-xs text-neutral-400 mt-1.5">
                  Hip codes: HWC (Acetabular Cup), HWB (Femoral Head), HTO (Hip Prosthesis)
                </p>
              </div>
            </div>

            {/* Local Data Sources - Clean Card */}
            <div className="bg-white rounded-2xl border border-neutral-200 p-6">
              <LocalDataConfig
                folderPath={state.folderPath}
                folderContents={state.folderContents}
                onFolderPathChange={(path) => dispatch({ type: 'SET_FOLDER_PATH', path })}
                onValidateFolder={async (path) => {
                  // Call backend API to analyze the folder
                  try {
                    const response = await analyzeFolder(path)
                    // Convert API response to FolderContents type
                    const contents: FolderContents = {
                      path: response.path,
                      validated: response.validated,
                      studyData: response.studyData,
                      protocol: response.protocol,
                      literature: response.literature,
                      extractedJson: response.extractedJson,
                    }
                    dispatch({ type: 'SET_FOLDER_CONTENTS', contents })
                    return contents
                  } catch (error) {
                    console.error('Folder analysis failed:', error)
                    throw error
                  }
                }}
              />
            </div>

            {/* Start Button */}
            <button
              onClick={handleStart}
              disabled={state.isLoading}
              className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-neutral-900 text-white font-medium rounded-2xl hover:bg-neutral-800 transition-all disabled:opacity-50"
            >
              {state.isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {state.loadingMessage}
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Start Configuration
                </>
              )}
            </button>
          </div>
        )}

        {/* Discovery Phase */}
        {state.phase === 'discovery' && (
          <div className="bg-white rounded-2xl border border-neutral-200 p-8">
            <div className="text-center mb-8">
              <h2 className="text-lg font-semibold text-neutral-900 mb-1">Discovering Sources</h2>
              <p className="text-sm text-neutral-500">{state.discoveryProgress}% complete</p>
            </div>

            {/* Progress Bar */}
            <div className="h-1 bg-neutral-100 rounded-full overflow-hidden mb-8">
              <div
                className="h-full bg-neutral-900 rounded-full transition-all duration-500"
                style={{ width: `${state.discoveryProgress}%` }}
              />
            </div>

            {/* Agent Progress - Three Sections */}
            <div className="space-y-6">
              {/* Local Data Sources - from validated folder */}
              {state.folderContents?.validated && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider">Local Data Sources</p>
                    {state.discoveryAgents.localData.status === 'running' && (
                      <span className="text-xs text-neutral-400">
                        Analyzing {state.discoveryAgents.localData.analyzed} of {state.discoveryAgents.localData.total} files...
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {/* Study Data */}
                    <div className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
                      state.discoveryAgents.localData.status === 'complete'
                        ? 'bg-emerald-50 border border-emerald-100'
                        : state.discoveryAgents.localData.status === 'running'
                          ? 'bg-blue-50 border border-blue-100'
                          : 'bg-neutral-50 border border-neutral-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-300 ${
                        state.discoveryAgents.localData.status === 'complete'
                          ? 'bg-emerald-600'
                          : state.discoveryAgents.localData.status === 'running'
                            ? 'bg-blue-500'
                            : 'bg-neutral-300'
                      }`}>
                        {state.discoveryAgents.localData.status === 'running' ? (
                          <Loader2 className="w-4 h-4 text-white animate-spin" />
                        ) : state.discoveryAgents.localData.status === 'complete' ? (
                          <Check className="w-4 h-4 text-white" />
                        ) : (
                          <Database className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900">Study Data</p>
                        <p className="text-xs text-neutral-500 truncate">
                          {state.folderContents.studyData.count} files
                        </p>
                      </div>
                      {state.discoveryAgents.localData.status === 'complete' && (
                        <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      )}
                    </div>

                    {/* Protocol */}
                    <div className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
                      state.discoveryAgents.localData.status === 'complete'
                        ? (state.folderContents.protocol.found ? 'bg-emerald-50 border border-emerald-100' : 'bg-amber-50 border border-amber-100')
                        : state.discoveryAgents.localData.status === 'running'
                          ? 'bg-blue-50 border border-blue-100'
                          : 'bg-neutral-50 border border-neutral-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-300 ${
                        state.discoveryAgents.localData.status === 'complete'
                          ? (state.folderContents.protocol.found ? 'bg-emerald-600' : 'bg-amber-500')
                          : state.discoveryAgents.localData.status === 'running'
                            ? 'bg-blue-500'
                            : 'bg-neutral-300'
                      }`}>
                        {state.discoveryAgents.localData.status === 'running' ? (
                          <Loader2 className="w-4 h-4 text-white animate-spin" />
                        ) : state.discoveryAgents.localData.status === 'complete' ? (
                          <FileText className="w-4 h-4 text-white" />
                        ) : (
                          <FileText className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900">Protocol</p>
                        <p className="text-xs text-neutral-500 truncate">
                          {state.discoveryAgents.localData.status === 'complete'
                            ? (state.folderContents.protocol.found ? state.folderContents.protocol.file : 'Not found')
                            : 'Scanning...'}
                        </p>
                      </div>
                      {state.discoveryAgents.localData.status === 'complete' && state.folderContents.protocol.found && (
                        <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      )}
                    </div>

                    {/* Literature */}
                    <div className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
                      state.discoveryAgents.localData.status === 'complete'
                        ? (state.folderContents.literature.count > 0 ? 'bg-emerald-50 border border-emerald-100' : 'bg-neutral-50')
                        : state.discoveryAgents.localData.status === 'running'
                          ? 'bg-blue-50 border border-blue-100'
                          : 'bg-neutral-50 border border-neutral-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-300 ${
                        state.discoveryAgents.localData.status === 'complete'
                          ? (state.folderContents.literature.count > 0 ? 'bg-emerald-600' : 'bg-neutral-300')
                          : state.discoveryAgents.localData.status === 'running'
                            ? 'bg-blue-500'
                            : 'bg-neutral-300'
                      }`}>
                        {state.discoveryAgents.localData.status === 'running' ? (
                          <Loader2 className="w-4 h-4 text-white animate-spin" />
                        ) : (
                          <BookOpen className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900">Literature</p>
                        <p className="text-xs text-neutral-500 truncate">
                          {state.discoveryAgents.localData.status === 'complete'
                            ? `${state.folderContents.literature.count} files`
                            : 'Scanning...'}
                        </p>
                      </div>
                      {state.discoveryAgents.localData.status === 'complete' && state.folderContents.literature.count > 0 && (
                        <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      )}
                    </div>

                    {/* Extracted JSON */}
                    <div className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
                      state.discoveryAgents.localData.status === 'complete'
                        ? (state.folderContents.extractedJson.count > 0 ? 'bg-emerald-50 border border-emerald-100' : 'bg-neutral-50')
                        : state.discoveryAgents.localData.status === 'running'
                          ? 'bg-blue-50 border border-blue-100'
                          : 'bg-neutral-50 border border-neutral-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-300 ${
                        state.discoveryAgents.localData.status === 'complete'
                          ? (state.folderContents.extractedJson.count > 0 ? 'bg-emerald-600' : 'bg-neutral-300')
                          : state.discoveryAgents.localData.status === 'running'
                            ? 'bg-blue-500'
                            : 'bg-neutral-300'
                      }`}>
                        {state.discoveryAgents.localData.status === 'running' ? (
                          <Loader2 className="w-4 h-4 text-white animate-spin" />
                        ) : (
                          <FileText className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900">Extracted JSON</p>
                        <p className="text-xs text-neutral-500 truncate">
                          {state.discoveryAgents.localData.status === 'complete'
                            ? `${state.folderContents.extractedJson.count} files`
                            : 'Scanning...'}
                        </p>
                      </div>
                      {state.discoveryAgents.localData.status === 'complete' && state.folderContents.extractedJson.count > 0 && (
                        <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      )}
                    </div>
                  </div>

                  {/* Progress bar for local data analysis */}
                  {state.discoveryAgents.localData.status === 'running' && (
                    <div className="mt-3">
                      <div className="h-1 bg-blue-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all duration-500"
                          style={{ width: `${state.discoveryAgents.localData.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Folder path display */}
                  <div className="mt-2 px-3 py-1.5 bg-neutral-100 rounded-lg">
                    <p className="text-xs text-neutral-500 truncate">
                      <span className="font-medium">Path:</span> {state.folderPath}
                    </p>
                  </div>
                </div>
              )}

              {/* Primary Sources */}
              <div>
                <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-3">Primary Sources</p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { key: 'literature', icon: BookOpen, label: 'Literature' },
                    { key: 'registry', icon: BarChart3, label: 'Registries' },
                    { key: 'competitive', icon: Database, label: 'Competitive' },
                    { key: 'fda', icon: Shield, label: 'FDA' },
                  ].map(({ key, icon: Icon, label }) => {
                    const agent = state.discoveryAgents[key as keyof typeof state.discoveryAgents]
                    return (
                      <div key={key} className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${agent.status === 'complete' ? 'bg-neutral-900' : 'bg-white'}`}>
                          {agent.status === 'running' ? (
                            <Loader2 className="w-4 h-4 text-neutral-400 animate-spin" />
                          ) : agent.status === 'complete' ? (
                            <Check className="w-4 h-4 text-white" />
                          ) : (
                            <Icon className="w-4 h-4 text-neutral-300" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-neutral-900">{label}</p>
                          <p className="text-xs text-neutral-400">{agent.count} found</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* ClinicalTrials.gov & Phase-Aware Sources */}
              <div>
                <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-3">ClinicalTrials.gov & Phase Analysis</p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { key: 'clinicalTrials', icon: FlaskConical, label: 'Own Trials' },
                    { key: 'earlierPhaseFda', icon: History, label: 'Earlier Phase FDA' },
                    { key: 'competitorTrials', icon: Users, label: 'Competitor Trials' },
                    { key: 'competitorFda', icon: ClipboardList, label: 'Competitor FDA' },
                  ].map(({ key, icon: Icon, label }) => {
                    const agent = state.discoveryAgents[key as keyof typeof state.discoveryAgents]
                    return (
                      <div key={key} className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${agent.status === 'complete' ? 'bg-indigo-600' : 'bg-white'}`}>
                          {agent.status === 'running' ? (
                            <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
                          ) : agent.status === 'complete' ? (
                            <Check className="w-4 h-4 text-white" />
                          ) : (
                            <Icon className="w-4 h-4 text-neutral-300" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-neutral-900">{label}</p>
                          <p className="text-xs text-neutral-400">{agent.count} found</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Review Phase */}
        {state.phase === 'review' && (
          <DataSourceWizard
            recommendations={state.recommendations}
            onApprove={handleApprove}
            onReject={handleReject}
            onComplete={handleCompleteReview}
            isLoading={state.isLoading}
            approvalSummary={approvalSummary}
            folderContents={state.folderContents}
            folderPath={state.folderPath}
            productContext={{
              productName: product.name,
              manufacturer: state.manufacturer,
              category: product.category,
              indication: product.indication,
              studyPhase: state.studyPhase,
              competitors: state.competitors,
              fdaProductCodes: state.fdaProductCodes,
            }}
            onSearchClinicalTrials={handleSearchClinicalTrials}
            onSearchFDASubmissions={handleSearchFDASubmissions}
          />
        )}

        {/* Research Phase */}
        {state.phase === 'research' && (
          <div className="bg-white rounded-2xl border border-neutral-200 p-12 text-center">
            <div className="w-12 h-12 bg-neutral-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Loader2 className="w-6 h-6 text-white animate-spin" />
            </div>
            <h2 className="text-lg font-semibold text-neutral-900 mb-1">Running Deep Research</h2>
            <p className="text-sm text-neutral-500">
              Generating reports on approved sources...
            </p>
          </div>
        )}

        {/* Complete Phase */}
        {state.phase === 'complete' && (
          <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
            <div className="p-8 text-center">
              <div className="w-12 h-12 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Check className="w-6 h-6 text-emerald-600" />
              </div>
              <h2 className="text-lg font-semibold text-neutral-900 mb-1">Configuration Complete</h2>
              <p className="text-sm text-neutral-500">
                {product.name} is ready for all personas
              </p>
            </div>

            <div className="px-6 pb-6 space-y-2">
              {/* Local folder */}
              {state.folderContents?.validated && (
                <ConfiguredSource
                  label="Study Folder"
                  fileName={state.folderPath.split('/').pop() || state.folderPath}
                  count={
                    state.folderContents.studyData.count +
                    (state.folderContents.protocol.found ? 1 : 0) +
                    state.folderContents.literature.count +
                    state.folderContents.extractedJson.count
                  }
                  icon="folder"
                />
              )}

              {/* Approved recommendations */}
              {state.recommendations.filter(r => r.status === 'approved').map(rec => (
                <ConfiguredSource
                  key={rec.id}
                  label={rec.type}
                  fileName={rec.name}
                  icon={rec.type === 'clinical' ? 'database' : rec.type === 'literature' ? 'publication' : 'document'}
                />
              ))}
            </div>

            <div className="p-4 border-t border-neutral-100">
              <Link
                href={`/product/${productId}`}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-neutral-900 text-white font-medium rounded-xl hover:bg-neutral-800 transition-all"
              >
                Go to Dashboard
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}
      </main>

      {/* Floating Chat Widget */}
      <div className="fixed bottom-6 right-6 z-50">
        {chatExpanded ? (
          /* Expanded Chat Panel */
          <div className="w-80 bg-white rounded-2xl shadow-2xl border border-neutral-200 overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
            {/* Header */}
            <div className="px-4 py-3 bg-neutral-900 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-white" />
                <span className="text-sm font-medium text-white">AI Assistant</span>
              </div>
              <button
                onClick={() => setChatExpanded(false)}
                className="w-6 h-6 rounded-lg bg-white/10 flex items-center justify-center text-white/70 hover:bg-white/20 hover:text-white transition-all"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Messages */}
            <div className="h-80 overflow-y-auto p-4 space-y-3 bg-neutral-50">
              {state.chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`
                      max-w-[85%] px-3 py-2 rounded-xl text-sm
                      ${msg.role === 'user'
                        ? 'bg-neutral-900 text-white'
                        : 'bg-white border border-neutral-200 text-neutral-700'
                      }
                    `}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}

              {state.chatLoading && (
                <div className="flex justify-start">
                  <div className="px-3 py-2 bg-white border border-neutral-200 rounded-xl">
                    <Loader2 className="w-4 h-4 text-neutral-400 animate-spin" />
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t border-neutral-100">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask anything..."
                  className="flex-1 px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!chatInput.trim() || state.chatLoading}
                  className="w-9 h-9 bg-neutral-900 text-white rounded-lg flex items-center justify-center hover:bg-neutral-800 transition-all disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Collapsed Chat Button */
          <button
            onClick={() => setChatExpanded(true)}
            className="w-14 h-14 bg-neutral-900 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-neutral-800 hover:scale-105 transition-all"
          >
            <MessageCircle className="w-6 h-6" />
            {state.chatMessages.length > 1 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-white text-neutral-900 text-xs font-medium rounded-full flex items-center justify-center border-2 border-neutral-900">
                {state.chatMessages.length}
              </span>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
