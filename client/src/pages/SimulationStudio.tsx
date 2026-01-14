import { useState, useMemo } from 'react'
import StudyLayout from './StudyLayout'
import {
  Play,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Info,
  Cpu,
  Users,
  AlertTriangle,
  RotateCcw
} from 'lucide-react'

interface SimulationStudioProps {
  params: { studyId: string }
}

const H34_CURRENT = {
  enrolled: 37,
  revisions: 2,
  followUpYears: 2,
  currentRevisionRate: 2 / 37,
}

const REGULATORY_THRESHOLDS = {
  fda_510k: { rate: 0.10, label: 'FDA 510(k)', description: '≤10% revision rate' },
  mdr_pmcf: { rate: 0.12, label: 'MDR PMCF', description: '≤12% revision rate' },
  registry_parity: { rate: 0.09, label: 'Registry Parity', description: '≤9% (NJR match)' },
}

function sampleBeta(successes: number, failures: number): number {
  const safeSuccesses = Math.max(0.1, successes)
  const safeFailures = Math.max(0.1, failures)
  
  const gamma = (shape: number) => {
    let sum = 0
    for (let i = 0; i < Math.ceil(shape); i++) {
      sum -= Math.log(Math.random())
    }
    return sum
  }
  const x = gamma(safeSuccesses)
  const y = gamma(safeFailures)
  return x / (x + y)
}

function sampleBinomial(n: number, p: number): number {
  let successes = 0
  for (let i = 0; i < n; i++) {
    if (Math.random() < p) successes++
  }
  return successes
}

interface SimulationResult {
  rates: number[]
  pPass: number
  mean: number
  p5: number
  p50: number
  p95: number
  scenario: string
  label: string
}

function runSimulation(
  iterations: number, 
  threshold: number,
  additionalPatients: number = 0,
  additionalRevisions: number = 0
): SimulationResult {
  const currentN = H34_CURRENT.enrolled
  const newN = currentN + additionalPatients
  const totalRevisions = Math.min(H34_CURRENT.revisions + additionalRevisions, newN - 1)
  
  let passCount = 0
  const rates: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    let finalRate: number
    
    if (additionalPatients > 0) {
      const sampledRate = sampleBeta(H34_CURRENT.revisions + 1, currentN - H34_CURRENT.revisions + 1)
      const projectedRevisions = sampleBinomial(additionalPatients, sampledRate)
      const allRevisions = Math.min(H34_CURRENT.revisions + projectedRevisions, newN - 1)
      finalRate = sampleBeta(allRevisions + 1, newN - allRevisions + 1)
    } else {
      finalRate = sampleBeta(totalRevisions + 1, newN - totalRevisions + 1)
    }
    
    rates.push(finalRate)
    if (finalRate <= threshold) passCount++
  }
  
  const sortedRates = [...rates].sort((a, b) => a - b)
  
  let scenario = 'baseline'
  let label = 'Current Data'
  if (additionalPatients > 0) {
    scenario = `+${additionalPatients}pts`
    label = `+${additionalPatients} patients (n=${newN})`
  }
  if (additionalRevisions > 0) {
    scenario = `+${additionalRevisions}rev`
    label = `+${additionalRevisions} revision${additionalRevisions > 1 ? 's' : ''} (${totalRevisions} total)`
  }
  
  return {
    rates,
    pPass: passCount / iterations,
    mean: rates.reduce((a, b) => a + b, 0) / rates.length,
    p5: sortedRates[Math.floor(iterations * 0.05)],
    p50: sortedRates[Math.floor(iterations * 0.50)],
    p95: sortedRates[Math.floor(iterations * 0.95)],
    scenario,
    label,
  }
}

