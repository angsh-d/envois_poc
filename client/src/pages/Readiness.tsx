import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchReadiness } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'

const mockData = {
  score: 72,
  summary: "2 critical blockers: sample size gap (8 evaluable vs 25 required) and 3 patients missing 1-year imaging. MCID at 62% is within literature range (60-80%). SAE documentation is complete.",
  categories: [
    { name: 'Primary Endpoint', status: 'watch', detail: '5/8 MCID achieved, need n=25', source: 'Protocol 6.1, Study Data' },
    { name: 'Safety Documentation', status: 'pass', detail: 'All SAE narratives complete (12/12)', source: 'Protocol 9.1, AE Sheet' },
    { name: 'Radiographic Data', status: 'gap', detail: '3 patients missing 1-year imaging', source: 'Protocol 7.2, Radiology' },
    { name: 'Sample Size', status: 'blocker', detail: '8/25 evaluable for interim', source: 'Protocol 5.1, Patient List' },
    { name: 'Visit Compliance', status: 'pass', detail: '96% within protocol windows', source: 'Protocol 6.2, Follow-up' },
    { name: 'AE Reporting', status: 'pass', detail: 'All AEs documented within 24hrs', source: 'Protocol 9.2, AE Sheet' },
  ],
  blockers: [
    { title: 'Sample size insufficient', description: 'Only 8 patients evaluable at 2-year endpoint vs 25 required for interim analysis', action: 'Wait for additional patient follow-up maturity' },
    { title: 'Missing radiographic data', description: '3 patients (015, 023, 031) missing 1-year imaging', action: 'Issue site queries to collect imaging' },
  ],
  timeline: {
    current: 'Q1 2026',
    projected: 'Q3 2026',
    milestones: [
      { date: 'Q1 2026', label: 'Current Status', completed: true },
      { date: 'Q2 2026', label: 'n=25 evaluable', completed: false },
      { date: 'Q3 2026', label: 'Interim ready', completed: false },
    ],
  },
}

export default function Readiness() {
  const [, params] = useRoute('/study/:studyId/readiness')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading } = useQuery({
    queryKey: ['readiness', studyId],
    queryFn: () => fetchReadiness(studyId),
    retry: false,
  })

  const readiness = data || mockData

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'watch': return <AlertTriangle className="w-5 h-5 text-amber-500" />
      case 'gap': return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'blocker': return <XCircle className="w-5 h-5 text-red-600" />
      default: return null
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pass': return <Badge variant="success">Pass</Badge>
      case 'watch': return <Badge variant="warning">Watch</Badge>
      case 'gap': return <Badge variant="danger">Gap</Badge>
      case 'blocker': return <Badge variant="danger">Blocker</Badge>
      default: return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Regulatory Readiness</h1>
        <p className="text-gray-500 mt-1">Submission readiness assessment for H-34 DELTA</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-1 flex flex-col items-center justify-center py-8">
          <div className="relative w-40 h-40">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="80" cy="80" r="70" stroke="#e5e7eb" strokeWidth="12" fill="none" />
              <circle
                cx="80" cy="80" r="70"
                stroke={readiness.score >= 80 ? '#22c55e' : readiness.score >= 60 ? '#f59e0b' : '#ef4444'}
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(readiness.score / 100) * 440} 440`}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-semibold text-gray-900">{readiness.score}%</span>
              <span className="text-sm text-gray-500">Readiness</span>
            </div>
          </div>
        </Card>

        <Card className="col-span-2">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">AI Assessment</h3>
              <p className="text-gray-600 leading-relaxed">{readiness.summary}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Category Status" subtitle="Requirement-by-requirement assessment" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Category</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Detail</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Source</th>
            </tr>
          </thead>
          <tbody>
            {readiness.categories.map((cat, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(cat.status)}
                    <span className="font-medium text-gray-800">{cat.name}</span>
                  </div>
                </td>
                <td className="py-4 px-4 text-center">{getStatusBadge(cat.status)}</td>
                <td className="py-4 px-4 text-sm text-gray-600">{cat.detail}</td>
                <td className="py-4 px-4 text-xs text-gray-400">{cat.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {readiness.blockers.length > 0 && (
        <Card className="border-l-4 border-red-500">
          <CardHeader title="Critical Blockers" action={<Badge variant="danger">{readiness.blockers.length}</Badge>} />
          <div className="space-y-4 mt-4">
            {readiness.blockers.map((blocker, i) => (
              <div key={i} className="p-4 bg-red-50 rounded-xl">
                <div className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-800">{blocker.title}</p>
                    <p className="text-sm text-gray-600 mt-1">{blocker.description}</p>
                    <p className="text-sm text-red-600 font-medium mt-2">Action: {blocker.action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Timeline Projection" subtitle={`Current: ${readiness.timeline.current} → Projected: ${readiness.timeline.projected}`} />
        <div className="mt-6 flex items-center">
          {readiness.timeline.milestones.map((milestone, i) => (
            <div key={i} className="flex-1 flex flex-col items-center relative">
              <div className={`w-4 h-4 rounded-full z-10 ${milestone.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
              {i < readiness.timeline.milestones.length - 1 && (
                <div className="absolute top-2 left-1/2 w-full h-0.5 bg-gray-200" />
              )}
              <p className="text-sm font-medium text-gray-800 mt-2">{milestone.date}</p>
              <p className="text-xs text-gray-500">{milestone.label}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
