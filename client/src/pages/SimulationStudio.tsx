import { useState } from 'react'
import StudyLayout from './StudyLayout'
import {
  Play,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  Info,
  Cpu,
  Users,
  AlertTriangle
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
  const gamma = (shape: number) => {
    let sum = 0
    for (let i = 0; i < Math.ceil(shape); i++) {
      sum -= Math.log(Math.random())
    }
    return sum
  }
  const x = gamma(successes)
  const y = gamma(failures)
  return x / (x + y)
}

function sampleBinomial(n: number, p: number): number {
  let successes = 0
  for (let i = 0; i < n; i++) {
    if (Math.random() < p) successes++
  }
  return successes
}

function runBaselineSimulation(iterations: number, threshold: number) {
  const revisions = H34_CURRENT.revisions
  const n = H34_CURRENT.enrolled
  let passCount = 0
  const rates: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const sampledRate = sampleBeta(revisions + 1, n - revisions + 1)
    rates.push(sampledRate)
    if (sampledRate <= threshold) passCount++
  }
  
  const sortedRates = [...rates].sort((a, b) => a - b)
  
  return {
    pPass: passCount / iterations,
    mean: rates.reduce((a, b) => a + b, 0) / rates.length,
    p5: sortedRates[Math.floor(iterations * 0.05)],
    p50: sortedRates[Math.floor(iterations * 0.50)],
    p95: sortedRates[Math.floor(iterations * 0.95)],
  }
}

function runEnrollmentSimulation(iterations: number, additionalPatients: number, threshold: number) {
  const currentRevisions = H34_CURRENT.revisions
  const currentN = H34_CURRENT.enrolled
  const newN = currentN + additionalPatients
  
  let passCount = 0
  
  for (let i = 0; i < iterations; i++) {
    const sampledRate = sampleBeta(currentRevisions + 1, currentN - currentRevisions + 1)
    const newRevisions = sampleBinomial(additionalPatients, sampledRate)
    const totalRevisions = currentRevisions + newRevisions
    const posteriorRate = sampleBeta(totalRevisions + 1, newN - totalRevisions + 1)
    
    if (posteriorRate <= threshold) passCount++
  }
  
  return {
    pPass: passCount / iterations,
    additionalPatients,
    newN,
  }
}

function runStressSimulation(iterations: number, additionalRevisions: number, threshold: number) {
  const totalRevisions = H34_CURRENT.revisions + additionalRevisions
  const n = H34_CURRENT.enrolled
  let passCount = 0
  
  for (let i = 0; i < iterations; i++) {
    const sampledRate = sampleBeta(totalRevisions + 1, n - totalRevisions + 1)
    if (sampledRate <= threshold) passCount++
  }
  
  return {
    pPass: passCount / iterations,
    additionalRevisions,
    totalRevisions,
  }
}

interface SimulationResults {
  baseline: ReturnType<typeof runBaselineSimulation>
  enrollment: ReturnType<typeof runEnrollmentSimulation>[]
  stress: ReturnType<typeof runStressSimulation>[]
}

function VerdictBadge({ probability, size = 'normal' }: { probability: number; size?: 'normal' | 'small' }) {
  const baseClasses = size === 'small' 
    ? 'px-2 py-1 text-xs rounded-full font-medium'
    : 'px-3 py-1.5 text-sm rounded-full font-semibold'
  
  if (probability >= 0.80) {
    return (
      <span className={`${baseClasses} bg-green-100 text-green-800`}>
        High Confidence
      </span>
    )
  } else if (probability >= 0.50) {
    return (
      <span className={`${baseClasses} bg-amber-100 text-amber-800`}>
        Uncertain
      </span>
    )
  } else {
    return (
      <span className={`${baseClasses} bg-red-100 text-red-800`}>
        At Risk
      </span>
    )
  }
}

