import { useState } from 'react'
import StudyLayout from './StudyLayout'
import {
  Shield,
  Users,
  AlertTriangle,
  Play,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react'

interface SimulationStudioProps {
  params: { studyId: string }
}

type ScenarioType = 'regulatory' | 'enrollment' | 'stress'

const H34_CURRENT = {
  enrolled: 37,
  revisions: 2,
  followUpYears: 2,
  currentRevisionRate: 2 / 37,
}

const REGULATORY_THRESHOLDS = {
  fda_510k: { rate: 0.10, label: 'FDA 510(k) Benchmark', description: '≤10% 5-year revision rate' },
  mdr_pmcf: { rate: 0.12, label: 'MDR PMCF Threshold', description: '≤12% cumulative revision' },
  registry_parity: { rate: 0.09, label: 'Registry Parity (NJR)', description: '≤9% to match NJR 5-year' },
}

const REGISTRY_BASELINE = {
  njr_5yr: 0.090,
  njr_ci_lower: 0.088,
  njr_ci_upper: 0.092,
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

function sampleNormal(mean: number, sd: number): number {
  const u1 = Math.random()
  const u2 = Math.random()
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  return mean + sd * z
}

function runRegulatorySimulation(iterations: number, threshold: number) {
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
  const pPass = passCount / iterations
  
  return {
    pPass,
    mean: rates.reduce((a, b) => a + b, 0) / rates.length,
    p5: sortedRates[Math.floor(iterations * 0.05)],
    p50: sortedRates[Math.floor(iterations * 0.50)],
    p95: sortedRates[Math.floor(iterations * 0.95)],
    threshold,
  }
}

function sampleBinomial(n: number, p: number): number {
  let successes = 0
  for (let i = 0; i < n; i++) {
    if (Math.random() < p) successes++
  }
  return successes
}

function runEnrollmentSimulation(iterations: number, additionalPatients: number, threshold: number) {
  const currentRevisions = H34_CURRENT.revisions
  const currentN = H34_CURRENT.enrolled
  const newN = currentN + additionalPatients
  
  let passCount = 0
  const rates: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const sampledRate = sampleBeta(currentRevisions + 1, currentN - currentRevisions + 1)
    const newRevisions = sampleBinomial(additionalPatients, sampledRate)
    const totalRevisions = currentRevisions + newRevisions
    const posteriorRate = sampleBeta(totalRevisions + 1, newN - totalRevisions + 1)
    
    rates.push(posteriorRate)
    if (posteriorRate <= threshold) passCount++
  }
  
  const sortedRates = [...rates].sort((a, b) => a - b)
  
  return {
    pPass: passCount / iterations,
    mean: rates.reduce((a, b) => a + b, 0) / rates.length,
    p5: sortedRates[Math.floor(iterations * 0.05)],
    p50: sortedRates[Math.floor(iterations * 0.50)],
    p95: sortedRates[Math.floor(iterations * 0.95)],
    newN,
    additionalPatients,
  }
}

function runStressTestSimulation(iterations: number, additionalRevisions: number, threshold: number) {
  const totalRevisions = H34_CURRENT.revisions + additionalRevisions
  const n = H34_CURRENT.enrolled
  let passCount = 0
  const rates: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const sampledRate = sampleBeta(totalRevisions + 1, n - totalRevisions + 1)
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
    totalRevisions,
    additionalRevisions,
  }
}

function VerdictBadge({ probability }: { probability: number }) {
  if (probability >= 0.80) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full">
        <CheckCircle className="w-5 h-5" />
        <span className="font-semibold">High Confidence</span>
      </div>
    )
  } else if (probability >= 0.50) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-amber-100 text-amber-800 rounded-full">
        <AlertCircle className="w-5 h-5" />
        <span className="font-semibold">Uncertain</span>
      </div>
    )
  } else {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-800 rounded-full">
        <XCircle className="w-5 h-5" />
        <span className="font-semibold">At Risk</span>
      </div>
    )
  }
}

