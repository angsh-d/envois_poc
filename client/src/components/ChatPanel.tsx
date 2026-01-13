import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, MessageCircle, X, Sparkles, Clock, Maximize2, Minimize2, Shield } from 'lucide-react'
import { ChatMessage, sendChatMessage, Source, Evidence } from '@/lib/api'
import { ResponseDisplay } from './ResponseDisplay'
import { ProvenanceCard } from './ProvenanceCard'
import { EvidencePanel } from './EvidencePanel'

interface ChatPanelProps {
  studyId: string
  context: string
  isOpen: boolean
  onToggle: () => void
}

// Panel size configurations
const PANEL_SIZES = {
  compact: { width: 420, height: 600 },
  expanded: { width: 720, height: 700 },
  fullscreen: { width: '90vw', height: '85vh' }
} as const

type PanelSize = keyof typeof PANEL_SIZES

interface CachedResponse {
  response: string
  sources: Source[]
  evidence?: Evidence
  timestamp: number
}

// Cache configuration for response persistence
// Version 4: Updated to include raw_data for drill-down transparency
const CACHE_KEY_PREFIX = 'chat_cache_v4_'
const CACHE_EXPIRY_MS = 24 * 60 * 60 * 1000 // 24 hours
const ARTIFICIAL_DELAY_MS = 1500 // Show spinner for cached responses

// Generate a hash key for caching
function generateCacheKey(message: string, context: string, studyId: string): string {
  const normalized = `${message.toLowerCase().trim()}|${context}|${studyId}`
  let hash = 0
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return `${CACHE_KEY_PREFIX}${Math.abs(hash).toString(36)}`
}

