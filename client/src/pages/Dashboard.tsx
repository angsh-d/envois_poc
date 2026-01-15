import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, StatCard } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { DashboardSkeleton } from '@/components/Skeleton'
import {
  fetchDashboardExecutiveSummary,
  fetchDashboardStudyProgress,
  fetchDashboardBenchmarks,
  fetchReadiness,
  fetchRiskSummary,
  type DashboardExecutiveSummary,
  type DashboardStudyProgress,
  type DashboardBenchmarks,
  type LiteratureCitation,
  type ReadinessResponse,
  type RiskSummaryResponse
} from '@/lib/api'
import { useRoute } from 'wouter'
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  HelpCircle
} from 'lucide-react'

const METRIC_INFO: Record<string, { displayName: string; tooltip: string }> = {
  hhs_improvement: {
    displayName: 'HHS Improvement',
    tooltip: 'Mean change in Harris Hip Score from baseline to 2 years. Includes only patients with both baseline and 2-year scores. Example: +34.9 means patients improved by ~35 points on average. Higher is better.'
  },
  hhs_baseline: {
    displayName: 'HHS Baseline',
    tooltip: 'Mean Harris Hip Score at study enrollment. Includes all patients with baseline HHS recorded. Example: 37.7 indicates moderate hip dysfunction before surgery. Range: 0-100.'
  },
  hhs_2yr: {
    displayName: 'HHS 2-Year',
    tooltip: 'Mean Harris Hip Score at 2-year follow-up. Includes patients who have reached 2-year visit. Example: 72.6 indicates good hip function post-surgery. Range: 0-100, higher is better.'
  },
  mcid_achievement: {
    displayName: 'MCID Achievement',
    tooltip: 'Percentage of patients achieving Minimal Clinically Important Difference (20+ point HHS improvement). Includes only patients with both baseline and 2-year scores. Example: 62.5% means 62.5 of 100 eligible patients had meaningful improvement.'
  },
  ohs_improvement: {
    displayName: 'OHS Improvement',
    tooltip: 'Mean change in Oxford Hip Score from baseline. Includes only patients with both baseline and follow-up OHS scores. Example: +15.8 means patients improved by ~16 points on average. Higher is better.'
  },
  survival_2yr: {
    displayName: '2-Year Survival',
    tooltip: 'Implant survival rate at 2 years (no revision surgery required). Calculated from all enrolled patients. Example: 94.6% means 94.6 of 100 implants still functioning. Higher is better.'
  },
  dislocation_rate: {
    displayName: 'Dislocation Rate',
    tooltip: 'Percentage of patients experiencing hip dislocation. Calculated from all adverse events across enrolled patients. Example: 2.5% means 2.5 dislocations per 100 patients. Lower is better.'
  },
  infection_rate: {
    displayName: 'Infection Rate',
    tooltip: 'Percentage of patients developing infection. Calculated from all adverse events across enrolled patients. Example: 1.2% means 1.2 infections per 100 procedures. Lower is better.'
  }
}

function statusToVariant(status: string): 'success' | 'warning' | 'danger' {
  switch (status?.toUpperCase()) {
    case 'GREEN':
      return 'success'
    case 'YELLOW':
      return 'warning'
    case 'RED':
      return 'danger'
    default:
      return 'warning'
  }
}

function getComparisonStatus(status: string | undefined): 'success' | 'warning' | 'danger' {
  switch (status) {
    case 'favorable':
      return 'success'
    case 'acceptable':
      return 'warning'
    case 'concerning':
      return 'danger'
    default:
      return 'warning'
  }
}

