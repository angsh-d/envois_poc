import { Link, useParams } from 'wouter'
import {
  ArrowRight,
  ArrowLeft,
  BarChart3,
  Zap,
  CheckCircle2,
  ClipboardCheck,
  Target,
  Shield,
  Settings2,
  Database,
  FileText,
  AlertTriangle,
} from 'lucide-react'
import { Card } from '@/components/Card'
import { Navbar } from '@/components/Navbar'

interface Product {
  id: string
  name: string
  category: string
  studyId: string
  protocolId: string
  status: 'active' | 'configured' | 'pending'
}

interface PersonaRole {
  id: string
  title: string
  department: string
  headline: string
  valueProps: string[]
  primaryAction: string
  icon: React.ComponentType<{ className?: string }>
  isConfiguration?: boolean
}

// Product mapping
const productData: Record<string, Product> = {
  'delta-tt': {
    id: 'delta-tt',
    name: 'DELTA TT Revision Cup',
    category: 'Hip Reconstruction',
    studyId: 'h34-delta',
    protocolId: 'H-34',
    status: 'active',
  },
  'empowr-dual': {
    id: 'empowr-dual',
    name: 'EMPOWR Dual Mobility',
    category: 'Hip Reconstruction',
    studyId: 'emp-dual',
    protocolId: 'EMP-01',
    status: 'configured',
  },
  'empowr-knee': {
    id: 'empowr-knee',
    name: 'EMPOWR Knee',
    category: 'Knee Reconstruction',
    studyId: 'emp-knee',
    protocolId: 'EMP-02',
    status: 'configured',
  },
}

const personas: PersonaRole[] = [
  {
    id: 'product-data-steward',
    title: 'Product Data Steward',
    department: 'Platform Configuration',
    headline: 'Configure knowledge base & data sources',
    valueProps: [
      'Connect clinical databases and data warehouses',
      'Configure knowledge base with product literature',
      'Set up registry benchmarks and thresholds',
    ],
    primaryAction: 'Configure Product',
    icon: Settings2,
    isConfiguration: true,
  },
  {
    id: 'product-manager',
    title: 'Product Manager',
    department: 'Product Development',
    headline: 'Data-driven device decisions',
    valueProps: [
      'Real-time safety signal monitoring vs. benchmarks',
      'Competitive positioning with AI-generated battle cards',
      'Claim validation with clinical evidence synthesis',
    ],
    primaryAction: 'Enter Command Center',
    icon: BarChart3,
  },
  {
    id: 'sales',
    title: 'Sales Representative',
    department: 'Commercial',
    headline: 'Win every competitive conversation',
    valueProps: [
      'Battle cards with evidence-backed rebuttals',
      'Talking points derived from real clinical data',
      'Surgeon objection handlers at your fingertips',
    ],
    primaryAction: 'Access Battle Cards',
    icon: Zap,
  },
  {
    id: 'marketing',
    title: 'Marketing Manager',
    department: 'Marketing & Communications',
    headline: 'Substantiate every claim',
    valueProps: [
      'AI-powered claim validation against clinical data',
      'Compliant language recommendations',
      'Evidence gaps identified automatically',
    ],
    primaryAction: 'Validate Claims',
    icon: CheckCircle2,
  },
  {
    id: 'clinical-operations',
    title: 'Clinical Operations',
    department: 'Clinical Operations Services',
    headline: 'Study health at a glance',
    valueProps: [
      'Real-time enrollment tracking against targets',
      'Protocol deviation patterns by site',
      'Data completeness monitoring',
    ],
    primaryAction: 'View Operations',
    icon: ClipboardCheck,
  },
  {
    id: 'strategy',
    title: 'Strategy Lead',
    department: 'Corporate Strategy',
    headline: 'Strategic intelligence synthesized',
    valueProps: [
      'Portfolio-wide risk assessment',
      'Competitive threat monitoring',
      'Market position analysis',
    ],
    primaryAction: 'Analyze Strategy',
    icon: Target,
  },
  {
    id: 'quality-head',
    title: 'Quality Head',
    department: 'Quality Assurance',
    headline: 'Vigilance signals prioritized',
    valueProps: [
      'Proactive safety signal detection',
      'Trend analysis across metrics',
      'Regulatory readiness tracking',
    ],
    primaryAction: 'Review Signals',
    icon: Shield,
  },
]

