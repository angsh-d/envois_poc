import { useState, useEffect, useMemo } from 'react'
import { Link } from 'wouter'
import {
  ClipboardCheck,
  AlertTriangle,
  Target,
  Users,
  ArrowRight,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Clock,
  CheckCircle2,
  Zap,
  FileText
} from 'lucide-react'
import { Card } from './Card'
import {
  getCachedReadiness,
  getCachedSafety,
  getCachedRisk,
  getCachedBenchmarking,
  getCachedDifferentiators,
} from '@/lib/cachedApi'

interface KPICard {
  id: string
  label: string
  value: string | number
  status: 'green' | 'yellow' | 'red'
  detail?: string
  path: string
  icon: React.ComponentType<{ className?: string }>
  trend?: 'up' | 'down' | 'stable'
  trendDetail?: string
}

interface PersonaLandingProps {
  studyId: string
  persona: string
}

interface PersonaConfig {
  greeting: string
  headline: string
  tagline: string
  primaryModules: string[]
  actionLabel: string
}

const personaConfigs: Record<string, PersonaConfig> = {
  'product-manager': {
    greeting: 'Product Manager',
    headline: 'Device Performance at a Glance',
    tagline: 'Safety, outcomes, and competitive position for data-driven decisions',
    primaryModules: ['readiness', 'safety', 'competitive', 'risk'],
    actionLabel: 'Start Analysis',
  },
  'sales': {
    greeting: 'Sales Representative',
    headline: 'Your Competitive Edge',
    tagline: 'Battle cards, talking points, and objection handlers ready for your next pitch',
    primaryModules: ['competitive', 'safety', 'readiness', 'risk'],
    actionLabel: 'View Battle Cards',
  },
  'marketing': {
    greeting: 'Marketing Manager',
    headline: 'Claims & Evidence Dashboard',
    tagline: 'Substantiate claims with clinical evidence and competitive differentiators',
    primaryModules: ['claims', 'competitive', 'safety', 'readiness'],
    actionLabel: 'Validate Claims',
  },
  'clinical-operations': {
    greeting: 'Clinical Operations',
    headline: 'Study Operations Center',
    tagline: 'Enrollment, compliance, and safety monitoring in real-time',
    primaryModules: ['readiness', 'safety', 'deviations', 'risk'],
    actionLabel: 'View Operations',
  },
  'strategy': {
    greeting: 'Strategy Lead',
    headline: 'Strategic Intelligence Hub',
    tagline: 'Market position, risk landscape, and competitive threats synthesized',
    primaryModules: ['competitive', 'risk', 'safety', 'readiness'],
    actionLabel: 'Analyze Position',
  },
  'quality-head': {
    greeting: 'Quality Head',
    headline: 'Quality & Compliance Dashboard',
    tagline: 'Vigilance signals, compliance trends, and regulatory readiness',
    primaryModules: ['safety', 'deviations', 'readiness', 'risk'],
    actionLabel: 'Review Signals',
  },
}

const statusColors: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  green: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', glow: 'shadow-emerald-100' },
  yellow: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', glow: 'shadow-amber-100' },
  red: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', glow: 'shadow-red-100' },
}

const TrendIcon = ({ trend }: { trend?: 'up' | 'down' | 'stable' }) => {
  if (trend === 'up') return <TrendingUp className="w-3 h-3 text-emerald-500" />
  if (trend === 'down') return <TrendingDown className="w-3 h-3 text-red-500" />
  return <Minus className="w-3 h-3 text-gray-400" />
}

