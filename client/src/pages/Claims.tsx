import { useState, useEffect } from 'react'
import { CheckCircle2, XCircle, AlertCircle, Send, Lightbulb, Shield, FileText, RefreshCw, ChevronDown, ChevronUp, HelpCircle, BookOpen } from 'lucide-react'
import { Card } from '@/components/Card'
import {
  validateClaim,
  fetchExampleClaims,
  fetchComplianceGuidelines,
  ClaimValidationResponse,
  ClaimValidationStatus,
  ClaimConfidenceLevel,
  ClaimEvidence
} from '@/lib/api'

interface ClaimsProps {
  studyId?: string
}

const statusConfig: Record<ClaimValidationStatus, { icon: React.ComponentType<{ className?: string }>; bg: string; text: string; border: string; label: string }> = {
  validated: { icon: CheckCircle2, bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Validated' },
  partial: { icon: AlertCircle, bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'Partially Validated' },
  not_validated: { icon: XCircle, bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'Not Validated' },
  insufficient_evidence: { icon: HelpCircle, bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200', label: 'Insufficient Evidence' },
}

const confidenceColors: Record<ClaimConfidenceLevel, { bg: string; text: string }> = {
  high: { bg: 'bg-emerald-100', text: 'text-emerald-800' },
  medium: { bg: 'bg-amber-100', text: 'text-amber-800' },
  low: { bg: 'bg-red-100', text: 'text-red-800' },
}

export default function Claims({ studyId }: ClaimsProps) {
  const [claimInput, setClaimInput] = useState('')
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<ClaimValidationResponse | null>(null)
  const [exampleClaims, setExampleClaims] = useState<Array<{ category: string; claim: string; expected: string }>>([])
  const [guidelines, setGuidelines] = useState<Array<{ category: string; guidance: string; example_issue: string }>>([])
  const [showGuidelines, setShowGuidelines] = useState(false)
  const [validationHistory, setValidationHistory] = useState<ClaimValidationResponse[]>([])
  const [expandedEvidence, setExpandedEvidence] = useState<'supporting' | 'contradicting' | null>(null)

  useEffect(() => {
    loadInitialData()
  }, [])

  async function loadInitialData() {
    try {
      const [examples, guidelinesData] = await Promise.all([
        fetchExampleClaims(),
        fetchComplianceGuidelines(),
      ])
      setExampleClaims(examples.example_claims)
      setGuidelines(guidelinesData.guidelines)
    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }

  async function handleValidate() {
    if (!claimInput.trim() || claimInput.length < 10) return

    setValidating(true)
    try {
      const result = await validateClaim(claimInput)
      setValidationResult(result)
      setValidationHistory(prev => [result, ...prev.slice(0, 4)])
    } catch (error) {
      console.error('Validation failed:', error)
    } finally {
      setValidating(false)
    }
  }

  function handleExampleClick(claim: string) {
    setClaimInput(claim)
  }

  function clearResults() {
    setValidationResult(null)
    setClaimInput('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Claim Validation</h1>
          <p className="text-gray-500 mt-1">Substantiate marketing claims with clinical evidence</p>
        </div>
        <button
          onClick={() => setShowGuidelines(!showGuidelines)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <BookOpen className="w-4 h-4" />
          Guidelines
          {showGuidelines ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Compliance Guidelines Panel */}
      {showGuidelines && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Guidelines</h3>
          <div className="space-y-4">
            {guidelines.map((guideline, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 text-xs font-medium bg-gray-200 text-gray-700 rounded-full">
                    {guideline.category}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{guideline.guidance}</p>
                <p className="text-xs text-red-600">
                  <span className="font-medium">Example Issue:</span> {guideline.example_issue}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Claim Input Section */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Enter Marketing Claim</h3>
        <div className="space-y-4">
          <div className="relative">
            <textarea
              value={claimInput}
              onChange={(e) => setClaimInput(e.target.value)}
              placeholder="Enter the marketing claim you want to validate (minimum 10 characters)..."
              className="w-full h-32 p-4 text-gray-900 bg-gray-50 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent transition-all"
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400">
              {claimInput.length} characters
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              <span className="text-sm text-gray-500">Try an example:</span>
            </div>
            <div className="flex items-center gap-2">
              {validationResult && (
                <button
                  onClick={clearResults}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Clear
                </button>
              )}
              <button
                onClick={handleValidate}
                disabled={claimInput.length < 10 || validating}
                className="flex items-center gap-2 px-6 py-2 text-sm text-white bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {validating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Validate Claim
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Example Claims */}
          <div className="flex flex-wrap gap-2">
            {exampleClaims.slice(0, 4).map((example, i) => (
              <button
                key={i}
                onClick={() => handleExampleClick(example.claim)}
                className="px-3 py-1.5 text-xs text-gray-600 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors border border-gray-200"
              >
                {example.category}: "{example.claim.slice(0, 40)}..."
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Validation Result */}
      {validationResult && (
        <div className="space-y-4">
          {/* Status Card */}
          <Card>
            <div className="flex items-start gap-4">
              {(() => {
                const config = statusConfig[validationResult.validation_status]
                const StatusIcon = config.icon
                return (
                  <>
                    <div className={`p-3 rounded-lg ${config.bg}`}>
                      <StatusIcon className={`w-6 h-6 ${config.text}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">Validation Result</h3>
                        <span className={`px-3 py-1 text-sm font-medium rounded-full ${config.bg} ${config.text} border ${config.border}`}>
                          {config.label}
                        </span>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${confidenceColors[validationResult.confidence_level].bg} ${confidenceColors[validationResult.confidence_level].text}`}>
                          {validationResult.confidence_level.toUpperCase()} confidence
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm italic mb-4">
                        "{validationResult.claim}"
                      </p>
                      {validationResult.analysis && (
                        <div className="p-3 bg-gray-50 rounded-lg mb-4">
                          <p className="text-sm text-gray-700 leading-relaxed">{validationResult.analysis}</p>
                        </div>
                      )}
                    </div>
                  </>
                )
              })()}
            </div>
          </Card>

          {/* Recommended Language */}
          {validationResult.recommended_language && (
            <Card>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <Lightbulb className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommended Alternative Language</h4>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800 leading-relaxed">
                      {validationResult.recommended_language}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Evidence Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Supporting Evidence */}
            <Card>
              <button
                onClick={() => setExpandedEvidence(expandedEvidence === 'supporting' ? null : 'supporting')}
                className="w-full flex items-center justify-between mb-3"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <h4 className="text-sm font-semibold text-gray-900">
                    Supporting Evidence ({validationResult.supporting_evidence.length})
                  </h4>
                </div>
                {expandedEvidence === 'supporting' ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>
              {(expandedEvidence === 'supporting' || validationResult.supporting_evidence.length <= 3) && (
                <div className="space-y-2">
                  {validationResult.supporting_evidence.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No supporting evidence found</p>
                  ) : (
                    validationResult.supporting_evidence.map((evidence: ClaimEvidence, i: number) => (
                      <div key={i} className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">
                            {evidence.type}
                          </span>
                          {evidence.claim_value && (
                            <span className="text-xs text-emerald-700 font-medium">{evidence.claim_value}</span>
                          )}
                        </div>
                        <p className="text-sm text-emerald-800">{evidence.evidence}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </Card>

            {/* Contradicting Evidence */}
            <Card>
              <button
                onClick={() => setExpandedEvidence(expandedEvidence === 'contradicting' ? null : 'contradicting')}
                className="w-full flex items-center justify-between mb-3"
              >
                <div className="flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-red-600" />
                  <h4 className="text-sm font-semibold text-gray-900">
                    Contradicting Evidence ({validationResult.contradicting_evidence.length})
                  </h4>
                </div>
                {expandedEvidence === 'contradicting' ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>
              {(expandedEvidence === 'contradicting' || validationResult.contradicting_evidence.length <= 3) && (
                <div className="space-y-2">
                  {validationResult.contradicting_evidence.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No contradicting evidence found</p>
                  ) : (
                    validationResult.contradicting_evidence.map((evidence: ClaimEvidence, i: number) => (
                      <div key={i} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full">
                            {evidence.type}
                          </span>
                        </div>
                        <p className="text-sm text-red-800">{evidence.evidence}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Evidence Gaps */}
          {validationResult.evidence_gaps.length > 0 && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                <h4 className="text-sm font-semibold text-gray-900">Evidence Gaps</h4>
              </div>
              <div className="space-y-2">
                {validationResult.evidence_gaps.map((gap: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                    <span className="text-amber-600 mt-0.5">-</span>
                    <p className="text-sm text-amber-800">{gap}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Compliance Notes */}
          {validationResult.compliance_notes.length > 0 && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-5 h-5 text-gray-600" />
                <h4 className="text-sm font-semibold text-gray-900">Compliance Notes</h4>
              </div>
              <div className="space-y-2">
                {validationResult.compliance_notes.map((note: string, i: number) => (
                  <div key={i} className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-gray-600">{note}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Data Sources */}
          <Card>
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-gray-500" />
              <h4 className="text-sm font-medium text-gray-700">Data Sources Used</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {validationResult.sources.map((source, i) => (
                <span
                  key={i}
                  className="px-3 py-1.5 text-xs font-medium bg-gray-50 text-gray-600 rounded-full border border-gray-200"
                >
                  {source.type as string}: {source.reference as string}
                </span>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Validation History */}
      {validationHistory.length > 0 && !validationResult && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Validations</h3>
          <div className="space-y-3">
            {validationHistory.map((result, i) => {
              const config = statusConfig[result.validation_status]
              const StatusIcon = config.icon
              return (
                <div
                  key={i}
                  onClick={() => setValidationResult(result)}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                >
                  <StatusIcon className={`w-5 h-5 ${config.text}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">{result.claim}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(result.validated_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
                    {config.label}
                  </span>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}
