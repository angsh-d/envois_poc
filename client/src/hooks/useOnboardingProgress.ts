import { useState, useEffect, useCallback, useRef } from 'react'
import {
  subscribeToProgress,
  ProgressEvent,
  ONBOARDING_PHASES,
} from '../lib/onboardingApi'

interface AgentProgress {
  status: string
  progress: number
  items_found?: number
}

interface ProgressState {
  phase: string
  overallProgress: number
  agentUpdates: Record<string, AgentProgress>
  isConnected: boolean
  isComplete: boolean
  error: string | null
  messages: string[]
}

interface UseOnboardingProgressOptions {
  onPhaseChange?: (phase: string) => void
  onProgress?: (progress: number) => void
  onComplete?: (data: Record<string, unknown>) => void
  onError?: (error: string) => void
}

export function useOnboardingProgress(
  sessionId: string | null,
  options: UseOnboardingProgressOptions = {}
) {
  const [state, setState] = useState<ProgressState>({
    phase: ONBOARDING_PHASES.CONTEXT_CAPTURE,
    overallProgress: 0,
    agentUpdates: {},
    isConnected: false,
    isComplete: false,
    error: null,
    messages: [],
  })

  const unsubscribeRef = useRef<(() => void) | null>(null)
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Handle incoming SSE events
  const handleEvent = useCallback((event: ProgressEvent) => {
    setState(prev => {
      const newState = { ...prev }

      switch (event.event_type) {
        case 'phase_change':
          newState.phase = event.phase
          if (event.message) {
            newState.messages = [...prev.messages, event.message]
          }
          optionsRef.current.onPhaseChange?.(event.phase)
          break

        case 'progress':
          newState.overallProgress = event.overall_progress
          if (event.agent_updates) {
            newState.agentUpdates = event.agent_updates as Record<string, AgentProgress>
          }
          optionsRef.current.onProgress?.(event.overall_progress)
          break

        case 'complete':
          newState.phase = ONBOARDING_PHASES.COMPLETE
          newState.overallProgress = 100
          newState.isComplete = true
          newState.isConnected = false
          if (event.message) {
            newState.messages = [...prev.messages, event.message]
          }
          optionsRef.current.onComplete?.(event.data || {})
          break

        case 'error':
          newState.error = event.message || 'An error occurred'
          newState.isConnected = false
          optionsRef.current.onError?.(newState.error)
          break
      }

      return newState
    })
  }, [])

  // Handle connection errors
  const handleError = useCallback((error: Error) => {
    setState(prev => ({
      ...prev,
      error: error.message,
      isConnected: false,
    }))
    optionsRef.current.onError?.(error.message)
  }, [])

  // Connect to SSE stream
  const connect = useCallback(() => {
    if (!sessionId) return

    // Clean up existing connection
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
    }

    setState(prev => ({
      ...prev,
      isConnected: true,
      error: null,
    }))

    unsubscribeRef.current = subscribeToProgress(
      sessionId,
      handleEvent,
      handleError
    )
  }, [sessionId, handleEvent, handleError])

  // Disconnect from SSE stream
  const disconnect = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }
    setState(prev => ({
      ...prev,
      isConnected: false,
    }))
  }, [])

  // Reset state
  const reset = useCallback(() => {
    disconnect()
    setState({
      phase: ONBOARDING_PHASES.CONTEXT_CAPTURE,
      overallProgress: 0,
      agentUpdates: {},
      isConnected: false,
      isComplete: false,
      error: null,
      messages: [],
    })
  }, [disconnect])

  // Auto-connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId, connect, disconnect])

  return {
    ...state,
    connect,
    disconnect,
    reset,
  }
}

// Helper hook to get formatted phase display
export function usePhaseDisplay(phase: string) {
  const phaseLabels: Record<string, string> = {
    context_capture: 'Analyzing Context',
    discovery: 'Discovering Sources',
    recommendations: 'Generating Recommendations',
    deep_research: 'Running Research',
    complete: 'Complete',
  }

  const phaseIcons: Record<string, string> = {
    context_capture: '🔍',
    discovery: '🔎',
    recommendations: '💡',
    deep_research: '📚',
    complete: '✅',
  }

  return {
    label: phaseLabels[phase] || phase,
    icon: phaseIcons[phase] || '⏳',
  }
}