function calculateReadinessScore(data: ReadinessResponse): number {
  let score = 0
  let total = 0

  // Enrollment contribution (40% weight)
  total += 40
  if (data.enrollment.is_ready) {
    score += 40
  } else {
    score += Math.min(40, (data.enrollment.percent_complete / 100) * 40)
  }

  // Compliance contribution (20% weight)
  total += 20
  if (data.compliance.is_ready) {
    score += 20
  } else {
    score += data.compliance.deviation_rate < 0.05 ? 15 : data.compliance.deviation_rate < 0.10 ? 10 : 5
  }

  // Safety contribution (20% weight)
  total += 20
  if (data.safety.is_ready) {
    score += 20
  } else {
    score += data.safety.n_signals === 0 ? 15 : data.safety.n_signals < 3 ? 10 : 5
  }

  // Data completeness contribution (20% weight)
  total += 20
  if (data.data_completeness.is_ready) {
    score += 20
  } else {
    score += Math.min(20, (data.data_completeness.completion_rate / 100) * 20)
  }

  return Math.round((score / total) * 100)
}

export default function Dashboard() {
  const [, params] = useRoute('/study/:studyId')
  const studyId = params?.studyId || 'h34-delta'

  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardExecutiveSummary,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    retry: 2,
  })

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['dashboard-progress'],
    queryFn: fetchDashboardStudyProgress,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    retry: 2,
  })

  const { data: benchmarks, isLoading: benchmarksLoading } = useQuery({
    queryKey: ['dashboard-benchmarks'],
    queryFn: fetchDashboardBenchmarks,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: readinessData, isLoading: readinessLoading } = useQuery({
    queryKey: ['readiness-assessment'],
    queryFn: fetchReadiness,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['risk-summary'],
    queryFn: fetchRiskSummary,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const isLoading = summaryLoading || progressLoading || benchmarksLoading || readinessLoading || riskLoading

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-gray-500 mt-1">H-34 DELTA Revision Cup Study Overview</p>
        </div>
        <DashboardSkeleton />
        <p className="text-center text-sm text-gray-400 mt-4">Loading dashboard data... This may take a moment on first visit.</p>
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-600">
        <AlertTriangle className="w-6 h-6 mr-2" />
        <span>Failed to load dashboard data. Please check the backend is running.</span>
      </div>
    )
  }

  const metricsMap = (summary?.metrics || []).reduce((acc, m) => {
    acc[m.name] = m
    return acc
  }, {} as Record<string, { name: string; value: string; status: string; trend: string }>)

  const safetyMetric = metricsMap['Safety Signals'] || { value: 'N/A', status: 'GREEN' }
  const complianceMetric = metricsMap['Protocol Compliance'] || { value: 'N/A', status: 'GREEN' }
  const enrollmentMetric = metricsMap['Enrollment'] || { value: 'N/A', status: 'YELLOW' }

  // Calculate weighted readiness score (same formula as Readiness page)
  const readinessScore = readinessData ? calculateReadinessScore(readinessData) : null
  const readinessScoreStatus = readinessScore !== null
    ? (readinessScore >= 80 ? 'GREEN' : readinessScore >= 50 ? 'YELLOW' : 'RED')
    : 'YELLOW'

  const benchmarkRows = buildBenchmarkRows(benchmarks)

  // Build dynamic tooltips based on actual data
  const enrollmentTooltip = progress
    ? `${progress.current_enrollment} of ${progress.target_enrollment} patients enrolled (${Math.round(progress.enrollment_pct)}%). Need ${Math.max(0, progress.target_enrollment - progress.current_enrollment)} more to reach target.`
    : 'Loading enrollment data...'

  const readinessTooltip = readinessData
    ? `Weighted score breakdown: Enrollment ${readinessData.enrollment.is_ready ? '✓' : `${Math.round(readinessData.enrollment.percent_complete)}%`} (40% weight) • Compliance ${readinessData.compliance.is_ready ? '✓' : `${Math.round((1 - readinessData.compliance.deviation_rate) * 100)}%`} (20%) • Safety ${readinessData.safety.is_ready ? '✓' : `${readinessData.safety.n_signals} signals`} (20%) • Data ${readinessData.data_completeness.is_ready ? '✓' : `${Math.round(readinessData.data_completeness.completion_rate)}%`} (20%)`
    : 'Loading readiness data...'

  const safetyTooltip = readinessData
    ? `${readinessData.safety.n_signals} safety metric(s) exceeding thresholds. Monitors: revision rate, dislocation rate, infection rate, fracture rate. Status: ${readinessData.safety.overall_status}.`
    : 'Loading safety data...'

  // Parse compliance value from dashboard API to ensure tooltip matches displayed value
  const complianceValue = complianceMetric.value !== 'N/A'
    ? parseInt(complianceMetric.value.replace('%', ''))
    : (readinessData ? Math.round((1 - readinessData.compliance.deviation_rate) * 100) : 0)
  const deviationRate = 100 - complianceValue

  const complianceTooltip = readinessData
    ? `${complianceValue}% of visits within protocol windows. Deviation rate: ${deviationRate}%. Critical: ${readinessData.compliance.by_severity?.critical || 0}, Major: ${readinessData.compliance.by_severity?.major || 0}, Minor: ${readinessData.compliance.by_severity?.minor || 0}.`
    : 'Loading compliance data...'

  const patientsTooltip = progress
    ? [
        `${progress.current_enrollment} enrolled of ${progress.target_enrollment} target.`,
        progress.evaluable_patients !== undefined ? `${progress.evaluable_patients} patients currently evaluable (have 2-year HHS data).` : null,
      ].filter(Boolean).join(' ')
    : 'Loading patient data...'

  // Calculate risk distribution
  const highRiskCount = riskData?.high_risk_patients?.length || 0
  const moderateRiskCount = riskData?.moderate_risk_patients?.length || 0
  const lowRiskCount = riskData?.low_risk_patients?.length || 0
  const totalRiskPatients = highRiskCount + moderateRiskCount + lowRiskCount

  const highRiskPct = totalRiskPatients > 0 ? Math.round((highRiskCount / totalRiskPatients) * 100) : 0
  const moderateRiskPct = totalRiskPatients > 0 ? Math.round((moderateRiskCount / totalRiskPatients) * 100) : 0
  const lowRiskPct = totalRiskPatients > 0 ? Math.round((lowRiskCount / totalRiskPatients) * 100) : 0
  const meanRiskScore = riskData?.mean_risk_score ? Math.round(riskData.mean_risk_score * 100) : 0

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Executive Dashboard</h1>
        <p className="text-gray-500 mt-1">H-34 DELTA Revision Cup Study Overview</p>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Summary</h3>
            <p className="text-gray-600 leading-relaxed">{summary?.narrative || summary?.headline || 'Loading...'}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-5 gap-4">
        <StatCard
          label="Enrollment"
          value={`${Math.round(progress?.enrollment_pct || 0)}%`}
          status={statusToVariant(enrollmentMetric.status)}
          tooltip={enrollmentTooltip}
        />
        <StatCard
          label="Readiness Score"
          value={readinessScore !== null ? `${readinessScore}%` : 'N/A'}
          status={statusToVariant(readinessScoreStatus)}
          tooltip={readinessTooltip}
        />
        <StatCard
          label="Safety Signals"
          value={safetyMetric.value}
          status={statusToVariant(safetyMetric.status)}
          tooltip={safetyTooltip}
        />
        <StatCard
          label="Compliance"
          value={complianceMetric.value}
          status={statusToVariant(complianceMetric.status)}
          tooltip={complianceTooltip}
        />
        <StatCard
          label="Patients"
          value={enrollmentMetric.value}
          status={statusToVariant(enrollmentMetric.status)}
          tooltip={patientsTooltip}
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <CardHeader
            title="Enrollment Progress"
            subtitle={`${progress?.current_enrollment || 0}/${progress?.target_enrollment || 50} patients`}
          />
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium text-gray-800">{Math.round(progress?.enrollment_pct || 0)}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-gray-700 to-gray-900 rounded-full transition-all duration-500"
                style={{ width: `${progress?.enrollment_pct || 0}%` }}
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Risk Distribution"
            subtitle={`${totalRiskPatients} patients assessed`}
          />
          <div className="mt-4 space-y-4">
            {/* Stacked horizontal bar - Apple greyscale */}
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex shadow-inner">
              <div
                className="h-full transition-all duration-500"
                style={{ width: `${highRiskPct}%`, backgroundColor: '#374151' }}
                title={`High Risk: ${highRiskCount}`}
              />
              <div
                className="h-full transition-all duration-500"
                style={{ width: `${moderateRiskPct}%`, backgroundColor: '#9ca3af' }}
                title={`Moderate Risk: ${moderateRiskCount}`}
              />
              <div
                className="h-full transition-all duration-500"
                style={{ width: `${lowRiskPct}%`, backgroundColor: '#e5e7eb' }}
                title={`Low Risk: ${lowRiskCount}`}
              />
            </div>

            {/* Legend with counts - minimal Apple style */}
            <div className="flex justify-between text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: '#374151' }} />
                <span className="text-gray-500">High</span>
                <span className="font-semibold text-gray-900 tabular-nums">{highRiskCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: '#9ca3af' }} />
                <span className="text-gray-500">Moderate</span>
                <span className="font-semibold text-gray-900 tabular-nums">{moderateRiskCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: '#e5e7eb' }} />
                <span className="text-gray-500">Low</span>
                <span className="font-semibold text-gray-900 tabular-nums">{lowRiskCount}</span>
              </div>
            </div>

            {/* Mean risk score - clean divider */}
            <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Mean Score</span>
              <span className="text-lg font-semibold text-gray-900 tabular-nums">{meanRiskScore}%</span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Attention Required"
            action={<Badge variant="danger">{summary?.top_priorities?.length || 0} items</Badge>}
          />
          <div className="space-y-3 mt-2">
            {(summary?.top_priorities || []).slice(0, 3).map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                <AlertTriangle className={`w-5 h-5 flex-shrink-0 ${
                  item.priority === 1 ? 'text-gray-700' :
                  item.priority === 2 ? 'text-gray-500' : 'text-gray-400'
                }`} />
                <div>
                  <p className="font-medium text-gray-800 text-sm">{item.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                </div>
              </div>
            ))}
            {(!summary?.top_priorities || summary.top_priorities.length === 0) && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl text-gray-700">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm">No critical action items</span>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Benchmarking" subtitle="H-34 study data compared against published literature and registry benchmarks" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">
                <span className="inline-flex items-center gap-1">
                  H-34 Study
                  <span className="group relative cursor-help">
                    <HelpCircle className="w-3.5 h-3.5 text-gray-400" />
                    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-64 pointer-events-none z-10 leading-relaxed text-left shadow-lg">
                      Mean values calculated from H-34 DELTA study patient data. Scores and rates include only patients with data at the relevant timepoints.
                    </span>
                  </span>
                </span>
              </th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">
                <span className="inline-flex items-center gap-1">
                  Benchmark
                  <span className="group relative cursor-help">
                    <HelpCircle className="w-3.5 h-3.5 text-gray-400" />
                    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10 shadow-lg">
                      Reference values from published literature
                    </span>
                  </span>
                </span>
              </th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Benchmark Source</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarkRows.map((row, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 group/row">
                <td className="py-3 px-4 text-sm font-medium text-gray-800">
                  <span className="inline-flex items-center gap-1.5">
                    {row.metric}
                    <span className="group relative cursor-help">
                      <HelpCircle className="w-3.5 h-3.5 text-gray-400 opacity-60 group-hover/row:opacity-100 transition-opacity" />
                      <span className="absolute bottom-full left-0 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-64 pointer-events-none z-10 leading-relaxed shadow-lg">
                        {row.tooltip}
                      </span>
                    </span>
                  </span>
                </td>
                <td className="py-3 px-4 text-sm text-center font-semibold text-gray-900">{row.studyValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.benchmarkValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">
                  <span className="group relative cursor-help inline-block">
                    <span className="border-b border-dashed border-gray-300">{row.benchmarkSource}</span>
                    {row.benchmarkSourceTooltip && (
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-72 pointer-events-none z-10 leading-relaxed text-left whitespace-pre-line shadow-lg">
                        {row.benchmarkSourceTooltip}
                      </span>
                    )}
                  </span>
                </td>
                <td className="py-3 px-4 text-center">
                  {row.status === 'success' ? (
                    <CheckCircle className="w-5 h-5 text-gray-600 mx-auto" />
                  ) : row.status === 'warning' ? (
                    <TrendingUp className="w-5 h-5 text-gray-500 mx-auto" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-gray-700 mx-auto" />
                  )}
                </td>
              </tr>
            ))}
            {benchmarkRows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500">
                  No benchmark comparisons available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function formatCitations(citations: LiteratureCitation[] | undefined): string {
  if (!citations || citations.length === 0) return 'Published Literature'
  if (citations.length <= 3) {
    return citations.map(c => c.citation).join('; ')
  }
  return `${citations.slice(0, 2).map(c => c.citation).join('; ')} +${citations.length - 2} more`
}

function buildBenchmarkRows(benchmarks: DashboardBenchmarks | undefined): Array<{
  metric: string
  metricKey: string
  tooltip: string
  studyValue: string
  benchmarkValue: string
  benchmarkSource: string
  benchmarkSourceTooltip: string
  status: 'success' | 'warning' | 'danger'
}> {
  if (!benchmarks?.comparisons) return []

  const citations = benchmarks.literature_citations
  const citationDisplay = formatCitations(citations)
  const citationTooltip = citations?.length 
    ? citations.map(c => `${c.citation}: ${c.title}`).join('\n')
    : 'Aggregated from published literature'

  return benchmarks.comparisons
    .filter(c => c.study_value !== undefined && c.study_value !== null)
    .map(c => {
      const metricInfo = METRIC_INFO[c.metric]
      const metricName = metricInfo?.displayName || c.metric
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
        .replace(/Hhs/g, 'HHS')
        .replace(/Ohs/g, 'OHS')
        .replace(/Mcid/g, 'MCID')

      const tooltip = metricInfo?.tooltip || `${metricName} comparison between H-34 study data and published literature benchmarks.`

      const metricLower = c.metric.toLowerCase()
      const isRateOrSurvival = metricLower.includes('rate') || metricLower.includes('survival') || metricLower.includes('achievement')
      const isImprovement = metricLower.includes('improvement')

      let studyValue: string
      if (isRateOrSurvival) {
        studyValue = `${((c.study_value || 0) * 100).toFixed(1)}%`
      } else if (isImprovement) {
        studyValue = c.study_value && c.study_value > 0 ? `+${c.study_value.toFixed(1)}` : `${c.study_value?.toFixed(1)}`
      } else {
        studyValue = c.study_value?.toFixed(1) || 'N/A'
      }

      let benchmarkValue: string
      if (c.benchmark_value !== undefined && c.benchmark_value !== null) {
        if (isRateOrSurvival) {
          benchmarkValue = `${((c.benchmark_value || 0) * 100).toFixed(1)}%`
        } else if (isImprovement) {
          benchmarkValue = c.benchmark_value > 0 ? `+${c.benchmark_value.toFixed(1)}` : c.benchmark_value.toFixed(1)
        } else {
          benchmarkValue = c.benchmark_value.toFixed(1)
        }
        if (c.benchmark_range && c.benchmark_range.length === 2) {
          const [min, max] = c.benchmark_range
          if (isRateOrSurvival) {
            benchmarkValue += ` (${(min * 100).toFixed(0)}-${(max * 100).toFixed(0)}%)`
          } else {
            benchmarkValue += ` (${min.toFixed(0)}-${max.toFixed(0)})`
          }
        }
      } else {
        benchmarkValue = 'N/A'
      }

      const benchmarkSource = c.source === 'Literature Aggregate' 
        ? citationDisplay 
        : c.source || 'Literature'

      return {
        metric: metricName,
        metricKey: c.metric,
        tooltip,
        studyValue,
        benchmarkValue,
        benchmarkSource,
        benchmarkSourceTooltip: c.source === 'Literature Aggregate' ? citationTooltip : c.source || '',
        status: getComparisonStatus(c.comparison_status),
      }
    })
}
