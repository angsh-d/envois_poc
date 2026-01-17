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
  display?: DisplayData
}

interface ChatRequest {
  message: string
  context: string
  study_id: string
  history?: ChatMessage[]
}

// Display types for intelligent chat responses
export type DisplayPreference = 'narrative' | 'table' | 'chart' | 'metric_grid' | 'mixed'
export type ChartType = 'line' | 'bar' | 'area' | 'scatter' | 'kaplan_meier'

export interface ChartDataPoint {
  x: number | string
  y: number
  label?: string
  group?: string
  ci_lower?: number
  ci_upper?: number
}

export interface ChartSeries {
  name: string
  color: string
  data: ChartDataPoint[]
}

export interface ReferenceLine {
  y: number
  label: string
  color?: string
  strokeDasharray?: string
}

export interface ChartConfig {
  chart_type: ChartType
  title: string
  x_label: string
  y_label: string
  series: ChartSeries[]
  reference_lines?: ReferenceLine[]
  y_domain?: [number, number]
  show_legend: boolean
  show_grid: boolean
}

export interface TableColumn {
  key: string
  label: string
  format: 'text' | 'number' | 'percent' | 'date'
}

export interface HighlightRule {
  column: string
  condition: string
  style: 'warning' | 'danger' | 'success'
}

export interface TableConfig {
  title?: string
  columns: TableColumn[]
  rows: Record<string, unknown>[]
  sortable: boolean
  highlight_rules?: HighlightRule[]
}

export interface MetricGridItem {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'neutral'
  delta?: string
  status?: 'success' | 'warning' | 'danger' | 'neutral'
  icon?: string
}

export interface DisplayData {
  preferred_display: DisplayPreference
  chart_data?: ChartConfig
  table_data?: TableConfig
  metric_grid?: MetricGridItem[]
  narrative_sections?: Array<{ title: string; content: string }>
}

interface ChatResponse {
  response: string
  sources: Source[]
  evidence?: Evidence
  suggested_followups?: string[]
  display?: DisplayData
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
  reported_rate: number | null
  reference: string
  doi?: string
  local_source?: string
  provenance?: {
    page?: number
    table?: string
    quote?: string
    context?: string
    local_source?: string
    doi?: string
  }
}

export interface MetricProvenance {
  data_sources: {
    event_count: string
    patient_count: string
    threshold: string
  }
  methodology: string
  calculation: string
  confidence_interval?: string
  threshold_source: string
  threshold_rationale: string
  regulatory_reference: string
  signal_classification?: string
}

export interface SafetyMetric {
  metric: string
  rate: number
  count: number
  total: number
  threshold: number
  signal: boolean
  threshold_exceeded_by: number
  ci_lower?: number
  ci_upper?: number
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
  monitored_metrics: SafetyMetric[]
  n_monitored: number
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
  patients_with_patient_level_deviations: number
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
  high_risk_count: number
  moderate_risk_count: number
  low_risk_count: number
  high_risk_pct: number
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

// Protocol Rules Update API
export interface ProtocolRuleUpdate {
  field_path: string
  value: string | number | boolean | string[]
}

export async function updateProtocolRule(fieldPath: string, value: string | number | boolean | string[]): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/protocol/rules`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ field_path: fieldPath, value }),
  })
  if (!response.ok) {
    throw new Error(`Failed to update protocol rule: ${response.statusText}`)
  }
  return response.json()
}

export async function updateProtocolRulesBatch(updates: ProtocolRuleUpdate[]): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}/protocol/rules/batch`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ updates }),
  })
  if (!response.ok) {
    throw new Error(`Failed to batch update protocol rules: ${response.statusText}`)
  }
  return response.json()
}

// Monte Carlo Simulation API Types
export interface MonteCarloRiskDistribution {
  age_over_80?: number
  bmi_over_35?: number
  diabetes?: number
  osteoporosis?: number
  rheumatoid_arthritis?: number
  chronic_kidney_disease?: number
  smoking?: number
  prior_revision?: number
  severe_bone_loss?: number
  paprosky_3b?: number
}

export interface MonteCarloRequest {
  n_patients: number
  threshold: string
  n_iterations: number
  risk_distribution?: MonteCarloRiskDistribution
  seed?: number
}

