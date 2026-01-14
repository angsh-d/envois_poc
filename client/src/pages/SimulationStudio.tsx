import { useState, useMemo } from 'react'
import StudyLayout from './StudyLayout'
import {
  Dices,
  BarChart3,
  Target,
  TrendingUp,
  Play,
  Info,
  RefreshCw
} from 'lucide-react'

interface SimulationStudioProps {
  params: { studyId: string }
}

type TabType = 'benchmark' | 'endpoint' | 'uncertainty'

const registryData = [
  { id: 'njr', name: 'NJR (UK)', survival5yr: 0.910, revisionRate5yr: 0.090, ci_lower: 0.088, ci_upper: 0.092 },
  { id: 'shar', name: 'SHAR (Sweden)', survival5yr: 0.850, revisionRate5yr: 0.150, ci_lower: 0.140, ci_upper: 0.160 },
  { id: 'nar', name: 'NAR (Norway)', survival5yr: 0.870, revisionRate5yr: 0.130, ci_lower: 0.120, ci_upper: 0.140 },
  { id: 'nzjr', name: 'NZJR (New Zealand)', survival5yr: 0.870, revisionRate5yr: 0.130, ci_lower: 0.115, ci_upper: 0.145 },
  { id: 'dhr', name: 'DHR (Denmark)', survival5yr: 0.920, revisionRate5yr: 0.080, ci_lower: 0.070, ci_upper: 0.090 },
  { id: 'eprd', name: 'EPRD (Germany)', survival5yr: 0.850, revisionRate5yr: 0.150, ci_lower: 0.140, ci_upper: 0.160 },
  { id: 'ajrr', name: 'AJRR (USA)', survival5yr: 0.880, revisionRate5yr: 0.120, ci_lower: 0.110, ci_upper: 0.130 },
  { id: 'cjrr', name: 'CJRR (Canada)', survival5yr: 0.875, revisionRate5yr: 0.125, ci_lower: 0.115, ci_upper: 0.135 },
  { id: 'aoanjrr', name: 'AOANJRR (Australia)', survival5yr: 0.885, revisionRate5yr: 0.115, ci_lower: 0.105, ci_upper: 0.125 },
]

const hazardRatios = [
  { factor: 'HHS <55 vs 81-100 (2yr)', hr: 4.34, ci_lower: 2.14, ci_upper: 7.95 },
  { factor: 'HHS <55 vs 81-100 (5yr)', hr: 3.08, ci_lower: 1.45, ci_upper: 5.84 },
  { factor: 'HHS <70 vs 90-100 (2yr)', hr: 2.32, ci_lower: 1.32, ci_upper: 3.85 },
  { factor: 'HHS Improvement ≤0 vs >50 (2yr)', hr: 18.1, ci_lower: 1.41, ci_upper: 234.8 },
  { factor: 'HHS ≤55 vs 81-100 (2yr, adj.)', hr: 3.90, ci_lower: 2.67, ci_upper: 5.69 },
  { factor: 'HHS ≤55 vs 81-100 (5yr, adj.)', hr: 2.48, ci_lower: 1.56, ci_upper: 3.95 },
]

function sampleLogNormal(mean: number, lower: number, upper: number): number {
  const logMean = Math.log(mean)
  const logSE = (Math.log(upper) - Math.log(lower)) / (2 * 1.96)
  const u1 = Math.random()
  const u2 = Math.random()
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  return Math.exp(logMean + logSE * z)
}

function sampleNormal(mean: number, lower: number, upper: number): number {
  const se = (upper - lower) / (2 * 1.96)
  const u1 = Math.random()
  const u2 = Math.random()
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  return mean + se * z
}

function runBenchmarkMonteCarlo(iterations: number, h34BaselineRate: number) {
  const results: { registry: string; samples: number[] }[] = []
  
  for (const reg of registryData) {
    const samples: number[] = []
    for (let i = 0; i < iterations; i++) {
      const sample = sampleNormal(reg.revisionRate5yr, reg.ci_lower, reg.ci_upper)
      samples.push(Math.max(0, Math.min(1, sample)))
    }
    results.push({ registry: reg.name, samples })
  }
  
  const h34Samples: number[] = []
  for (let i = 0; i < iterations; i++) {
    const hrSample = sampleLogNormal(hazardRatios[1].hr, hazardRatios[1].ci_lower, hazardRatios[1].ci_upper)
    const adjustedRate = h34BaselineRate * (1 + (hrSample - 1) * 0.15)
    h34Samples.push(Math.max(0, Math.min(1, adjustedRate)))
  }
  results.unshift({ registry: 'H-34 Study (Projected)', samples: h34Samples })
  
  return results
}

