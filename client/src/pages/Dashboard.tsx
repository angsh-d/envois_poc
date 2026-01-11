import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, StatCard } from '@/components/Card'
import { Badge } from '@/components/Badge'
import { fetchDashboard } from '@/lib/api'
import { useRoute } from 'wouter'
import { Sparkles, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'

const mockData = {
  summary: "Study progressing well. Readiness at 72% with 2 blockers to address. Fracture signal monitored but explained by population characteristics. 4 high-risk patients flagged for enhanced surveillance.",
  kpis: {
    readiness: { value: '72%', status: 'warning' as const },
    safety: { value: '1 signal', status: 'warning' as const },
    compliance: { value: '96%', status: 'success' as const },
    atRisk: { value: '4 patients', status: 'danger' as const },
  },
  enrollment: { current: 37, target: 50, percentage: 74 },
  benchmarks: [
    { metric: 'HHS Improvement', h34: '+34.9', literature: '+28-45', registry: '+32', status: 'success' },
    { metric: 'MCID Achievement', h34: '62%', literature: '60-80%', registry: '68%', status: 'success' },
    { metric: 'Revision Rate', h34: '8.1%', literature: '5-8%', registry: '6.2%', status: 'warning' },
    { metric: '2yr Survival', h34: '92%', literature: '90-96%', registry: '94%', status: 'success' },
  ],
  attentionItems: [
    { title: 'Sample size gap', description: '8/25 evaluable patients for interim analysis', severity: 'critical' },
    { title: '3 patients missing 1-year imaging', description: 'Radiographic data incomplete', severity: 'high' },
    { title: 'Fracture rate monitoring', description: '13% rate explained by osteoporosis prevalence', severity: 'medium' },
  ],
}

export default function Dashboard() {
  const [, params] = useRoute('/study/:studyId')
  const studyId = params?.studyId || 'h34-delta'

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', studyId],
    queryFn: () => fetchDashboard(studyId),
    retry: false,
  })

  const dashboard = data || mockData

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

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
            <p className="text-gray-600 leading-relaxed">{dashboard.summary}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Readiness" value={dashboard.kpis.readiness.value} status={dashboard.kpis.readiness.status} />
        <StatCard label="Safety Signals" value={dashboard.kpis.safety.value} status={dashboard.kpis.safety.status} />
        <StatCard label="Compliance" value={dashboard.kpis.compliance.value} status={dashboard.kpis.compliance.status} />
        <StatCard label="At-Risk Patients" value={dashboard.kpis.atRisk.value} status={dashboard.kpis.atRisk.status} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Enrollment Progress" subtitle={`${dashboard.enrollment.current}/${dashboard.enrollment.target} patients`} />
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium text-gray-800">{dashboard.enrollment.percentage}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-gray-700 to-gray-900 rounded-full transition-all duration-500"
                style={{ width: `${dashboard.enrollment.percentage}%` }}
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader 
            title="Attention Required" 
            action={<Badge variant="danger">{dashboard.attentionItems.length} items</Badge>}
          />
          <div className="space-y-3 mt-2">
            {dashboard.attentionItems.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                <AlertTriangle className={`w-5 h-5 flex-shrink-0 ${
                  item.severity === 'critical' ? 'text-red-500' :
                  item.severity === 'high' ? 'text-amber-500' : 'text-gray-400'
                }`} />
                <div>
                  <p className="font-medium text-gray-800 text-sm">{item.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                </div>
              </div>
            ))}
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
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Literature</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Registry</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.benchmarks.map((row, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0">
                <td className="py-3 px-4 text-sm font-medium text-gray-800">{row.metric}</td>
                <td className="py-3 px-4 text-sm text-center font-semibold text-gray-900">{row.h34}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.literature}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.registry}</td>
                <td className="py-3 px-4 text-center">
                  {row.status === 'success' ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                  ) : row.status === 'warning' ? (
                    <TrendingUp className="w-5 h-5 text-amber-500 mx-auto" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-500 mx-auto" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
