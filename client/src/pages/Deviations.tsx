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
      description: '12-month visit completed 45 days outside protocol window',
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
  }

  return (
    <div className="min-h-screen">
      <section className="pt-24 pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto text-center">
          <div className="animate-fade-in-up opacity-0">
            <Badge variant="info" size="sm">UC3 · Document-as-Code</Badge>
          </div>
          <h1 className="text-display-lg mt-4 animate-fade-in-up opacity-0 stagger-1">
            Protocol Deviations
          </h1>
          <p className="text-body-lg text-neutral-500 mt-4 max-w-[700px] mx-auto animate-fade-in-up opacity-0 stagger-2">
            Automated detection using Document-as-Code execution. 
            Every patient, every visit validated against protocol rules in real-time.
          </p>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[980px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 animate-fade-in-up opacity-0 stagger-3">
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Total</p>
              <p className="text-display-md mt-1">{stats.total}</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Major</p>
              <p className="text-display-md mt-1 text-[#ff3b30]">{stats.major}</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Minor</p>
              <p className="text-display-md mt-1 text-[#ff9500]">{stats.minor}</p>
            </Card>
            <Card className="p-6 text-center" hover>
              <p className="text-caption text-neutral-500 uppercase tracking-wider">Open</p>
              <p className="text-display-md mt-1 text-[#ff3b30]">{stats.open}</p>
            </Card>
          </div>
        </div>
      </section>

      <section className="pb-16 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <Card variant="elevated" className="overflow-hidden">
            <div className="p-6 border-b border-neutral-100 flex items-center justify-between">
              <p className="text-headline text-neutral-900">Detected Deviations</p>
              <div className="flex gap-3">
                <Button variant="secondary" size="sm">Export</Button>
                <Button variant="primary" size="sm">Generate CSR</Button>
              </div>
            </div>
            <div className="divide-y divide-neutral-100">
              {deviations.map((d) => (
                <div key={d.id} className={cn(
                  'p-6 hover:bg-neutral-50 transition-colors',
                  d.severity === 'major' && 'bg-[#ff3b30]/[0.02]'
                )}>
                  <div className="flex flex-wrap items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-body font-semibold text-neutral-900">{d.id}</span>
                      <Badge variant={d.severity === 'major' ? 'danger' : 'warning'} size="sm">
                        {d.severity}
                      </Badge>
                      <Badge variant={d.status === 'open' ? 'danger' : d.status === 'documented' ? 'warning' : 'success'} size="sm">
                        {d.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-body-sm text-neutral-400">
                      <span>{d.patientId}</span>
                      <span>{d.detectedDate}</span>
                    </div>
                  </div>
                  <p className="text-body text-neutral-700 mb-2">{d.description}</p>
                  <div className="flex items-center justify-between">
                    <p className="text-body-sm text-neutral-400">{d.protocolRef}</p>
                    {d.status === 'open' && (
                      <Button variant="ghost" size="sm">Document</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>

      <section className="pb-20 px-6 lg:px-12">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">How It Works</p>
              <div className="space-y-5">
                {[
                  { step: '1', title: 'Protocol Rules Loaded', desc: 'YAML defines timing windows and requirements' },
                  { step: '2', title: 'Patient Data Scanned', desc: 'Every visit compared against protocol' },
                  { step: '3', title: 'Deviations Classified', desc: 'Major vs minor based on severity thresholds' },
                  { step: '4', title: 'Actions Generated', desc: 'Remediation steps and CSR guidance' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4">
                    <div className="w-8 h-8 rounded-lg bg-neutral-900 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-body-sm font-semibold">{item.step}</span>
                    </div>
                    <div>
                      <p className="text-body font-medium text-neutral-900">{item.title}</p>
                      <p className="text-body-sm text-neutral-500">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-8" variant="elevated">
              <p className="text-headline text-neutral-900 mb-6">Protocol Rules Active</p>
              <div className="space-y-3">
                {[
                  'Visit Window: +30/-14 days',
                  'HHS Assessment: All timepoints',
                  'Radiographic: 6mo, 12mo, 24mo',
                  'SAE Narrative: Required',
                  'Informed Consent: Pre-procedure',
                ].map((rule, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50">
                    <div className="flex items-center gap-3">
                      <span className="w-1.5 h-1.5 bg-[#34c759] rounded-full" />
                      <span className="text-body-sm text-neutral-700">{rule}</span>
                    </div>
                    <Badge variant="success" size="sm">Active</Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
