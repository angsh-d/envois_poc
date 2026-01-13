import { Link } from 'wouter'
import { ArrowRight, ArrowLeft, Brain, Shield, Activity, Users, Sparkles, Zap, Network, Database } from 'lucide-react'
import { Card } from '@/components/Card'
import { Navbar } from '@/components/Navbar'

const studies = [
  {
    id: 'h34-delta',
    name: 'H-34 DELTA Revision Cup',
    description: 'Post-market clinical follow-up study for acetabular revision',
    patients: 37,
    status: 'Active',
    enrollment: '74%',
  },
]

const features = [
  {
    icon: Brain,
    title: 'Multi-Agent Intelligence',
    description: 'Six specialized AI agents orchestrated in real-time: Data, Registry, Literature, Safety, Protocol, and Synthesis agents working in concert',
  },
  {
    icon: Shield,
    title: 'Regulatory Readiness',
    description: 'Continuous gap analysis against FDA/EMA requirements with automated submission readiness scoring and actionable remediation paths',
  },
  {
    icon: Activity,
    title: 'Safety Signal Detection',
    description: 'Cross-source contextualization of adverse events against 5 global registries, 6 literature benchmarks, and protocol thresholds',
  },
  {
    icon: Users,
    title: 'Predictive Risk Stratification',
    description: 'Ensemble ML model combining XGBoost predictions with literature-derived hazard ratios for explainable patient risk scoring',
  },
]

const capabilities = [
  { icon: Network, label: 'Protocol-as-Code', desc: 'USDM 4.0 digitization' },
  { icon: Database, label: 'Unified Data Layer', desc: 'PostgreSQL + pgvector' },
  { icon: Zap, label: 'Real-time RAG', desc: 'Semantic literature search' },
  { icon: Sparkles, label: 'LLM Synthesis', desc: 'Gemini-powered narratives' },
]

export default function StudySelect() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main>
        <section className="pt-12 pb-6 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-6">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Role Selection</span>
            </Link>
            <h1 className="text-4xl font-semibold text-gray-900 tracking-tight mb-4">
              Clinical Strategy Analyst
            </h1>
            <p className="text-lg text-gray-500 mb-8">
              Manage and interpret multi-source registry data, identify trends and outliers in clinical outcomes, generate automated strategic reports
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              {capabilities.map((cap) => (
                <div key={cap.label} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl shadow-sm">
                  <cap.icon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">{cap.label}</span>
                  <span className="text-xs text-gray-400">{cap.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-12 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-6 mb-24">
              {features.map((feature, i) => (
                <div
                  key={feature.title}
                  className={`animate-fade-in-up stagger-${i + 1} opacity-0`}
                >
                  <Card className="h-full">
                    <feature.icon className="w-10 h-10 text-gray-800 mb-4" strokeWidth={1.5} />
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{feature.title}</h3>
                    <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-12 px-6 pb-32">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-semibold text-gray-900 mb-2 tracking-tight">Studies</h2>
            <p className="text-gray-500 mb-8">Select a study to view its clinical intelligence dashboard</p>

            <div className="space-y-4">
              {studies.map((study) => (
                <Link key={study.id} href={`/study/${study.id}`}>
                  <Card hoverable className="group">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-semibold text-gray-800 group-hover:text-gray-900 transition-colors">
                            {study.name}
                          </h3>
                          <span className="px-2.5 py-0.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                            {study.status}
                          </span>
                        </div>
                        <p className="text-gray-500 mb-4">{study.description}</p>
                        <div className="flex gap-6">
                          <div>
                            <span className="text-2xl font-semibold text-gray-800">{study.patients}</span>
                            <span className="text-sm text-gray-500 ml-1">patients</span>
                          </div>
                          <div>
                            <span className="text-2xl font-semibold text-gray-800">{study.enrollment}</span>
                            <span className="text-sm text-gray-500 ml-1">enrolled</span>
                          </div>
                        </div>
                      </div>
                      <div className="ml-6">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                          <ArrowRight className="w-5 h-5 text-gray-600 group-hover:translate-x-0.5 transition-transform" />
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
