import StudyLayout from './StudyLayout'
import {
  Database,
  Bot,
  FileText,
  BookOpen,
  Globe,
  Sparkles,
  Info,
  ChevronRight,
  Layers,
  Shield,
  Activity
} from 'lucide-react'

interface AgentsProps {
  params: { studyId: string }
}

export default function Agents({ params }: AgentsProps) {
  const dataSources = [
    { id: 'h34-data', name: 'H-34 Study Data', icon: FileText, type: 'Structured', format: 'Excel', agents: ['data', 'safety', 'risk'] },
    { id: 'protocol-usdm', name: 'Protocol (USDM)', icon: FileText, type: 'Protocol-as-Code', format: 'JSON', agents: ['protocol'] },
    { id: 'literature', name: 'Literature PDFs', icon: BookOpen, type: 'Unstructured', format: 'PDF → Vectors', agents: ['literature'] },
    { id: 'registry', name: 'Registry Norms', icon: Globe, type: 'Curated', format: 'YAML', agents: ['registry'] },
    { id: 'vectorstore', name: 'Vector Store', icon: Layers, type: 'Embeddings', format: 'pgvector', agents: ['literature', 'protocol'] },
    { id: 'rules', name: 'Safety Thresholds', icon: Shield, type: 'Rules', format: 'YAML', agents: ['safety'] },
  ]

  const llmTools = [
    { id: 'llm-ensemble', name: 'Ensemble of Foundation LLMs', type: 'Language Models', desc: 'Reasoning & generation' },
    { id: 'embeddings', name: 'Embedding Models', type: 'Embeddings', desc: 'Semantic search' },
    { id: 'ml-models', name: 'ML Classifiers', type: 'ML Models', desc: 'Risk prediction' },
    { id: 'rag', name: 'RAG Pipeline', type: 'Retrieval', desc: 'Context injection' },
  ]

  const specialistAgents = [
    { id: 'data', name: 'Clinical Data Agent', shortName: 'Data Agent', icon: Database, desc: 'Retrieves & analyzes patient data', tools: ['LLM', 'SQL'] },
    { id: 'registry', name: 'Registry Benchmark Agent', shortName: 'Registry Agent', icon: Globe, desc: 'Compares against global registries', tools: ['LLM', 'YAML'] },
    { id: 'literature', name: 'Literature Evidence Agent', shortName: 'Literature Agent', icon: BookOpen, desc: 'RAG-powered citation retrieval', tools: ['LLM', 'RAG', 'Embeddings'] },
    { id: 'safety', name: 'Safety Signal Agent', shortName: 'Safety Agent', icon: Shield, desc: 'Detects adverse event signals', tools: ['LLM', 'Rules'] },
    { id: 'protocol', name: 'Protocol Compliance Agent', shortName: 'Protocol Agent', icon: FileText, desc: 'Validates against digitized protocol', tools: ['LLM', 'USDM'] },
    { id: 'risk', name: 'Risk Stratification Agent', shortName: 'Risk Agent', icon: Activity, desc: 'ML-powered risk prediction', tools: ['LLM', 'XGBoost'] },
  ]

  const agents = [
    {
      id: 'orchestrator',
      name: 'Orchestrator Agent',
      type: 'orchestrator' as const,
      description: 'Analyzes incoming requests, identifies required specialist agents, and delegates tasks appropriately. Manages the execution flow and coordinates parallel agent invocations.',
      capabilities: [
        'Request classification and intent detection',
        'Task decomposition and delegation',
        'Agent selection based on query requirements',
        'Parallel execution coordination'
      ]
    },
    {
      id: 'clinical-data',
      name: 'Clinical Data Agent',
      type: 'specialist' as const,
      description: 'Retrieves and analyzes patient-level clinical data from the H-34 study database. Can query specific patients, timepoints, and outcome measures.',
      capabilities: [
        'Patient-level data retrieval',
        'Outcome score analysis (HHS, OHS, EQ-5D)',
        'Temporal trend analysis',
        'Statistical summaries'
      ]
    },
    {
      id: 'registry',
      name: 'Registry Benchmark Agent',
      type: 'specialist' as const,
      description: 'Compares study metrics against international joint replacement registry benchmarks from 9 registries (NJR, SHAR, NAR, NZJR, DHR, EPRD, AJRR, CJRR, AOANJRR).',
      capabilities: [
        'Survival rate benchmarking',
        'Revision rate comparisons',
        'Geographic outcome variations',
        'Revision THA population-specific norms'
      ]
    },
    {
      id: 'literature',
      name: 'Literature Evidence Agent',
      type: 'specialist' as const,
      description: 'Retrieves relevant evidence from indexed literature using RAG (Retrieval-Augmented Generation). Provides citations with full provenance metadata.',
      capabilities: [
        'Semantic literature search (pgvector)',
        'Citation retrieval with page numbers',
        'Evidence synthesis',
        'Benchmark extraction'
      ]
    },
    {
      id: 'protocol',
      name: 'Protocol Agent',
      type: 'specialist' as const,
      description: 'Validates study activities against the digitized protocol (USDM format). Detects protocol deviations by comparing expected vs. actual procedures.',
      capabilities: [
        'Visit compliance checking',
        'Procedure validation',
        'Timing window verification',
        'Deviation detection & classification'
      ]
    },
    {
      id: 'safety',
      name: 'Safety Signal Agent',
      type: 'specialist' as const,
      description: 'Monitors for adverse events and safety signals by comparing study data against predefined thresholds and registry benchmarks.',
      capabilities: [
        'Adverse event detection',
        'Signal-to-noise analysis',
        'Threshold breach alerts',
        'Cross-reference with literature'
      ]
    },
    {
      id: 'risk',
      name: 'Risk Stratification Agent',
      type: 'specialist' as const,
      description: 'Applies ML models to predict patient-level risk of revision, complications, or poor outcomes based on clinical features.',
      capabilities: [
        'XGBoost risk prediction',
        'Feature importance analysis',
        'Cohort risk stratification',
        'Hazard ratio application from literature'
      ]
    },
    {
      id: 'synthesis',
      name: 'Synthesis Agent',
      type: 'synthesis' as const,
      description: 'Combines outputs from all specialist agents into coherent, evidence-based responses. Generates formatted reports with proper citations.',
      capabilities: [
        'Multi-source evidence synthesis',
        'Confidence scoring',
        'Citation formatting',
        'Executive summary generation'
      ]
    }
  ]

  return (
    <StudyLayout studyId={params.studyId}>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">AI Agents</h1>
          <p className="text-gray-500 mt-1">Multi-agent architecture and specialist capabilities</p>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Multi-Agent Architecture</h3>
          </div>
          <p className="text-sm text-gray-600">The platform uses specialized AI agents that leverage LLMs and ML models as tools to analyze clinical data, compare against benchmarks, and generate evidence-based insights.</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="bg-gray-200 px-4 py-3 border-b border-gray-300">
            <h3 className="font-semibold text-gray-800 text-sm">Agentic System Architecture</h3>
          </div>
          <div className="p-6 bg-gray-50">
            <div className="flex flex-col items-center gap-3">
              <div className="w-full border border-gray-200 rounded-xl p-4 bg-white">
                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-3 font-semibold">Data Layer</p>
                <div className="grid grid-cols-3 lg:grid-cols-6 gap-2 w-full">
                  {dataSources.map((source) => {
                    const Icon = source.icon
                    return (
                      <div key={source.id} className="bg-gray-50 border border-gray-200 rounded-lg p-2 text-center">
                        <div className="w-5 h-5 bg-white border border-gray-200 rounded flex items-center justify-center mx-auto mb-1">
                          <Icon className="w-3 h-3 text-gray-500" />
                        </div>
                        <p className="text-[9px] font-medium text-gray-700 leading-tight">{source.name}</p>
                        <p className="text-[8px] text-gray-400">{source.format}</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex items-center justify-center w-full">
                <div className="flex-1 h-px bg-gray-200"></div>
                <ChevronRight className="w-4 h-4 text-gray-300 rotate-90 mx-2" />
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>

              <div className="w-full border border-gray-300 rounded-xl p-4 bg-gray-100">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3 font-semibold">LLM & ML Tools Layer</p>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                  {llmTools.map((tool) => (
                    <div key={tool.id} className="bg-white border border-gray-200 rounded-lg p-2.5 text-center">
                      <div className="flex items-center justify-center gap-1.5 mb-1">
                        <Sparkles className="w-3 h-3 text-gray-500" />
                        <p className="text-[10px] font-semibold text-gray-700">{tool.name}</p>
                      </div>
                      <p className="text-[8px] text-gray-400">{tool.type}</p>
                      <p className="text-[8px] text-gray-500 mt-0.5">{tool.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-center w-full">
                <div className="flex-1 h-px bg-gray-200"></div>
                <ChevronRight className="w-4 h-4 text-gray-300 rotate-90 mx-2" />
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>

              <div className="w-full border border-gray-400 rounded-xl p-4 bg-gray-200">
                <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-3 font-semibold">Specialist Agents Layer</p>
                <div className="grid grid-cols-2 lg:grid-cols-6 gap-2 w-full">
                  {specialistAgents.map((agent) => {
                    const Icon = agent.icon
                    return (
                      <div key={agent.id} className="bg-white border border-gray-300 rounded-lg p-2.5 text-center hover:shadow-sm transition-shadow">
                        <div className="w-7 h-7 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-1.5">
                          <Icon className="w-4 h-4 text-gray-600" />
                        </div>
                        <p className="text-[10px] font-semibold text-gray-800">{agent.shortName}</p>
                        <p className="text-[8px] text-gray-500 leading-tight">{agent.desc}</p>
                        <div className="flex items-center justify-center gap-1 mt-1.5 flex-wrap">
                          {agent.tools.map((tool) => (
                            <span key={tool} className="text-[7px] bg-gray-100 text-gray-500 px-1 py-0.5 rounded">{tool}</span>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex items-center justify-center w-full">
                <div className="flex-1 h-px bg-gray-200"></div>
                <ChevronRight className="w-4 h-4 text-gray-300 rotate-90 mx-2" />
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>

              <div className="w-full border border-gray-400 rounded-xl p-4 bg-gray-300">
                <p className="text-[10px] text-gray-700 uppercase tracking-wide mb-3 font-semibold">Orchestration & Synthesis Layer</p>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  <div className="bg-white border border-gray-400 rounded-lg p-3 text-center shadow-sm">
                    <div className="flex items-center justify-center gap-2 mb-1">
                      <Bot className="w-4 h-4 text-gray-700" />
                      <p className="text-sm font-semibold text-gray-900">Orchestrator Agent</p>
                    </div>
                    <p className="text-xs text-gray-600">Routes queries to specialists, coordinates parallel execution</p>
                  </div>
                  <div className="bg-white border border-gray-400 rounded-lg p-3 text-center shadow-sm">
                    <div className="flex items-center justify-center gap-2 mb-1">
                      <Sparkles className="w-4 h-4 text-gray-700" />
                      <p className="text-sm font-semibold text-gray-900">Synthesis Agent</p>
                    </div>
                    <p className="text-xs text-gray-600">Combines specialist outputs into coherent responses</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center w-full">
                <div className="flex-1 h-px bg-gray-300"></div>
                <ChevronRight className="w-4 h-4 text-gray-400 rotate-90 mx-2" />
                <div className="flex-1 h-px bg-gray-300"></div>
              </div>

              <div className="w-full border border-gray-500 rounded-xl p-4 bg-gray-500">
                <p className="text-[10px] text-white uppercase tracking-wide mb-3 font-semibold">UI & Application Layer</p>
                <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">Dashboard</p>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">Readiness</p>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">Safety</p>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">Deviations</p>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">Risk</p>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-2 text-center shadow-sm">
                    <p className="text-[9px] font-medium text-gray-800">AI Chat</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map((agent) => (
            <div key={agent.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-sm transition-shadow">
              <div className={`px-4 py-3 border-b ${
                agent.type === 'orchestrator' ? 'bg-gray-200 border-gray-300' :
                agent.type === 'synthesis' ? 'bg-gray-100 border-gray-200' :
                'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-gray-600" />
                    <h3 className="font-semibold text-gray-900 text-sm">{agent.name}</h3>
                  </div>
                  <span className={`px-2 py-0.5 text-[10px] font-medium rounded ${
                    agent.type === 'orchestrator' ? 'bg-gray-600 text-white' :
                    agent.type === 'synthesis' ? 'bg-gray-500 text-white' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {agent.type.toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
                <div className="space-y-1.5">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Capabilities</p>
                  <ul className="space-y-1">
                    {agent.capabilities.map((cap, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-gray-600">
                        <div className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></div>
                        {cap}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-gray-50 rounded-xl p-4 flex items-start gap-3 border border-gray-200">
          <Info className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-gray-600">
            <p className="font-medium text-gray-700 mb-1">Agent Communication</p>
            <p>Agents communicate through a message-passing architecture. The Orchestrator routes requests to appropriate specialists, collects their outputs, and the Synthesis Agent generates coherent responses using the Gemini LLM.</p>
          </div>
        </div>
      </div>
    </StudyLayout>
  )
}
