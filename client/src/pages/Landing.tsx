import { Link } from 'wouter'
import { ArrowRight, Sparkles, Zap, Network, Database, Lock } from 'lucide-react'
import { Card } from '@/components/Card'
import { Navbar } from '@/components/Navbar'

const roles = [
  {
    id: 'clinical-strategy-analyst',
    title: 'Clinical Strategy Analyst',
    department: 'Clinical Strategy Team',
    responsibilities: 'Registry data interpretation, trend analysis, strategic planning, report generation',
    enabled: true,
    path: '/role/clinical-strategy-analyst',
  },
  {
    id: 'clinical-data-manager',
    title: 'Clinical Data Manager',
    department: 'Clinical Operation Services (COS)',
    responsibilities: 'Data cleaning, consistency checks, eCRF management, site metrics',
    enabled: false,
    path: '/role/clinical-data-manager',
  },
  {
    id: 'clinical-research-associate',
    title: 'Clinical Research Associate',
    department: 'Company Initiated Studies (CIS)',
    responsibilities: 'Monitoring visits, milestones, study progress tracking, patient data preparation',
    enabled: false,
    path: '/role/clinical-research-associate',
  },
  {
    id: 'scientific-comms-specialist',
    title: 'Scientific Comms. Specialist',
    department: 'Scientific Communication & IIS',
    responsibilities: 'Literature searches, clinical visuals, stakeholder communication, IIS support',
    enabled: false,
    path: '/role/scientific-comms-specialist',
  },
]

const capabilities = [
  { icon: Network, label: 'Protocol-as-Code', desc: 'USDM 4.0 digitization' },
  { icon: Database, label: 'Unified Data Layer', desc: 'PostgreSQL + pgvector' },
  { icon: Zap, label: 'Real-time RAG', desc: 'Semantic literature search' },
  { icon: Sparkles, label: 'LLM Synthesis', desc: 'Gemini-powered narratives' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main>
        <section className="py-20 px-6 bg-gradient-to-b from-white to-gray-50">
          <div className="max-w-5xl mx-auto text-center animate-fade-in-up">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full text-sm text-gray-600 mb-8">
              <Sparkles className="w-4 h-4" />
              <span>Powered by Multi-Agent AI Architecture</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-semibold text-gray-900 tracking-tight leading-[1.1]">
              Clinical Data Intelligence
              <br />
              <span className="bg-gradient-to-r from-gray-600 to-gray-400 bg-clip-text text-transparent">Platform</span>
            </h1>
            <p className="mt-8 text-xl md:text-2xl text-gray-500 max-w-3xl mx-auto leading-relaxed">
              AI-native platform unifying clinical studies, global registries, published literature, and real-world evidence into actionable insights for faster, smarter decision-making.
            </p>
            <p className="mt-4 text-lg text-gray-400 max-w-2xl mx-auto">
              Empowering Clinical Strategy, Scientific Affairs, Operations, and cross-functional teams with automated analytics that replace manual tasks with high-level strategic work.
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
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

        <section className="py-16 px-6 pb-32">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-semibold text-gray-900 tracking-tight">Choose Your Role</h2>
              <p className="mt-2 text-gray-500">Select your role to access personalized clinical intelligence tools</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {roles.map((role, i) => (
                role.enabled ? (
                  <Link key={role.id} href={role.path}>
                    <Card hoverable className={`group h-full animate-fade-in-up stagger-${i + 1} opacity-0`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-gray-800 group-hover:text-gray-900 transition-colors mb-1">
                            {role.title}
                          </h3>
                          <p className="text-sm text-gray-500 mb-4">{role.department}</p>
                          <p className="text-sm text-gray-600 leading-relaxed">{role.responsibilities}</p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                            <ArrowRight className="w-4 h-4 text-gray-600 group-hover:translate-x-0.5 transition-transform" />
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ) : (
                  <div key={role.id} className={`animate-fade-in-up stagger-${i + 1} opacity-0`}>
                    <Card className="h-full opacity-60 cursor-not-allowed">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-gray-500 mb-1">
                            {role.title}
                          </h3>
                          <p className="text-sm text-gray-400 mb-4">{role.department}</p>
                          <p className="text-sm text-gray-400 leading-relaxed">{role.responsibilities}</p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                            <Lock className="w-4 h-4 text-gray-400" />
                          </div>
                        </div>
                      </div>
                    </Card>
                  </div>
                )
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