export interface MonteCarloResponse {
  success: boolean
  n_iterations: number
  n_patients: number
  threshold: number
  threshold_name: string
  mean_revision_rate: number
  median_revision_rate: number
  p5_revision_rate: number
  p95_revision_rate: number
  std_revision_rate: number
  probability_pass: number
  probability_pass_pct: number
  verdict: 'high_confidence' | 'uncertain' | 'at_risk'
  verdict_label: string
  variance_contributions: Record<string, number>
  execution_time_ms: number
  generated_at: string
}

export interface HazardRatioSpec {
  factor: string
  point_estimate: number
  ci_lower: number
  ci_upper: number
  source: string
}

export interface HazardRatiosResponse {
  success: boolean
  n_factors: number
  factors: HazardRatioSpec[]
  sources: string[]
}

export interface ScenarioSpec {
  name: string
  description?: string
  risk_distribution?: MonteCarloRiskDistribution
  exclusions?: string[]
}

export interface ScenarioResult {
  name: string
  description: string
  probability_pass: number
  probability_pass_pct: number
  mean_revision_rate: number
  mean_revision_rate_pct: number
  p5_revision_rate: number
  p95_revision_rate: number
  ci_90: string
  verdict: string
  delta_probability?: number
  delta_probability_pct?: number
  delta_mean_rate?: number
}

export interface ScenarioComparisonResponse {
  success: boolean
  n_scenarios: number
  threshold: string
  threshold_name: string
  scenarios: ScenarioResult[]
  generated_at: string
}

export async function runMonteCarloSimulation(request: MonteCarloRequest): Promise<MonteCarloResponse> {
  const response = await fetch(`${API_BASE}/simulation/monte-carlo/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Monte Carlo simulation failed: ${response.statusText}`)
  }
  return response.json()
}

