import { useState, useRef, useEffect, useCallback } from 'react'
import { Bot, User, Sparkles, Send, ChevronDown, AlertCircle, RefreshCw, Lightbulb, HelpCircle } from 'lucide-react'
import {
  addMessage as addMessageApi,
  getConversationHistory,
  chatWithAI,
  ChatMessage as ApiChatMessage,
  ChatResponseData
} from '../lib/onboardingApi'

interface ChatMessage {
  id: string | number
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  metadata?: Record<string, any>
}

interface OnboardingChatProps {
  messages: ChatMessage[]
  isLoading?: boolean
  onSendMessage?: (message: string) => void
  showInput?: boolean
  placeholder?: string
  sessionId?: string  // Session ID for persisting messages to backend
  persistMessages?: boolean  // Whether to persist messages to backend
  suggestedActions?: string[]  // AI-suggested actions
  followUpQuestions?: string[]  // AI-suggested follow-up questions
  onActionClick?: (action: string) => void  // Handler for action clicks
  onQuestionClick?: (question: string) => void  // Handler for follow-up question clicks
  currentPhase?: string  // Current onboarding phase for context
}

export function OnboardingChat({
  messages,
  isLoading,
  onSendMessage,
  showInput = false,
  placeholder = "Ask a question about configuration...",
  sessionId,
  persistMessages = false,
  suggestedActions = [],
  followUpQuestions = [],
  onActionClick,
  onQuestionClick,
  currentPhase,
}: OnboardingChatProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const [persistError, setPersistError] = useState<string | null>(null)

  // Persist message to backend if session ID is provided
  const persistMessage = useCallback(async (
    role: 'user' | 'assistant' | 'system',
    content: string,
    metadata?: Record<string, any>
  ) => {
    if (!persistMessages || !sessionId) return

    try {
      await addMessageApi(sessionId, { role, content, metadata })
      setPersistError(null)
    } catch (error) {
      console.error('Failed to persist message:', error)
      setPersistError('Failed to save message')
    }
  }, [sessionId, persistMessages])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // Check if we need to show scroll button
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && onSendMessage) {
      const message = inputValue.trim()
      setInputValue('')

      // Persist user message to backend
      await persistMessage('user', message)

      // Call the onSendMessage handler
      onSendMessage(message)
    }
  }

  return (
    <div className="flex flex-col bg-white border border-neutral-200 rounded-2xl overflow-hidden">
      {/* Persist Error Banner */}
      {persistError && (
        <div className="flex items-center gap-2 px-3 py-2 bg-neutral-50 border-b border-neutral-200 text-sm text-neutral-600">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{persistError}</span>
          <button
            onClick={() => setPersistError(null)}
            className="ml-auto text-neutral-500 hover:text-neutral-800"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Messages Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 max-h-96"
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-neutral-900 rounded-xl flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 bg-neutral-100 rounded-2xl p-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-neutral-500 text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-20 right-6 p-2 bg-white rounded-full shadow-lg border border-neutral-200 hover:bg-neutral-50 transition-colors"
        >
          <ChevronDown className="w-4 h-4 text-neutral-600" />
        </button>
      )}

      {/* Suggested Actions */}
      {suggestedActions.length > 0 && !isLoading && (
        <div className="px-4 py-2 bg-neutral-50 border-t border-neutral-100">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-3.5 h-3.5 text-neutral-500" />
            <span className="text-xs font-medium text-neutral-600">Suggested Actions</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedActions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => onActionClick?.(action)}
                className="px-3 py-1.5 text-xs bg-white border border-neutral-200 text-neutral-700 rounded-xl hover:bg-neutral-100 hover:border-neutral-300 transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Follow-up Questions */}
      {followUpQuestions.length > 0 && !isLoading && (
        <div className="px-4 py-2 bg-neutral-50 border-t border-neutral-100">
          <div className="flex items-center gap-2 mb-2">
            <HelpCircle className="w-3.5 h-3.5 text-neutral-500" />
            <span className="text-xs font-medium text-neutral-600">You might want to ask</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {followUpQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => onQuestionClick?.(question)}
                className="px-3 py-1.5 text-xs bg-white border border-neutral-200 text-neutral-700 rounded-xl hover:bg-neutral-100 hover:border-neutral-300 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      {showInput && onSendMessage && (
        <form onSubmit={handleSubmit} className="p-3 bg-neutral-50 border-t border-neutral-100">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={placeholder}
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 text-sm bg-white border border-neutral-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="w-10 h-10 bg-neutral-900 text-white rounded-xl flex items-center justify-center hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isAssistant = message.role === 'assistant'
  const isSystem = message.role === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="px-3 py-1 bg-neutral-100 rounded-full text-xs text-neutral-500">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-start gap-3 ${!isAssistant ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center ${
        isAssistant ? 'bg-neutral-900' : 'bg-neutral-700'
      }`}>
        {isAssistant ? (
          <Bot className="w-4 h-4 text-white" />
        ) : (
          <User className="w-4 h-4 text-white" />
        )}
      </div>
      <div className={`flex-1 max-w-[85%] ${!isAssistant ? 'text-right' : ''}`}>
        {isAssistant && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-neutral-700">AI Assistant</span>
            <Sparkles className="w-3 h-3 text-neutral-400" />
          </div>
        )}
        <div className={`inline-block rounded-2xl p-3 ${
          isAssistant
            ? 'bg-neutral-100 text-neutral-800'
            : 'bg-neutral-900 text-white'
        }`}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
        {message.timestamp && (
          <div className={`text-xs text-neutral-400 mt-1 ${!isAssistant ? 'text-right' : ''}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  )
}

// Simplified single-message version for backward compatibility
interface SimpleOnboardingChatProps {
  message: string
  isLoading?: boolean
}

export function SimpleOnboardingChat({ message, isLoading }: SimpleOnboardingChatProps) {
  const messages: ChatMessage[] = message ? [{
    id: '1',
    role: 'assistant',
    content: message,
  }] : []

  return <OnboardingChat messages={messages} isLoading={isLoading} />
}

// Hook to manage conversation history with persistence
export function useConversationHistory(sessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load conversation history from backend
  const loadHistory = useCallback(async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      const response = await getConversationHistory(sessionId)
      const loadedMessages: ChatMessage[] = response.messages.map(m => ({
        id: m.id,
        role: m.role as 'user' | 'assistant' | 'system',
        content: m.content,
        timestamp: m.created_at,
        metadata: m.metadata as Record<string, any>,
      }))
      setMessages(loadedMessages)
      setError(null)
    } catch (err) {
      console.error('Failed to load conversation history:', err)
      setError('Failed to load conversation history')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  // Add a message to the local state
  const addMessage = useCallback((message: Omit<ChatMessage, 'id'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `local-${Date.now()}`,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, newMessage])
    return newMessage
  }, [])

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  // Load history on session ID change
  useEffect(() => {
    if (sessionId) {
      loadHistory()
    } else {
      setMessages([])
    }
  }, [sessionId, loadHistory])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    addMessage,
    clearMessages,
    loadHistory,
    setMessages,
    clearError,
  }
}


// Hook to manage full conversational flow with AI
export function useOnboardingChat(sessionId?: string, currentPhase?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestedActions, setSuggestedActions] = useState<string[]>([])
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([])

  // Load conversation history from backend
  const loadHistory = useCallback(async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      const response = await getConversationHistory(sessionId)
      const loadedMessages: ChatMessage[] = response.messages.map(m => ({
        id: m.id,
        role: m.role as 'user' | 'assistant' | 'system',
        content: m.content,
        timestamp: m.created_at,
        metadata: m.metadata as Record<string, any>,
      }))
      setMessages(loadedMessages)
      setError(null)
    } catch (err) {
      console.error('Failed to load conversation history:', err)
      setError('Failed to load conversation history')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  // Send a message and get AI response
  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId || !message.trim()) return

    // Add user message to local state immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setSuggestedActions([])
    setFollowUpQuestions([])
    setError(null)

    try {
      // Call the chat API
      const response = await chatWithAI(sessionId, {
        message,
        context: {
          phase: currentPhase,
        }
      })

      // Add AI response to local state
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMessage])

      // Update suggested actions and follow-up questions
      setSuggestedActions(response.suggested_actions || [])
      setFollowUpQuestions(response.follow_up_questions || [])

    } catch (err) {
      console.error('Failed to send chat message:', err)
      setError('Failed to send message. Please try again.')

      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, currentPhase])

  // Handle clicking a suggested action
  const handleActionClick = useCallback((action: string) => {
    // Actions are typically imperative, convert to a request
    sendMessage(`Please ${action.toLowerCase()}`)
  }, [sendMessage])

  // Handle clicking a follow-up question
  const handleQuestionClick = useCallback((question: string) => {
    sendMessage(question)
  }, [sendMessage])

  // Add initial assistant message
  const addInitialMessage = useCallback((content: string) => {
    const message: ChatMessage = {
      id: `initial-${Date.now()}`,
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => {
      // Don't add if there's already messages
      if (prev.length > 0) return prev
      return [message]
    })
  }, [])

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([])
    setSuggestedActions([])
    setFollowUpQuestions([])
  }, [])

  // Load history on session ID change
  useEffect(() => {
    if (sessionId) {
      loadHistory()
    } else {
      setMessages([])
    }
  }, [sessionId, loadHistory])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    suggestedActions,
    followUpQuestions,
    sendMessage,
    handleActionClick,
    handleQuestionClick,
    addInitialMessage,
    clearMessages,
    loadHistory,
    clearError,
  }
}