function ProbabilityCard({ 
  probability, 
  label, 
  sublabel,
  delta,
  highlighted = false 
}: { 
  probability: number
  label: string
  sublabel?: string
  delta?: number
  highlighted?: boolean
}) {
  const bgColor = probability >= 0.80 ? 'bg-green-50 border-green-200' 
    : probability >= 0.50 ? 'bg-amber-50 border-amber-200' 
    : 'bg-red-50 border-red-200'
  
  const textColor = probability >= 0.80 ? 'text-green-700' 
    : probability >= 0.50 ? 'text-amber-700' 
    : 'text-red-700'

  return (
    <div className={`p-4 rounded-xl border ${highlighted ? bgColor : 'bg-gray-50 border-gray-200'} text-center transition-all`}>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${highlighted ? textColor : 'text-gray-900'}`}>
        {(probability * 100).toFixed(0)}%
      </div>
      {sublabel && <div className="text-xs text-gray-400 mt-0.5">{sublabel}</div>}
      {delta !== undefined && (
        <div className={`flex items-center justify-center gap-1 mt-1 text-xs ${delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-400'}`}>
          {delta > 0 ? <TrendingUp className="w-3 h-3" /> : delta < 0 ? <TrendingDown className="w-3 h-3" /> : null}
          {delta > 0 ? '+' : ''}{(delta * 100).toFixed(0)}%
        </div>
      )}
    </div>
  )
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [iterations] = useState(5000)
  const [isRunning, setIsRunning] = useState(false)
  const [selectedThreshold, setSelectedThreshold] = useState<keyof typeof REGULATORY_THRESHOLDS>('fda_510k')
  const [results, setResults] = useState<SimulationResults | null>(null)
  const [showMethodology, setShowMethodology] = useState(false)
  const [simulationProgress, setSimulationProgress] = useState(0)

  const runAllSimulations = () => {
    setIsRunning(true)
    setSimulationProgress(0)
    
    const progressInterval = setInterval(() => {
      setSimulationProgress(prev => Math.min(prev + Math.random() * 12 + 4, 95))
    }, 150)
    
    setTimeout(() => {
      const threshold = REGULATORY_THRESHOLDS[selectedThreshold].rate
      
      const baseline = runBaselineSimulation(iterations, threshold)
      
      const enrollment = [20, 50, 100].map(n => 
        runEnrollmentSimulation(iterations, n, threshold)
      )
      
      const stress = [1, 2, 3].map(r => 
        runStressSimulation(iterations, r, threshold)
      )
      
      setResults({ baseline, enrollment, stress })
      
      clearInterval(progressInterval)
      setSimulationProgress(100)
      setTimeout(() => {
        setIsRunning(false)
        setSimulationProgress(0)
      }, 200)
    }, 2000)
  }

  const threshold = REGULATORY_THRESHOLDS[selectedThreshold]

  return (
    <StudyLayout studyId={params.studyId}>
      <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
        
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
            Simulation Studio
          </h1>
          <p className="text-xl text-gray-600">
            Will H-34 meet the revision rate benchmark?
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="text-sm text-gray-500">Current Study Data</div>
              <div className="text-lg font-medium text-gray-900">
                {H34_CURRENT.revisions} revisions in {H34_CURRENT.enrolled} patients 
                <span className="text-gray-500 font-normal"> ({(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}% observed)</span>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Benchmark</label>
                <select 
                  value={selectedThreshold}
                  onChange={(e) => {
                    setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS)
                    setResults(null)
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
                >
                  {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                    <option key={key} value={key}>{val.label} (≤{(val.rate * 100).toFixed(0)}%)</option>
                  ))}
                </select>
              </div>
              
              <button
                onClick={runAllSimulations}
                disabled={isRunning}
                className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-colors font-medium"
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

        {!isRunning && results && (
          <div className="space-y-6">
            
            <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
              <div className="text-center space-y-4">
                <div className="text-sm text-gray-500 uppercase tracking-wide">
                  Probability of Meeting {threshold.label} Benchmark
                </div>
                <div className="flex items-center justify-center gap-4">
                  <div className={`text-7xl font-bold ${
                    results.baseline.pPass >= 0.80 ? 'text-green-600' 
                    : results.baseline.pPass >= 0.50 ? 'text-amber-600' 
                    : 'text-red-600'
                  }`}>
                    {(results.baseline.pPass * 100).toFixed(0)}%
                  </div>
                  <VerdictBadge probability={results.baseline.pPass} />
                </div>
                <div className="text-gray-500">
                  Based on current data: {H34_CURRENT.revisions} revisions / {H34_CURRENT.enrolled} patients
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold text-gray-900">If we enroll more patients...</h3>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {results.enrollment.map((r) => (
                    <ProbabilityCard
                      key={r.additionalPatients}
                      probability={r.pPass}
                      label={`+${r.additionalPatients} patients`}
                      sublabel={`n=${r.newN}`}
                      delta={r.pPass - results.baseline.pPass}
                      highlighted={r.pPass >= 0.80}
                    />
                  ))}
                </div>
                <div className="mt-4 text-sm text-gray-600 bg-blue-50 rounded-lg p-3">
                  {results.enrollment.some(r => r.pPass >= 0.80) ? (
                    <>
                      <strong className="text-blue-800">Recommendation:</strong> Adding {results.enrollment.find(r => r.pPass >= 0.80)?.additionalPatients}+ patients would bring confidence above 80%.
                    </>
                  ) : (
                    <>
                      <strong className="text-blue-800">Note:</strong> Even with 100 more patients, success probability remains below 80%. Consider additional strategies.
                    </>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <h3 className="font-semibold text-gray-900">If we see more revisions...</h3>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {results.stress.map((r) => (
                    <ProbabilityCard
                      key={r.additionalRevisions}
                      probability={r.pPass}
                      label={`+${r.additionalRevisions} revision${r.additionalRevisions > 1 ? 's' : ''}`}
                      sublabel={`${r.totalRevisions} total`}
                      delta={r.pPass - results.baseline.pPass}
                      highlighted={r.pPass < 0.50}
                    />
                  ))}
                </div>
                <div className="mt-4 text-sm text-gray-600 bg-red-50 rounded-lg p-3">
                  {results.stress.find(r => r.pPass < 0.50) ? (
                    <>
                      <strong className="text-red-800">Warning:</strong> Just {results.stress.find(r => r.pPass < 0.50)?.additionalRevisions} more revision(s) would put success probability below 50%. Monitor closely.
                    </>
                  ) : (
                    <>
                      <strong className="text-amber-800">Moderate buffer:</strong> The study can absorb a few more revisions while maintaining viability.
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-2xl border border-gray-200 p-6">
              <div className="text-sm text-gray-600 space-y-2">
                <div className="font-medium text-gray-800">Summary</div>
                <p>
                  With current data, there's a <strong>{(results.baseline.pPass * 100).toFixed(0)}%</strong> chance of meeting the {threshold.label} benchmark (≤{(threshold.rate * 100).toFixed(0)}% revision rate).
                  {results.baseline.pPass >= 0.80 
                    ? " The study is on track with high confidence."
                    : results.baseline.pPass >= 0.50 
                    ? " Outcome is uncertain - consider enrollment expansion or enhanced monitoring."
                    : " The study is at risk - immediate action is recommended."
                  }
                </p>
              </div>
            </div>
          </div>
        )}

        {!isRunning && !results && (
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-12 text-center">
            <div className="text-gray-400 mb-4">
              <Play className="w-12 h-12 mx-auto" />
            </div>
            <div className="text-gray-600">
              Select a benchmark and click <strong>Run Simulation</strong> to see results
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
            <div className="p-6 pt-2 space-y-5 border-t border-gray-100 text-sm">
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">What is Monte Carlo Simulation?</h4>
                <p className="text-gray-600">
                  We run {iterations.toLocaleString()} random simulations based on current data. Each simulation asks: 
                  "Given what we've observed, what might the true revision rate be?" We count how often 
                  the simulated rate stays below the benchmark - that's your probability.
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Why is the probability not 100%?</h4>
                <p className="text-gray-600">
                  With only {H34_CURRENT.enrolled} patients and {H34_CURRENT.revisions} revisions, there's uncertainty. 
                  The observed rate ({(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}%) might not be the "true" rate. 
                  The simulation captures this uncertainty - the true rate could reasonably be anywhere from ~2% to ~15%.
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Enrollment Scenarios</h4>
                <p className="text-gray-600">
                  Adding patients dilutes uncertainty. More data = more confidence in the true rate. 
                  Each scenario projects expected new revisions based on current patterns, then recalculates the probability.
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Stress Test Scenarios</h4>
                <p className="text-gray-600">
                  These show what happens if things go wrong. If {H34_CURRENT.revisions + 2} total revisions occur, 
                  the revised rate becomes {((H34_CURRENT.revisions + 2) / H34_CURRENT.enrolled * 100).toFixed(1)}% - 
                  which may exceed the benchmark, dramatically lowering success probability.
                </p>
              </div>
              
              <div className="flex gap-4 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-gray-600">≥80%: High Confidence</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span className="text-gray-600">50-79%: Uncertain</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
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