export async function compareMonteCarloScenarios(
  scenarios: ScenarioSpec[],
  nPatients: number = 549,
  threshold: string = 'fda_510k',
  nIterations: number = 10000,
  seed: number = 42
): Promise<ScenarioComparisonResponse> {
  const response = await fetch(`${API_BASE}/simulation/monte-carlo/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      scenarios,
      n_patients: nPatients,
      threshold,
      n_iterations: nIterations,
      seed,
    }),
  })
  if (!response.ok) {
    throw new Error(`Scenario comparison failed: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchHazardRatios(): Promise<HazardRatiosResponse> {
  const response = await fetch(`${API_BASE}/simulation/monte-carlo/hazard-ratios`)
  if (!response.ok) {
    throw new Error(`Failed to fetch hazard ratios: ${response.statusText}`)
  }
  return response.json()
}

export async function quickMonteCarloSimulation(
  nPatients: number = 549,
  threshold: string = 'fda_510k'
): Promise<MonteCarloResponse> {
  const response = await fetch(`${API_BASE}/simulation/monte-carlo/quick?n_patients=${nPatients}&threshold=${threshold}`)
  if (!response.ok) {
    throw new Error(`Quick simulation failed: ${response.statusText}`)
  }
  return response.json()
}

// Data Browser API Types
export interface DataBrowserTableInfo {
  name: string
  row_count: number
  description: string
}

export interface DataBrowserColumnSchema {
  name: string
  type: string
  nullable: boolean
  primary_key: boolean
}

export interface DataBrowserTableDataResponse {
  rows: Record<string, unknown>[]
  total: number
  page: number
  limit: number
  columns: DataBrowserColumnSchema[]
}

export async function fetchDataBrowserTables(): Promise<DataBrowserTableInfo[]> {
  const response = await fetch(`${API_BASE}/data-browser/tables`)
  if (!response.ok) {
    throw new Error(`Failed to fetch tables: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDataBrowserTableData(
  tableName: string,
  page: number = 1,
  limit: number = 25,
  sortBy?: string,
  sortDir: 'asc' | 'desc' = 'asc'
): Promise<DataBrowserTableDataResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort_dir: sortDir,
  })
  if (sortBy) {
    params.set('sort_by', sortBy)
  }
  const response = await fetch(`${API_BASE}/data-browser/tables/${tableName}?${params}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch table data: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDataBrowserTableSchema(tableName: string): Promise<DataBrowserColumnSchema[]> {
  const response = await fetch(`${API_BASE}/data-browser/tables/${tableName}/schema`)
  if (!response.ok) {
    throw new Error(`Failed to fetch table schema: ${response.statusText}`)
  }
  return response.json()
}

export async function updateDataBrowserRow(
  tableName: string,
  rowId: number,
  data: Record<string, unknown>
): Promise<{ success: boolean; updated: Record<string, unknown> }> {
  const response = await fetch(`${API_BASE}/data-browser/tables/${tableName}/${rowId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Failed to update row: ${response.statusText}`)
  }
  return response.json()
}

// ============================================================================
// ENHANCED CHAT API - Advanced Agentic Capabilities
// ============================================================================

export type AlertSeverity = 'critical' | 'warning' | 'info' | 'resolved'
export type AlertCategory = 'threshold_exceeded' | 'threshold_approaching' | 'trend_detected' | 'outlier_detected' | 'data_quality' | 'compliance_issue'

export interface SafetyAlert {
  id: string
  category: AlertCategory
  severity: AlertSeverity
  title: string
  description: string
  metric_name: string
  current_value: number
  threshold_value?: number
  benchmark_value?: number
  trend_direction?: 'increasing' | 'decreasing' | 'stable'
  affected_patients: string[]
  data_source: string
  created_at: string
  acknowledged: boolean
  acknowledged_at?: string
  acknowledged_by?: string
  recommendations: string[]
  related_alerts: string[]
}

export interface ReasoningStep {
  step: string
  input_data: Record<string, unknown>
  reasoning: string
  output: Record<string, unknown>
  confidence: number
  timestamp: string
}

export interface EnhancedChatRequest {
  message: string
  session_id?: string
  study_id?: string
  context?: string
  enable_reasoning?: boolean
  enable_investigation?: boolean
}

export interface EnhancedChatResponse {
  response: string
  session_id: string
  sources: Source[]
  reasoning_trace?: ReasoningStep[]
  follow_up_suggestions: string[]
  safety_alerts?: SafetyAlert[]
  confidence: number
  display_preference: DisplayPreference
}

export interface SafetyAlertSummary {
  total_active: number
  critical_count: number
  warning_count: number
  alerts: SafetyAlert[]
  proactive_insights: string[]
}

export interface CorrelationRequest {
  variable_1_name: string
  variable_1_values: number[]
  variable_2_name: string
  variable_2_values: number[]
  correlation_type?: 'pearson' | 'spearman'
}

export interface CorrelationResponse {
  variable_1: string
  variable_2: string
  correlation_type: string
  coefficient: number
  p_value: number
  sample_size: number
  significance: 'highly_significant' | 'significant' | 'marginally_significant' | 'not_significant'
  interpretation: string
  confidence_interval?: [number, number]
}

export interface InvestigationRequest {
  question: string
  study_id?: string
  max_depth?: number
}

export interface InvestigationHypothesis {
  id: string
  statement: string
  rationale: string
  status: 'proposed' | 'investigating' | 'supported' | 'refuted' | 'inconclusive'
  supporting_evidence: string[]
  refuting_evidence: string[]
  confidence: number
}

export interface InvestigationRecommendation {
  recommendation: string
  priority: 'high' | 'medium' | 'low'
  rationale: string
  effort: 'high' | 'medium' | 'low'
  expected_impact: string
}

export interface InvestigationResponse {
  question: string
  summary: string
  hypotheses: InvestigationHypothesis[]
  findings: Array<{ finding: string; source: string; confidence: number }>
  recommendations: InvestigationRecommendation[]
  reasoning_trace: ReasoningStep[]
  confidence: number
}

export interface ProactiveSuggestions {
  page_context: string
  suggestions: string[]
  safety_insights: string[]
  trending_topics: string[]
}

// Enhanced Chat API Functions

export async function sendEnhancedChatMessage(
  request: EnhancedChatRequest
): Promise<EnhancedChatResponse> {
  const response = await fetch(`${API_BASE}/enhanced-chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Enhanced chat request failed: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchSafetyAlerts(
  severity?: AlertSeverity,
  acknowledged?: boolean
): Promise<SafetyAlertSummary> {
  const params = new URLSearchParams()
  if (severity) params.set('severity', severity)
  if (acknowledged !== undefined) params.set('acknowledged', String(acknowledged))

  const url = params.toString()
    ? `${API_BASE}/enhanced-chat/safety-alerts?${params}`
    : `${API_BASE}/enhanced-chat/safety-alerts`

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch safety alerts: ${response.statusText}`)
  }
  return response.json()
}

export async function acknowledgeAlert(alertId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/enhanced-chat/safety-alerts/${alertId}/acknowledge`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to acknowledge alert: ${response.statusText}`)
  }
  return response.json()
}

export async function analyzeCorrelation(request: CorrelationRequest): Promise<CorrelationResponse> {
  const response = await fetch(`${API_BASE}/enhanced-chat/analyze/correlation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Correlation analysis failed: ${response.statusText}`)
  }
  return response.json()
}

