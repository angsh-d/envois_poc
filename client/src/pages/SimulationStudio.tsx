import { useState, useEffect } from 'react'
import StudyLayout from './StudyLayout'
import {
  Play,
  RefreshCw,
  ChevronDown,
  Activity,
  Target,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  BarChart2,
  Check,
} from 'lucide-react'
import {
  runMonteCarloSimulation,
  fetchHazardRatios,
  MonteCarloResponse,
  HazardRatioSpec,
} from '../lib/api'

interface SimulationStudioProps {
  params: { studyId: string }
}

const REGULATORY_THRESHOLDS = {
  fda_510k: { rate: 0.10, label: 'FDA 510(k)', description: '≤10% revision rate' },
  mdr_pmcf: { rate: 0.12, label: 'MDR PMCF', description: '≤12% revision rate' },
  registry_parity: { rate: 0.09, label: 'Registry Parity', description: '≤9% (NJR average)' },
}

const RISK_FACTORS: Record<string, { label: string; defaultEnabled: boolean }> = {
  age_over_80: { label: 'Age ≥80', defaultEnabled: true },
  bmi_over_35: { label: 'BMI ≥35', defaultEnabled: true },
  diabetes: { label: 'Diabetes', defaultEnabled: true },
  osteoporosis: { label: 'Osteoporosis', defaultEnabled: true },
  rheumatoid_arthritis: { label: 'Rheumatoid Arthritis', defaultEnabled: false },
  chronic_kidney_disease: { label: 'Chronic Kidney Disease', defaultEnabled: false },
  smoking: { label: 'Current Smoker', defaultEnabled: true },
  prior_revision: { label: 'Prior Revision', defaultEnabled: true },
  severe_bone_loss: { label: 'Severe Bone Loss', defaultEnabled: true },
  paprosky_3b: { label: 'Paprosky 3B', defaultEnabled: false },
}

// Minimal Distribution Curve
function DistributionCurve({
  mean,
  std,
  threshold,
  pPass,
}: {
  mean: number
  std: number
  threshold: number
  pPass: number
}) {
  const width = 480
  const height = 140
  const padding = { top: 24, right: 30, bottom: 32, left: 30 }
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom

  const minX = Math.max(0, mean - 4 * std)
  const maxX = Math.min(0.25, mean + 4 * std)
  const xRange = maxX - minX

  const normalPDF = (x: number) => {
    const z = (x - mean) / std
    return Math.exp(-0.5 * z * z) / (std * Math.sqrt(2 * Math.PI))
  }

  const curvePoints: Array<{ x: number; y: number }> = []
  let maxY = 0
  for (let i = 0; i <= 80; i++) {
    const x = minX + (i / 80) * xRange
    const y = normalPDF(x)
    maxY = Math.max(maxY, y)
    curvePoints.push({ x, y })
  }

  const scaleX = (x: number) => padding.left + ((x - minX) / xRange) * plotWidth
  const scaleY = (y: number) => padding.top + plotHeight - (y / maxY) * plotHeight

  const curvePath = curvePoints
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.x)} ${scaleY(p.y)}`)
    .join(' ')

  const fillPath = curvePath + ` L ${scaleX(maxX)} ${scaleY(0)} L ${scaleX(minX)} ${scaleY(0)} Z`

  const passPoints = curvePoints.filter(p => p.x <= threshold)
  const passFillPath = passPoints.length > 0
    ? passPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.x)} ${scaleY(p.y)}`).join(' ')
      + ` L ${scaleX(Math.min(threshold, maxX))} ${scaleY(0)} L ${scaleX(minX)} ${scaleY(0)} Z`
    : ''

  const thresholdX = scaleX(threshold)
  const meanX = scaleX(mean)

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {passFillPath && (
          <path d={passFillPath} fill={pPass >= 0.80 ? 'rgba(0,0,0,0.06)' : pPass >= 0.50 ? 'rgba(0,0,0,0.04)' : 'rgba(0,0,0,0.03)'} />
        )}
        <path d={fillPath} fill="rgba(0,0,0,0.03)" />
        <path d={curvePath} fill="none" stroke="#000" strokeWidth="1.5" opacity="0.7" />

        <line x1={thresholdX} y1={padding.top} x2={thresholdX} y2={padding.top + plotHeight} stroke="#000" strokeWidth="1" strokeDasharray="4,3" opacity="0.4" />
        <text x={thresholdX} y={padding.top - 8} fontSize="10" textAnchor="middle" fill="#666">
          {(threshold * 100).toFixed(0)}% limit
        </text>

        <circle cx={meanX} cy={scaleY(normalPDF(mean))} r="3" fill="#000" />

        <line x1={padding.left} y1={padding.top + plotHeight} x2={padding.left + plotWidth} y2={padding.top + plotHeight} stroke="#e5e5e5" strokeWidth="1" />

        {[0, 0.05, 0.10, 0.15, 0.20].filter(t => t >= minX && t <= maxX).map(tick => (
          <text key={tick} x={scaleX(tick)} y={height - 8} fontSize="9" textAnchor="middle" fill="#999">
            {(tick * 100).toFixed(0)}%
          </text>
        ))}
      </svg>
    </div>
  )
}

