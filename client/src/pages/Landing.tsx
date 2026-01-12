import { Link } from 'wouter'
import { ArrowRight, Brain, Shield, Activity, Users } from 'lucide-react'
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
    title: 'AI-Powered Insights',
    description: 'Multi-agent system analyzing study data, protocol, literature, and registry benchmarks',
  },
  {
    icon: Shield,
    title: 'Regulatory Readiness',
    description: 'Real-time gap analysis with automated submission readiness assessment',
  },
  {
    icon: Activity,
    title: 'Safety Intelligence',
    description: 'Cross-source contextualization of adverse events with literature and registry data',
  },
  {
    icon: Users,
    title: 'Patient Risk Stratification',
    description: 'ML-powered risk scoring with explainable factors and monitoring recommendations',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main>
        <section className="py-24 px-6">
          <div className="max-w-4xl mx-auto text-center animate-fade-in-up">
            <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 tracking-tight leading-tight">
              Clinical Intelligence
              <br />
              <span className="text-gray-400">Platform</span>
            </h1>
            <p className="mt-6 text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
              AI-powered insights for post-market clinical studies. Transform disparate data sources into actionable regulatory intelligence.
            </p>
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
                          <span className="px-2.5 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
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
