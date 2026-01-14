import { useState } from 'react'
import StudyLayout from './StudyLayout'
import {
  Database,
  Bot,
  FileText,
  BookOpen,
  Globe,
  CheckCircle,
  Beaker,
  Sparkles,
  TrendingUp,
  Info,
  AlertTriangle,
  ChevronRight,
  Cpu,
  Network,
  Layers,
  Search,
  Shield,
  Activity,
  GitBranch
} from 'lucide-react'

interface DataAgentsProps {
  params: { studyId: string }
}

type TabType = 'data' | 'agents'
type DataSubTab = 'real' | 'synthetic' | 'models' | 'lineage'

export default function DataAgents({ params }: DataAgentsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('data')
  const [dataSubTab, setDataSubTab] = useState<DataSubTab>('real')

  const tabs = [
    { id: 'data' as const, label: 'Data Sources', icon: Database },
    { id: 'agents' as const, label: 'Agents', icon: Bot },
  ]

  const dataSubTabs = [
    { id: 'real' as const, label: 'Real Data', icon: CheckCircle },
    { id: 'synthetic' as const, label: 'Synthetic Data', icon: Beaker },
    { id: 'models' as const, label: 'AI & ML Models', icon: Sparkles },
    { id: 'lineage' as const, label: 'Data Lineage', icon: GitBranch },
  ]

  const agents = [
    {
      id: 'orchestrator',
      name: 'Orchestrator Agent',
      icon: Network,
      description: 'Central coordinator that routes requests to specialized agents and synthesizes responses',
      capabilities: ['Request routing', 'Agent coordination', 'Response synthesis', 'Context management'],
      inputs: ['User queries', 'API requests', 'System events'],
      outputs: ['Synthesized responses', 'Agent task assignments', 'Execution plans'],
      level: 0
    },
    {
      id: 'data',
      name: 'Data Agent',
      icon: Database,
      description: 'Processes and analyzes clinical study data from the H-34 Excel dataset',
      capabilities: ['Patient data retrieval', 'Statistical analysis', 'Data validation', 'Cohort filtering'],
      inputs: ['H-34 Excel (37 patients)', 'Unified schema', 'Query parameters'],
      outputs: ['Patient records', 'Aggregate statistics', 'Data quality metrics'],
      level: 1
    },
    {
      id: 'registry',
      name: 'Registry Agent',
      icon: Globe,
      description: 'Retrieves and compares data against international joint replacement registry benchmarks for revision THA',
      capabilities: ['Registry data lookup', 'Benchmark comparison', 'Revision THA survival analysis', 'Regional comparison'],
      inputs: ['Registry YAML (9 registries)', 'Study metrics', 'Comparison parameters'],
      outputs: ['Registry benchmarks', 'Comparison reports', 'Revision survival rates'],
      level: 1
    },
    {
      id: 'literature',
      name: 'Literature Agent',
      icon: BookOpen,
      description: 'Searches and extracts insights from indexed peer-reviewed publications using RAG',
      capabilities: ['Semantic search', 'Citation retrieval', 'Hazard ratio extraction', 'Evidence synthesis'],
      inputs: ['Literature PDFs (12)', 'ChromaDB vectors', 'Search queries'],
      outputs: ['Relevant citations', 'Extracted data points', 'Evidence summaries'],
      level: 1
    },
    {
      id: 'safety',
      name: 'Safety Agent',
      icon: Shield,
      description: 'Monitors and analyzes adverse events, safety signals, and device-related issues',
      capabilities: ['AE detection', 'Signal analysis', 'Causality assessment', 'Trend monitoring'],
      inputs: ['Adverse event data', 'Device reports', 'Safety thresholds'],
      outputs: ['Safety signals', 'Risk assessments', 'Alert recommendations'],
      level: 1
    },
    {
      id: 'protocol',
      name: 'Protocol Agent',
      icon: FileText,
      description: 'Validates study conduct against digitized protocol rules and visit windows',
      capabilities: ['Protocol validation', 'Deviation detection', 'Window checking', 'Compliance scoring'],
      inputs: ['Protocol YAML rules', 'Visit data', 'Assessment schedules'],
      outputs: ['Deviations', 'Compliance reports', 'Protocol adherence scores'],
      level: 1
    },
    {
      id: 'risk',
      name: 'Risk Agent',
      icon: Activity,
      description: 'Predicts patient risk using ML models and literature-based hazard ratios',
      capabilities: ['Risk prediction', 'Feature extraction', 'Hazard calculation', 'Cohort stratification'],
      inputs: ['Patient features', 'XGBoost model', 'Literature HRs'],
      outputs: ['Risk scores', 'Risk levels', 'Contributing factors'],
      level: 1
    },
    {
      id: 'synthesis',
      name: 'Synthesis Agent',
      icon: Sparkles,
      description: 'Combines outputs from all agents using LLM to generate coherent narratives',
      capabilities: ['Response generation', 'Context weaving', 'Insight synthesis', 'Natural language output'],
      inputs: ['Agent outputs', 'LLM context', 'User preferences'],
      outputs: ['Natural language responses', 'Executive summaries', 'Recommendations'],
      level: 2
    },
  ]

  const renderDataSources = () => (
    <div className="space-y-6">
      <div className="flex gap-2 border-b border-gray-100 pb-4">
        {dataSubTabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setDataSubTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                dataSubTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {dataSubTab === 'real' && (
        <div className="space-y-6">
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">Real Data Sources</h3>
            </div>
            <p className="text-sm text-gray-600">These data sources contain real, provided data from actual clinical studies, published literature, and curated registry reports.</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">H-34 Clinical Study Data</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA</span>
              </div>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-500 w-44">Source File</td>
                    <td className="py-2 font-mono text-xs text-gray-800">H-34DELTARevisionstudy_export_20250912.xlsx</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">File Size</td>
                    <td className="py-2 text-gray-800">138 KB (21 Excel sheets)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Patient Count</td>
                    <td className="py-2 font-medium text-gray-800">37 enrolled patients</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Data Elements</td>
                    <td className="py-2 text-gray-800">Demographics, preoperative assessments, intraoperative data, surgery details, follow-up visits (6 timepoints), adverse events, HHS/OHS scores, revision outcomes</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Follow-up Schedule</td>
                    <td className="py-2 text-gray-800">Discharge, 2 months, 6 months, 1 year, 2 years</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Data Loader</td>
                    <td className="py-2 font-mono text-xs text-gray-600">H34ExcelLoader → Pydantic unified_schema.py</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Published Literature</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA</span>
              </div>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-gray-900">4</div>
                  <div className="text-xs text-gray-500">Publications with extracted benchmarks</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-gray-900">8.1 MB</div>
                  <div className="text-xs text-gray-500">Indexed literature corpus</div>
                </div>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Publication</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Key Benchmarks Extracted</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 pr-4 text-gray-800">Singh et al. 2016 (n=2,667)</td>
                    <td className="py-2 text-gray-600 text-xs">HHS MCID thresholds, effect sizes, revision risk prediction</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 text-gray-800">Steckel et al. 2025 (n=117)</td>
                    <td className="py-2 text-gray-600 text-xs">Short-stem THA outcomes, HHS improvement (45.2→88.4)</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 text-gray-800">Bazan et al. 2025 (n=344)</td>
                    <td className="py-2 text-gray-600 text-xs">Stem comparison, clinical/radiological outcomes</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 text-gray-800">Vasios et al. 2025 (n=11)</td>
                    <td className="py-2 text-gray-600 text-xs">Acetabular revision with bone loss, cup-cage constructs</td>
                  </tr>
                </tbody>
              </table>
              <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                <strong>Storage:</strong> literature_benchmarks.yaml (curated with full provenance)
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Registry Benchmark Data</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA (Curated)</span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-4">
                Values curated from official annual reports of international joint replacement registries.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm table-fixed">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium w-20">Registry</th>
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium w-24">Region</th>
                      <th className="text-right py-2 pr-6 text-gray-500 font-medium w-24">Procedures</th>
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium w-24">Years</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Revision THA Metrics</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">NJR</td>
                      <td className="py-2 pr-4 text-gray-600">UK</td>
                      <td className="py-2 pr-6 text-right text-gray-800">38,456</td>
                      <td className="py-2 pr-4 text-gray-600">2003-2023</td>
                      <td className="py-2 text-gray-600 text-xs">95.8% survival (10yr), outcomes</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">SHAR</td>
                      <td className="py-2 pr-4 text-gray-600">Sweden</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~25,000</td>
                      <td className="py-2 pr-4 text-gray-600">1979-2023</td>
                      <td className="py-2 text-gray-600 text-xs">77.8% survival (10yr), PROMs</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">NAR</td>
                      <td className="py-2 pr-4 text-gray-600">Norway</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~12,000</td>
                      <td className="py-2 pr-4 text-gray-600">1987-2023</td>
                      <td className="py-2 text-gray-600 text-xs">79% survival (10yr), re-revision rates</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">NZJR</td>
                      <td className="py-2 pr-4 text-gray-600">New Zealand</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~8,500</td>
                      <td className="py-2 pr-4 text-gray-600">1999-2023</td>
                      <td className="py-2 text-gray-600 text-xs">79% survival (10yr), K-M curves</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">DHR</td>
                      <td className="py-2 pr-4 text-gray-600">Denmark</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~6,500</td>
                      <td className="py-2 pr-4 text-gray-600">1995-2023</td>
                      <td className="py-2 text-gray-600 text-xs">90% survival (10yr), revision reasons</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">EPRD</td>
                      <td className="py-2 pr-4 text-gray-600">Germany</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~45,000</td>
                      <td className="py-2 pr-4 text-gray-600">2012-2023</td>
                      <td className="py-2 text-gray-600 text-xs">85% survival (5yr), K-M analysis</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">AJRR</td>
                      <td className="py-2 pr-4 text-gray-600">USA</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~89,000</td>
                      <td className="py-2 pr-4 text-gray-600">2012-2023</td>
                      <td className="py-2 text-gray-600 text-xs">Revision rates, complications</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">CJRR</td>
                      <td className="py-2 pr-4 text-gray-600">Canada</td>
                      <td className="py-2 pr-6 text-right text-gray-800">~15,000</td>
                      <td className="py-2 pr-4 text-gray-600">2001-2023</td>
                      <td className="py-2 text-gray-600 text-xs">Revision rates, hospital outcomes</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium text-gray-800">AOANJRR</td>
                      <td className="py-2 pr-4 text-gray-600">Australia</td>
                      <td className="py-2 pr-6 text-right text-gray-800">45,892</td>
                      <td className="py-2 pr-4 text-gray-600">1999-2023</td>
                      <td className="py-2 text-gray-600 text-xs">Survival (1-15yr), revision reasons</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                <strong>Source:</strong> Official annual reports (2023-2024) with full provenance metadata (page numbers, tables, exact quotes)
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Protocol-as-Code & USDM Data</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA</span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-4">
                The clinical study protocol has been digitized into machine-readable formats following the CDISC Unified Study Definitions Model (USDM) standard.
              </p>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-gray-900">3</div>
                  <div className="text-xs text-gray-500">USDM JSON files</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-gray-900">USDM 4.0</div>
                  <div className="text-xs text-gray-500">Standard version</div>
                </div>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">File</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Description</th>
                    <th className="text-right py-2 text-gray-500 font-medium">Elements</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 font-mono text-xs text-gray-800">soa_usdm.json</td>
                    <td className="py-2 text-gray-600 text-xs">Schedule of Activities - visits, procedures, timing windows</td>
                    <td className="py-2 text-right text-gray-800">6 visits, 15+ procedures</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-mono text-xs text-gray-800">eligibility_criteria.json</td>
                    <td className="py-2 text-gray-600 text-xs">Inclusion/exclusion criteria with coded terms</td>
                    <td className="py-2 text-right text-gray-800">12 inclusion, 8 exclusion</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-mono text-xs text-gray-800">usdm_4.0.json</td>
                    <td className="py-2 text-gray-600 text-xs">Full protocol digitization with study design, endpoints, domains</td>
                    <td className="py-2 text-right text-gray-800">Complete protocol</td>
                  </tr>
                </tbody>
              </table>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="font-medium text-gray-800 mb-3">Protocol Domains Extracted</h4>
                <div className="flex flex-wrap gap-2">
                  {['Laboratory Tests', 'Physical Exam', 'Imaging', 'PROs (HHS/OHS)', 'Adverse Events', 'Concomitant Meds', 'Surgical Details', 'Follow-up Windows'].map((domain, i) => (
                    <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg">{domain}</span>
                  ))}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                <strong>Storage:</strong> data/raw/protocol/*.json | <strong>Standard:</strong> CDISC USDM 4.0 | <strong>Used by:</strong> Protocol Agent, Deviation Detection
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Vector Store & Semantic Index</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">DATA STORE</span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-4">
                Literature and protocol documents are embedded and stored in ChromaDB for semantic retrieval.
              </p>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-500 w-44">Vector Database</td>
                    <td className="py-2 text-gray-800">ChromaDB (persistent)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Embedding Model</td>
                    <td className="py-2 font-mono text-xs text-gray-800">all-MiniLM-L6-v2 (384 dimensions)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Documents Indexed</td>
                    <td className="py-2 text-gray-800">12 literature PDFs + protocol sections</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Storage Location</td>
                    <td className="py-2 font-mono text-xs text-gray-600">data/vectorstore/</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Used By</td>
                    <td className="py-2 text-gray-800">Literature Agent (RAG), Chat Interface</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Structured Rules (YAML)</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA</span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-4">
                Protocol rules and benchmarks curated from source documents and stored as structured YAML.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <p className="font-medium text-gray-800 text-sm font-mono">protocol_rules.yaml</p>
                  <p className="text-xs text-gray-600">Visit windows, assessments, timing rules</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <p className="font-medium text-gray-800 text-sm font-mono">literature_benchmarks.yaml</p>
                  <p className="text-xs text-gray-600">Extracted hazard ratios, survival rates</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <p className="font-medium text-gray-800 text-sm font-mono">registry_norms.yaml</p>
                  <p className="text-xs text-gray-600">International registry benchmarks</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <p className="font-medium text-gray-800 text-sm font-mono">safety_thresholds.yaml</p>
                  <p className="text-xs text-gray-600">AE thresholds, signal detection rules</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {dataSubTab === 'synthetic' && (
        <div className="space-y-6">
          <div className="bg-gray-100 border border-gray-300 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">Synthetic Data Disclosure</h3>
            </div>
            <p className="text-sm text-gray-700">The following data is synthetically generated by this application. All synthetic records are marked with <code className="bg-gray-200 px-1 rounded text-xs">is_synthetic=True</code> for full transparency.</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Beaker className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Synthetic Patient Records</h3>
                </div>
                <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded">SYNTHETIC</span>
              </div>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-600 w-44">Purpose</td>
                    <td className="py-2 text-gray-800">Data augmentation for ML model training</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Generator</td>
                    <td className="py-2 font-mono text-xs text-gray-800">SyntheticH34Generator class</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Output File</td>
                    <td className="py-2 font-mono text-xs text-gray-800">H-34_SYNTHETIC_PRODUCTION.xlsx (353 KB)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Records Generated</td>
                    <td className="py-2 font-medium text-gray-800">300 synthetic patients</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-600">Based On</td>
                    <td className="py-2 text-gray-800">Real H-34 data distributions (68% female, age mean 66.4, BMI 28.6)</td>
                  </tr>
                </tbody>
              </table>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="font-medium text-gray-800 mb-3">Synthetic Data Characteristics</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">Demographics</p>
                    <p className="text-xs text-gray-600">Randomized within real data ranges</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">HHS Trajectory</p>
                    <p className="text-xs text-gray-600">Recovery curve model with individual variation</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">Adverse Events</p>
                    <p className="text-xs text-gray-600">35% AE rate, 80% serious (literature-aligned)</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">Revision Rate</p>
                    <p className="text-xs text-gray-600">8% (aligned with literature benchmarks)</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">Follow-up Completion</p>
                    <p className="text-xs text-gray-600">85% at 2mo → 45% at 2yr (realistic dropout)</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <p className="font-medium text-gray-800 text-sm">Transparency Flag</p>
                    <p className="text-xs text-gray-600">All records marked is_synthetic=True</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <h4 className="font-medium text-gray-800 mb-3">Summary: Real vs Synthetic</h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500 font-medium">Data Category</th>
                  <th className="text-center py-2 text-gray-500 font-medium">Status</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr>
                  <td className="py-2 text-gray-800">H-34 Study Data (Excel)</td>
                  <td className="py-2 text-center"><span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">REAL</span></td>
                  <td className="py-2 text-gray-600">37 patients</td>
                </tr>
                <tr>
                  <td className="py-2 text-gray-800">Synthetic Training Data</td>
                  <td className="py-2 text-center"><span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">SYNTHETIC</span></td>
                  <td className="py-2 text-gray-600">300 patients</td>
                </tr>
                <tr>
                  <td className="py-2 text-gray-800">Literature Benchmarks</td>
                  <td className="py-2 text-center"><span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">REAL</span></td>
                  <td className="py-2 text-gray-600">12 publications</td>
                </tr>
                <tr>
                  <td className="py-2 text-gray-800">Registry Norms</td>
                  <td className="py-2 text-center"><span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">REAL (Curated)</span></td>
                  <td className="py-2 text-gray-600">9 registries, 285K+ revision THA procedures</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {dataSubTab === 'models' && (
        <div className="space-y-6">
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">AI & ML Architecture</h3>
            </div>
            <p className="text-sm text-gray-600">This platform uses an ensemble of foundation LLMs combined with traditional machine learning for risk prediction.</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Foundation LLM Ensemble</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">RAG Architecture</span>
              </div>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-500 w-44">Architecture</td>
                    <td className="py-2 text-gray-800">Ensemble of foundation LLMs with Retrieval-Augmented Generation (RAG)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Orchestration</td>
                    <td className="py-2 text-gray-800">Multi-agent system with specialized agents (Data, Registry, Literature, Safety, Protocol, Risk)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Context Injection</td>
                    <td className="py-2 text-gray-800">Clinical data, registry benchmarks, and literature injected at inference time</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Custom Training</td>
                    <td className="py-2 text-gray-800">None — pre-trained foundation models only. No fine-tuning on patient data.</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Fallback Strategy</td>
                    <td className="py-2 text-gray-800">Automatic failover to secondary LLM if primary unavailable</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">XGBoost Risk Prediction Model</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">ML - Trained</span>
              </div>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-500 w-44">Algorithm</td>
                    <td className="py-2 text-gray-800">XGBoost Classifier (Gradient Boosting)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Training Data</td>
                    <td className="py-2 text-gray-800">337 samples (37 real + 300 synthetic patients)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Train/Test Split</td>
                    <td className="py-2 text-gray-800">80% train / 20% test</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Target Variable</td>
                    <td className="py-2 text-gray-800">Binary: revision + device removal OR SAE OR severe device-related AE</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">Model Files</td>
                    <td className="py-2 font-mono text-xs text-gray-600">risk_model.joblib, risk_scaler.joblib, model_metadata.json</td>
                  </tr>
                </tbody>
              </table>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <h4 className="font-medium text-gray-800 mb-3">13 Input Features</h4>
                <div className="flex flex-wrap gap-2">
                  {['age', 'bmi', 'is_female', 'is_smoker', 'is_former_smoker', 'has_osteoporosis', 'has_prior_surgery', 'bmi_over_30', 'bmi_over_35', 'age_over_70', 'age_over_80', 'poor_bone_quality', 'surgery_duration_long'].map((f) => (
                    <span key={f} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded font-mono">{f}</span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <h4 className="font-medium text-gray-800 mb-3">Model Performance</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <div className="text-xl font-bold text-gray-900">0.54</div>
                    <div className="text-xs text-gray-500">ROC AUC</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <div className="text-xl font-bold text-gray-900">58%</div>
                    <div className="text-xs text-gray-500">Accuracy</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <div className="text-xl font-bold text-gray-900">0.51±0.07</div>
                    <div className="text-xs text-gray-500">CV AUC</div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">Note: Modest performance due to small training dataset. Combines with literature hazard ratios for ensemble scoring.</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Literature Hazard Ratios (HHS-Based Revision Risk)</h3>
                </div>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">From Singh 2016</span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-600 mb-4">Hazard ratios for THA revision risk based on Harris Hip Score thresholds, extracted from Singh et al. 2016 (n=2,667).</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Risk Factor (HHS Threshold)</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">HR</th>
                    <th className="text-left py-2 text-gray-500 font-medium">95% CI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS &lt;55 vs 81-100 (2yr)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">4.34</td><td className="py-1.5 text-gray-500 text-xs">2.14-7.95</td></tr>
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS &lt;55 vs 81-100 (5yr)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">3.08</td><td className="py-1.5 text-gray-500 text-xs">1.45-5.84</td></tr>
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS &lt;70 vs 90-100 (2yr)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">2.32</td><td className="py-1.5 text-gray-500 text-xs">1.32-3.85</td></tr>
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS Improvement ≤0 vs &gt;50 (2yr)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">18.1</td><td className="py-1.5 text-gray-500 text-xs">1.41-234.8</td></tr>
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS ≤55 vs 81-100 (2yr, adj.)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">3.90</td><td className="py-1.5 text-gray-500 text-xs">2.67-5.69</td></tr>
                  <tr><td className="py-1.5 pr-4 text-gray-800">HHS ≤55 vs 81-100 (5yr, adj.)</td><td className="py-1.5 pr-4 text-right font-mono text-gray-800">2.48</td><td className="py-1.5 text-gray-500 text-xs">1.56-3.95</td></tr>
                </tbody>
              </table>
              <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
                <strong>Source:</strong> Singh et al. BMC Musculoskeletal Disorders 2016, Table 2 & 5 (with full provenance)
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-5 h-5 text-gray-400" />
              <h4 className="font-medium text-gray-700">Deep Learning</h4>
            </div>
            <p className="text-sm text-gray-600">No custom deep learning models (neural networks, transformers, CNNs) are used. ChromaDB uses text-embedding-004 for vector indexing only.</p>
          </div>
        </div>
      )}

      {dataSubTab === 'lineage' && (
        <div className="space-y-6">
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <GitBranch className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">Data Flow & Lineage</h3>
            </div>
            <p className="text-sm text-gray-600">How data flows from sources through processing to AI agents and user interfaces.</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Data Architecture</h3>
            </div>
            <div className="p-4 font-mono text-xs leading-relaxed bg-gray-900 text-gray-100 rounded-lg mx-4 my-4 overflow-x-auto">
              <pre>{`┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  H-34 Excel (37 pts)  │  Literature PDFs (12)  │  Registry YAML (9)     │
│         ↓             │          ↓              │         ↓              │
│    Excel Loader       │    PDF Extractor        │    YAML Loader         │
│         ↓             │          ↓              │         ↓              │
│  Unified Schema       │   Vector Store          │  Registry Agent        │
│  (Pydantic)           │   (ChromaDB)            │                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  DataAgent  │ RegistryAgent │ LiteratureAgent │ SafetyAgent │ RiskAgent │
│      ↓             ↓               ↓                ↓             ↓      │
│                    └───────────────┴────────────────┴─────────────┘      │
│                                    ↓                                     │
│                          SynthesisAgent (LLM)                            │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       ML/RISK SCORING                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Real + Synthetic Data (337)  →  Feature Extraction  →  XGBoost Model   │
│  Literature Hazard Ratios     →  RiskModel.predict() →  Ensemble Score  │
│                                                                          │
│  Final Risk = 60% ML Score + 40% HR Score → Risk Level (High/Med/Low)   │
└─────────────────────────────────────────────────────────────────────────┘`}</pre>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Source Attribution & Confidence</h3>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Source Type</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Tracked Metadata</th>
                    <th className="text-center py-2 text-gray-500 font-medium">Confidence Range</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="py-2 text-gray-800">STUDY_DATA</td>
                    <td className="py-2 text-gray-600 text-xs">Patient count, file source</td>
                    <td className="py-2 text-center font-mono text-gray-800">1.0</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">REGISTRY</td>
                    <td className="py-2 text-gray-600 text-xs">Abbreviation, year, n_procedures, data_years</td>
                    <td className="py-2 text-center font-mono text-gray-800">0.85-0.98</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">LITERATURE</td>
                    <td className="py-2 text-gray-600 text-xs">Citation, journal, year, n_patients</td>
                    <td className="py-2 text-center font-mono text-gray-800">0.80-0.95</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">ML_MODEL</td>
                    <td className="py-2 text-gray-600 text-xs">Training date, feature list, AUC</td>
                    <td className="py-2 text-center font-mono text-gray-800">0.54-0.70</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">PROTOCOL</td>
                    <td className="py-2 text-gray-600 text-xs">Protocol version, rule source</td>
                    <td className="py-2 text-center font-mono text-gray-800">1.0</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Key Data Files</h3>
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">File</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Location</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Contents</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono text-xs">
                  <tr>
                    <td className="py-2 text-gray-800">H-34DELTARevisionstudy_export_20250912.xlsx</td>
                    <td className="py-2 text-gray-600">/data/raw/study/</td>
                    <td className="py-2 text-gray-600">Real patient data</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">H-34_SYNTHETIC_PRODUCTION.xlsx</td>
                    <td className="py-2 text-gray-600">/data/processed/</td>
                    <td className="py-2 text-gray-600">Synthetic training data</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">registry_norms.yaml</td>
                    <td className="py-2 text-gray-600">/data/processed/document_as_code/</td>
                    <td className="py-2 text-gray-600">Registry benchmarks</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">literature_benchmarks.yaml</td>
                    <td className="py-2 text-gray-600">/data/processed/document_as_code/</td>
                    <td className="py-2 text-gray-600">Literature hazard ratios</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-800">risk_model.joblib</td>
                    <td className="py-2 text-gray-600">/data/ml/</td>
                    <td className="py-2 text-gray-600">Trained XGBoost model</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-4 flex items-start gap-3 border border-gray-200">
            <Info className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-gray-600">
              <p className="font-medium text-gray-700 mb-1">Production Deployment</p>
              <p>In production, this platform would integrate with validated clinical databases (EDC, CTMS, safety databases) through secure APIs with full audit trails, role-based access control, and 21 CFR Part 11 compliance.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const dataSources = [
    { id: 'h34-data', name: 'H-34 Study Data', icon: FileText, type: 'Structured', format: 'Excel', agents: ['data', 'safety', 'risk'] },
    { id: 'protocol-usdm', name: 'Protocol (USDM)', icon: FileText, type: 'Protocol-as-Code', format: 'JSON', agents: ['protocol'] },
    { id: 'literature', name: 'Literature PDFs', icon: BookOpen, type: 'Unstructured', format: 'PDF → Vectors', agents: ['literature'] },
    { id: 'registry', name: 'Registry Norms', icon: Globe, type: 'Curated', format: 'YAML', agents: ['registry'] },
    { id: 'vectorstore', name: 'Vector Store', icon: Layers, type: 'Embeddings', format: 'ChromaDB', agents: ['literature', 'protocol'] },
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

  const renderAgents = () => (
    <div className="space-y-8">
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
                        <Icon className="w-3.5 h-3.5 text-gray-600" />
                      </div>
                      <p className="text-[10px] font-semibold text-gray-800 leading-tight">{agent.shortName}</p>
                      <p className="text-[8px] text-gray-500 mt-0.5 leading-tight">{agent.desc}</p>
                      <div className="mt-1.5 flex flex-wrap justify-center gap-0.5">
                        {agent.tools.slice(0, 2).map((t) => (
                          <span key={t} className="text-[7px] px-1 py-0.5 bg-gray-100 text-gray-500 rounded">{t}</span>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="flex items-center justify-center w-full">
              <div className="flex-1 h-px bg-gray-300"></div>
              <ChevronRight className="w-4 h-4 text-gray-400 rotate-90 mx-2" />
              <div className="flex-1 h-px bg-gray-300"></div>
            </div>

            <div className="w-full max-w-2xl">
              <div className="bg-gray-600 text-white rounded-xl p-4 text-center border border-gray-500">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Network className="w-5 h-5" />
                  <span className="font-semibold">Orchestrator Agent</span>
                </div>
                <p className="text-xs text-gray-300">Task decomposition, agent routing, context management & response coordination</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center w-full">
              <div className="flex-1 h-px bg-gray-300"></div>
              <ChevronRight className="w-4 h-4 text-gray-400 rotate-90 mx-2" />
              <div className="flex-1 h-px bg-gray-300"></div>
            </div>
            
            <div className="w-full max-w-xl">
              <div className="bg-gray-500 text-white rounded-xl p-4 text-center border border-gray-400">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Sparkles className="w-5 h-5" />
                  <span className="font-semibold">Synthesis Agent</span>
                </div>
                <p className="text-xs text-gray-200">LLM-powered response synthesis, narrative generation & insight consolidation</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center w-full">
              <div className="flex-1 h-px bg-gray-200"></div>
              <ChevronRight className="w-4 h-4 text-gray-300 rotate-90 mx-2" />
              <div className="flex-1 h-px bg-gray-200"></div>
            </div>
            
            <div className="w-full border border-gray-200 rounded-xl p-4 bg-white">
              <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-3 font-semibold">User Interface Layer</p>
              <div className="w-full grid grid-cols-3 gap-2">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-center">
                  <Layers className="w-4 h-4 text-gray-500 mx-auto mb-1" />
                  <p className="text-[10px] font-medium text-gray-700">Dashboard</p>
                  <p className="text-[8px] text-gray-400">KPIs & visualizations</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-center">
                  <Search className="w-4 h-4 text-gray-500 mx-auto mb-1" />
                  <p className="text-[10px] font-medium text-gray-700">Chat Interface</p>
                  <p className="text-[8px] text-gray-400">Natural language Q&A</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-center">
                  <FileText className="w-4 h-4 text-gray-500 mx-auto mb-1" />
                  <p className="text-[10px] font-medium text-gray-700">Reports</p>
                  <p className="text-[8px] text-gray-400">Generated narratives</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900 text-sm">Agent Capabilities & Tool Usage</h3>
        </div>
        <div className="p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Agent</th>
                <th className="text-left py-2 text-gray-500 font-medium">Purpose</th>
                <th className="text-left py-2 text-gray-500 font-medium">Data Sources</th>
                <th className="text-left py-2 text-gray-500 font-medium">LLM/ML Tools</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {specialistAgents.map((agent) => {
                const agentSources = dataSources.filter(s => s.agents.includes(agent.id))
                return (
                  <tr key={agent.id}>
                    <td className="py-2 font-medium text-gray-800">{agent.name}</td>
                    <td className="py-2 text-gray-600 text-xs">{agent.desc}</td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-1">
                        {agentSources.map((s) => (
                          <span key={s.id} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-[10px] rounded">{s.name}</span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-1">
                        {agent.tools.map((t) => (
                          <span key={t} className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-[10px] rounded font-medium">{t}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">Agent Details</h3>
        {agents.map((agent) => {
          const Icon = agent.icon
          return (
            <div key={agent.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="p-4 flex items-start gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  agent.level === 0 ? 'bg-gray-600' : agent.level === 2 ? 'bg-gray-500' : 'bg-gray-100'
                }`}>
                  <Icon className={`w-6 h-6 ${agent.level === 0 || agent.level === 2 ? 'text-white' : 'text-gray-600'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                      agent.level === 0 ? 'bg-gray-600 text-white' : 
                      agent.level === 2 ? 'bg-gray-500 text-white' : 
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {agent.level === 0 ? 'COORDINATOR' : agent.level === 2 ? 'SYNTHESIS' : 'SPECIALIST'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{agent.description}</p>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-2">Capabilities</p>
                      <ul className="space-y-1">
                        {agent.capabilities.map((cap, i) => (
                          <li key={i} className="flex items-center gap-1.5 text-xs text-gray-700">
                            <ChevronRight className="w-3 h-3 text-gray-400" />
                            {cap}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-2">Inputs</p>
                      <ul className="space-y-1">
                        {agent.inputs.map((input, i) => (
                          <li key={i} className="text-xs text-gray-600 font-mono bg-gray-50 px-2 py-1 rounded">{input}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-2">Outputs</p>
                      <ul className="space-y-1">
                        {agent.outputs.map((output, i) => (
                          <li key={i} className="text-xs text-gray-600 font-mono bg-gray-50 px-2 py-1 rounded">{output}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="bg-gray-50 rounded-xl p-4 flex items-start gap-3 border border-gray-200">
        <Info className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
        <div className="text-xs text-gray-600">
          <p className="font-medium text-gray-700 mb-1">Agent Communication</p>
          <p>Agents communicate through a message-passing architecture. The Orchestrator routes requests to appropriate specialists, collects their outputs, and the Synthesis Agent generates coherent responses using the Gemini LLM.</p>
        </div>
      </div>
    </div>
  )

  return (
    <StudyLayout studyId={params.studyId}>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Data & Agents</h1>
          <p className="text-gray-500 mt-1">Data sources, AI models, and agent architecture</p>
        </div>

        <div className="flex gap-2 border-b border-gray-200 pb-4">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {activeTab === 'data' && renderDataSources()}
        {activeTab === 'agents' && renderAgents()}
      </div>
    </StudyLayout>
  )
}
