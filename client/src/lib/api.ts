const API_BASE = '/api/v1'

export type ConfidenceLevel = 'high' | 'moderate' | 'low' | 'insufficient'
export type DataLineage = 'raw_data' | 'calculated' | 'llm_synthesis' | 'aggregated'

export interface SourceMetadata {
  abbreviation?: string
  report_year?: number
  data_years?: string
  n_procedures?: number
  data_completeness?: number
  publication_id?: string
  publication_title?: string
  publication_year?: number
  n_patients?: number
  follow_up_years?: number
  strengths?: string[]
  limitations?: string[]
}

export interface Source {
  type: string
  reference: string
  detail?: string
  confidence: number
  confidence_level: ConfidenceLevel
  lineage: DataLineage
  metadata?: SourceMetadata
}

export interface RevisionReason {
  reason: string
  percentage: number
  description?: string
}

export interface SourceRawData {
  full_name?: string
  abbreviation?: string
  report_year?: number
  data_years?: string
  population?: string
  n_procedures?: number
  n_primary?: number
  survival_1yr?: number
  survival_2yr?: number
  survival_5yr?: number
  survival_10yr?: number
  survival_15yr?: number
  revision_rate_1yr?: number
  revision_rate_2yr?: number
  revision_rate_median?: number
  revision_rate_p75?: number
  revision_rate_p95?: number
  revision_reasons?: RevisionReason[]
}

export interface EvidenceDataPoint {
  source: string
  source_type: string
  value?: number
  value_formatted: string
  sample_size?: number
  year?: string
  context?: string
  raw_data?: SourceRawData
}

export interface EvidenceMetric {
  metric_name: string
  claim: string
  aggregated_value?: string
  calculation_method?: string
  data_points: EvidenceDataPoint[]
  confidence_level: string
}

export interface Evidence {
  summary: string
  metrics: EvidenceMetric[]
  total_sources: number
  total_sample_size?: number
}

export interface ChatMessage {
  role: string
  content: string
  sources?: Source[]
  evidence?: Evidence
  timestamp: string
  codeResponse?: CodeGenerationResponse
}

interface ChatRequest {
  message: string
  context: string
  study_id: string
  history?: ChatMessage[]
}

interface ChatResponse {
  response: string
  sources: Source[]
  evidence?: Evidence
  suggested_followups?: string[]
}

export async function sendChatMessage(
  message: string,
  context: string,
  studyId: string,
  history: ChatMessage[] = []
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
    context,
    study_id: studyId,
    history
  }
  
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })
  
  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`)
  }
  
  return response.json()
}

export interface CodeGenerationResponse {
  success: boolean
  language: string
  code: string
  explanation: string
  error?: string
  execution_result?: string
  execution_error?: string
  data_preview?: {
    columns: string[]
    row_count: number
    sample_rows: Record<string, unknown>[]
  }
  warnings: string[]
  suggested_followups: string[]
}

export async function generateCode(
  request: string,
  language?: string,
  execute: boolean = false,
  studyId: string = 'H-34'
): Promise<CodeGenerationResponse> {
  const response = await fetch(`${API_BASE}/chat/generate-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      request,
      language,
      execute,
      study_id: studyId
    })
  })
  
  if (!response.ok) {
    throw new Error(`Code generation failed: ${response.statusText}`)
  }
  
  return response.json()
}

export function isCodeGenerationRequest(message: string): boolean {
  const keywords = [
    'write code', 'generate code', 'code for', 'show me code', 'python code',
    'r code', 'sql query', 'sql code', 'c code', 'script for', 'program for',
    'write a script', 'write a query', 'create code', 'give me code',
    'kaplan-meier code', 'survival code', 'write python', 'write r', 'write sql',
    'in python', 'in r', 'using r', 'query for', 'query to', 'code to', 'script to'
  ]
  const messageLower = message.toLowerCase()
  return keywords.some(kw => messageLower.includes(kw))
}

export interface DashboardMetric {
  name: string
  value: number | string
  status: 'on_track' | 'warning' | 'critical' | 'success' | 'danger'
  trend?: string
  detail?: string
}

export interface DashboardPriority {
  priority: number | string
  title?: string
  description?: string
  status: string
  action?: string
}

