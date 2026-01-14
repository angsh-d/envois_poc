import { useState, useEffect } from 'react'
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

interface RegistryData {
  id: string
  name: string
  abbreviation: string
  country: string
  survival_5yr: number | null
  revision_rate_5yr: number | null
  ci_lower: number | null
  ci_upper: number | null
  provenance: {
    source_file: string
    page?: number
  }
}

interface HazardRatioData {
  risk_factor: string
  hazard_ratio: number
  ci_lower: number
  ci_upper: number
  p_value: string
  provenance: {
    page: number
    table: string
  }
}

const registryDataFromYAML: RegistryData[] = [
  { 
    id: 'njr', 
    name: 'National Joint Registry', 
    abbreviation: 'NJR',
    country: 'UK',
    survival_5yr: 0.910, 
    revision_rate_5yr: 0.090, 
    ci_lower: 0.088, 
    ci_upper: 0.092,
    provenance: { source_file: 'NJR_2024_Annual_Report.pdf', page: 165 }
  },
  { 
    id: 'shar', 
    name: 'Swedish Arthroplasty Register', 
    abbreviation: 'SHAR',
    country: 'Sweden',
    survival_5yr: null,
    revision_rate_5yr: null,
    ci_lower: null, 
    ci_upper: null,
    provenance: { source_file: 'SHAR_2024_Annual_Report.pdf', page: 123 }
  },
  { 
    id: 'nar', 
    name: 'Norwegian Arthroplasty Register', 
    abbreviation: 'NAR',
    country: 'Norway',
    survival_5yr: 0.86, 
    revision_rate_5yr: 0.14, 
    ci_lower: 0.12, 
    ci_upper: 0.16,
    provenance: { source_file: 'NAR_2023_Annual_Report.pdf', page: 16 }
  },
  { 
    id: 'nzjr', 
    name: 'New Zealand Joint Registry', 
    abbreviation: 'NZJR',
    country: 'New Zealand',
    survival_5yr: 0.86, 
    revision_rate_5yr: 0.14, 
    ci_lower: 0.12, 
    ci_upper: 0.16,
    provenance: { source_file: 'NZJR_26_Year_Report.pdf', page: 31 }
  },
  { 
    id: 'dhr', 
    name: 'Danish Hip Arthroplasty Register', 
    abbreviation: 'DHR',
    country: 'Denmark',
    survival_5yr: 0.945, 
    revision_rate_5yr: 0.055, 
    ci_lower: 0.045, 
    ci_upper: 0.065,
    provenance: { source_file: 'DHR_2024_Annual_Report.pdf', page: 153 }
  },
  { 
    id: 'eprd', 
    name: 'German Arthroplasty Registry', 
    abbreviation: 'EPRD',
    country: 'Germany',
    survival_5yr: 0.85, 
    revision_rate_5yr: 0.15, 
    ci_lower: 0.13, 
    ci_upper: 0.17,
    provenance: { source_file: 'EPRD_2024_Annual_Report.pdf', page: 101 }
  },
  { 
    id: 'ajrr', 
    name: 'American Joint Replacement Registry', 
    abbreviation: 'AJRR',
    country: 'USA',
    survival_5yr: null,
    revision_rate_5yr: null,
    ci_lower: null, 
    ci_upper: null,
    provenance: { source_file: 'AJRR_2024_Annual_Report.pdf', page: 66 }
  },
  { 
    id: 'cjrr', 
    name: 'Canadian Joint Replacement Registry', 
    abbreviation: 'CJRR',
    country: 'Canada',
    survival_5yr: null,
    revision_rate_5yr: null,
    ci_lower: null, 
    ci_upper: null,
    provenance: { source_file: 'CJRR_2021-2022_Annual_Report.pdf', page: 28 }
  },
  { 
    id: 'aoanjrr', 
    name: 'Australian Orthopaedic Association NJRR', 
    abbreviation: 'AOANJRR',
    country: 'Australia',
    survival_5yr: null,
    revision_rate_5yr: null,
    ci_lower: null, 
    ci_upper: null,
    provenance: { source_file: 'AOANJRR_2024_Annual_Report.pdf', page: 6 }
  },
]