export async function runInvestigation(request: InvestigationRequest): Promise<InvestigationResponse> {
  const response = await fetch(`${API_BASE}/enhanced-chat/investigate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Investigation failed: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchProactiveSuggestions(pageContext: string): Promise<ProactiveSuggestions> {
  const response = await fetch(`${API_BASE}/enhanced-chat/suggestions/${pageContext}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch suggestions: ${response.statusText}`)
  }
  return response.json()
}

export async function getSessionInfo(sessionId: string): Promise<{
  session_id: string
  study_id: string
  created_at: string
  updated_at: string
  message_count: number
  page_context: string
  has_summary: boolean
}> {
  const response = await fetch(`${API_BASE}/enhanced-chat/session/${sessionId}`)
  if (!response.ok) {
    throw new Error(`Failed to get session info: ${response.statusText}`)
  }
  return response.json()
}

export async function endSession(sessionId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/enhanced-chat/session/${sessionId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Failed to end session: ${response.statusText}`)
  }
  return response.json()
}

// ============================================================================
// UC7: COMPETITIVE INTELLIGENCE API
// ============================================================================

export type CompetitivePosition = 'STRONG' | 'COMPETITIVE' | 'DEVELOPING'

export interface QuickStat {
  stat: string
  value: string
  context: string
}

export interface Differentiator {
  category: string
  differentiator: string
  evidence: string
}

export interface Rebuttal {
  objection: string
  rebuttal: string
}

export interface CompetitiveLandscapeResponse {
  success: boolean
  report_type: string
  generated_at: string
  study_metrics: Record<string, unknown>
  competitive_landscape?: string
  registry_comparison: Array<Record<string, unknown>>
  literature_benchmarks: Record<string, unknown>
  key_differentiators: Differentiator[]
  sources: Array<Record<string, unknown>>
  confidence: number
}

export interface BenchmarkingResponse {
  success: boolean
  report_type: string
  generated_at: string
  study_metrics: Record<string, unknown>
  registry_benchmarks: Record<string, unknown>
  literature_comparison: Array<Record<string, unknown>>
  overall_position: {
    position: CompetitivePosition
    description: string
    favorable_metrics: number
    total_metrics: number
  }
  sources: Array<Record<string, unknown>>
  confidence: number
}

export interface BattleCardResponse {
  success: boolean
  report_type: string
  generated_at: string
  product: string
  battle_card_content?: string
  quick_stats: QuickStat[]
  talking_points: string[]
  rebuttals: Rebuttal[]
  sources: Array<Record<string, unknown>>
  confidence: number
}

