import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, StatCard } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { DashboardSkeleton } from '@/components/Skeleton'
import {
  fetchDashboardExecutiveSummary,
  fetchDashboardStudyProgress,
  fetchDashboardBenchmarks,
  type DashboardExecutiveSummary,
  type DashboardStudyProgress,
  type DashboardBenchmarks
} from '@/lib/api'
import { useRoute } from 'wouter'
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

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

  const isLoading = summaryLoading || progressLoading || benchmarksLoading

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

  const readinessMetric = metricsMap['Regulatory Readiness'] || { value: 'N/A', status: 'YELLOW' }
  const safetyMetric = metricsMap['Safety Signals'] || { value: 'N/A', status: 'GREEN' }
  const complianceMetric = metricsMap['Protocol Compliance'] || { value: 'N/A', status: 'GREEN' }
  const enrollmentMetric = metricsMap['Enrollment'] || { value: 'N/A', status: 'YELLOW' }

  const benchmarkRows = buildBenchmarkRows(benchmarks)

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

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Readiness"
          value={readinessMetric.value}
          status={statusToVariant(readinessMetric.status)}
        />
        <StatCard
          label="Safety Signals"
          value={safetyMetric.value}
          status={statusToVariant(safetyMetric.status)}
        />
        <StatCard
          label="Compliance"
          value={complianceMetric.value}
          status={statusToVariant(complianceMetric.status)}
        />
        <StatCard
          label="Enrollment"
          value={enrollmentMetric.value}
          status={statusToVariant(enrollmentMetric.status)}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
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
        <CardHeader title="Benchmarking" subtitle="H-34 performance vs literature and registry data" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">H-34</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Benchmark</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Source</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarkRows.map((row, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0">
                <td className="py-3 px-4 text-sm font-medium text-gray-800">{row.metric}</td>
                <td className="py-3 px-4 text-sm text-center font-semibold text-gray-900">{row.studyValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.benchmarkValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.source}</td>
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

function buildBenchmarkRows(benchmarks: DashboardBenchmarks | undefined): Array<{
  metric: string
  studyValue: string
  benchmarkValue: string
  source: string
  status: 'success' | 'warning' | 'danger'
}> {
  if (!benchmarks?.comparisons) return []

  return benchmarks.comparisons
    .filter(c => c.study_value !== undefined && c.study_value !== null)
    .slice(0, 6)
    .map(c => {
      let metricName = c.metric
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())

      let studyValue: string
      if (c.metric.includes('rate') || c.metric.includes('survival') || c.metric.includes('achievement')) {
        studyValue = `${((c.study_value || 0) * 100).toFixed(1)}%`
      } else if (c.metric.includes('improvement')) {
        studyValue = c.study_value && c.study_value > 0 ? `+${c.study_value.toFixed(1)}` : `${c.study_value?.toFixed(1)}`
      } else {
        studyValue = c.study_value?.toFixed(1) || 'N/A'
      }

      let benchmarkValue: string
      if (c.benchmark_value !== undefined && c.benchmark_value !== null) {
        if (c.metric.includes('rate') || c.metric.includes('survival')) {
          benchmarkValue = `${((c.benchmark_value || 0) * 100).toFixed(1)}%`
        } else if (c.metric.includes('improvement')) {
          benchmarkValue = c.benchmark_value > 0 ? `+${c.benchmark_value.toFixed(1)}` : c.benchmark_value.toFixed(1)
        } else {
          benchmarkValue = c.benchmark_value.toFixed(1)
        }
        if (c.benchmark_range && c.benchmark_range.length === 2) {
          const [min, max] = c.benchmark_range
          if (c.metric.includes('rate') || c.metric.includes('survival')) {
            benchmarkValue += ` (${(min * 100).toFixed(0)}-${(max * 100).toFixed(0)}%)`
          } else {
            benchmarkValue += ` (${min.toFixed(0)}-${max.toFixed(0)})`
          }
        }
      } else {
        benchmarkValue = 'N/A'
      }

      return {
        metric: metricName,
        studyValue,
        benchmarkValue,
        source: c.source || 'Unknown',
        status: getComparisonStatus(c.comparison_status),
      }
    })
}