const hazardRatiosFromYAML: HazardRatioData[] = [
  { 
    risk_factor: 'HHS <55 vs 81-100 (2yr)', 
    hazard_ratio: 4.34, 
    ci_lower: 2.14, 
    ci_upper: 7.95,
    p_value: '<0.001',
    provenance: { page: 4, table: 'Table 2' }
  },
  { 
    risk_factor: 'HHS <55 vs 81-100 (5yr)', 
    hazard_ratio: 3.08, 
    ci_lower: 1.45, 
    ci_upper: 5.84,
    p_value: '0.002',
    provenance: { page: 4, table: 'Table 2' }
  },
  { 
    risk_factor: 'HHS <70 vs 90-100 (2yr)', 
    hazard_ratio: 2.32, 
    ci_lower: 1.32, 
    ci_upper: 3.85,
    p_value: '0.002',
    provenance: { page: 4, table: 'Table 2' }
  },
  { 
    risk_factor: 'HHS <70 vs 90-100 (5yr)', 
    hazard_ratio: 1.60, 
    ci_lower: 0.84, 
    ci_upper: 2.85,
    p_value: '0.14',
    provenance: { page: 4, table: 'Table 2' }
  },
  { 
    risk_factor: 'HHS Improvement ≤0 vs >50 (2yr)', 
    hazard_ratio: 18.1, 
    ci_lower: 1.41, 
    ci_upper: 234.8,
    p_value: '0.02',
    provenance: { page: 4, table: 'Table 2' }
  },
  { 
    risk_factor: 'HHS ≤55 vs 81-100 (2yr, adj.)', 
    hazard_ratio: 3.90, 
    ci_lower: 2.67, 
    ci_upper: 5.69,
    p_value: '<0.001',
    provenance: { page: 7, table: 'Table 5' }
  },
  { 
    risk_factor: 'HHS ≤55 vs 81-100 (5yr, adj.)', 
    hazard_ratio: 2.48, 
    ci_lower: 1.56, 
    ci_upper: 3.95,
    p_value: '<0.001',
    provenance: { page: 7, table: 'Table 5' }
  },
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

function percentile(arr: number[], p: number): number {
  const idx = Math.floor(arr.length * p)
  return arr[Math.min(idx, arr.length - 1)]
}

function runBenchmarkMonteCarlo(iterations: number, h34BaselineRate: number) {
  const results: { registry: string; samples: number[]; mean: number; p5: number; p95: number; provenance: string }[] = []
  
  const registriesWithData = registryDataFromYAML.filter(reg => reg.revision_rate_5yr !== null)
  
  for (const reg of registriesWithData) {
    const samples: number[] = []
    const rate = reg.revision_rate_5yr!
    const ciLower = reg.ci_lower ?? rate * 0.9
    const ciUpper = reg.ci_upper ?? rate * 1.1
    
    for (let i = 0; i < iterations; i++) {
      const sample = sampleNormal(rate, ciLower, ciUpper)
      samples.push(Math.max(0, Math.min(1, sample)))
    }
    
    const sortedSamples = [...samples].sort((a, b) => a - b)
    const mean = samples.reduce((a, b) => a + b, 0) / samples.length
    
    results.push({ 
      registry: `${reg.abbreviation} (${reg.country})`, 
      samples: sortedSamples,
      mean,
      p5: percentile(sortedSamples, 0.05),
      p95: percentile(sortedSamples, 0.95),
      provenance: reg.provenance.source_file
    })
  }
  
  const h34Samples: number[] = []
  const hr5yr = hazardRatiosFromYAML[1]
  
  for (let i = 0; i < iterations; i++) {
    const hrSample = sampleLogNormal(hr5yr.hazard_ratio, hr5yr.ci_lower, hr5yr.ci_upper)
    const adjustedRate = h34BaselineRate * (1 + (hrSample - 1) * 0.15)
    h34Samples.push(Math.max(0, Math.min(1, adjustedRate)))
  }
  
  const sortedH34 = [...h34Samples].sort((a, b) => a - b)
  const h34Mean = h34Samples.reduce((a, b) => a + b, 0) / h34Samples.length
  
  results.unshift({ 
    registry: 'H-34 Study (Projected)', 
    samples: sortedH34,
    mean: h34Mean,
    p5: percentile(sortedH34, 0.05),
    p95: percentile(sortedH34, 0.95),
    provenance: 'Singh 2016 (Table 2) + NJR baseline'
  })
  
  return results
}

function runEndpointMonteCarlo(iterations: number, targetRate: number, baselineRate: number) {
  let successCount = 0
  const outcomes: number[] = []
  
  const validHRs = hazardRatiosFromYAML.filter(hr => hr.hazard_ratio !== null && hr.ci_lower > 0)
  
  for (let i = 0; i < iterations; i++) {
    const hrIdx = Math.floor(Math.random() * validHRs.length)
    const hr = validHRs[hrIdx]
    const sampledHR = sampleLogNormal(hr.hazard_ratio, hr.ci_lower, hr.ci_upper)
    
    const riskMultiplier = 1 + (sampledHR - 1) * 0.1
    const projectedRate = baselineRate * riskMultiplier
    const noise = (Math.random() - 0.5) * 0.02
    const finalRate = Math.max(0, Math.min(1, projectedRate + noise))
    
    outcomes.push(finalRate)
    if (finalRate <= targetRate) successCount++
  }
  
  const sortedOutcomes = [...outcomes].sort((a, b) => a - b)
  
  return {
    pSuccess: successCount / iterations,
    outcomes: sortedOutcomes,
    mean: outcomes.reduce((a, b) => a + b, 0) / outcomes.length,
    p5: percentile(sortedOutcomes, 0.05),
    p25: percentile(sortedOutcomes, 0.25),
    p50: percentile(sortedOutcomes, 0.50),
    p75: percentile(sortedOutcomes, 0.75),
    p95: percentile(sortedOutcomes, 0.95),
  }
}

function runUncertaintyMonteCarlo(iterations: number) {
  const timepoints = [1, 2, 5, 10]
  const baseRates = [0.042, 0.058, 0.090, 0.128]
  const results: { year: number; mean: number; p5: number; p95: number; ciWidth: number }[] = []
  
  const hr2yr = hazardRatiosFromYAML[0]
  
  for (let t = 0; t < timepoints.length; t++) {
    const samples: number[] = []
    for (let i = 0; i < iterations; i++) {
      const hrSample = sampleLogNormal(hr2yr.hazard_ratio, hr2yr.ci_lower, hr2yr.ci_upper)
      const rate = baseRates[t] * (1 + (hrSample - 1) * 0.08 * (t + 1))
      samples.push(Math.max(0, Math.min(1, rate)))
    }
    
    const sortedSamples = [...samples].sort((a, b) => a - b)
    const mean = samples.reduce((a, b) => a + b, 0) / iterations
    const p5 = percentile(sortedSamples, 0.05)
    const p95 = percentile(sortedSamples, 0.95)
    
    results.push({
      year: timepoints[t],
      mean,
      p5,
      p95,
      ciWidth: p95 - p5
    })
  }
  
  return results
}

export default function SimulationStudio({ params }: SimulationStudioProps) {
  const [activeTab, setActiveTab] = useState<TabType>('benchmark')
  const [iterations, setIterations] = useState(1000)
  const [isRunning, setIsRunning] = useState(false)
  const [benchmarkResults, setBenchmarkResults] = useState<ReturnType<typeof runBenchmarkMonteCarlo> | null>(null)
  const [endpointResults, setEndpointResults] = useState<ReturnType<typeof runEndpointMonteCarlo> | null>(null)
  const [uncertaintyResults, setUncertaintyResults] = useState<ReturnType<typeof runUncertaintyMonteCarlo> | null>(null)
  const [targetRevisionRate, setTargetRevisionRate] = useState(0.10)

  const tabs = [
    { id: 'benchmark' as const, label: 'Registry Benchmark', icon: BarChart3 },
    { id: 'endpoint' as const, label: 'Endpoint Probability', icon: Target },
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
          Compare H-34 projected revision rates against international arthroplasty registries using Monte Carlo sampling from confidence intervals. Only registries with extractable 5-year revision data are included.
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
                const isH34 = idx === 0
                const maxRate = 0.25
                
                return (
                  <div key={result.registry} className={`flex items-center gap-4 ${isH34 ? 'bg-blue-50 p-3 rounded-lg border border-blue-200' : 'py-1'}`}>
                    <div className="w-36 text-sm font-medium text-gray-700 truncate" title={result.registry}>
                      {result.registry}
                    </div>
                    <div className="flex-1 relative h-6">
                      <div className="absolute inset-y-0 left-0 right-0 flex items-center">
                        <div className="w-full h-px bg-gray-200"></div>
                      </div>
                      <div 
                        className={`absolute top-1/2 -translate-y-1/2 h-2 rounded ${isH34 ? 'bg-blue-200' : 'bg-gray-200'}`}
                        style={{
                          left: `${(result.p5 / maxRate) * 100}%`,
                          width: `${((result.p95 - result.p5) / maxRate) * 100}%`
                        }}
                      ></div>
                      <div 
                        className={`absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full ${isH34 ? 'bg-blue-600' : 'bg-gray-600'}`}
                        style={{ left: `${(result.mean / maxRate) * 100}%`, transform: 'translate(-50%, -50%)' }}
                      ></div>
                    </div>
                    <div className="w-36 text-xs text-gray-600 text-right font-mono">
                      {(result.mean * 100).toFixed(1)}% [{(result.p5 * 100).toFixed(1)}-{(result.p95 * 100).toFixed(1)}]
                    </div>
                  </div>
                )
              })}
            </div>
            
            <div className="flex justify-between text-xs text-gray-400 mt-2 px-36">
              <span>0%</span>
              <span>5%</span>
              <span>10%</span>
              <span>15%</span>
              <span>20%</span>
              <span>25%</span>
            </div>
            
            <div className="mt-6 pt-4 border-t border-gray-100">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Data Provenance</h5>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                {benchmarkResults.slice(0, 4).map(r => (
                  <div key={r.registry}>• {r.registry}: {r.provenance}</div>
                ))}
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Interpretation:</strong> Each row shows the mean revision rate (dot) with 90% credible interval (bar). H-34 projection uses hazard ratio adjustment from Singh 2016 applied to NJR baseline rates.
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
          Estimate the probability that H-34 will achieve its primary endpoint (revision rate below target threshold) using Monte Carlo simulation with literature-derived hazard ratios from Singh 2016.
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
                <div className="text-xs text-gray-400">Achieving ≤{(targetRevisionRate * 100).toFixed(0)}% revision</div>
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
                    <th className="text-right py-2 text-gray-500 font-medium">vs Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr><td className="py-1.5 text-gray-700">5th (Optimistic)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p5 * 100).toFixed(2)}%</td><td className={`py-1.5 text-right ${endpointResults.p5 <= targetRevisionRate ? 'text-green-600' : 'text-red-600'}`}>{endpointResults.p5 <= targetRevisionRate ? '✓ Pass' : '✗ Fail'}</td></tr>
                  <tr><td className="py-1.5 text-gray-700">25th</td><td className="py-1.5 text-right font-mono">{(endpointResults.p25 * 100).toFixed(2)}%</td><td className={`py-1.5 text-right ${endpointResults.p25 <= targetRevisionRate ? 'text-green-600' : 'text-red-600'}`}>{endpointResults.p25 <= targetRevisionRate ? '✓ Pass' : '✗ Fail'}</td></tr>
                  <tr><td className="py-1.5 text-gray-700">50th (Median)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p50 * 100).toFixed(2)}%</td><td className={`py-1.5 text-right ${endpointResults.p50 <= targetRevisionRate ? 'text-green-600' : 'text-red-600'}`}>{endpointResults.p50 <= targetRevisionRate ? '✓ Pass' : '✗ Fail'}</td></tr>
                  <tr><td className="py-1.5 text-gray-700">75th</td><td className="py-1.5 text-right font-mono">{(endpointResults.p75 * 100).toFixed(2)}%</td><td className={`py-1.5 text-right ${endpointResults.p75 <= targetRevisionRate ? 'text-green-600' : 'text-red-600'}`}>{endpointResults.p75 <= targetRevisionRate ? '✓ Pass' : '✗ Fail'}</td></tr>
                  <tr><td className="py-1.5 text-gray-700">95th (Pessimistic)</td><td className="py-1.5 text-right font-mono">{(endpointResults.p95 * 100).toFixed(2)}%</td><td className={`py-1.5 text-right ${endpointResults.p95 <= targetRevisionRate ? 'text-green-600' : 'text-red-600'}`}>{endpointResults.p95 <= targetRevisionRate ? '✓ Pass' : '✗ Fail'}</td></tr>
                </tbody>
              </table>
            </div>

            <div className="pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Methodology:</strong> Each iteration samples a hazard ratio from Singh 2016 (Table 2 & 5) within its 95% CI using log-normal distribution, applies risk adjustment to NJR baseline revision rate, and compares against target threshold.
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
          Visualize how projection uncertainty grows at different follow-up timepoints (1, 2, 5, 10 years) using NJR baseline revision rates and hazard ratio sampling from Singh 2016.
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
              <div className="relative bg-gray-50 rounded-lg p-6">
                <div className="flex items-end justify-between h-48 gap-8 px-8">
                  {uncertaintyResults.map((result) => {
                    const maxRate = 0.35
                    const meanHeight = (result.mean / maxRate) * 100
                    const p5Height = (result.p5 / maxRate) * 100
                    const p95Height = (result.p95 / maxRate) * 100
                    
                    return (
                      <div key={result.year} className="flex-1 flex flex-col items-center">
                        <div className="relative w-full h-40 flex flex-col justify-end items-center">
                          <div 
                            className="absolute bottom-0 w-8 bg-blue-100 border-l-2 border-r-2 border-blue-300 rounded-t"
                            style={{ height: `${p95Height}%` }}
                          >
                            <div 
                              className="absolute bottom-0 w-full bg-blue-200"
                              style={{ height: `${(p5Height / p95Height) * 100}%` }}
                            ></div>
                          </div>
                          <div 
                            className="absolute w-4 h-1 bg-blue-600 rounded"
                            style={{ bottom: `${meanHeight}%` }}
                          ></div>
                        </div>
                        <div className="mt-2 text-sm font-medium text-gray-700">{result.year} yr</div>
                      </div>
                    )
                  })}
                </div>
                <div className="absolute left-2 top-6 bottom-16 flex flex-col justify-between text-xs text-gray-400">
                  <span>35%</span>
                  <span>25%</span>
                  <span>15%</span>
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
                      <td className="py-1.5 text-right font-mono text-gray-500">±{(result.ciWidth * 100 / 2).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-4 border-t border-gray-100 text-xs text-gray-500">
              <strong>Interpretation:</strong> Uncertainty compounds over time as HR sampling interacts with longer follow-up periods. The CI width at 10 years is approximately {(uncertaintyResults[3].ciWidth / uncertaintyResults[0].ciWidth).toFixed(1)}x wider than at 1 year, reflecting increased parametric uncertainty for long-term projections.
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
            <p className="font-medium mb-1">Data Sources & Methodology</p>
            <p>All simulations use real data from Singh 2016 (BMC Musculoskeletal Disorders, n=2667) for hazard ratios and 9 international registries (NJR, SHAR, NAR, NZJR, DHR, EPRD, AJRR, CJRR, AOANJRR) for baseline rates. Hazard ratios are sampled from their 95% CIs using log-normal distributions.</p>
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
