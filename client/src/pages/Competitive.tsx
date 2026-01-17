import { useState, useEffect } from 'react'
import { Target, Award, Shield, Zap, Download, RefreshCw, ChevronDown, ChevronUp, MessageSquare, TrendingUp, FileText } from 'lucide-react'
import { Card } from '@/components/Card'
import {
  CompetitiveLandscapeResponse,
  BattleCardResponse,
  BenchmarkingResponse,
  Differentiator,
  Rebuttal,
  QuickStat
} from '@/lib/api'
import {
  getCachedCompetitiveLandscape,
  getCachedBenchmarking,
  getCachedBattleCard,
  refreshModuleData
} from '@/lib/cachedApi'

type ViewMode = 'landscape' | 'battlecard' | 'benchmarks'

interface CompetitiveProps {
  studyId?: string
}

const statusColors: Record<string, { bg: string; text: string; border: string }> = {
  STRONG: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  COMPETITIVE: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  DEVELOPING: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
}

export default function Competitive({ studyId }: CompetitiveProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('landscape')
  const [landscapeData, setLandscapeData] = useState<CompetitiveLandscapeResponse | null>(null)
  const [battleCardData, setBattleCardData] = useState<BattleCardResponse | null>(null)
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedDifferentiator, setExpandedDifferentiator] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [viewMode])

  async function loadData(forceRefresh = false) {
    setLoading(true)
    try {
      if (viewMode === 'landscape') {
        const data = await getCachedCompetitiveLandscape(forceRefresh)
        setLandscapeData(data)
      } else if (viewMode === 'battlecard') {
        const data = await getCachedBattleCard(forceRefresh)
        setBattleCardData(data)
      } else if (viewMode === 'benchmarks') {
        const data = await getCachedBenchmarking(forceRefresh)
        setBenchmarkData(data)
      }
    } catch (error) {
      console.error('Failed to load competitive data:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleRefresh() {
    await refreshModuleData('competitive')
    loadData(true)
  }

  const handleExport = () => {
    // Create export content based on current view
    let content = ''
    let filename = ''

    if (viewMode === 'battlecard' && battleCardData) {
      filename = 'battle-card.md'
      content = `# DELTA Revision Cup Battle Card\n\n`
      content += `Generated: ${new Date(battleCardData.generated_at).toLocaleDateString()}\n\n`
      content += `## Quick Stats\n\n`
      battleCardData.quick_stats.forEach((stat: QuickStat) => {
        content += `- **${stat.stat}**: ${stat.value} (${stat.context})\n`
      })
      content += `\n## Key Talking Points\n\n`
      battleCardData.talking_points.forEach((point: string, i: number) => {
        content += `${i + 1}. ${point}\n`
      })
      content += `\n## Objection Handling\n\n`
      battleCardData.rebuttals.forEach((r: Rebuttal) => {
        content += `**Objection:** ${r.objection}\n`
        content += `**Response:** ${r.rebuttal}\n\n`
      })
    } else if (viewMode === 'landscape' && landscapeData) {
      filename = 'competitive-landscape.md'
      content = `# Competitive Landscape Analysis\n\n`
      content += `Generated: ${new Date(landscapeData.generated_at).toLocaleDateString()}\n\n`
      if (landscapeData.competitive_landscape) {
        content += `## Overview\n\n${landscapeData.competitive_landscape}\n\n`
      }
      content += `## Key Differentiators\n\n`
      landscapeData.key_differentiators.forEach((d: Differentiator) => {
        content += `### ${d.category}\n`
        content += `- **Differentiator:** ${d.differentiator}\n`
        content += `- **Evidence:** ${d.evidence}\n\n`
      })
    }

    // Download file
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-4" />
          <div className="h-4 bg-gray-200 rounded w-96 mb-8" />
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded-lg" />
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded-xl" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Competitive Intelligence</h1>
          <p className="text-gray-500 mt-1">Market position, differentiators, and sales enablement</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-lg w-fit">
        <button
          onClick={() => setViewMode('landscape')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${
            viewMode === 'landscape'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Target className="w-4 h-4" />
          Landscape
        </button>
        <button
          onClick={() => setViewMode('battlecard')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${
            viewMode === 'battlecard'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Zap className="w-4 h-4" />
          Battle Card
        </button>
        <button
          onClick={() => setViewMode('benchmarks')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${
            viewMode === 'benchmarks'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Benchmarks
        </button>
      </div>

      {/* Landscape View */}
      {viewMode === 'landscape' && landscapeData && (
        <div className="space-y-6">
          {/* Overall Position */}
          <Card>
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gray-100 rounded-lg">
                <Target className="w-6 h-6 text-gray-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">Market Position</h3>
                <p className="text-gray-600 mt-1 leading-relaxed">
                  {landscapeData.competitive_landscape || 'DELTA Revision Cup demonstrates competitive positioning in the revision hip arthroplasty market with favorable clinical outcomes compared to registry benchmarks.'}
                </p>
                <div className="mt-4 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Confidence:</span>
                    <div className="flex items-center gap-1">
                      <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gray-700 rounded-full"
                          style={{ width: `${landscapeData.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">
                        {Math.round(landscapeData.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Key Differentiators */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Differentiators</h3>
            <div className="space-y-3">
              {landscapeData.key_differentiators.map((diff: Differentiator, i: number) => (
                <Card key={i} className="cursor-pointer" hoverable onClick={() => setExpandedDifferentiator(expandedDifferentiator === i ? null : i)}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-emerald-50 rounded-lg mt-0.5">
                        <Award className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                            {diff.category}
                          </span>
                        </div>
                        <p className="text-gray-900 font-medium mt-1">{diff.differentiator}</p>
                        {expandedDifferentiator === i && (
                          <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                            <span className="font-medium text-gray-700">Evidence: </span>
                            {diff.evidence}
                          </p>
                        )}
                      </div>
                    </div>
                    {expandedDifferentiator === i ? (
                      <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Registry Comparison Matrix */}
          {landscapeData.registry_comparison.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Registry Comparison</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-600">Registry</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">Metric</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Registry Value</th>
                      <th className="text-center py-3 px-4 font-medium text-gray-600">Comparison</th>
                    </tr>
                  </thead>
                  <tbody>
                    {landscapeData.registry_comparison.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100 last:border-0">
                        <td className="py-3 px-4 font-medium text-gray-900">{row.registry as string}</td>
                        <td className="py-3 px-4 text-gray-600">{row.metric as string}</td>
                        <td className="py-3 px-4 text-right text-gray-900">
                          {row.registry_value != null ? `${Number(row.registry_value).toFixed(1)}%` : '-'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            row.comparison === 'favorable' ? 'bg-emerald-50 text-emerald-700' :
                            row.comparison === 'comparable' ? 'bg-blue-50 text-blue-700' :
                            'bg-amber-50 text-amber-700'
                          }`}>
                            {row.comparison as string || 'N/A'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Data Sources */}
          <Card>
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-gray-500" />
              <h4 className="text-sm font-medium text-gray-700">Data Sources</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {landscapeData.sources.map((source, i) => (
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

      {/* Battle Card View */}
      {viewMode === 'battlecard' && battleCardData && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {battleCardData.quick_stats.map((stat: QuickStat, i: number) => (
              <Card key={i}>
                <div className="text-center">
                  <p className="text-sm text-gray-500 mb-1">{stat.stat}</p>
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                  <p className="text-xs text-gray-400 mt-1">{stat.context}</p>
                </div>
              </Card>
            ))}
          </div>

          {/* Battle Card Content */}
          {battleCardData.battle_card_content && (
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">Battle Card Narrative</h3>
              </div>
              <div className="prose prose-sm max-w-none text-gray-600 leading-relaxed whitespace-pre-line">
                {battleCardData.battle_card_content}
              </div>
            </Card>
          )}

          {/* Talking Points */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Key Talking Points</h3>
            </div>
            <div className="space-y-3">
              {battleCardData.talking_points.map((point: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="flex-shrink-0 w-6 h-6 bg-gray-800 text-white rounded-full flex items-center justify-center text-xs font-medium">
                    {i + 1}
                  </span>
                  <p className="text-gray-700 leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Objection Handling */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Objection Handling</h3>
            </div>
            <div className="space-y-4">
              {battleCardData.rebuttals.map((rebuttal: Rebuttal, i: number) => (
                <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="p-3 bg-red-50 border-b border-gray-200">
                    <p className="text-sm font-medium text-red-800">
                      <span className="text-red-600">Objection:</span> {rebuttal.objection}
                    </p>
                  </div>
                  <div className="p-3 bg-emerald-50">
                    <p className="text-sm text-emerald-800">
                      <span className="font-medium text-emerald-700">Response:</span> {rebuttal.rebuttal}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Benchmarks View */}
      {viewMode === 'benchmarks' && benchmarkData && (
        <div className="space-y-6">
          {/* Overall Position */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${statusColors[benchmarkData.overall_position.position].bg}`}>
                  <TrendingUp className={`w-6 h-6 ${statusColors[benchmarkData.overall_position.position].text}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900">Overall Position</h3>
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusColors[benchmarkData.overall_position.position].bg} ${statusColors[benchmarkData.overall_position.position].text} ${statusColors[benchmarkData.overall_position.position].border} border`}>
                      {benchmarkData.overall_position.position}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">{benchmarkData.overall_position.description}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-3xl font-semibold text-gray-900">
                  {benchmarkData.overall_position.favorable_metrics}/{benchmarkData.overall_position.total_metrics}
                </p>
                <p className="text-sm text-gray-500">favorable metrics</p>
              </div>
            </div>
          </Card>

          {/* Registry Benchmarks */}
          {benchmarkData.registry_benchmarks && Object.keys(benchmarkData.registry_benchmarks).length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Registry Benchmarks</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(benchmarkData.registry_benchmarks).map(([registry, metrics]) => (
                  <div key={registry} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <h4 className="font-medium text-gray-900 mb-3">{registry}</h4>
                    <div className="space-y-2 text-sm">
                      {typeof metrics === 'object' && metrics !== null && Object.entries(metrics as Record<string, unknown>).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-600">{key}</span>
                          <span className="font-medium text-gray-900">
                            {typeof value === 'number' ? `${value.toFixed(1)}%` : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Literature Comparison */}
          {benchmarkData.literature_comparison.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Literature Comparison</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-600">Source</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">Metric</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Published Value</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">H-34 Value</th>
                      <th className="text-center py-3 px-4 font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarkData.literature_comparison.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100 last:border-0">
                        <td className="py-3 px-4 font-medium text-gray-900">{row.source as string}</td>
                        <td className="py-3 px-4 text-gray-600">{row.metric as string}</td>
                        <td className="py-3 px-4 text-right text-gray-900">{row.published_value as string}</td>
                        <td className="py-3 px-4 text-right text-gray-900">{row.study_value as string}</td>
                        <td className="py-3 px-4 text-center">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            row.status === 'favorable' ? 'bg-emerald-50 text-emerald-700' :
                            row.status === 'comparable' ? 'bg-blue-50 text-blue-700' :
                            'bg-amber-50 text-amber-700'
                          }`}>
                            {row.status as string}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Confidence */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>Analysis Confidence:</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gray-700 rounded-full"
                  style={{ width: `${benchmarkData.confidence * 100}%` }}
                />
              </div>
              <span className="font-medium text-gray-700">{Math.round(benchmarkData.confidence * 100)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
