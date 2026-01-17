/**
 * Research API client for deep research status polling.
 * Provides functions to interact with the async research endpoints.
 */

const API_BASE = '/api/v1'

export type ResearchJobStatus = 'pending' | 'running' | 'ingesting' | 'researching' | 'generating' | 'complete' | 'failed'

export interface ResearchStage {
  name: string
  status: 'pending' | 'running' | 'complete' | 'failed'
  progress: number
  started_at?: string
  completed_at?: string
  error?: string
}

export interface ResearchStatusResponse {
  job_id: string
  session_id: string
  status: ResearchJobStatus
  progress: number
  current_stage: string | null
  current_stage_label: string
  stages: ResearchStage[]
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
  result_data?: Record<string, unknown>
}

export interface StartResearchResponse {
  job_id: string
  session_id: string
  status: string
  message: string
  redirect_to: string
}

/**
 * Start a deep research job for the given session.
 * Returns immediately with job details - processing happens in background.
 */
export async function startDeepResearch(sessionId: string): Promise<StartResearchResponse> {
  const response = await fetch(`${API_BASE}/onboarding/${sessionId}/research/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to start research' }))
    throw new Error(error.detail || 'Failed to start research')
  }

  return response.json()
}

/**
 * Get the current status of a research job.
 */
export async function getResearchStatus(sessionId: string): Promise<ResearchStatusResponse> {
  const response = await fetch(`${API_BASE}/onboarding/${sessionId}/research/status`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get research status' }))
    throw new Error(error.detail || 'Failed to get research status')
  }

  return response.json()
}

/**
 * Cancel an in-progress research job.
 */
export async function cancelResearch(sessionId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/onboarding/${sessionId}/research/cancel`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to cancel research' }))
    throw new Error(error.detail || 'Failed to cancel research')
  }

  return response.json()
}

/**
 * Get a human-readable label for a stage name.
 */
export function getStageLabel(stageName: string): string {
  const labels: Record<string, string> = {
    data_ingestion: 'Processing Data Sources',
    competitive_landscape: 'Analyzing Competitive Landscape',
    sota_analysis: 'Researching State of the Art',
    regulatory_analysis: 'Analyzing Regulatory Precedents',
    report_generation: 'Generating Intelligence Reports',
  }
  return labels[stageName] || stageName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

/**
 * Check if research is still in progress.
 */
export function isResearchInProgress(status: ResearchJobStatus): boolean {
  return ['pending', 'running', 'ingesting', 'researching', 'generating'].includes(status)
}

/**
 * Check if research completed successfully.
 */
export function isResearchComplete(status: ResearchJobStatus): boolean {
  return status === 'complete'
}

/**
 * Check if research failed.
 */
export function isResearchFailed(status: ResearchJobStatus): boolean {
  return status === 'failed'
}