// Get cached response
function getCachedResponse(key: string): CachedResponse | null {
  try {
    const cached = localStorage.getItem(key)
    if (!cached) return null

    const parsed: CachedResponse = JSON.parse(cached)
    if (Date.now() - parsed.timestamp > CACHE_EXPIRY_MS) {
      localStorage.removeItem(key)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

// Set cached response
function setCachedResponse(key: string, response: string, sources: Source[], evidence?: Evidence): void {
  try {
    const data: CachedResponse = {
      response,
      sources,
      evidence,
      timestamp: Date.now()
    }
    localStorage.setItem(key, JSON.stringify(data))
  } catch {
    // Storage full or unavailable - silently fail
  }
}

// Format timestamp
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

export function ChatPanel({ studyId, context, isOpen, onToggle }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isCached, setIsCached] = useState(false)
  const [panelSize, setPanelSize] = useState<PanelSize>('compact')
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const toggleSize = useCallback(() => {
    setPanelSize(current => {
      if (current === 'compact') return 'expanded'
      if (current === 'expanded') return 'fullscreen'
      return 'compact'
    })
  }, [])

  const currentSize = PANEL_SIZES[panelSize]
  const panelWidth = typeof currentSize.width === 'number' ? `${currentSize.width}px` : currentSize.width
  const panelHeight = typeof currentSize.height === 'number' ? `${currentSize.height}px` : currentSize.height

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [isOpen])

  // Keyboard shortcuts: Escape to minimize
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (panelSize !== 'compact') {
          setPanelSize('compact')
        } else {
          onToggle()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, panelSize, onToggle])

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)
    setIsCached(false)

    // Check cache first
    const cacheKey = generateCacheKey(currentInput, context, studyId)
    const cached = getCachedResponse(cacheKey)

    try {
      if (cached) {
        // Serve cached response with artificial delay
        setIsCached(true)
        await new Promise(resolve => setTimeout(resolve, ARTIFICIAL_DELAY_MS))

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: cached.response,
          sources: cached.sources,
          evidence: cached.evidence,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else {
        // Fetch fresh response
        const response = await sendChatMessage(
          currentInput,
          context,
          studyId,
          messages
        )

        // Cache the response
        setCachedResponse(cacheKey, response.response, response.sources, response.evidence)

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          sources: response.sources,
          evidence: response.evidence,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])

        // Update suggested followups if provided
        if (response.suggested_followups && response.suggested_followups.length > 0) {
          setSuggestedFollowups(response.suggested_followups)
        }
      }
    } catch {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setIsCached(false)
    }
  }, [input, isLoading, context, studyId, messages])

  // Initial suggested questions showcasing new capabilities
  const initialSuggestedQuestions = [
    'How do our outcomes compare to all 5 international registries?',
    'What are the primary causes of revision across registries?',
    'How close are we to any concern thresholds?',
    'Which registry has outcomes most similar to our study?',
  ]

  // Use dynamic followups if available, otherwise initial questions
  const displayedQuestions = suggestedFollowups.length > 0
    ? suggestedFollowups.slice(0, 4)
    : initialSuggestedQuestions

  // Floating action button when closed
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg flex items-center justify-center z-50 transition-all duration-300 hover:scale-110 active:scale-95 group"
        style={{
          background: 'linear-gradient(135deg, #1d1d1f 0%, #424245 100%)',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1) inset'
        }}
      >
        <div className="absolute inset-0 rounded-full bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
        <MessageCircle className="w-6 h-6 text-white" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#007aff] rounded-full flex items-center justify-center">
          <Sparkles className="w-2.5 h-2.5 text-white" />
        </span>
      </button>
    )
  }

  return (
    <div
      className={`fixed rounded-2xl shadow-2xl flex flex-col z-50 animate-slide-up overflow-hidden transition-all duration-300 ease-out ${
        panelSize === 'fullscreen' ? 'bottom-[5vh] right-[5vw]' : 'bottom-6 right-6'
      }`}
      style={{
        width: panelWidth,
        height: panelHeight,
        background: 'rgba(255, 255, 255, 0.92)',
        backdropFilter: 'blur(40px) saturate(180%)',
        WebkitBackdropFilter: 'blur(40px) saturate(180%)',
        boxShadow: '0 24px 80px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 0, 0, 0.05)'
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 border-b border-gray-200/60"
        style={{
          background: 'linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(250,250,250,0.8) 100%)'
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center"
            style={{
              background: '#1d1d1f',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
            }}
          >
            <Sparkles className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] text-gray-800 leading-tight">Clinical AI Assistant</h3>
            <p className="text-[11px] text-gray-500 leading-tight">Powered by multi-agent intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleSize}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors active:bg-gray-200"
            title={panelSize === 'fullscreen' ? 'Minimize' : 'Expand'}
          >
            {panelSize === 'fullscreen' ? (
              <Minimize2 className="w-4 h-4 text-gray-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-400" />
            )}
          </button>
          <button
            onClick={onToggle}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors active:bg-gray-200"
          >
            <X className="w-4.5 h-4.5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 chat-scrollbar">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center mb-4 bg-gray-100"
            >
              <Sparkles className="w-7 h-7 text-gray-600" />
            </div>
            <h4 className="text-[17px] font-semibold text-gray-800 mb-1">How can I help?</h4>
            <p className="text-[13px] text-gray-500 text-center mb-6 max-w-[280px]">
              Ask me anything about your clinical study data, safety signals, or regulatory readiness.
            </p>
            <div className="w-full space-y-2">
              {displayedQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setInput(q)}
                  className="w-full text-left px-4 py-3 text-[13px] text-gray-700 bg-gray-50/80 rounded-xl hover:bg-gray-100 transition-all duration-200 border border-gray-100 hover:border-gray-200 group"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <span className="opacity-80 group-hover:opacity-100 transition-opacity">{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-message-in`}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className={`max-w-[88%] ${msg.role === 'assistant' ? 'flex gap-2.5' : ''}`}>
              {msg.role === 'assistant' && (
                <div
                  className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5 bg-gray-800"
                >
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
              )}
              <div>
                <div
                  className={`px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'rounded-br-md'
                      : 'rounded-bl-md bg-white border border-gray-100'
                  }`}
                  style={msg.role === 'user' ? {
                    background: 'linear-gradient(135deg, #1d1d1f 0%, #424245 100%)',
                    color: 'white'
                  } : {
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
                  }}
                >
                  {msg.role === 'assistant' ? (
                    <ResponseDisplay content={msg.content} isExpanded={panelSize !== 'compact'} />
                  ) : (
                    <p className="text-[14px] leading-relaxed whitespace-pre-wrap text-white">
                      {msg.content}
                    </p>
                  )}
                </div>

                {/* Key Evidence Panel - shows actual data values */}
                {msg.evidence && msg.evidence.metrics && msg.evidence.metrics.length > 0 && (
                  <EvidencePanel evidence={msg.evidence} />
                )}

                {/* Sources with expandable provenance cards */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    <div className="flex items-center gap-1 text-[11px] text-gray-500 font-medium">
                      <Shield className="w-3 h-3" />
                      <span>Sources & Provenance</span>
                    </div>
                    {msg.sources.map((source: Source, j: number) => (
                      <ProvenanceCard key={j} source={source} />
                    ))}
                  </div>
                )}

                {/* Timestamp */}
                <p className={`text-[10px] text-gray-400 mt-1.5 ${msg.role === 'user' ? 'text-right' : ''}`}>
                  {formatTime(msg.timestamp)}
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* Follow-up suggestions after conversation */}
        {messages.length > 0 && !isLoading && suggestedFollowups.length > 0 && (
          <div className="animate-fade-in">
            <p className="text-[11px] text-gray-400 mb-2 font-medium">Suggested follow-ups:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedFollowups.slice(0, 3).map((q, i) => (
                <button
                  key={i}
                  onClick={() => setInput(q)}
                  className="text-[12px] text-gray-700 bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-full transition-colors border border-gray-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start animate-message-in">
            <div className="flex gap-2.5">
              <div
                className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center animate-pulse-subtle bg-gray-800"
              >
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="bg-white border border-gray-100 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-thinking-dot"
                      style={{ animationDelay: '0ms' }}
                    />
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-thinking-dot"
                      style={{ animationDelay: '200ms' }}
                    />
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-thinking-dot"
                      style={{ animationDelay: '400ms' }}
                    />
                  </div>
                  {isCached && (
                    <span className="flex items-center gap-1 text-[11px] text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>Retrieving...</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div
        className="px-4 py-3 border-t border-gray-200/60"
        style={{
          background: 'linear-gradient(180deg, rgba(250,250,250,0.8) 0%, rgba(255,255,255,0.9) 100%)'
        }}
      >
        <div
          className="flex items-center gap-2 bg-gray-100/80 rounded-full px-4 py-1 transition-all duration-200 focus-within:bg-white focus-within:ring-2 focus-within:ring-gray-300 focus-within:shadow-sm"
          style={{ border: '1px solid rgba(0, 0, 0, 0.06)' }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask a question..."
            className="flex-1 bg-transparent py-2.5 text-[14px] text-gray-800 placeholder-gray-400 focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
            style={{
              background: input.trim() && !isLoading
                ? '#1d1d1f'
                : '#d2d2d7',
              boxShadow: input.trim() && !isLoading
                ? '0 2px 8px rgba(0, 0, 0, 0.15)'
                : 'none'
            }}
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
        <p className="text-[10px] text-gray-400 text-center mt-2">
          Responses may be cached for faster retrieval
        </p>
      </div>
    </div>
  )
}
