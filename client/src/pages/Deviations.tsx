import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchDeviations } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, FileWarning, Calendar, TrendingUp } from 'lucide-react'

const mockData = {
  summary: "6 protocol deviations detected across 148 visit-assessments (4.1% rate). 3 minor timing deviations, 2 major window violations, and 1 critical deviation affecting primary endpoint evaluability. Most common cause: 6-month visit scheduling delays.",
  stats: {
    total: 148,
    compliant: 142,
    deviations: 6,
    rate: '4.1%',
  },
  deviations: [
    { patient: '015', visit: '6-Month', expected: 'Mar 15, 2025', actual: 'Apr 22, 2025', delta: '+38 days', class: 'minor', impact: 'None', rule: 'Window: Day 180 ± 30' },
    { patient: '023', visit: '2-Year', expected: 'Sep 10, 2025', actual: 'Missing', delta: '-', class: 'critical', impact: 'Primary endpoint', rule: 'Day 730 ± 60' },
    { patient: '031', visit: '1-Year', expected: 'Jun 15, 2025', actual: 'Aug 20, 2025', delta: '+66 days', class: 'major', impact: 'Imaging delay', rule: 'Window: Day 365 ± 60' },
    { patient: '008', visit: '6-Month', expected: 'Feb 28, 2025', actual: 'Mar 25, 2025', delta: '+25 days', class: 'minor', impact: 'None', rule: 'Window: Day 180 ± 30' },
    { patient: '019', visit: '6-Month', expected: 'Apr 10, 2025', actual: 'May 15, 2025', delta: '+35 days', class: 'minor', impact: 'None', rule: 'Window: Day 180 ± 30' },
    { patient: '027', visit: '1-Year', expected: 'Aug 01, 2025', actual: 'Oct 05, 2025', delta: '+65 days', class: 'major', impact: 'Imaging delay', rule: 'Window: Day 365 ± 60' },
  ],
  breakdown: {
    minor: 3,
    major: 2,
    critical: 1,
  },
  trendData: [
    { month: 'Aug 2025', count: 0 },
    { month: 'Sep 2025', count: 1 },
    { month: 'Oct 2025', count: 2 },
    { month: 'Nov 2025', count: 1 },
    { month: 'Dec 2025', count: 1 },
    { month: 'Jan 2026', count: 1 },
  ],
}

export default function Deviations() {
  const [, params] = useRoute('/study/:studyId/deviations')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading } = useQuery({
    queryKey: ['deviations', studyId],
    queryFn: () => fetchDeviations(studyId),
    retry: false,
  })

  const deviations = data || mockData

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  const getClassBadge = (cls: string) => {
    switch (cls) {
      case 'minor': return <Badge variant="neutral">Minor</Badge>
      case 'major': return <Badge variant="warning">Major</Badge>
      case 'critical': return <Badge variant="danger">Critical</Badge>
      default: return <Badge variant="neutral">{cls}</Badge>
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Protocol Deviations</h1>
        <p className="text-gray-500 mt-1">Automated deviation detection using Document-as-Code rules</p>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Summary</h3>
            <p className="text-gray-600 leading-relaxed">{deviations.summary}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-4 gap-4">
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Evaluations</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{deviations.stats.total}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Compliant</p>
          <p className="text-3xl font-semibold text-green-600 mt-2">{deviations.stats.compliant}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Deviations</p>
          <p className="text-3xl font-semibold text-red-600 mt-2">{deviations.stats.deviations}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Rate</p>
          <p className="text-3xl font-semibold text-gray-800 mt-2">{deviations.stats.rate}</p>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span className="font-medium text-gray-800">Minor</span>
            <span className="ml-auto text-2xl font-semibold text-gray-600">{deviations.breakdown.minor}</span>
          </div>
          <p className="text-sm text-gray-500">Within 1.5x window extension</p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="font-medium text-gray-800">Major</span>
            <span className="ml-auto text-2xl font-semibold text-amber-600">{deviations.breakdown.major}</span>
          </div>
          <p className="text-sm text-gray-500">Beyond window or missing assessment</p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="font-medium text-gray-800">Critical</span>
            <span className="ml-auto text-2xl font-semibold text-red-600">{deviations.breakdown.critical}</span>
          </div>
          <p className="text-sm text-gray-500">Affects endpoint evaluability</p>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Deviation Registry"
          action={<Badge variant="neutral">{deviations.deviations.length} total</Badge>}
        />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-3 text-sm font-medium text-gray-500">Patient</th>
              <th className="text-left py-3 px-3 text-sm font-medium text-gray-500">Visit</th>
              <th className="text-left py-3 px-3 text-sm font-medium text-gray-500">Expected</th>
              <th className="text-left py-3 px-3 text-sm font-medium text-gray-500">Actual</th>
              <th className="text-center py-3 px-3 text-sm font-medium text-gray-500">Delta</th>
              <th className="text-center py-3 px-3 text-sm font-medium text-gray-500">Class</th>
              <th className="text-left py-3 px-3 text-sm font-medium text-gray-500">Impact</th>
            </tr>
          </thead>
          <tbody>
            {deviations.deviations.map((dev, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <FileWarning className={`w-4 h-4 ${
                      dev.class === 'critical' ? 'text-red-500' :
                      dev.class === 'major' ? 'text-amber-500' : 'text-gray-400'
                    }`} />
                    <span className="font-mono text-sm font-medium text-gray-800">{dev.patient}</span>
                  </div>
                </td>
                <td className="py-3 px-3 text-sm text-gray-600">{dev.visit}</td>
                <td className="py-3 px-3 text-sm text-gray-500">{dev.expected}</td>
                <td className="py-3 px-3 text-sm text-gray-800">{dev.actual}</td>
                <td className="py-3 px-3 text-center text-sm font-medium text-gray-600">{dev.delta}</td>
                <td className="py-3 px-3 text-center">{getClassBadge(dev.class)}</td>
                <td className="py-3 px-3 text-sm text-gray-500">{dev.impact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card>
        <CardHeader title="Deviation Trend" subtitle="Monthly deviation count over study period" />
        <div className="mt-6 flex items-end gap-4 h-32">
          {deviations.trendData.map((point, i) => (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-gray-200 rounded-t transition-all duration-500 hover:bg-gray-300"
                style={{ height: `${(point.count / 3) * 100}%`, minHeight: point.count > 0 ? '8px' : '0' }}
              />
              <p className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-top-left translate-y-2">{point.month}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