export async function fetchCompetitiveLandscape(): Promise<CompetitiveLandscapeResponse> {
  const response = await fetch(`${API_BASE}/uc7/landscape`)
  if (!response.ok) {
    throw new Error(`Failed to fetch competitive landscape: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchCompetitiveBenchmarking(): Promise<BenchmarkingResponse> {
  const response = await fetch(`${API_BASE}/uc7/benchmarking`)
  if (!response.ok) {
    throw new Error(`Failed to fetch competitive benchmarking: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchBattleCard(): Promise<BattleCardResponse> {
  const response = await fetch(`${API_BASE}/uc7/battle-card`)
  if (!response.ok) {
    throw new Error(`Failed to fetch battle card: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDifferentiators(): Promise<{
  success: boolean
  generated_at: string
  product: string
  differentiators: Differentiator[]
  sources: Array<Record<string, unknown>>
}> {
  const response = await fetch(`${API_BASE}/uc7/differentiators`)
  if (!response.ok) {
    throw new Error(`Failed to fetch differentiators: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchTalkingPoints(): Promise<{
  success: boolean
  generated_at: string
  product: string
  talking_points: string[]
  quick_stats: QuickStat[]
  sources: Array<Record<string, unknown>>
}> {
  const response = await fetch(`${API_BASE}/uc7/talking-points`)
  if (!response.ok) {
    throw new Error(`Failed to fetch talking points: ${response.statusText}`)
  }
  return response.json()
}

// ============================================================================
// UC10: CLAIM VALIDATION API
// ============================================================================

export type ClaimValidationStatus = 'validated' | 'partial' | 'not_validated' | 'insufficient_evidence'
export type ClaimConfidenceLevel = 'high' | 'medium' | 'low'

export interface ClaimEvidence {
  type: string
  evidence: string
  claim_value?: string
}

export interface ClaimValidationResponse {
  success: boolean
  claim: string
  validated_at: string
  claim_validated: boolean | string
  validation_status: ClaimValidationStatus
  supporting_evidence: ClaimEvidence[]
  contradicting_evidence: ClaimEvidence[]
  evidence_gaps: string[]
  confidence_level: ClaimConfidenceLevel
  recommended_language?: string
  analysis?: string
  compliance_notes: string[]
  sources: Array<Record<string, unknown>>
  study_data_used: Record<string, unknown>
}

export interface ClaimBatchResult {
  claim: string
  validated?: boolean | string
  status?: ClaimValidationStatus
  confidence?: ClaimConfidenceLevel
  recommended_language?: string
  error?: string
}

export interface ClaimBatchResponse {
  success: boolean
  validated_at: string
  n_claims: number
  summary: {
    validated: number
    partial: number
    not_validated: number
  }
  results: ClaimBatchResult[]
}

export async function validateClaim(claim: string): Promise<ClaimValidationResponse> {
  const response = await fetch(`${API_BASE}/uc10/validate-claim`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ claim }),
  })
  if (!response.ok) {
    throw new Error(`Failed to validate claim: ${response.statusText}`)
  }
  return response.json()
}

export async function validateClaimsBatch(claims: string[]): Promise<ClaimBatchResponse> {
  const response = await fetch(`${API_BASE}/uc10/validate-batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(claims),
  })
  if (!response.ok) {
    throw new Error(`Failed to validate claims batch: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchExampleClaims(): Promise<{
  example_claims: Array<{
    category: string
    claim: string
    expected: string
  }>
  validation_statuses: Array<{
    status: string
    description: string
  }>
}> {
  const response = await fetch(`${API_BASE}/uc10/example-claims`)
  if (!response.ok) {
    throw new Error(`Failed to fetch example claims: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchComplianceGuidelines(): Promise<{
  guidelines: Array<{
    category: string
    guidance: string
    example_issue: string
  }>
  regulatory_references: string[]
}> {
  const response = await fetch(`${API_BASE}/uc10/compliance-guidelines`)
  if (!response.ok) {
    throw new Error(`Failed to fetch compliance guidelines: ${response.statusText}`)
  }
  return response.json()
}

// ============================================================================
// PRODUCTS API
// ============================================================================

export type ProductStatus = 'active' | 'configured' | 'pending'

export interface Product {
  id: string
  name: string
  category: string
  description: string
  status: ProductStatus
  indication: string
  study_phase?: string
  study_id?: string
  data_last_updated?: string
}

export interface ProductsResponse {
  success: boolean
  products: Product[]
  total: number
  generated_at: string
}

export interface DataTimestampResponse {
  last_updated: string
  formatted: string
}

export async function fetchProducts(): Promise<ProductsResponse> {
  const response = await fetch(`${API_BASE}/products`)
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchProduct(productId: string): Promise<Product> {
  const response = await fetch(`${API_BASE}/products/${productId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch product: ${response.statusText}`)
  }
  return response.json()
}

export async function fetchDataTimestamp(): Promise<DataTimestampResponse> {
  const response = await fetch(`${API_BASE}/products/data-timestamp`)
  if (!response.ok) {
    throw new Error(`Failed to fetch data timestamp: ${response.statusText}`)
  }
  return response.json()
}