function runEndpointMonteCarlo(iterations: number, targetRate: number, baselineRate: number) {
  let successCount = 0
  const outcomes: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const hrIdx = Math.floor(Math.random() * hazardRatios.length)
    const hr = hazardRatios[hrIdx]
    const sampledHR = sampleLogNormal(hr.hr, hr.ci_lower, hr.ci_upper)
    
    const riskMultiplier = 1 + (sampledHR - 1) * 0.1
    const projectedRate = baselineRate * riskMultiplier
    const finalRate = Math.max(0, Math.min(1, projectedRate + (Math.random() - 0.5) * 0.02))
    
    outcomes.push(finalRate)
    if (finalRate <= targetRate) successCount++
  }
  
  return {
    pSuccess: successCount / iterations,
    outcomes,
    mean: outcomes.reduce((a, b) => a + b, 0) / outcomes.length,
    p5: outcomes.sort((a, b) => a - b)[Math.floor(iterations * 0.05)],
    p25: outcomes.sort((a, b) => a - b)[Math.floor(iterations * 0.25)],
    p50: outcomes.sort((a, b) => a - b)[Math.floor(iterations * 0.50)],
    p75: outcomes.sort((a, b) => a - b)[Math.floor(iterations * 0.75)],
    p95: outcomes.sort((a, b) => a - b)[Math.floor(iterations * 0.95)],
  }
}

function runUncertaintyMonteCarlo(iterations: number) {
  const timepoints = [1, 2, 5, 10]
  const baseRates = [0.042, 0.058, 0.090, 0.128]
  const results: { year: number; mean: number; p5: number; p95: number; samples: number[] }[] = []
  
  for (let t = 0; t < timepoints.length; t++) {
    const samples: number[] = []
    for (let i = 0; i < iterations; i++) {
      const hrSample = sampleLogNormal(hazardRatios[0].hr, hazardRatios[0].ci_lower, hazardRatios[0].ci_upper)
      const rate = baseRates[t] * (1 + (hrSample - 1) * 0.08 * (t + 1))
      samples.push(Math.max(0, Math.min(1, rate)))
    }
    samples.sort((a, b) => a - b)
    results.push({
      year: timepoints[t],
      mean: samples.reduce((a, b) => a + b, 0) / iterations,
      p5: samples[Math.floor(iterations * 0.05)],
      p95: samples[Math.floor(iterations * 0.95)],
      samples
    })
  }
  
  return results
}