function ProbabilityMeter({ probability, label }: { probability: number; label: string }) {
  const percentage = probability * 100
  const color = probability >= 0.80 ? 'bg-green-500' : probability >= 0.50 ? 'bg-amber-500' : 'bg-red-500'
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-bold text-gray-900">{percentage.toFixed(1)}%</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  )
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [activeScenario, setActiveScenario] = useState<ScenarioType>('regulatory')
  const [iterations, setIterations] = useState(5000)
  const [isRunning, setIsRunning] = useState(false)
  
  const [selectedThreshold, setSelectedThreshold] = useState<keyof typeof REGULATORY_THRESHOLDS>('fda_510k')
  const [regulatoryResult, setRegulatoryResult] = useState<ReturnType<typeof runRegulatorySimulation> | null>(null)
  
  const [additionalPatients, setAdditionalPatients] = useState(20)
  const [enrollmentResults, setEnrollmentResults] = useState<ReturnType<typeof runEnrollmentSimulation>[] | null>(null)
  const [enrollmentBaseline, setEnrollmentBaseline] = useState<number | null>(null)
  
  const [additionalRevisions, setAdditionalRevisions] = useState(2)
  const [stressResult, setStressResult] = useState<ReturnType<typeof runStressTestSimulation> | null>(null)

  const scenarios = [
    { id: 'regulatory' as const, label: 'Regulatory Go/No-Go', icon: Shield, question: 'Will we pass regulatory thresholds?' },
    { id: 'enrollment' as const, label: 'Enrollment Decision', icon: Users, question: 'Should we add more patients?' },
    { id: 'stress' as const, label: 'Stress Test', icon: AlertTriangle, question: 'What if more revisions occur?' },
  ]

  const runSimulation = () => {
    setIsRunning(true)
    setTimeout(() => {
      const threshold = REGULATORY_THRESHOLDS[selectedThreshold].rate
      
      if (activeScenario === 'regulatory') {
        const result = runRegulatorySimulation(iterations, threshold)
        setRegulatoryResult(result)
      } else if (activeScenario === 'enrollment') {
        const baseline = runRegulatorySimulation(iterations, threshold)
        setEnrollmentBaseline(baseline.pPass)
        const results = [10, 20, 50, 100].map(n => 
          runEnrollmentSimulation(iterations, n, threshold)
        )
        setEnrollmentResults(results)
      } else if (activeScenario === 'stress') {
        const result = runStressTestSimulation(iterations, additionalRevisions, threshold)
        setStressResult(result)
      }
      setIsRunning(false)
    }, 100)
  }

  const renderRegulatoryScenario = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Question: Will H-34 pass regulatory revision rate thresholds?
        </h3>
        <p className="text-gray-600">
          Based on current data ({H34_CURRENT.revisions} revisions in {H34_CURRENT.enrolled} patients), 
          this simulation estimates the probability of meeting regulatory benchmarks using Bayesian inference.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Regulatory Threshold</label>
              <select 
                value={selectedThreshold}
                onChange={(e) => setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm min-w-[200px]"
              >
                {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                  <option key={key} value={key}>{val.label} ({(val.rate * 100).toFixed(0)}%)</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations}
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {regulatoryResult && (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-6 bg-gray-50 rounded-xl">
              <div>
                <div className="text-5xl font-bold text-gray-900">
                  {(regulatoryResult.pPass * 100).toFixed(1)}%
                </div>
                <div className="text-gray-600 mt-1">
                  Probability of passing {REGULATORY_THRESHOLDS[selectedThreshold].label}
                </div>
              </div>
              <VerdictBadge probability={regulatoryResult.pPass} />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Projected Revision Rate Distribution</h4>
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-600">Current observed rate</td>
                      <td className="py-2 text-right font-mono">{(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Simulated mean</td>
                      <td className="py-2 text-right font-mono">{(regulatoryResult.mean * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">5th percentile (optimistic)</td>
                      <td className="py-2 text-right font-mono text-green-600">{(regulatoryResult.p5 * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">50th percentile (median)</td>
                      <td className="py-2 text-right font-mono">{(regulatoryResult.p50 * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">95th percentile (pessimistic)</td>
                      <td className="py-2 text-right font-mono text-red-600">{(regulatoryResult.p95 * 100).toFixed(1)}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Recommendation</h4>
                <div className={`p-4 rounded-lg ${regulatoryResult.pPass >= 0.80 ? 'bg-green-50 border border-green-200' : regulatoryResult.pPass >= 0.50 ? 'bg-amber-50 border border-amber-200' : 'bg-red-50 border border-red-200'}`}>
                  {regulatoryResult.pPass >= 0.80 ? (
                    <p className="text-green-800">
                      <strong>Proceed with confidence.</strong> Current data strongly supports meeting the {REGULATORY_THRESHOLDS[selectedThreshold].description} threshold. Continue monitoring but no immediate action required.
                    </p>
                  ) : regulatoryResult.pPass >= 0.50 ? (
                    <p className="text-amber-800">
                      <strong>Proceed with caution.</strong> Outcome is uncertain. Consider extending follow-up period or increasing enrollment to strengthen the evidence base before regulatory submission.
                    </p>
                  ) : (
                    <p className="text-red-800">
                      <strong>Risk mitigation needed.</strong> Current trajectory suggests difficulty meeting threshold. Recommend root cause analysis of revision cases and proactive PMCF enhancement.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderEnrollmentScenario = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Question: Should we enroll more patients to improve regulatory success probability?
        </h3>
        <p className="text-gray-600">
          This simulation projects how adding 10, 20, 50, or 100 additional patients would impact the probability 
          of meeting the selected regulatory threshold, assuming similar revision patterns.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Target Threshold</label>
              <select 
                value={selectedThreshold}
                onChange={(e) => setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm min-w-[200px]"
              >
                {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                  <option key={key} value={key}>{val.label} ({(val.rate * 100).toFixed(0)}%)</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations}
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {enrollmentResults && enrollmentBaseline !== null && (
          <div className="space-y-6">
            <div className="p-4 bg-gray-100 rounded-lg mb-4">
              <div className="text-sm text-gray-600">Current baseline (n={H34_CURRENT.enrolled}): <span className="font-bold text-gray-900">{(enrollmentBaseline * 100).toFixed(1)}%</span> probability of success</div>
            </div>
            <div className="grid grid-cols-4 gap-4">
              {enrollmentResults.map((result) => {
                const improvement = result.pPass - enrollmentBaseline
                
                return (
                  <div key={result.additionalPatients} className="bg-gray-50 rounded-xl p-4 text-center">
                    <div className="text-sm text-gray-500 mb-1">+{result.additionalPatients} patients</div>
                    <div className="text-3xl font-bold text-gray-900">{(result.pPass * 100).toFixed(0)}%</div>
                    <div className="text-xs text-gray-500 mt-1">n = {result.newN}</div>
                    <div className={`flex items-center justify-center gap-1 mt-2 text-sm ${improvement > 0 ? 'text-green-600' : improvement < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                      {improvement > 0 ? <TrendingUp className="w-4 h-4" /> : improvement < 0 ? <TrendingDown className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                      {improvement > 0 ? '+' : ''}{(improvement * 100).toFixed(1)}% vs current
                    </div>
                  </div>
                )
              })}
            </div>

            <div>
              <h4 className="font-medium text-gray-800 mb-3">Projected Success by Enrollment Level</h4>
              <div className="space-y-3">
                {enrollmentResults.map((result) => (
                  <ProbabilityMeter 
                    key={result.additionalPatients}
                    probability={result.pPass} 
                    label={`n=${result.newN} (+${result.additionalPatients} patients)`}
                  />
                ))}
              </div>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Recommendation</h4>
              {(() => {
                const best = enrollmentResults.reduce((a, b) => a.pPass > b.pPass ? a : b)
                const marginalGain = enrollmentResults.find(r => r.pPass >= 0.80)
                
                if (marginalGain) {
                  return (
                    <p className="text-blue-800">
                      <strong>Consider adding {marginalGain.additionalPatients} patients.</strong> This would increase total enrollment to {marginalGain.newN} and achieve ≥80% probability of regulatory success. The incremental data strengthens the safety evidence base.
                    </p>
                  )
                } else {
                  return (
                    <p className="text-blue-800">
                      <strong>Enrollment alone may not be sufficient.</strong> Even with +100 patients, success probability remains below 80%. Consider addressing underlying revision patterns or adjusting regulatory strategy.
                    </p>
                  )
                }
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderStressTestScenario = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Question: What if we see additional revisions in the next follow-up period?
        </h3>
        <p className="text-gray-600">
          This stress test simulates the impact of {additionalRevisions} additional revision(s) on regulatory success probability. 
          Use this to understand risk exposure and plan mitigation strategies.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Additional Revisions</label>
              <select 
                value={additionalRevisions}
                onChange={(e) => setAdditionalRevisions(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value={1}>+1 revision</option>
                <option value={2}>+2 revisions</option>
                <option value={3}>+3 revisions</option>
                <option value={4}>+4 revisions</option>
                <option value={5}>+5 revisions</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Target Threshold</label>
              <select 
                value={selectedThreshold}
                onChange={(e) => setSelectedThreshold(e.target.value as keyof typeof REGULATORY_THRESHOLDS)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm min-w-[200px]"
              >
                {Object.entries(REGULATORY_THRESHOLDS).map(([key, val]) => (
                  <option key={key} value={key}>{val.label} ({(val.rate * 100).toFixed(0)}%)</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations}
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Simulating...' : 'Run Stress Test'}
          </button>
        </div>

        {stressResult && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-gray-50 rounded-xl">
                <div className="text-sm text-gray-500 mb-2">Current State</div>
                <div className="text-3xl font-bold text-gray-900">{H34_CURRENT.revisions} revisions</div>
                <div className="text-gray-600">in {H34_CURRENT.enrolled} patients ({(H34_CURRENT.currentRevisionRate * 100).toFixed(1)}%)</div>
              </div>
              <div className="p-6 bg-red-50 border border-red-200 rounded-xl">
                <div className="text-sm text-red-600 mb-2">Stress Scenario</div>
                <div className="text-3xl font-bold text-red-700">{stressResult.totalRevisions} revisions</div>
                <div className="text-red-600">in {H34_CURRENT.enrolled} patients ({(stressResult.mean * 100).toFixed(1)}% projected)</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-6 bg-gray-50 rounded-xl">
              <div>
                <div className="text-sm text-gray-500 mb-1">Probability of Still Passing {REGULATORY_THRESHOLDS[selectedThreshold].label}</div>
                <div className="text-5xl font-bold text-gray-900">
                  {(stressResult.pPass * 100).toFixed(1)}%
                </div>
              </div>
              <VerdictBadge probability={stressResult.pPass} />
            </div>

            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-800 mb-3">Risk Analysis</h4>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-600">New revision rate (mean)</td>
                    <td className="py-2 text-right font-mono">{(stressResult.mean * 100).toFixed(1)}%</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Worst case (95th percentile)</td>
                    <td className="py-2 text-right font-mono text-red-600">{(stressResult.p95 * 100).toFixed(1)}%</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Threshold</td>
                    <td className="py-2 text-right font-mono">{(REGULATORY_THRESHOLDS[selectedThreshold].rate * 100).toFixed(0)}%</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Buffer remaining</td>
                    <td className={`py-2 text-right font-mono ${REGULATORY_THRESHOLDS[selectedThreshold].rate - stressResult.mean > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {((REGULATORY_THRESHOLDS[selectedThreshold].rate - stressResult.mean) * 100).toFixed(1)}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className={`p-4 rounded-lg ${stressResult.pPass >= 0.50 ? 'bg-amber-50 border border-amber-200' : 'bg-red-50 border border-red-200'}`}>
              <h4 className={`font-medium mb-2 ${stressResult.pPass >= 0.50 ? 'text-amber-900' : 'text-red-900'}`}>Contingency Planning</h4>
              {stressResult.pPass >= 0.50 ? (
                <p className={stressResult.pPass >= 0.50 ? 'text-amber-800' : 'text-red-800'}>
                  <strong>Study remains viable but vulnerable.</strong> If {stressResult.additionalRevisions} more revision(s) occur, 
                  regulatory success probability drops but remains manageable. Prepare enhanced surveillance protocols 
                  and consider proactive communication with regulators.
                </p>
              ) : (
                <p className="text-red-800">
                  <strong>Significant risk exposure.</strong> This scenario would materially threaten regulatory approval. 
                  Immediate actions: (1) Investigate common factors in existing revisions, (2) Review surgical technique protocols, 
                  (3) Consider interim analysis to assess continuation criteria.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <StudyLayout studyId={params.studyId}>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Simulation Studio</h1>
          <p className="text-gray-500 mt-1">Decision-focused Monte Carlo simulations for clinical strategy</p>
        </div>

        <div className="bg-gray-100 rounded-xl p-1 inline-flex gap-1">
          {scenarios.map((scenario) => {
            const Icon = scenario.icon
            return (
              <button
                key={scenario.id}
                onClick={() => setActiveScenario(scenario.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeScenario === scenario.id
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {scenario.label}
              </button>
            )
          })}
        </div>

        {activeScenario === 'regulatory' && renderRegulatoryScenario()}
        {activeScenario === 'enrollment' && renderEnrollmentScenario()}
        {activeScenario === 'stress' && renderStressTestScenario()}

        <div className="text-xs text-gray-400 pt-4 border-t border-gray-100">
          <strong>Methodology:</strong> Simulations use Bayesian beta-binomial inference with current H-34 data 
          ({H34_CURRENT.revisions} revisions / {H34_CURRENT.enrolled} patients). Success probabilities represent 
          posterior estimates of meeting specified thresholds given observed data and sampling uncertainty.
        </div>
      </div>
    </StudyLayout>
  )
}