export interface DashboardExecutiveSummary {
  success: boolean
  generated_at: string
  overall_status: string
  headline: string
  metrics: DashboardMetric[]
  top_priorities: DashboardPriority[]
  key_findings: string[]
  narrative?: string
  data_sources: string[]
}

export interface DashboardStudyProgress {
  success: boolean
  generated_at: string
  target_enrollment: number
  current_enrollment: number
  enrollment_pct: number
  interim_target: number
  status: string
  evaluable_patients: number
  completion_rate: number
  protocol_id?: string
  primary_endpoint: Record<string, unknown>
  sources: Array<Record<string, unknown>>
}

export interface BenchmarkComparison {
  metric: string
  study_value: number
  benchmark_value: number
  benchmark_range?: [number, number]
  benchmark_source: string
  source?: string
  comparison_status?: string
  status: 'favorable' | 'comparable' | 'unfavorable' | 'success' | 'warning' | 'danger'
  detail?: string
}

export interface LiteratureCitation {
  id: string
  citation: string
  title: string
  year: number
}

export interface DashboardBenchmarks {
  success: boolean
  generated_at: string
  comparisons: BenchmarkComparison[]
  literature_sources: string[]
  literature_citations: LiteratureCitation[]
  registry_sources: string[]
}

export async function fetchDashboardExecutiveSummary(): Promise<DashboardExecutiveSummary> {
  const response = await fetch(`${API_BASE}/uc5/dashboard/executive-summary`)
  if (!response.ok) {
    throw new Error(`Failed to fetch executive summary: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDashboardStudyProgress(): Promise<DashboardStudyProgress> {
  const response = await fetch(`${API_BASE}/uc5/dashboard/study-progress`)
  if (!response.ok) {
    throw new Error(`Failed to fetch study progress: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDashboardBenchmarks(): Promise<DashboardBenchmarks> {
  const response = await fetch(`${API_BASE}/uc5/dashboard/benchmarks`)
  if (!response.ok) {
    throw new Error(`Failed to fetch benchmarks: ${response.statusText}`)
  }
  return response.json()
}

export interface ReadinessResponse {
  success: boolean
  assessment_date: string
  protocol_id?: string
  protocol_version?: string
  is_ready: boolean
  ready_for_submission: boolean
  blocking_issues: Array<{
    category: string
    issue: string
    provenance?: Record<string, unknown>
  }>
  enrollment: {
    enrolled: number
    target: number
    interim_target: number
    percent_complete: number
    status: string
    is_ready: boolean
  }
  compliance: {
    deviation_rate: number
    by_severity: Record<string, number>
    status: string
    is_ready: boolean
  }
  safety: {
    n_signals: number
    overall_status: string
    is_ready: boolean
  }
  data_completeness: {
    enrolled: number
    completed: number
    withdrawn: number
    evaluable: number
    completion_rate: number
    is_ready: boolean
  }
  narrative?: string
  sources: Array<{
    type: string
    reference: string
    confidence: number
    details?: {
      data_source?: string
      data_fields?: string[]
      query_types?: string[]
      protocol_id?: string
      sample_size_target?: number
      primary_endpoint?: string
      regulatory_reference?: string
      calculation?: string
      protocol_reference?: string
      thresholds_source?: string
      metrics_evaluated?: string[]
    }
  }>
  execution_time_ms: number
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const response = await fetch(`${API_BASE}/uc1/readiness/assessment`)
  if (!response.ok) {
    throw new Error(`Failed to fetch readiness: ${response.statusText}`)
  }
  return response.json()
}

export interface SafetySignal {
  metric: string
  rate: number
  threshold: number
  signal_level: 'high' | 'medium' | 'low'
  recommended_action: string
}

export interface AffectedPatient {
  patient_id: string
  event_description: string
  severity: string
  event_date: string | null
  is_sae: boolean
  demographics: {
    gender: string | null
    age: number | null
    bmi: number | null
    diagnosis: string | null
  }
}

export interface LiteratureCitation {
  citation_id: string
  title: string
  year: number
  journal: string
  n_patients: number
  reported_rate: number
  reference: string
}

export interface MetricProvenance {
  data_sources: {
    event_count: string
    patient_count: string
    threshold: string
  }
  methodology: string
  calculation: string
  threshold_source: string
  threshold_rationale: string
  regulatory_reference: string
}

export interface SafetyMetric {
  metric: string
  rate: number
  count: number
  total: number
  threshold: number
  signal: boolean
  threshold_exceeded_by: number
  provenance?: MetricProvenance
  affected_patients?: AffectedPatient[]
  literature_citations?: LiteratureCitation[]
  signal_level?: string
  recommended_action?: string
}

export interface RegistryBenchmark {
  registry_id: string
  name: string
  abbreviation: string
  report_year: number
  n_procedures: number
  revision_rate_2yr: number
  survival_2yr: number
}

export interface RegistryComparison {
  metric: string
  study_value: number
  registry_median: number
  registry_p75: number
  registry_p95: number
  signal: boolean
  signal_level: string | null
  difference: number
  favorable: boolean
  percentile_position: string
}

export interface SafetyResponse {
  success: boolean
  detection_date: string
  signals: SafetyMetric[]
  n_signals: number
  high_priority: SafetyMetric[]
  medium_priority: SafetyMetric[]
  requires_dsmb_review: boolean
  sources: Array<{ type: string; reference: string; confidence?: number }>
  execution_time_ms: number
}

export async function fetchSafetySignals(): Promise<SafetyResponse> {
  const response = await fetch(`${API_BASE}/uc2/safety/signals`)
  if (!response.ok) {
    throw new Error(`Failed to fetch safety signals: ${response.statusText}`)
  }
  return response.json()
}

export interface DeviationRecord {
  patient_id: string
  deviation_type: string
  severity: 'major' | 'minor' | 'critical' | string
  classification: string
  visit: string
  description: string
  date?: string
  resolution?: string
  impact?: string
  action?: string
  requires_explanation?: boolean
  affects_evaluability?: boolean
}

export interface DetectorResult {
  detector: string
  description: string
  deviations_found: number
  findings: string[]
}

export interface DeviationsResponse {
  success: boolean
  assessment_date: string
  total_visits: number
  total_deviations: number
  visits_with_deviations: number
  compliant_visits: number
  deviation_rate: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  by_visit: Record<string, number>
  deviations: DeviationRecord[]
  detector_results: DetectorResult[]
  protocol_version?: string
  sources: Array<{ type: string; reference: string; confidence: number }>
  execution_time_ms: number
}

export async function fetchDeviations(_studyId?: string): Promise<DeviationsResponse> {
  const response = await fetch(`${API_BASE}/uc3/deviations/summary`)
  if (!response.ok) {
    throw new Error(`Failed to fetch deviations: ${response.statusText}`)
  }
  return response.json()
}

export interface ContributingFactor {
  factor: string
  hazard_ratio: number
  contribution: number
  category?: string
}

export interface DemographicFactor {
  factor: string
  display_name: string
  value: number | boolean
  impact: 'low' | 'moderate' | 'high'
  category: string
}

export interface Recommendation {
  action: string
  rationale: string
  priority: string
}

export interface PatientRiskDetail {
  patient_id: string
  risk_score: number
  clinical_risk_score?: number
  demographic_risk_score?: number
  n_risk_factors: number
  n_demographic_factors?: number
  contributing_factors: ContributingFactor[]
  clinical_factors?: ContributingFactor[]
  demographic_factors?: DemographicFactor[]
  recommendations: Recommendation[]
}

export interface FactorPrevalence {
  factor: string
  count: number
  percentage: number
  hazard_ratio: number
}

export interface RiskSummaryResponse {
  success: boolean
  assessment_date: string
  n_patients: number
  risk_distribution: Record<string, number>
  high_risk_patients: PatientRiskDetail[]
  moderate_risk_patients: PatientRiskDetail[]
  low_risk_patients: PatientRiskDetail[]
  factor_prevalence: FactorPrevalence[]
  mean_risk_score: number
  median_risk_score?: number
  std_risk_score?: number
  note?: string
}

export async function fetchRiskSummary(): Promise<RiskSummaryResponse> {
  const response = await fetch(`${API_BASE}/uc4/risk/population`)
  if (!response.ok) {
    throw new Error(`Failed to fetch risk summary: ${response.statusText}`)
  }
  return response.json()
}