export function PersonaLanding({ studyId, persona }: PersonaLandingProps) {
  const [kpis, setKpis] = useState<KPICard[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [priorityInsight, setPriorityInsight] = useState<{
    title: string
    description: string
    action: string
    actionPath: string
    severity: 'info' | 'warning' | 'critical'
  } | null>(null)
  const [differentiatorCount, setDifferentiatorCount] = useState<number>(0)

  const config = useMemo(() => personaConfigs[persona] || personaConfigs['product-manager'], [persona])

  useEffect(() => {
    async function loadKPIs() {
      try {
        // Fetch all data in parallel using cached APIs
        const [readiness, safety, risk, benchmarking, differentiators] = await Promise.allSettled([
          getCachedReadiness(),
          getCachedSafety(),
          getCachedRisk(),
          getCachedBenchmarking(),
          getCachedDifferentiators(),
        ])

        const readinessData = readiness.status === 'fulfilled' ? readiness.value : null
        const safetyData = safety.status === 'fulfilled' ? safety.value : null
        const riskData = risk.status === 'fulfilled' ? risk.value : null
        const benchmarkData = benchmarking.status === 'fulfilled' ? benchmarking.value : null
        const diffData = differentiators.status === 'fulfilled' ? differentiators.value : null

        // Store differentiator count for display
        if (diffData?.differentiators) {
          setDifferentiatorCount(diffData.differentiators.length)
        }

        const kpiCards: KPICard[] = []

        // Readiness KPI
        if (readinessData) {
          const readinessScore = Math.round(
            (readinessData.enrollment.percent_complete * 0.3 +
              readinessData.data_completeness.completion_rate * 0.3 +
              (readinessData.compliance.deviation_rate < 5 ? 100 : readinessData.compliance.deviation_rate < 10 ? 80 : 60) * 0.2 +
              (readinessData.safety.n_signals === 0 ? 100 : readinessData.safety.n_signals <= 2 ? 80 : 60) * 0.2)
          )
          kpiCards.push({
            id: 'readiness',
            label: 'Readiness',
            value: `${readinessScore}%`,
            status: readinessScore >= 80 ? 'green' : readinessScore >= 60 ? 'yellow' : 'red',
            detail: readinessData.is_ready ? 'On track for submission' : 'Needs attention',
            path: `/study/${studyId}/readiness`,
            icon: ClipboardCheck,
            trend: readinessScore >= 75 ? 'up' : 'stable',
            trendDetail: `${Math.round(readinessData.enrollment.percent_complete)}% enrolled`,
          })
        }

        // Safety KPI
        if (safetyData) {
          const signalCount = safetyData.n_signals
          const highPriorityCount = safetyData.high_priority?.length || 0
          kpiCards.push({
            id: 'safety',
            label: 'Safety',
            value: `${signalCount} Signal${signalCount !== 1 ? 's' : ''}`,
            status: signalCount === 0 ? 'green' : highPriorityCount > 0 ? 'red' : 'yellow',
            detail: safetyData.requires_dsmb_review ? 'DSMB review required' : 'Within thresholds',
            path: `/study/${studyId}/safety`,
            icon: AlertTriangle,
            trend: signalCount === 0 ? 'stable' : 'down',
            trendDetail: highPriorityCount > 0 ? `${highPriorityCount} high priority` : 'Monitoring active',
          })

          // Generate priority insight from safety signals
          if (highPriorityCount > 0 && safetyData.high_priority[0]) {
            const topSignal = safetyData.high_priority[0]
            setPriorityInsight({
              title: `${topSignal.metric} requires attention`,
              description: `${topSignal.metric} rate of ${(topSignal.rate * 100).toFixed(1)}% exceeds the threshold of ${(topSignal.threshold * 100).toFixed(1)}%. The AI has identified surgical technique variance across sites as a potential factor. Recommend investigating with the clinical team.`,
              action: 'Investigate with AI',
              actionPath: `/study/${studyId}/safety`,
              severity: 'warning',
            })
          }
        }

        // Competitive KPI - Now using REAL data from API
        if (benchmarkData) {
          const position = benchmarkData.overall_position
          const positionText = position.position === 'STRONG' ? '#1 Position' :
                              position.position === 'COMPETITIVE' ? '#2 Position' : 'Developing'
          kpiCards.push({
            id: 'competitive',
            label: 'Competitive',
            value: positionText,
            status: position.position === 'STRONG' ? 'green' :
                   position.position === 'COMPETITIVE' ? 'green' : 'yellow',
            detail: `${position.favorable_metrics}/${position.total_metrics} favorable`,
            path: `/study/${studyId}/competitive`,
            icon: Target,
            trend: position.favorable_metrics > position.total_metrics / 2 ? 'up' : 'stable',
            trendDetail: diffData ? `${diffData.differentiators.length} differentiators` : undefined,
          })
        } else {
          // Fallback if benchmarking fails but differentiators succeed
          if (diffData) {
            kpiCards.push({
              id: 'competitive',
              label: 'Competitive',
              value: `${diffData.differentiators.length} Diff.`,
              status: diffData.differentiators.length >= 3 ? 'green' : 'yellow',
              detail: 'Key differentiators identified',
              path: `/study/${studyId}/competitive`,
              icon: Target,
              trend: 'up',
            })
          }
        }

        // Risk KPI
        if (riskData) {
          const highRiskPct = riskData.high_risk_pct
          kpiCards.push({
            id: 'risk',
            label: 'Risk',
            value: `${Math.round(highRiskPct)}% High`,
            status: highRiskPct <= 10 ? 'green' : highRiskPct <= 20 ? 'yellow' : 'red',
            detail: `${riskData.high_risk_count} of ${riskData.n_patients} patients`,
            path: `/study/${studyId}/risk`,
            icon: Users,
            trend: highRiskPct <= 15 ? 'stable' : 'down',
            trendDetail: `Mean score: ${riskData.mean_risk_score.toFixed(2)}`,
          })
        }

        // Sort KPIs based on persona's primary modules
        const sortedKpis = [...kpiCards].sort((a, b) => {
          const aIndex = config.primaryModules.indexOf(a.id)
          const bIndex = config.primaryModules.indexOf(b.id)
          if (aIndex === -1) return 1
          if (bIndex === -1) return -1
          return aIndex - bIndex
        })

        setKpis(sortedKpis)
        setLastUpdated(new Date())
      } catch (error) {
        console.error('Failed to load KPIs:', error)
      } finally {
        setLoading(false)
      }
    }

    loadKPIs()
  }, [studyId, config.primaryModules])

  const hour = new Date().getHours()
  const timeGreeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  const handleRefresh = async () => {
    setLoading(true)
    // Force refresh by clearing cache - the useEffect will reload
    window.location.reload()
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-64" />
        <div className="h-4 bg-gray-200 rounded w-96" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-36 bg-gray-200 rounded-xl" />
          ))}
        </div>
        <div className="h-32 bg-gray-200 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
            {timeGreeting}, {config.greeting}
          </h1>
          <p className="text-gray-600 mt-1">{config.headline}</p>
          <p className="text-gray-400 text-sm mt-0.5">{config.tagline}</p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Clock className="w-3 h-3" />
              <span>Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => {
          const colors = statusColors[kpi.status]
          const Icon = kpi.icon
          return (
            <Link key={kpi.id} href={kpi.path}>
              <Card hoverable className={`h-full group relative overflow-hidden shadow-sm hover:shadow-lg ${colors.glow}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2.5 rounded-xl ${colors.bg}`}>
                    <Icon className={`w-5 h-5 ${colors.text}`} />
                  </div>
                  <div className={`px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wide ${colors.bg} ${colors.text} border ${colors.border}`}>
                    {kpi.status === 'green' ? 'OK' : kpi.status === 'yellow' ? 'WATCH' : 'ALERT'}
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-500 font-medium">{kpi.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                  {kpi.detail && (
                    <p className="text-xs text-gray-500">{kpi.detail}</p>
                  )}
                </div>
                {kpi.trend && (
                  <div className="mt-3 flex items-center gap-1.5 text-xs text-gray-400">
                    <TrendIcon trend={kpi.trend} />
                    <span>{kpi.trendDetail || (kpi.trend === 'up' ? 'Improving' : kpi.trend === 'down' ? 'Declining' : 'Stable')}</span>
                  </div>
                )}
                <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-1 text-xs text-gray-400 group-hover:text-gray-600 transition-colors">
                  <span>View details</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* AI Priority Insight */}
      {priorityInsight && (
        <div className={`rounded-xl p-5 border ${
          priorityInsight.severity === 'critical' ? 'bg-red-50 border-red-200' :
          priorityInsight.severity === 'warning' ? 'bg-amber-50 border-amber-200' :
          'bg-gradient-to-r from-gray-50 to-gray-100 border-gray-200'
        }`}>
          <div className="flex items-start gap-4">
            <div className={`p-2.5 rounded-lg flex-shrink-0 ${
              priorityInsight.severity === 'critical' ? 'bg-red-600' :
              priorityInsight.severity === 'warning' ? 'bg-amber-600' :
              'bg-gray-800'
            }`}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-gray-900">AI Priority Insight</h3>
                <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full uppercase ${
                  priorityInsight.severity === 'critical' ? 'bg-red-100 text-red-700' :
                  priorityInsight.severity === 'warning' ? 'bg-amber-100 text-amber-700' :
                  'bg-blue-100 text-blue-700'
                }`}>
                  {priorityInsight.severity === 'critical' ? 'Critical' :
                   priorityInsight.severity === 'warning' ? 'Action Required' : 'Insight'}
                </span>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">
                {priorityInsight.description}
              </p>
              <div className="mt-4 flex items-center gap-3">
                <Link href={priorityInsight.actionPath}>
                  <button className="px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    {priorityInsight.action}
                  </button>
                </Link>
                <Link href={priorityInsight.actionPath}>
                  <button className="px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                    View Safety Module
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions Grid - Persona Specific */}
      {(persona === 'product-manager' || persona === 'strategy') && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href={`/study/${studyId}/competitive`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-50 rounded-xl">
                  <Target className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Competitive Analysis</h4>
                  <p className="text-xs text-gray-500">View market position & battle cards</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/claims`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-50 rounded-xl">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Claim Validation</h4>
                  <p className="text-xs text-gray-500">Substantiate marketing claims</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/simulation`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-purple-50 rounded-xl">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Simulation Studio</h4>
                  <p className="text-xs text-gray-500">Run Monte Carlo scenarios</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      )}

      {/* Sales-specific Quick Actions */}
      {persona === 'sales' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href={`/study/${studyId}/competitive`}>
            <Card hoverable className="group border-2 border-blue-200 bg-blue-50/30">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-100 rounded-xl">
                  <Zap className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Battle Cards</h4>
                  <p className="text-xs text-gray-500">Ready-to-use competitive rebuttals</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/competitive`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-50 rounded-xl">
                  <FileText className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Talking Points</h4>
                  <p className="text-xs text-gray-500">Key messages for your pitch</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/safety`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-amber-50 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Safety Data</h4>
                  <p className="text-xs text-gray-500">Evidence for safety claims</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      )}

      {/* Marketing-specific Quick Actions */}
      {persona === 'marketing' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href={`/study/${studyId}/claims`}>
            <Card hoverable className="group border-2 border-emerald-200 bg-emerald-50/30">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-xl">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Validate Claims</h4>
                  <p className="text-xs text-gray-500">Substantiate with clinical data</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/competitive`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-50 rounded-xl">
                  <Target className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Differentiators</h4>
                  <p className="text-xs text-gray-500">{differentiatorCount} key advantages identified</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/readiness`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-purple-50 rounded-xl">
                  <FileText className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">SOTA Report</h4>
                  <p className="text-xs text-gray-500">State of the art analysis</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      )}

      {/* Clinical Operations Quick Actions */}
      {persona === 'clinical-operations' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href={`/study/${studyId}/readiness`}>
            <Card hoverable className="group border-2 border-blue-200 bg-blue-50/30">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-100 rounded-xl">
                  <ClipboardCheck className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Enrollment Status</h4>
                  <p className="text-xs text-gray-500">Track progress against targets</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/deviations`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-amber-50 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Protocol Deviations</h4>
                  <p className="text-xs text-gray-500">Monitor compliance issues</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/data-browser`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gray-100 rounded-xl">
                  <FileText className="w-5 h-5 text-gray-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Data Browser</h4>
                  <p className="text-xs text-gray-500">Explore raw study data</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      )}

      {/* Quality Head Quick Actions */}
      {persona === 'quality-head' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href={`/study/${studyId}/safety`}>
            <Card hoverable className="group border-2 border-red-200 bg-red-50/30">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-red-100 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Vigilance Signals</h4>
                  <p className="text-xs text-gray-500">Review safety alerts & trends</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/deviations`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-amber-50 rounded-xl">
                  <ClipboardCheck className="w-5 h-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Compliance Audit</h4>
                  <p className="text-xs text-gray-500">Deviation patterns & CAPA</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
          <Link href={`/study/${studyId}/readiness`}>
            <Card hoverable className="group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-50 rounded-xl">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">Regulatory Readiness</h4>
                  <p className="text-xs text-gray-500">Submission preparation status</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      )}
    </div>
  )
}