// Pyramid Chart for Variance Contribution
function VarianceChart({ contributions }: { contributions: Record<string, number> }) {
  // Exclude baseline_rate - it's not actionable
  const riskFactorsOnly = Object.entries(contributions)
    .filter(([key]) => key !== 'baseline_rate')
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)

  // Recalculate percentages relative to risk factors only
  const total = riskFactorsOnly.reduce((sum, [, v]) => sum + v, 0)
  const normalized = riskFactorsOnly.map(([key, value]) => [key, total > 0 ? (value / total) * 100 : 0] as [string, number])
  const maxValue = Math.max(...normalized.map(([, v]) => v), 1)

  const labels: Record<string, string> = {
    age_over_80: 'Age ≥80',
    bmi_over_35: 'BMI ≥35',
    diabetes: 'Diabetes',
    osteoporosis: 'Osteoporosis',
    rheumatoid_arthritis: 'Rheumatoid Arthritis',
    chronic_kidney_disease: 'Chronic Kidney Disease',
    smoking: 'Smoking',
    prior_revision: 'Prior Revision',
    severe_bone_loss: 'Severe Bone Loss',
    paprosky_3b: 'Paprosky 3B',
  }

  if (normalized.length === 0) return null

  return (
    <div className="space-y-2">
      {normalized.map(([factor, value], index) => {
        const widthPercent = (value / maxValue) * 100
        return (
          <div key={factor} className="flex items-center justify-center gap-3">
            <div className="w-32 text-xs text-gray-500 text-right">{labels[factor] || factor}</div>
            <div className="w-48 flex justify-center">
              <div
                className="h-5 rounded-sm transition-all flex items-center justify-center"
                style={{
                  width: `${widthPercent}%`,
                  minWidth: '20px',
                  background: `rgba(0,0,0,${0.15 + (0.4 * (1 - index / normalized.length))})`,
                }}
              >
                <span className="text-[10px] text-white font-medium">{value.toFixed(0)}%</span>
              </div>
            </div>
            <div className="w-32" />
          </div>
        )
      })}
    </div>
  )
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [isRunning, setIsRunning] = useState(false)
  const [selectedThreshold, setSelectedThreshold] = useState<keyof typeof REGULATORY_THRESHOLDS>('fda_510k')
  const [nPatients, setNPatients] = useState(549)
  const [showWhyMonteCarlo, setShowWhyMonteCarlo] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const [enabledFactors, setEnabledFactors] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {}
    Object.entries(RISK_FACTORS).forEach(([key, config]) => {
      initial[key] = config.defaultEnabled
    })
    return initial
  })

  const [result, setResult] = useState<MonteCarloResponse | null>(null)
  const [hazardRatios, setHazardRatios] = useState<HazardRatioSpec[]>([])

  const threshold = REGULATORY_THRESHOLDS[selectedThreshold]

  useEffect(() => {
    fetchHazardRatios().then(response => {
      if (response.success) setHazardRatios(response.factors)
    }).catch(console.error)
  }, [])

  const toggleFactor = (key: string) => {
    setEnabledFactors(prev => ({ ...prev, [key]: !prev[key] }))
    setResult(null)
  }

  const enabledCount = Object.values(enabledFactors).filter(Boolean).length

  const getHR = (factor: string) => hazardRatios.find(hr => hr.factor === factor)

  // Generate deterministic seed from inputs for reproducibility
  const computeSeed = (patients: number, threshold: string, factors: Record<string, boolean>) => {
    const enabledKeys = Object.keys(factors).filter(k => factors[k]).sort().join(',')
    const inputString = `${patients}-${threshold}-${enabledKeys}`
    // Simple hash function
    let hash = 0
    for (let i = 0; i < inputString.length; i++) {
      const char = inputString.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }

  const runSimulation = async () => {
    setIsRunning(true)
    setResult(null)
    try {
      const riskDistribution: Record<string, number> = {}
      const prevalences: Record<string, number> = {
        age_over_80: 0.08, bmi_over_35: 0.12, diabetes: 0.15, osteoporosis: 0.12,
        rheumatoid_arthritis: 0.04, chronic_kidney_disease: 0.06, smoking: 0.08,
        prior_revision: 0.10, severe_bone_loss: 0.15, paprosky_3b: 0.06,
      }
      Object.keys(RISK_FACTORS).forEach(key => {
        riskDistribution[key] = enabledFactors[key] ? (prevalences[key] || 0.10) : 0
      })

      // Use deterministic seed so same inputs = same outputs
      const seed = computeSeed(nPatients, selectedThreshold, enabledFactors)

      const response = await runMonteCarloSimulation({
        n_patients: nPatients,
        threshold: selectedThreshold,
        n_iterations: 10000,
        risk_distribution: riskDistribution,
        seed: seed,
      })
      setResult(response)
    } catch (error) {
      console.error('Simulation failed:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const pPass = result?.probability_pass ?? 0
  const isHighConfidence = pPass >= 0.80
  const isUncertain = pPass >= 0.50 && pPass < 0.80
  const isAtRisk = pPass < 0.50

  return (
    <StudyLayout studyId={params.studyId} chatContext="simulation">
      <div className="max-w-3xl mx-auto py-8 px-4">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 text-xs text-gray-400 uppercase tracking-widest mb-4">
            <Activity className="w-3.5 h-3.5" />
            Monte Carlo Analysis
          </div>
          <h1 className="text-2xl font-medium text-gray-900 mb-2">
            Will your study meet the benchmark?
          </h1>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Simulate outcomes across 10,000 scenarios to understand regulatory success probability.
          </p>
        </div>

        {/* Why Monte Carlo - Collapsible */}
        <button
          onClick={() => setShowWhyMonteCarlo(!showWhyMonteCarlo)}
          className="w-full flex items-center justify-between py-3 text-left border-b border-gray-100 mb-8"
        >
          <span className="text-sm text-gray-500 flex items-center gap-2">
            <HelpCircle className="w-4 h-4" />
            Why simulation instead of calculation?
          </span>
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showWhyMonteCarlo ? 'rotate-180' : ''}`} />
        </button>

        {showWhyMonteCarlo && (
          <div className="mb-10 p-5 bg-gray-50 rounded-xl text-sm text-gray-600 space-y-3">
            <p><strong className="text-gray-900">Every hazard ratio has a range.</strong> Age ≥80 isn't exactly 1.85× risk—it could be anywhere from 1.4× to 2.4× based on the underlying studies.</p>
            <p><strong className="text-gray-900">Risks multiply together.</strong> When 6 factors each have uncertain ranges, the combined uncertainty compounds dramatically.</p>
            <p><strong className="text-gray-900">Monte Carlo samples from all ranges</strong> simultaneously across 10,000 scenarios, showing the full distribution of possible outcomes.</p>
          </div>
        )}

        {/* Configuration */}
        <div className="space-y-8">

          {/* Cohort & Benchmark */}
          <div className="grid grid-cols-2 gap-8">
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider block mb-3">Cohort Size</label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={50}
                  max={2000}
                  step={50}
                  value={nPatients}
                  onChange={(e) => { setNPatients(Number(e.target.value)); setResult(null) }}
                  className="flex-1 h-1 bg-gray-200 rounded-full appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-gray-900"
                />
                <span className="text-sm font-medium text-gray-900 tabular-nums w-20 text-right">{nPatients}</span>
              </div>
            </div>

            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider block mb-3">Benchmark</label>
              <select
                value={selectedThreshold}
                onChange={(e) => { setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS); setResult(null) }}
                className="w-full bg-transparent border-0 border-b border-gray-200 py-2 text-sm text-gray-900 focus:outline-none focus:border-gray-900 cursor-pointer"
              >
                {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                  <option key={key} value={key}>{val.label} (≤{(val.rate * 100).toFixed(0)}%)</option>
                ))}
              </select>
            </div>
          </div>

          {/* Risk Factors */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="text-xs text-gray-500 uppercase tracking-wider">Risk Factors ({enabledCount} selected)</label>
              <button
                onClick={() => {
                  const allEnabled = Object.values(enabledFactors).every(Boolean)
                  const newState: Record<string, boolean> = {}
                  Object.keys(enabledFactors).forEach(key => { newState[key] = !allEnabled })
                  setEnabledFactors(newState)
                  setResult(null)
                }}
                className="text-xs text-gray-400 hover:text-gray-900"
              >
                {Object.values(enabledFactors).every(Boolean) ? 'Clear all' : 'Select all'}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-x-8 gap-y-3">
              {Object.entries(RISK_FACTORS).map(([key, config]) => {
                const hr = getHR(key)
                // Scale: 1.0 to 3.0 maps to 0% to 100%
                const scaleMin = 1.0
                const scaleMax = 3.0
                const toPercent = (val: number) => Math.max(0, Math.min(100, ((val - scaleMin) / (scaleMax - scaleMin)) * 100))

                return (
                  <div
                    key={key}
                    onClick={() => toggleFactor(key)}
                    className="cursor-pointer group"
                  >
                    <div className="flex items-center gap-3 mb-1.5">
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${
                          enabledFactors[key]
                            ? 'bg-gray-900 border-gray-900'
                            : 'border-gray-300 group-hover:border-gray-400'
                        }`}
                      >
                        {enabledFactors[key] && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                      </div>
                      <span className={`text-sm flex-1 ${enabledFactors[key] ? 'text-gray-900' : 'text-gray-500'}`}>
                        {config.label}
                      </span>
                    </div>
                    {hr && (
                      <div className="ml-7 flex items-center gap-2">
                        <span className="text-[10px] text-gray-400 w-8 tabular-nums">{hr.ci_lower.toFixed(1)}×</span>
                        <div className="flex-1 h-2 bg-gray-100 rounded-full relative overflow-hidden">
                          {/* Gradient showing distribution - darker in middle, fades at edges */}
                          <div
                            className={`absolute inset-0 rounded-full transition-all ${
                              enabledFactors[key] ? 'opacity-100' : 'opacity-40'
                            }`}
                            style={{
                              background: enabledFactors[key]
                                ? 'linear-gradient(90deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.1) 100%)'
                                : 'linear-gradient(90deg, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.15) 50%, rgba(0,0,0,0.05) 100%)',
                            }}
                          />
                        </div>
                        <span className="text-[10px] text-gray-400 w-8 tabular-nums">{hr.ci_upper.toFixed(1)}×</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Run Button */}
          <div className="pt-4">
            <button
              onClick={runSimulation}
              disabled={isRunning || enabledCount === 0}
              className="w-full py-3 bg-gray-900 text-white text-sm font-medium rounded-lg
                hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all
                flex items-center justify-center gap-2"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running simulation...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Simulation
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {!isRunning && result && (
          <div className="mt-12 pt-10 border-t border-gray-100 space-y-10">

            {/* Primary Result */}
            <div className="text-center">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">
                Probability of Success
              </div>
              <div className="text-6xl font-light text-gray-900 tabular-nums mb-3">
                {result.probability_pass_pct.toFixed(0)}%
              </div>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                isHighConfidence ? 'bg-gray-100 text-gray-700' :
                isUncertain ? 'bg-gray-100 text-gray-600' :
                'bg-gray-100 text-gray-600'
              }`}>
                {isHighConfidence && <><CheckCircle2 className="w-3.5 h-3.5" /> High Confidence</>}
                {isUncertain && <><AlertTriangle className="w-3.5 h-3.5" /> Uncertain</>}
                {isAtRisk && <><XCircle className="w-3.5 h-3.5" /> At Risk</>}
              </div>
            </div>

            {/* Distribution */}
            <div className="py-4">
              <DistributionCurve
                mean={result.mean_revision_rate}
                std={result.std_revision_rate}
                threshold={threshold.rate}
                pPass={result.probability_pass}
              />
              <div className="flex justify-center gap-8 mt-4 text-xs text-gray-500">
                <span>Expected: <strong className="text-gray-900">{(result.mean_revision_rate * 100).toFixed(1)}%</strong></span>
                <span>Range: {(result.p5_revision_rate * 100).toFixed(1)}% – {(result.p95_revision_rate * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-2xl font-light text-gray-900">{(result.mean_revision_rate * 100).toFixed(1)}%</div>
                <div className="text-xs text-gray-500 mt-1">Expected Rate</div>
              </div>
              <div>
                <div className="text-2xl font-light text-gray-900">{(result.p95_revision_rate * 100).toFixed(1)}%</div>
                <div className="text-xs text-gray-500 mt-1">Worst Case (95th)</div>
              </div>
              <div>
                <div className="text-2xl font-light text-gray-900">{(threshold.rate * 100).toFixed(0)}%</div>
                <div className="text-xs text-gray-500 mt-1">{threshold.label} Limit</div>
              </div>
            </div>

            {/* Interpretation */}
            <div className={`p-6 rounded-xl ${
              isHighConfidence ? 'bg-gray-50' :
              isUncertain ? 'bg-amber-50/50' :
              'bg-red-50/50'
            }`}>
              <div className="flex items-start gap-4">
                <div className="mt-0.5">
                  {isHighConfidence && <CheckCircle2 className="w-5 h-5 text-gray-600" />}
                  {isUncertain && <AlertTriangle className="w-5 h-5 text-amber-600" />}
                  {isAtRisk && <XCircle className="w-5 h-5 text-red-600" />}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {isHighConfidence && 'Likely to meet benchmark'}
                    {isUncertain && 'Outcome is uncertain'}
                    {isAtRisk && 'Unlikely to meet benchmark'}
                  </h4>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {isHighConfidence && (
                      <>With {(pPass * 100).toFixed(0)}% confidence, the expected {(result.mean_revision_rate * 100).toFixed(1)}% revision rate falls safely below the {(threshold.rate * 100).toFixed(0)}% threshold. Current patient selection criteria are well-positioned.</>
                    )}
                    {isUncertain && (
                      <>The {(pPass * 100).toFixed(0)}% success probability indicates the outcome could go either way. Consider adjusting risk factor criteria to improve confidence.</>
                    )}
                    {isAtRisk && (
                      <>Only {(pPass * 100).toFixed(0)}% chance of meeting the benchmark. Consider excluding high-risk patients or selecting a different regulatory pathway.</>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="space-y-3">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider">Recommendations</h4>
              <div className="space-y-2">
                {isHighConfidence && (
                  <>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Proceed with current enrollment criteria
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Monitor high-risk subgroups during enrollment
                    </div>
                  </>
                )}
                {isUncertain && (
                  <>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Try disabling high-impact risk factors to see effect
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Consider tightening enrollment criteria
                    </div>
                  </>
                )}
                {isAtRisk && (
                  <>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Revise enrollment to exclude highest-risk patients
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      Consider MDR PMCF pathway (12% threshold)
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Variance Drivers - Collapsible */}
            <div className="border-t border-gray-100 pt-6">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between py-2 text-left"
              >
                <span className="text-xs text-gray-500 uppercase tracking-wider flex items-center gap-2">
                  <BarChart2 className="w-3.5 h-3.5" />
                  Uncertainty Drivers
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
              </button>

              {showAdvanced && (
                <div className="mt-4">
                  <VarianceChart contributions={result.variance_contributions} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isRunning && !result && (
          <div className="mt-12 pt-10 border-t border-gray-100 text-center py-16">
            <Target className="w-8 h-8 text-gray-300 mx-auto mb-4" />
            <p className="text-sm text-gray-400">Run simulation to see results</p>
          </div>
        )}

      </div>
    </StudyLayout>
  )
}
