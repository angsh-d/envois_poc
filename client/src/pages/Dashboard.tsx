import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle, Users, TrendingUp, FileCheck, Clock, CheckCircle2 } from 'lucide-react'
import { Card, StatCard } from '../components/Card'
import { ProgressBar } from '../components/ProgressBar'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { fetchAPI } from '../lib/utils'
import { Link } from 'wouter'

interface HealthResponse {
  status: string
  study_name: string
  version: string
}

export default function Dashboard() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetchAPI<HealthResponse>('/health'),
  })

  const studyMetrics = {
    enrolled: 37,
    target: 50,
    evaluable: 8,
    readiness: 72,
    safetySignals: 2,
    deviations: 4,
    atRisk: 7,
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="success">Active Study</Badge>
            {isLoading ? (
              <Badge>Loading...</Badge>
            ) : (
              <Badge variant="info">{health?.version || 'v1.0'}</Badge>
            )}
          </div>
          <h1 className="text-5xl font-semibold text-black tracking-tight mb-3">
            H-34 DELTA Revision Cup
          </h1>
          <p className="text-xl text-gray-500 font-light max-w-2xl">
            Clinical Intelligence Dashboard powered by Multi-Agent AI. Real-time regulatory readiness, 
            safety monitoring, and patient risk stratification.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <StatCard
            title="Enrolled Patients"
            value={studyMetrics.enrolled}
            subtitle={`of ${studyMetrics.target} target`}
            trend="up"
            trendValue="+3 this month"
            icon={<Users className="w-6 h-6 text-gray-600" />}
          />
          <StatCard
            title="Evaluable at 2yr"
            value={studyMetrics.evaluable}
            subtitle="reached primary endpoint"
            icon={<CheckCircle2 className="w-6 h-6 text-gray-600" />}
          />
          <StatCard
            title="Safety Signals"
            value={studyMetrics.safetySignals}
            subtitle="requiring attention"
            trend="neutral"
            trendValue="Stable"
            icon={<Shield className="w-6 h-6 text-gray-600" />}
          />
          <StatCard
            title="At-Risk Patients"
            value={studyMetrics.atRisk}
            subtitle="enhanced monitoring"
            icon={<AlertTriangle className="w-6 h-6 text-gray-600" />}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-black">Submission Readiness</h2>
                <p className="text-gray-500 mt-1">Gap analysis across 4 data sources</p>
              </div>
              <Link href="/readiness">
                <Button variant="secondary" size="sm">View Details</Button>
              </Link>
            </div>
            
            <div className="mb-8">
              <div className="flex items-end gap-4 mb-4">
                <span className="text-6xl font-bold text-black tracking-tight">{studyMetrics.readiness}%</span>
                <span className="text-gray-500 pb-2">Target: 90% for submission</span>
              </div>
              <ProgressBar 
                value={studyMetrics.readiness} 
                size="lg" 
                showLabel={false}
                color={studyMetrics.readiness >= 90 ? 'success' : studyMetrics.readiness >= 70 ? 'warning' : 'danger'}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 text-red-600 mb-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-medium text-sm">Blockers</span>
                </div>
                <p className="text-sm text-gray-600">17 patients need 2-year follow-up</p>
                <p className="text-sm text-gray-600">3 patients missing radiographic data</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 text-yellow-600 mb-2">
                  <Clock className="w-4 h-4" />
                  <span className="font-medium text-sm">Timeline</span>
                </div>
                <p className="text-sm text-gray-600">+30 days: 78% ready</p>
                <p className="text-sm text-gray-600">+180 days: 92% ready</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-black">Quick Actions</h2>
            </div>
            <div className="space-y-3">
              <Link href="/readiness">
                <button className="w-full flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left">
                  <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                    <FileCheck className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-black">Regulatory Readiness</p>
                    <p className="text-sm text-gray-500">Full gap analysis</p>
                  </div>
                </button>
              </Link>
              <Link href="/safety">
                <button className="w-full flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left">
                  <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                    <Shield className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-black">Safety Signals</p>
                    <p className="text-sm text-gray-500">Cross-source analysis</p>
                  </div>
                </button>
              </Link>
              <Link href="/deviations">
                <button className="w-full flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left">
                  <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-black">Protocol Deviations</p>
                    <p className="text-sm text-gray-500">Automated detection</p>
                  </div>
                </button>
              </Link>
              <Link href="/risk">
                <button className="w-full flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left">
                  <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-black">Patient Risk</p>
                    <p className="text-sm text-gray-500">ML-powered stratification</p>
                  </div>
                </button>
              </Link>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="flex items-center gap-2 mb-6">
              <Shield className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-black">Active Safety Signals</h2>
            </div>
            <div className="space-y-4">
              <div className="p-4 border border-red-200 bg-red-50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="danger">Elevated</Badge>
                  <span className="text-xs text-gray-500">Detected 2 days ago</span>
                </div>
                <p className="font-medium text-black">Periprosthetic Fracture Rate: 13%</p>
                <p className="text-sm text-gray-600 mt-1">
                  Rate exceeds literature benchmark (4-8%). Cross-source analysis indicates correlation 
                  with high osteoporosis prevalence (32%) in cohort.
                </p>
                <div className="flex gap-2 mt-3">
                  <Link href="/safety">
                    <Button variant="ghost" size="sm">View Analysis</Button>
                  </Link>
                </div>
              </div>
              <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="warning">Watch</Badge>
                  <span className="text-xs text-gray-500">Monitoring</span>
                </div>
                <p className="font-medium text-black">Revision Rate: 8.1%</p>
                <p className="text-sm text-gray-600 mt-1">
                  At upper boundary of registry benchmark (6.2%). Early failure cluster identified.
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-black">Outcome Metrics</h2>
            </div>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">MCID Achievement (HHS ≥20pt)</span>
                  <span className="text-sm font-medium">62%</span>
                </div>
                <ProgressBar value={62} size="sm" color="success" showLabel={false} />
                <p className="text-xs text-gray-500 mt-1">Literature benchmark: 72%</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">2-Year Survival</span>
                  <span className="text-sm font-medium">92%</span>
                </div>
                <ProgressBar value={92} size="sm" color="success" showLabel={false} />
                <p className="text-xs text-gray-500 mt-1">Registry benchmark: 94%</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">SAE Documentation</span>
                  <span className="text-sm font-medium">100%</span>
                </div>
                <ProgressBar value={100} size="sm" color="success" showLabel={false} />
                <p className="text-xs text-gray-500 mt-1">12/12 SAEs with narratives</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Visit Completion</span>
                  <span className="text-sm font-medium">85%</span>
                </div>
                <ProgressBar value={85} size="sm" showLabel={false} />
                <p className="text-xs text-gray-500 mt-1">Protocol requirement: 80%</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="mt-10 text-center text-sm text-gray-400">
          <p>Powered by Multi-Agent AI with Document-as-Code Intelligence</p>
          <p className="mt-1">Protocol + Study Data + Literature + Registry — 4 Sources, 1 Intelligence Layer</p>
        </div>
      </div>
    </div>
  )
}