function percentile(arr: number[], p: number): number {
  const sorted = [...arr].sort((a, b) => a - b)
  const idx = Math.floor(sorted.length * p)
  return sorted[idx]
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [activeTab, setActiveTab] = useState<TabType>('benchmark')
  const [iterations, setIterations] = useState(1000)
  const [isRunning, setIsRunning] = useState(false)
  const [benchmarkResults, setBenchmarkResults] = useState<{ registry: string; samples: number[] }[] | null>(null)
  const [endpointResults, setEndpointResults] = useState<ReturnType<typeof runEndpointMonteCarlo> | null>(null)
  const [uncertaintyResults, setUncertaintyResults] = useState<ReturnType<typeof runUncertaintyMonteCarlo> | null>(null)
  const [targetRevisionRate, setTargetRevisionRate] = useState(0.10)

  const tabs = [
    { id: 'benchmark' as const, label: 'Registry Benchmark Positioning', icon: BarChart3 },
    { id: 'endpoint' as const, label: 'Endpoint Achievement Probability', icon: Target },
    { id: 'uncertainty' as const, label: 'Uncertainty Over Time', icon: TrendingUp },
  ]

  const runSimulation = () => {
    setIsRunning(true)
    setTimeout(() => {
      if (activeTab === 'benchmark') {
        const results = runBenchmarkMonteCarlo(iterations, 0.08)
        setBenchmarkResults(results)
      } else if (activeTab === 'endpoint') {
        const results = runEndpointMonteCarlo(iterations, targetRevisionRate, 0.08)
        setEndpointResults(results)
      } else if (activeTab === 'uncertainty') {
        const results = runUncertaintyMonteCarlo(iterations)
        setUncertaintyResults(results)
      }
      setIsRunning(false)
    }, 100)
  }

  const renderBenchmarkTab = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Registry Benchmark Positioning</h3>
        </div>
        <p className="text-sm text-gray-600">
          Compare H-34 projected revision rates against 9 international arthroplasty registries using Monte Carlo sampling from confidence intervals.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations} 
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value={100}>100</option>
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Running...' : 'Run Simulation'}
          </button>
        </div>

        {benchmarkResults && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-800 mb-4">Forest Plot: 5-Year Revision Rate Distributions</h4>
            <div className="space-y-3">
              {benchmarkResults.map((result, idx) => {
                const mean = result.samples.reduce((a, b) => a + b, 0) / result.samples.length
                const p5 = percentile(result.samples, 0.05)
                const p95 = percentile(result.samples, 0.95)
                const isH34 = idx === 0
                
                return (
                  <div key={result.registry} className={`flex items-center gap-4 ${isH34 ? 'bg-blue-50 p-2 rounded-lg border border-blue-200' : ''}`}>
                    <div className="w-40 text-sm font-medium text-gray-700 truncate">{result.registry}</div>
                    <div className="flex-1 relative h-8">
                      <div className="absolute inset-y-0 left-0 right-0 flex items-center">
                        <div className="w-full h-px bg-gray-200"></div>
                      </div>
                      <div 
                        className="absolute top-1/2 -translate-y-1/2 h-2 bg-gray-300 rounded"
                        style={{
                          left: `${p5 * 100 * 5}%`,
                          width: `${(p95 - p5) * 100 * 5}%`
                        }}
                      ></div>
                      <div 
                        className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full ${isH34 ? 'bg-blue-600' : 'bg-gray-600'}`}
                        style={{ left: `${mean * 100 * 5}%` }}
                      ></div>
                    </div>
                    <div className="w-32 text-xs text-gray-600 text-right">
                      {(mean * 100).toFixed(1)}% [{(p5 * 100).toFixed(1)}-{(p95 * 100).toFixed(1)}]
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Interpretation:</strong> Each row shows the mean revision rate (dot) with 90% credible interval (bar). H-34 projection uses hazard ratio adjustment from Singh 2016.
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderEndpointTab = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <Target className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Endpoint Achievement Probability</h3>
        </div>
        <p className="text-sm text-gray-600">
          Estimate the probability that the H-34 study will achieve its primary endpoint (revision rate below target threshold) using Monte Carlo simulation with literature-derived hazard ratios.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Target Revision Rate</label>
              <select 
                value={targetRevisionRate} 
                onChange={(e) => setTargetRevisionRate(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value={0.05}>5%</option>
                <option value={0.08}>8%</option>
                <option value={0.10}>10%</option>
                <option value={0.12}>12%</option>
                <option value={0.15}>15%</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations} 
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value={100}>100</option>
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Running...' : 'Run Simulation'}
          </button>
        </div>

        {endpointResults && (
          <div className="mt-6 space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-xl p-4 text-center">
                <div className={`text-4xl font-bold ${endpointResults.pSuccess >= 0.8 ? 'text-green-600' : endpointResults.pSuccess >= 0.5 ? 'text-amber-600' : 'text-red-600'}`}>
                  {(endpointResults.pSuccess * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">P(Success)</div>
                <div className="text-xs text-gray-400">Probability of achieving ≤{(targetRevisionRate * 100).toFixed(0)}% revision rate</div>
              </div>
              <div className="bg-gray-50 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-gray-800">{(endpointResults.mean * 100).toFixed(1)}%</div>
                <div className="text-sm text-gray-600 mt-1">Mean Projected Rate</div>
              </div>
              <div className="bg-gray-50 rounded-xl p-4 text-center">
                <div className="text-lg font-bold text-gray-800">
                  {(endpointResults.p5 * 100).toFixed(1)}% - {(endpointResults.p95 * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">90% Credible Interval</div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-800 mb-3">Distribution Summary</h4>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Percentile</th>
                    <th className="text-right py-2 text-gray-500 font-medium">Revision Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr><td className="py-1.5 text-gray-700">5th (Optimistic)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p5 * 100).toFixed(2)}%</td></tr>
                  <tr><td className="py-1.5 text-gray-700">25th</td><td className="py-1.5 text-right font-mono">{(endpointResults.p25 * 100).toFixed(2)}%</td></tr>
                  <tr><td className="py-1.5 text-gray-700">50th (Median)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p50 * 100).toFixed(2)}%</td></tr>
                  <tr><td className="py-1.5 text-gray-700">75th</td><td className="py-1.5 text-right font-mono">{(endpointResults.p75 * 100).toFixed(2)}%</td></tr>
                  <tr><td className="py-1.5 text-gray-700">95th (Pessimistic)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p95 * 100).toFixed(2)}%</td></tr>
                </tbody>
              </table>
            </div>

            <div className="pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Methodology:</strong> Each iteration samples a hazard ratio from Singh 2016 (Table 2 & 5) within its 95% CI, applies risk adjustment to baseline revision rate, and compares against target threshold.
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderUncertaintyTab = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Uncertainty Over Time</h3>
        </div>
        <p className="text-sm text-gray-600">
          Visualize how projection uncertainty grows at different follow-up timepoints (1, 2, 5, 10 years) using registry baseline rates and HR sampling.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Iterations</label>
              <select 
                value={iterations} 
                onChange={(e) => setIterations(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value={100}>100</option>
                <option value={1000}>1,000</option>
                <option value={5000}>5,000</option>
                <option value={10000}>10,000</option>
              </select>
            </div>
          </div>
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Running...' : 'Run Simulation'}
          </button>
        </div>

        {uncertaintyResults && (
          <div className="mt-6 space-y-6">
            <div>
              <h4 className="font-medium text-gray-800 mb-4">Confidence Bands by Follow-up Year</h4>
              <div className="relative h-64 bg-gray-50 rounded-lg p-4">
                <div className="absolute left-12 right-4 top-4 bottom-8">
                  {uncertaintyResults.map((result, idx) => {
                    const xPos = (idx / (uncertaintyResults.length - 1)) * 100
                    const yMean = 100 - (result.mean * 100 * 4)
                    const yP5 = 100 - (result.p5 * 100 * 4)
                    const yP95 = 100 - (result.p95 * 100 * 4)
                    
                    return (
                      <div key={result.year} className="absolute" style={{ left: `${xPos}%`, transform: 'translateX(-50%)' }}>
                        <div 
                          className="absolute w-6 bg-blue-100 border-l border-r border-blue-300"
                          style={{ 
                            top: `${yP95}%`, 
                            height: `${yP5 - yP95}%`,
                            left: '-12px'
                          }}
                        ></div>
                        <div 
                          className="absolute w-3 h-3 bg-blue-600 rounded-full"
                          style={{ top: `${yMean}%`, left: '-6px', transform: 'translateY(-50%)' }}
                        ></div>
                        <div className="absolute top-full mt-2 text-xs text-gray-600 font-medium" style={{ left: '0', transform: 'translateX(-50%)' }}>
                          {result.year}yr
                        </div>
                      </div>
                    )
                  })}
                  <div className="absolute left-0 top-0 bottom-0 w-px bg-gray-300"></div>
                  <div className="absolute left-0 right-0 bottom-0 h-px bg-gray-300"></div>
                </div>
                <div className="absolute left-0 top-4 bottom-8 flex flex-col justify-between text-xs text-gray-500">
                  <span>25%</span>
                  <span>20%</span>
                  <span>15%</span>
                  <span>10%</span>
                  <span>5%</span>
                  <span>0%</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-800 mb-3">Numerical Summary</h4>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Timepoint</th>
                    <th className="text-right py-2 text-gray-500 font-medium">Mean</th>
                    <th className="text-right py-2 text-gray-500 font-medium">5th %ile</th>
                    <th className="text-right py-2 text-gray-500 font-medium">95th %ile</th>
                    <th className="text-right py-2 text-gray-500 font-medium">CI Width</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {uncertaintyResults.map((result) => (
                    <tr key={result.year}>
                      <td className="py-1.5 text-gray-700 font-medium">{result.year}-Year</td>
                      <td className="py-1.5 text-right font-mono">{(result.mean * 100).toFixed(2)}%</td>
                      <td className="py-1.5 text-right font-mono text-green-600">{(result.p5 * 100).toFixed(2)}%</td>
                      <td className="py-1.5 text-right font-mono text-red-600">{(result.p95 * 100).toFixed(2)}%</td>
                      <td className="py-1.5 text-right font-mono text-gray-500">±{((result.p95 - result.p5) * 100 / 2).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Interpretation:</strong> Uncertainty compounds over time as HR sampling interacts with longer follow-up periods. The CI width at 10 years is approximately {uncertaintyResults.length > 0 ? ((uncertaintyResults[3].p95 - uncertaintyResults[3].p5) / (uncertaintyResults[0].p95 - uncertaintyResults[0].p5)).toFixed(1) : 'N/A'}x wider than at 1 year.
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
          <p className="text-gray-500 mt-1">Monte Carlo simulations for clinical outcome projections</p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-amber-800">
            <p className="font-medium mb-1">Simulation Methodology</p>
            <p>All simulations use real data from literature benchmarks (Singh 2016) and 9 international registries. Hazard ratios are sampled from their 95% confidence intervals using log-normal distributions to reflect uncertainty in risk estimates.</p>
          </div>
        </div>

        <div className="flex gap-2 border-b border-gray-100 pb-4">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {activeTab === 'benchmark' && renderBenchmarkTab()}
        {activeTab === 'endpoint' && renderEndpointTab()}
        {activeTab === 'uncertainty' && renderUncertaintyTab()}
      </div>
    </StudyLayout>
  )
}
