import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, XCircle, AlertTriangle, Clock, FileText, Download, Mail, ArrowRight } from 'lucide-react'
import { Card } from '../components/Card'
import { ProgressBar } from '../components/ProgressBar'
import { Badge } from '../components/Badge'
import { fetchAPI, cn } from '../lib/utils'

interface ReadinessData {
  overall_readiness: number
  categories: Array<{
    name: string
    status: 'pass' | 'gap' | 'watch'
    finding: string
    action: string
  }>
  blockers: string[]
  warnings: string[]
  timeline: Array<{ days: number; readiness: number; milestone: string }>
  provenance: string[]
}

export default function Readiness() {
  const { data } = useQuery({
    queryKey: ['readiness'],
    queryFn: () => fetchAPI<ReadinessData>('/api/v1/uc1/readiness'),
    retry: false,
  })

  const mockData: ReadinessData = {
    overall_readiness: 72,
    categories: [
      { name: 'Primary Endpoint', status: 'pass', finding: '62% MCID (≥50% required)', action: 'None' },
      { name: 'Sample Size', status: 'gap', finding: '8/25 evaluable (32%)', action: 'Chase 17 patients' },
      { name: 'Literature Benchmark', status: 'pass', finding: 'Within published ranges', action: 'None' },
      { name: 'Registry Comparison', status: 'watch', finding: 'Revision rate at 95th %ile', action: 'Add narrative' },
      { name: 'Safety Documentation', status: 'pass', finding: 'All SAEs have narratives', action: 'None' },
      { name: 'Radiographic Data', status: 'gap', finding: '3 patients missing 1yr', action: 'Chase list below' },
      { name: 'Protocol Deviations', status: 'watch', finding: '4 timing deviations', action: 'Document in CSR' },
    ],
    blockers: [
      '17 additional patients need 2-year follow-up',
      'Patients 12, 19, 27 missing 1-year imaging',
    ],
    warnings: [
      'Revision rate narrative: Explain 8.1% vs registry 6.2% (early failure cluster)',
      'Protocol deviations: Document 4 timing deviations in CSR',
    ],
    timeline: [
      { days: 0, readiness: 72, milestone: 'Current' },
      { days: 30, readiness: 78, milestone: 'Chase radiographic' },
      { days: 90, readiness: 85, milestone: 'Additional 2yr FU' },
      { days: 180, readiness: 92, milestone: 'Target n=25' },
    ],
    provenance: [
      'Protocol (CIP v2.0 Sections 8, 10)',
      'Study Data (Sheets 1, 17, 18, 20)',
      'Literature (Meding 2025, Vasios et al)',
      'Registry (AOANJRR 2024)',
    ],
  }

  const displayData = data || mockData

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />
      case 'gap':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'watch':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pass':
        return <Badge variant="success">PASS</Badge>
      case 'gap':
        return <Badge variant="danger">GAP</Badge>
      case 'watch':
        return <Badge variant="warning">WATCH</Badge>
      default:
        return null
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="info">UC1</Badge>
            <Badge>Multi-Agent Analysis</Badge>
          </div>
          <h1 className="text-5xl font-semibold text-black tracking-tight mb-3">
            Regulatory Submission Readiness
          </h1>
          <p className="text-xl text-gray-500 font-light max-w-3xl">
            Comprehensive gap analysis across Protocol, Study Data, Literature Benchmarks, and Registry Norms. 
            5 specialized AI agents collaborate to produce actionable remediation checklist.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <Card className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-2">Overall Readiness</p>
              <div className="flex items-baseline gap-4">
                <span className="text-7xl font-bold text-black tracking-tight">{displayData.overall_readiness}%</span>
                <span className="text-xl text-gray-500">Target: 90% for submission</span>
              </div>
            </div>
            <div className="flex-1 max-w-md">
              <ProgressBar 
                value={displayData.overall_readiness} 
                size="lg" 
                showLabel={false}
                color={displayData.overall_readiness >= 90 ? 'success' : displayData.overall_readiness >= 70 ? 'warning' : 'danger'}
              />
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-2">
            <h2 className="text-2xl font-semibold text-black mb-6">Category Status</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Category</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Finding</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Action Required</th>
                  </tr>
                </thead>
                <tbody>
                  {displayData.categories.map((category, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(category.status)}
                          <span className="font-medium text-black">{category.name}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4">{getStatusBadge(category.status)}</td>
                      <td className="py-4 px-4 text-sm text-gray-600">{category.finding}</td>
                      <td className="py-4 px-4 text-sm text-gray-600">{category.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="space-y-6">
            <Card className="border-l-4 border-l-red-500">
              <div className="flex items-center gap-2 mb-4">
                <XCircle className="w-5 h-5 text-red-600" />
                <h3 className="text-lg font-semibold text-black">Blockers</h3>
              </div>
              <p className="text-sm text-gray-500 mb-4">Must resolve before submission</p>
              <ul className="space-y-3">
                {displayData.blockers.map((blocker, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></span>
                    <span className="text-sm text-gray-700">{blocker}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="border-l-4 border-l-yellow-500">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <h3 className="text-lg font-semibold text-black">Warnings</h3>
              </div>
              <p className="text-sm text-gray-500 mb-4">Should address, not blocking</p>
              <ul className="space-y-3">
                {displayData.warnings.map((warning, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></span>
                    <span className="text-sm text-gray-700">{warning}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <div className="flex items-center gap-2 mb-6">
              <Clock className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-black">Projected Timeline</h2>
            </div>
            <div className="space-y-4">
              {displayData.timeline.map((point, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className={cn(
                    'w-12 text-center py-1 rounded-lg text-sm font-medium',
                    point.readiness >= 90 ? 'bg-green-100 text-green-800' :
                    point.readiness >= 80 ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  )}>
                    +{point.days}d
                  </div>
                  <div className="flex-1">
                    <ProgressBar value={point.readiness} size="sm" showLabel={false} />
                  </div>
                  <div className="w-24 text-right">
                    <span className={cn(
                      'font-semibold',
                      point.readiness >= 90 ? 'text-green-600' : 'text-gray-900'
                    )}>
                      {point.readiness}%
                    </span>
                  </div>
                  <div className="w-40 text-sm text-gray-600">{point.milestone}</div>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-800">Submission viable at +180 days</span>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-6">
              <FileText className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-black">Actions</h2>
            </div>
            <div className="space-y-3">
              <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <Download className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-black">Download Checklist PDF</span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400" />
              </button>
              <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-black">Generate Chase List</span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400" />
              </button>
              <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-black">Draft CSR Section</span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400" />
              </button>
              <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-black">Email Report to Team</span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </Card>
        </div>

        <Card>
          <h2 className="text-lg font-semibold text-black mb-4">Provenance</h2>
          <div className="flex flex-wrap gap-2">
            {displayData.provenance.map((source, index) => (
              <Badge key={index} variant="default">{source}</Badge>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
