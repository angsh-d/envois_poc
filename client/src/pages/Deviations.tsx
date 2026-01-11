import { AlertTriangle, Clock, User, FileText, CheckCircle2, XCircle } from 'lucide-react'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { cn } from '../lib/utils'

interface Deviation {
  id: string
  patientId: string
  type: string
  severity: 'major' | 'minor'
  category: string
  description: string
  detectedDate: string
  protocolRef: string
  status: 'open' | 'documented' | 'resolved'
}

export default function Deviations() {
  const deviations: Deviation[] = [
    {
      id: 'DEV-001',
      patientId: 'H34-012',
      type: 'Timing',
      severity: 'minor',
      category: 'Visit Window',
      description: '12-month visit completed 45 days outside protocol window (+30/-14 days)',
      detectedDate: '2025-11-15',
      protocolRef: 'CIP v2.0 Section 6.3',
      status: 'open',
    },
    {
      id: 'DEV-002',
      patientId: 'H34-019',
      type: 'Timing',
      severity: 'minor',
      category: 'Visit Window',
      description: '6-month HHS assessment delayed by 21 days',
      detectedDate: '2025-10-22',
      protocolRef: 'CIP v2.0 Section 6.3',
      status: 'documented',
    },
    {
      id: 'DEV-003',
      patientId: 'H34-027',
      type: 'Missing Data',
      severity: 'major',
      category: 'Radiographic',
      description: '12-month X-ray not obtained; patient refused imaging',
      detectedDate: '2025-09-30',
      protocolRef: 'CIP v2.0 Section 7.2',
      status: 'open',
    },
    {
      id: 'DEV-004',
      patientId: 'H34-008',
      type: 'Timing',
      severity: 'minor',
      category: 'Visit Window',
      description: '24-month visit scheduled 18 days early',
      detectedDate: '2025-12-01',
      protocolRef: 'CIP v2.0 Section 6.3',
      status: 'open',
    },
  ]

  const stats = {
    total: deviations.length,
    major: deviations.filter(d => d.severity === 'major').length,
    minor: deviations.filter(d => d.severity === 'minor').length,
    open: deviations.filter(d => d.status === 'open').length,
    documented: deviations.filter(d => d.status === 'documented').length,
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <Badge variant="danger">Open</Badge>
      case 'documented':
        return <Badge variant="warning">Documented</Badge>
      case 'resolved':
        return <Badge variant="success">Resolved</Badge>
      default:
        return null
    }
  }

  const getSeverityBadge = (severity: string) => {
    return severity === 'major' 
      ? <Badge variant="danger">Major</Badge>
      : <Badge variant="warning">Minor</Badge>
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="info">UC3</Badge>
            <Badge>Document-as-Code</Badge>
          </div>
          <h1 className="text-5xl font-semibold text-black tracking-tight mb-3">
            Protocol Deviation Detection
          </h1>
          <p className="text-xl text-gray-500 font-light max-w-3xl">
            Automated detection of protocol deviations using Document-as-Code execution. 
            Every patient, every visit validated against protocol_rules.yaml in real-time.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Total Deviations</p>
            <p className="text-4xl font-bold text-black">{stats.total}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Major</p>
            <p className="text-4xl font-bold text-red-600">{stats.major}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Minor</p>
            <p className="text-4xl font-bold text-yellow-600">{stats.minor}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Open</p>
            <p className="text-4xl font-bold text-red-600">{stats.open}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Documented</p>
            <p className="text-4xl font-bold text-yellow-600">{stats.documented}</p>
          </Card>
        </div>

        <Card className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-black">Detected Deviations</h2>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm">Export Report</Button>
              <Button variant="primary" size="sm">Generate CSR Section</Button>
            </div>
          </div>

          <div className="space-y-4">
            {deviations.map((deviation) => (
              <div
                key={deviation.id}
                className={cn(
                  'p-6 rounded-xl border-2',
                  deviation.severity === 'major' 
                    ? 'border-red-200 bg-red-50' 
                    : 'border-yellow-200 bg-yellow-50'
                )}
              >
                <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      deviation.severity === 'major' ? 'bg-red-100' : 'bg-yellow-100'
                    )}>
                      <AlertTriangle className={cn(
                        'w-5 h-5',
                        deviation.severity === 'major' ? 'text-red-600' : 'text-yellow-600'
                      )} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-black">{deviation.id}</span>
                        {getSeverityBadge(deviation.severity)}
                        {getStatusBadge(deviation.status)}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{deviation.type} - {deviation.category}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      <span>{deviation.patientId}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>{deviation.detectedDate}</span>
                    </div>
                  </div>
                </div>

                <p className="text-gray-700 mb-4">{deviation.description}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <FileText className="w-4 h-4" />
                    <span>{deviation.protocolRef}</span>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm">View Details</Button>
                    {deviation.status === 'open' && (
                      <Button variant="secondary" size="sm">Document</Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-xl font-semibold text-black mb-6">How It Works</h2>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-sm">1</span>
                </div>
                <div>
                  <p className="font-medium text-black">Protocol Rules Loaded</p>
                  <p className="text-sm text-gray-600">protocol_rules.yaml defines all timing windows, required assessments, and data requirements</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-sm">2</span>
                </div>
                <div>
                  <p className="font-medium text-black">Patient Data Scanned</p>
                  <p className="text-sm text-gray-600">Every visit date, assessment, and data point compared against protocol requirements</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-sm">3</span>
                </div>
                <div>
                  <p className="font-medium text-black">Deviations Classified</p>
                  <p className="text-sm text-gray-600">Major vs minor classification based on protocol-defined severity thresholds</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-sm">4</span>
                </div>
                <div>
                  <p className="font-medium text-black">Actions Generated</p>
                  <p className="text-sm text-gray-600">Specific remediation steps and CSR documentation guidance provided</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold text-black mb-6">Protocol Rules Active</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm">Visit Window: +30/-14 days</span>
                </div>
                <Badge size="sm">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm">HHS Assessment: All timepoints</span>
                </div>
                <Badge size="sm">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm">Radiographic: 6mo, 12mo, 24mo</span>
                </div>
                <Badge size="sm">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm">SAE Narrative: Required</span>
                </div>
                <Badge size="sm">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm">Informed Consent: Pre-procedure</span>
                </div>
                <Badge size="sm">Active</Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