function DistributionChart({ 
  rates, 
  threshold, 
  pPass,
  comparisonRates
}: { 
  rates: number[]
  threshold: number
  pPass: number
  comparisonRates?: number[]
}) {
  const bins = 40
  const maxRate = 0.30
  const binWidth = maxRate / bins
  
  const histogram = useMemo(() => {
    const counts = new Array(bins).fill(0)
    rates.forEach(rate => {
      const binIndex = Math.min(Math.floor(rate / binWidth), bins - 1)
      counts[binIndex]++
    })
    return counts.map(c => c / rates.length)
  }, [rates])
  
  const comparisonHistogram = useMemo(() => {
    if (!comparisonRates) return null
    const counts = new Array(bins).fill(0)
    comparisonRates.forEach(rate => {
      const binIndex = Math.min(Math.floor(rate / binWidth), bins - 1)
      counts[binIndex]++
    })
    return counts.map(c => c / comparisonRates.length)
  }, [comparisonRates])
  
  const maxHeight = Math.max(...histogram, ...(comparisonHistogram || []))
  const chartHeight = 160
  const chartWidth = 100
  
  const thresholdX = (threshold / maxRate) * chartWidth

  return (
    <div className="space-y-2">
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight + 30}`} className="w-full h-48">
        {comparisonHistogram && comparisonHistogram.map((height, i) => (
          <rect
            key={`comp-${i}`}
            x={(i / bins) * chartWidth}
            y={chartHeight - (height / maxHeight) * chartHeight}
            width={chartWidth / bins - 0.2}
            height={(height / maxHeight) * chartHeight}
            fill="#e5e7eb"
            opacity={0.7}
          />
        ))}
        
        {histogram.map((height, i) => {
          const binStart = i * binWidth
          const isPassingBin = binStart + binWidth <= threshold
          return (
            <rect
              key={i}
              x={(i / bins) * chartWidth}
              y={chartHeight - (height / maxHeight) * chartHeight}
              width={chartWidth / bins - 0.2}
              height={(height / maxHeight) * chartHeight}
              fill={isPassingBin ? '#22c55e' : '#ef4444'}
              opacity={0.8}
            />
          )
        })}
        
        <line
          x1={thresholdX}
          y1={0}
          x2={thresholdX}
          y2={chartHeight}
          stroke="#1f2937"
          strokeWidth={0.5}
          strokeDasharray="2,2"
        />
        
        <text x={thresholdX} y={chartHeight + 12} fontSize="4" textAnchor="middle" fill="#1f2937" fontWeight="bold">
          {(threshold * 100).toFixed(0)}%
        </text>
        <text x={thresholdX} y={chartHeight + 18} fontSize="3" textAnchor="middle" fill="#6b7280">
          threshold
        </text>
        
        <text x={2} y={chartHeight + 12} fontSize="3" fill="#6b7280">0%</text>
        <text x={chartWidth - 2} y={chartHeight + 12} fontSize="3" textAnchor="end" fill="#6b7280">30%</text>
        
        <text x={chartWidth / 2} y={chartHeight + 28} fontSize="3.5" textAnchor="middle" fill="#6b7280">
          Simulated Revision Rate Distribution
        </text>
      </svg>
      
      <div className="flex justify-center gap-6 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span className="text-gray-600">Pass ({(pPass * 100).toFixed(0)}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-red-500"></div>
          <span className="text-gray-600">Fail ({((1 - pPass) * 100).toFixed(0)}%)</span>
        </div>
        {comparisonRates && (
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-gray-300"></div>
            <span className="text-gray-600">Baseline (for comparison)</span>
          </div>
        )}
      </div>
    </div>
  )
}

function VerdictBadge({ probability }: { probability: number }) {
  if (probability >= 0.80) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full font-semibold bg-green-100 text-green-800">
        <CheckCircle className="w-4 h-4" /> High Confidence
      </span>
    )
  } else if (probability >= 0.50) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full font-semibold bg-amber-100 text-amber-800">
        <AlertCircle className="w-4 h-4" /> Uncertain
      </span>
    )
  } else {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full font-semibold bg-red-100 text-red-800">
        <XCircle className="w-4 h-4" /> At Risk
      </span>
    )
  }
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [iterations] = useState(5000)
  const [isRunning, setIsRunning] = useState(false)
  const [selectedThreshold, setSelectedThreshold] = useState<keyof typeof REGULATORY_THRESHOLDS>('fda_510k')
  const [baselineResult, setBaselineResult] = useState<SimulationResult | null>(null)
  const [activeScenario, setActiveScenario] = useState<SimulationResult | null>(null)
  const [showMethodology, setShowMethodology] = useState(false)
  const [simulationProgress, setSimulationProgress] = useState(0)

  const threshold = REGULATORY_THRESHOLDS[selectedThreshold]

  const runBaselineSimulation = () => {
    setIsRunning(true)
    setSimulationProgress(0)
    setActiveScenario(null)
    
    const progressInterval = setInterval(() => {
      setSimulationProgress(prev => Math.min(prev + Math.random() * 12 + 4, 95))
    }, 150)
    
    setTimeout(() => {
      const result = runSimulation(iterations, threshold.rate, 0, 0)
      setBaselineResult(result)
      setActiveScenario(null)
      
      clearInterval(progressInterval)
      setSimulationProgress(100)
      setTimeout(() => {
        setIsRunning(false)
        setSimulationProgress(0)
      }, 200)
    }, 1500)
  }

  const applyScenario = (additionalPatients: number, additionalRevisions: number) => {
    if (!baselineResult) return
    
    const result = runSimulation(iterations, threshold.rate, additionalPatients, additionalRevisions)
    setActiveScenario(result)
  }

  const resetToBaseline = () => {
    setActiveScenario(null)
  }

  const currentResult = activeScenario || baselineResult
  const showComparison = activeScenario !== null && baselineResult !== null

  return (
    <StudyLayout studyId={params.studyId}>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        
        <div className="text-center space-y-1">
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
            Simulation Studio
          </h1>
          <p className="text-lg text-gray-600">
            Will H-34 meet the revision rate benchmark?
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-0.5">
              <div className="text-xs text-gray-500 uppercase tracking-wide">Current Study Data</div>
              <div className="text-base font-medium text-gray-900">
                {H34_CURRENT.revisions} revisions in {H34_CURRENT.enrolled} patients 
                <span className="text-gray-500 font-normal ml-1">({(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}%)</span>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Benchmark</label>
                <select 
                  value={selectedThreshold}
                  onChange={(e) => {
                    setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS)
                    setBaselineResult(null)
                    setActiveScenario(null)
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
                >
                  {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                    <option key={key} value={key}>{val.label} (≤{(val.rate * 100).toFixed(0)}%)</option>
                  ))}
                </select>
              </div>
              
              <button
                onClick={runBaselineSimulation}
                disabled={isRunning}
                className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-colors font-medium mt-5"
              >
                {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {isRunning ? 'Running...' : 'Run Simulation'}
              </button>
            </div>
          </div>
        </div>

        {isRunning && (
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-6">
            <div className="flex items-center gap-3 text-gray-600 mb-3">
              <Cpu className="w-5 h-5 animate-pulse" />
              <span>Running {iterations.toLocaleString()} Monte Carlo iterations...</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gray-800 transition-all duration-150"
                style={{ width: `${simulationProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {!isRunning && currentResult && (
          <div className="space-y-6">
            
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                    Probability of Meeting {threshold.label} Benchmark
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-5xl font-bold ${
                      currentResult.pPass >= 0.80 ? 'text-green-600' 
                      : currentResult.pPass >= 0.50 ? 'text-amber-600' 
                      : 'text-red-600'
                    }`}>
                      {(currentResult.pPass * 100).toFixed(0)}%
                    </span>
                    <VerdictBadge probability={currentResult.pPass} />
                  </div>
                </div>
                
                {activeScenario && (
                  <div className="text-right">
                    <div className="text-xs text-gray-500 mb-1">Active Scenario</div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700 bg-gray-100 px-2 py-1 rounded">
                        {activeScenario.label}
                      </span>
                      <button 
                        onClick={resetToBaseline}
                        className="text-gray-400 hover:text-gray-600 p-1"
                        title="Reset to baseline"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    </div>
                    {baselineResult && (
                      <div className={`text-sm mt-1 ${
                        activeScenario.pPass > baselineResult.pPass ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {activeScenario.pPass > baselineResult.pPass ? '+' : ''}
                        {((activeScenario.pPass - baselineResult.pPass) * 100).toFixed(0)}% vs baseline
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <DistributionChart 
                rates={currentResult.rates} 
                threshold={threshold.rate}
                pPass={currentResult.pPass}
                comparisonRates={showComparison ? baselineResult?.rates : undefined}
              />
              
              <div className="mt-4 grid grid-cols-4 gap-3 text-center text-sm">
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-gray-500 text-xs">Observed</div>
                  <div className="font-mono font-semibold">{(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-gray-500 text-xs">Simulated Mean</div>
                  <div className="font-mono font-semibold">{(currentResult.mean * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-green-50 rounded-lg p-2">
                  <div className="text-green-600 text-xs">5th %ile (best)</div>
                  <div className="font-mono font-semibold text-green-700">{(currentResult.p5 * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-red-50 rounded-lg p-2">
                  <div className="text-red-600 text-xs">95th %ile (worst)</div>
                  <div className="font-mono font-semibold text-red-700">{(currentResult.p95 * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4">Apply "What-If" Scenarios</h3>
              <p className="text-sm text-gray-500 mb-4">
                Click a scenario to see how the distribution changes. The baseline (gray) will show for comparison.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700">If we enroll more patients...</span>
                  </div>
                  <div className="flex gap-2">
                    {[20, 50, 100].map(n => (
                      <button
                        key={n}
                        onClick={() => applyScenario(n, 0)}
                        className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                          activeScenario?.scenario === `+${n}pts`
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700'
                        }`}
                      >
                        +{n} patients
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-gray-700">If we see more revisions...</span>
                  </div>
                  <div className="flex gap-2">
                    {[1, 2, 3].map(r => (
                      <button
                        key={r}
                        onClick={() => applyScenario(0, r)}
                        className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                          activeScenario?.scenario === `+${r}rev`
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-red-50 hover:text-red-700'
                        }`}
                      >
                        +{r} rev
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-2xl border border-gray-200 p-5">
              <div className="text-sm text-gray-700">
                <strong>Summary:</strong> With {activeScenario ? activeScenario.label.toLowerCase() : 'current data'}, 
                there's a <strong className={
                  currentResult.pPass >= 0.80 ? 'text-green-700' 
                  : currentResult.pPass >= 0.50 ? 'text-amber-700' 
                  : 'text-red-700'
                }>{(currentResult.pPass * 100).toFixed(0)}%</strong> chance of meeting the {threshold.label} benchmark.
                {currentResult.pPass >= 0.80 
                  ? " The outlook is favorable."
                  : currentResult.pPass >= 0.50 
                  ? " Outcome is uncertain - consider strategies to improve confidence."
                  : " This scenario puts regulatory approval at significant risk."
                }
              </div>
            </div>
          </div>
        )}

        {!isRunning && !baselineResult && (
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-12 text-center">
            <div className="text-gray-400 mb-4">
              <Play className="w-12 h-12 mx-auto" />
            </div>
            <div className="text-gray-600">
              Select a benchmark and click <strong>Run Simulation</strong> to analyze probability
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Info className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">How This Simulation Works</span>
            </div>
            {showMethodology ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </button>
          
          {showMethodology && (
            <div className="p-6 pt-2 space-y-4 border-t border-gray-100 text-sm">
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">The Distribution Chart</h4>
                <p className="text-gray-600">
                  The chart shows all {iterations.toLocaleString()} simulated revision rates. Green bars are rates that pass the threshold, red bars fail.
                  The vertical dashed line is your benchmark. The wider the distribution, the more uncertain the estimate.
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">What-If Scenarios</h4>
                <p className="text-gray-600">
                  When you apply a scenario, the distribution shifts. Adding patients narrows uncertainty (taller, narrower curve). 
                  Adding revisions shifts the curve right (toward higher rates). The gray baseline stays visible for comparison.
                </p>
              </div>
              
              <div className="flex gap-4 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green-500"></div>
                  <span className="text-gray-600">≥80%: High Confidence</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-amber-500"></div>
                  <span className="text-gray-600">50-79%: Uncertain</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500"></div>
                  <span className="text-gray-600">&lt;50%: At Risk</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </StudyLayout>
  )
}