export default function ProductPersonas() {
  const { productId } = useParams<{ productId: string }>()
  const product = productData[productId || '']

  if (!product) {
    return (
      <div className="min-h-screen bg-[#fafafa]">
        <Navbar />
        <main className="py-16 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h1 className="text-2xl font-semibold text-gray-900">Product Not Found</h1>
            <p className="mt-2 text-gray-500">The requested product could not be found.</p>
            <Link href="/" className="inline-flex items-center gap-2 mt-6 text-gray-900 hover:text-gray-600">
              <ArrowLeft className="w-4 h-4" />
              Back to Products
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const configPersona = personas.find(p => p.isConfiguration)
  const workflowPersonas = personas.filter(p => !p.isConfiguration)

  const getPersonaPath = (persona: PersonaRole) => {
    if (persona.isConfiguration) {
      return `/product/${productId}/configure`
    }
    return `/study/${product.studyId}?persona=${persona.id}`
  }

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <Navbar />

      <main>
        {/* Header Section */}
        <section className="py-12 px-6 bg-white border-b border-gray-100">
          <div className="max-w-5xl mx-auto">
            <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors mb-6">
              <ArrowLeft className="w-4 h-4" />
              Back to Products
            </Link>

            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 uppercase tracking-wide mb-1">{product.category}</p>
                <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
                  {product.name}
                </h1>
                <p className="mt-2 text-gray-500">
                  Protocol {product.protocolId} &middot; Select your role to access personalized intelligence
                </p>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 rounded-full text-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>
                <span className="text-white font-medium">
                  {product.status === 'active' ? 'Active Study' : 'Configured'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Configuration Persona Section */}
        {configPersona && (
          <section className="py-8 px-6 bg-gray-50 border-b border-gray-100">
            <div className="max-w-5xl mx-auto">
              <Link href={getPersonaPath(configPersona)}>
                <Card hoverable className="group transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50 bg-white">
                  <div className="flex items-center gap-6">
                    <div className="flex-shrink-0 w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center group-hover:bg-gray-900 transition-colors">
                      <configPersona.icon className="w-7 h-7 text-gray-600 group-hover:text-white transition-colors" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-lg font-semibold text-gray-900">{configPersona.title}</h3>
                        <span className="px-2 py-0.5 bg-amber-50 border border-amber-100 rounded text-xs text-amber-600 font-medium">
                          One-time Setup
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">{configPersona.headline}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="hidden md:flex items-center gap-4 text-sm text-gray-400">
                        <span className="flex items-center gap-1.5">
                          <Database className="w-4 h-4" />
                          Data Sources
                        </span>
                        <span className="flex items-center gap-1.5">
                          <FileText className="w-4 h-4" />
                          Knowledge Base
                        </span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                </Card>
              </Link>
            </div>
          </section>
        )}

        {/* Workflow Personas Section */}
        <section className="py-12 px-6 pb-24">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 tracking-tight">Select Your Role</h2>
              <p className="mt-2 text-gray-500">Personalized intelligence for your workflow</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workflowPersonas.map((persona, i) => {
                const Icon = persona.icon

                return (
                  <Link key={persona.id} href={getPersonaPath(persona)}>
                    <div className={`animate-fade-in-up stagger-${i + 1} opacity-0 h-full`}>
                      <Card
                        hoverable
                        className="h-full flex flex-col group transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50"
                      >
                        {/* Header */}
                        <div className="flex items-start gap-3 mb-4">
                          <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center group-hover:bg-gray-900 transition-colors">
                            <Icon className="w-5 h-5 text-gray-600 group-hover:text-white transition-colors" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="text-base font-semibold text-gray-900">
                              {persona.title}
                            </h3>
                            <p className="text-xs text-gray-400">{persona.department}</p>
                          </div>
                        </div>

                        {/* Headline */}
                        <p className="text-sm font-medium text-gray-900 mb-3">{persona.headline}</p>

                        {/* Value Props */}
                        <ul className="flex-1 space-y-2 mb-4">
                          {persona.valueProps.map((prop, j) => (
                            <li key={j} className="flex items-start gap-2 text-sm text-gray-500">
                              <span className="w-1 h-1 bg-gray-300 rounded-full mt-2 flex-shrink-0" />
                              <span className="leading-relaxed">{prop}</span>
                            </li>
                          ))}
                        </ul>

                        {/* CTA */}
                        <div className="pt-4 border-t border-gray-100 mt-auto">
                          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-900 group-hover:text-gray-600 transition-colors">
                            {persona.primaryAction}
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                          </span>
                        </div>
                      </Card>
                    </div>
                  </Link>
                )
              })}
            </div>

            {/* Bottom note */}
            <div className="mt-12 text-center">
              <p className="text-xs text-gray-400">
                All personas access the same underlying data with role-optimized views
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
