import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, StatCard } from '@/components/Card'
import { Badge } from '@/components/Badge'
import {
  fetchDashboardExecutiveSummary,
  fetchDashboardStudyProgress,
  fetchDashboardBenchmarks,
  type DashboardExecutiveSummary,
  type DashboardStudyProgress,
  type DashboardBenchmarks
} from '@/lib/api'
import { useRoute } from 'wouter'
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Database,
  X,
  BookOpen,
  Globe,
  FileText,
  Beaker,
  Info
} from 'lucide-react'

// Tab type for Data Catalog
type DataCatalogTab = 'real' | 'synthetic' | 'models' | 'lineage'

// Data Catalog Modal Component - Comprehensive, accurate data documentation
function DataSourcesModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<DataCatalogTab>('real')

  if (!isOpen) return null

  const tabs = [
    { id: 'real' as const, label: 'Real Data', icon: CheckCircle, color: 'text-gray-700' },
    { id: 'synthetic' as const, label: 'Synthetic Data', icon: Beaker, color: 'text-gray-700' },
    { id: 'models' as const, label: 'AI & ML Models', icon: Sparkles, color: 'text-gray-700' },
    { id: 'lineage' as const, label: 'Data Lineage', icon: Database, color: 'text-gray-700' },
  ]

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[92vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Data Catalog</h2>
              <p className="text-sm text-gray-500">Complete inventory of data sources, AI/ML models, and data lineage</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 py-3 border-b border-gray-100 bg-gray-50">
          <div className="flex gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-white shadow-sm border border-gray-200 text-gray-900'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${activeTab === tab.id ? tab.color : ''}`} />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(92vh-140px)]">

          {/* ========== TAB 1: REAL DATA ========== */}
          {activeTab === 'real' && (
            <div className="space-y-6">
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Real Data Sources</h3>
                </div>
                <p className="text-sm text-gray-600">These data sources contain real, provided data from actual clinical studies, published literature, and curated registry reports.</p>
              </div>

              {/* H-34 Study Data */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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

              {/* Literature Data */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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
                      <div className="text-2xl font-bold text-gray-900">12</div>
                      <div className="text-xs text-gray-500">Peer-reviewed PDFs indexed</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-gray-900">11.8 MB</div>
                      <div className="text-xs text-gray-500">Total literature corpus</div>
                    </div>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 text-gray-500 font-medium">Publication</th>
                        <th className="text-left py-2 text-gray-500 font-medium">Key Benchmarks Extracted</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      <tr>
                        <td className="py-2 text-gray-800">Bozic 2015 (n=51,345)</td>
                        <td className="py-2 text-gray-600 text-xs">2yr revision: 6.2%, hazard ratios for age, BMI, diabetes</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-800">Della Valle 2020 (n=892)</td>
                        <td className="py-2 text-gray-600 text-xs">Severe bone loss HR: 2.15, Osteoporosis HR: 2.42</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-800">Lombardi 2018 (n=456)</td>
                        <td className="py-2 text-gray-600 text-xs">Paprosky 3B defect HR: 2.85, Smoking HR: 1.52</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-800">Berry 2022 (n=1,247)</td>
                        <td className="py-2 text-gray-600 text-xs">RA HR: 1.68, CKD HR: 1.92</td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-800">+ 8 more publications</td>
                        <td className="py-2 text-gray-600 text-xs">Dixon 2025, Harris 2025, Kinoshita, Meding 2025, etc.</td>
                      </tr>
                    </tbody>
                  </table>
                  <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                    <strong>Storage:</strong> literature_benchmarks.yaml (curated), ChromaDB vector store (semantic search)
                  </div>
                </div>
              </div>

              {/* Registry Data */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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
                    Values curated from official annual reports of international joint replacement registries. Stored in <code className="text-xs bg-gray-100 px-1 rounded">registry_norms.yaml</code>.
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 text-gray-500 font-medium">Registry</th>
                          <th className="text-left py-2 text-gray-500 font-medium">Region</th>
                          <th className="text-right py-2 text-gray-500 font-medium">Procedures</th>
                          <th className="text-left py-2 text-gray-500 font-medium">Data Years</th>
                          <th className="text-left py-2 text-gray-500 font-medium">Metrics Available</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        <tr>
                          <td className="py-2 font-medium text-gray-800">AOANJRR</td>
                          <td className="py-2 text-gray-600">Australia</td>
                          <td className="py-2 text-right text-gray-800">45,892</td>
                          <td className="py-2 text-gray-600">1999-2023</td>
                          <td className="py-2 text-gray-600 text-xs">Survival (1-15yr), revision rates, reasons</td>
                        </tr>
                        <tr>
                          <td className="py-2 font-medium text-gray-800">NJR</td>
                          <td className="py-2 text-gray-600">UK</td>
                          <td className="py-2 text-right text-gray-800">38,456</td>
                          <td className="py-2 text-gray-600">2003-2023</td>
                          <td className="py-2 text-gray-600 text-xs">Survival, outcomes, implant tracking</td>
                        </tr>
                        <tr>
                          <td className="py-2 font-medium text-gray-800">SHAR</td>
                          <td className="py-2 text-gray-600">Sweden</td>
                          <td className="py-2 text-right text-gray-800">~25,000</td>
                          <td className="py-2 text-gray-600">1979-2023</td>
                          <td className="py-2 text-gray-600 text-xs">Long-term survival, PROMs</td>
                        </tr>
                        <tr>
                          <td className="py-2 font-medium text-gray-800">AJRR</td>
                          <td className="py-2 text-gray-600">USA</td>
                          <td className="py-2 text-right text-gray-800">~89,000</td>
                          <td className="py-2 text-gray-600">2012-2023</td>
                          <td className="py-2 text-gray-600 text-xs">Revision rates, complications</td>
                        </tr>
                        <tr>
                          <td className="py-2 font-medium text-gray-800">CJRR</td>
                          <td className="py-2 text-gray-600">Canada</td>
                          <td className="py-2 text-right text-gray-800">~15,000</td>
                          <td className="py-2 text-gray-600">2001-2023</td>
                          <td className="py-2 text-gray-600 text-xs">Revision rates, hospital outcomes</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                    <strong>Note:</strong> These are curated benchmark values from published registry reports, not live API connections.
                  </div>
                </div>
              </div>

              {/* Protocol Rules */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <h3 className="font-semibold text-gray-900">Protocol Rules</h3>
                    </div>
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">REAL DATA</span>
                  </div>
                </div>
                <div className="p-4 text-sm text-gray-600">
                  Protocol rules extracted from H-34 protocol PDF and stored in YAML. Used for visit window validation and deviation detection.
                </div>
              </div>
            </div>
          )}

          {/* ========== TAB 2: SYNTHETIC DATA ========== */}
          {activeTab === 'synthetic' && (
            <div className="space-y-6">
              <div className="bg-gray-100 border border-gray-300 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Synthetic Data Disclosure</h3>
                </div>
                <p className="text-sm text-gray-700">The following data is synthetically generated by this application. All synthetic records are marked with <code className="bg-gray-200 px-1 rounded text-xs">is_synthetic=True</code> for full transparency.</p>
              </div>

              {/* Synthetic Patient Data */}
              <div className="border border-gray-200 rounded-xl overflow-hidden bg-gray-50/50">
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
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">Demographics</p>
                        <p className="text-xs text-gray-600">Randomized within real data ranges</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">HHS Trajectory</p>
                        <p className="text-xs text-gray-600">Recovery curve model with individual variation</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">Adverse Events</p>
                        <p className="text-xs text-gray-600">35% AE rate, 80% serious (literature-aligned)</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">Revision Rate</p>
                        <p className="text-xs text-gray-600">8% (aligned with literature benchmarks)</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">Follow-up Completion</p>
                        <p className="text-xs text-gray-600">85% at 2mo → 45% at 2yr (realistic dropout)</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="font-medium text-gray-800 text-sm">Transparency Flag</p>
                        <p className="text-xs text-gray-600">All records marked is_synthetic=True</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>


              {/* Summary */}
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
                      <td className="py-2 text-gray-600">5 registries, 218K+ procedures</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ========== TAB 3: AI & ML MODELS ========== */}
          {activeTab === 'models' && (
            <div className="space-y-6">
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-semibold text-indigo-900">AI & ML Architecture</h3>
                </div>
                <p className="text-sm text-indigo-800">This platform uses an ensemble of foundation LLMs combined with traditional machine learning for risk prediction.</p>
              </div>

              {/* LLM Ensemble */}
              <div className="border border-indigo-200 rounded-xl overflow-hidden">
                <div className="bg-indigo-50 px-4 py-3 border-b border-indigo-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-indigo-600" />
                      <h3 className="font-semibold text-indigo-900">Foundation LLM Ensemble</h3>
                    </div>
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded">RAG Architecture</span>
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

              {/* XGBoost Risk Model */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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

              {/* Hazard Ratio Ensemble */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-gray-600" />
                      <h3 className="font-semibold text-gray-900">Literature Hazard Ratio Ensemble</h3>
                    </div>
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">Statistical</span>
                  </div>
                </div>
                <div className="p-4">
                  <p className="text-sm text-gray-600 mb-4">Published hazard ratios extracted from peer-reviewed literature via RAG + LLM, combined statistically for risk scoring.</p>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 text-gray-500 font-medium">Risk Factor</th>
                        <th className="text-right py-2 text-gray-500 font-medium">Hazard Ratio</th>
                        <th className="text-left py-2 text-gray-500 font-medium">Source</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      <tr><td className="py-1.5 text-gray-800">Age &gt;80</td><td className="py-1.5 text-right font-mono text-gray-800">1.45</td><td className="py-1.5 text-gray-500 text-xs">Bozic 2015</td></tr>
                      <tr><td className="py-1.5 text-gray-800">BMI &gt;35</td><td className="py-1.5 text-right font-mono text-gray-800">1.38</td><td className="py-1.5 text-gray-500 text-xs">Bozic 2015</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Severe bone loss</td><td className="py-1.5 text-right font-mono text-gray-800">2.15</td><td className="py-1.5 text-gray-500 text-xs">Della Valle 2020</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Osteoporosis</td><td className="py-1.5 text-right font-mono text-gray-800">2.42</td><td className="py-1.5 text-gray-500 text-xs">Della Valle 2020</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Paprosky 3B defect</td><td className="py-1.5 text-right font-mono text-gray-800">2.85</td><td className="py-1.5 text-gray-500 text-xs">Lombardi 2018</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Smoking</td><td className="py-1.5 text-right font-mono text-gray-800">1.52</td><td className="py-1.5 text-gray-500 text-xs">Lombardi 2018</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Rheumatoid arthritis</td><td className="py-1.5 text-right font-mono text-gray-800">1.68</td><td className="py-1.5 text-gray-500 text-xs">Berry 2022</td></tr>
                      <tr><td className="py-1.5 text-gray-800">Chronic kidney disease</td><td className="py-1.5 text-right font-mono text-gray-800">1.92</td><td className="py-1.5 text-gray-500 text-xs">Berry 2022</td></tr>
                    </tbody>
                  </table>
                  <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
                    <strong>Ensemble Formula:</strong> Final Risk = 60% × ML Score + 40% × HR Score
                  </div>
                </div>
              </div>

              {/* No Deep Learning */}
              <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-5 h-5 text-gray-400" />
                  <h4 className="font-medium text-gray-700">Deep Learning</h4>
                </div>
                <p className="text-sm text-gray-600">No custom deep learning models (neural networks, transformers, CNNs) are used. ChromaDB uses text-embedding-004 for vector indexing only.</p>
              </div>
            </div>
          )}

          {/* ========== TAB 4: DATA LINEAGE ========== */}
          {activeTab === 'lineage' && (
            <div className="space-y-6">
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Data Flow & Lineage</h3>
                </div>
                <p className="text-sm text-gray-600">How data flows from sources through processing to AI agents and user interfaces.</p>
              </div>

              {/* Data Flow Diagram */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-900">Data Architecture</h3>
                </div>
                <div className="p-4 font-mono text-xs leading-relaxed bg-gray-900 text-gray-100 rounded-lg mx-4 my-4 overflow-x-auto">
                  <pre>{`┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  H-34 Excel (37 pts)  │  Literature PDFs (12)  │  Registry YAML (5)     │
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

              {/* Source Attribution */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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

              {/* File Inventory */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
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

              {/* Production Note */}
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
      </div>
    </div>
  )
}

// Helper functions to convert API status to UI status
function statusToVariant(status: string): 'success' | 'warning' | 'danger' {
  switch (status?.toUpperCase()) {
    case 'GREEN':
      return 'success'
    case 'YELLOW':
      return 'warning'
    case 'RED':
      return 'danger'
    default:
      return 'warning'
  }
}

function formatMetricValue(value: number | undefined, type: string): string {
  if (value === undefined || value === null) return 'N/A'
  if (type.includes('rate') || type.includes('survival') || type.includes('achievement')) {
    return `${(value * 100).toFixed(1)}%`
  }
  if (type.includes('improvement')) {
    return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1)
  }
  return value.toFixed(1)
}

function getComparisonStatus(status: string | undefined): 'success' | 'warning' | 'danger' {
  switch (status) {
    case 'favorable':
      return 'success'
    case 'acceptable':
      return 'warning'
    case 'concerning':
      return 'danger'
    default:
      return 'warning'
  }
}

export default function Dashboard() {
  const [, params] = useRoute('/study/:studyId')
  const studyId = params?.studyId || 'h34-delta'
  const [showDataSources, setShowDataSources] = useState(false)

  // Fetch executive summary (overall status, metrics, priorities, narrative)
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardExecutiveSummary,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  // Fetch study progress (enrollment data)
  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['dashboard-progress'],
    queryFn: fetchDashboardStudyProgress,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  // Fetch benchmarks (comparison table)
  const { data: benchmarks, isLoading: benchmarksLoading } = useQuery({
    queryKey: ['dashboard-benchmarks'],
    queryFn: fetchDashboardBenchmarks,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const isLoading = summaryLoading || progressLoading || benchmarksLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-gray-800 rounded-full" />
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-600">
        <AlertTriangle className="w-6 h-6 mr-2" />
        <span>Failed to load dashboard data. Please check the backend is running.</span>
      </div>
    )
  }

  // Extract KPIs from metrics array
  const metricsMap = (summary?.metrics || []).reduce((acc, m) => {
    acc[m.name] = m
    return acc
  }, {} as Record<string, { name: string; value: string; status: string; trend: string }>)

  const readinessMetric = metricsMap['Regulatory Readiness'] || { value: 'N/A', status: 'YELLOW' }
  const safetyMetric = metricsMap['Safety Signals'] || { value: 'N/A', status: 'GREEN' }
  const complianceMetric = metricsMap['Protocol Compliance'] || { value: 'N/A', status: 'GREEN' }
  const enrollmentMetric = metricsMap['Enrollment'] || { value: 'N/A', status: 'YELLOW' }

  // Build benchmark rows from real data
  const benchmarkRows = buildBenchmarkRows(benchmarks)

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* Data Sources Modal */}
      <DataSourcesModal isOpen={showDataSources} onClose={() => setShowDataSources(false)} />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-gray-500 mt-1">H-34 DELTA Revision Cup Study Overview</p>
        </div>
        <button
          onClick={() => setShowDataSources(true)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
        >
          <Database className="w-4 h-4" />
          <span>Data Sources</span>
        </button>
      </div>

      <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">AI Summary</h3>
            <p className="text-gray-600 leading-relaxed">{summary?.narrative || summary?.headline || 'Loading...'}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Readiness"
          value={readinessMetric.value}
          status={statusToVariant(readinessMetric.status)}
        />
        <StatCard
          label="Safety Signals"
          value={safetyMetric.value}
          status={statusToVariant(safetyMetric.status)}
        />
        <StatCard
          label="Compliance"
          value={complianceMetric.value}
          status={statusToVariant(complianceMetric.status)}
        />
        <StatCard
          label="Enrollment"
          value={enrollmentMetric.value}
          status={statusToVariant(enrollmentMetric.status)}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader
            title="Enrollment Progress"
            subtitle={`${progress?.current_enrollment || 0}/${progress?.target_enrollment || 50} patients`}
          />
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium text-gray-800">{Math.round(progress?.enrollment_pct || 0)}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-gray-700 to-gray-900 rounded-full transition-all duration-500"
                style={{ width: `${progress?.enrollment_pct || 0}%` }}
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Attention Required"
            action={<Badge variant="danger">{summary?.top_priorities?.length || 0} items</Badge>}
          />
          <div className="space-y-3 mt-2">
            {(summary?.top_priorities || []).slice(0, 3).map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                <AlertTriangle className={`w-5 h-5 flex-shrink-0 ${
                  item.priority === 1 ? 'text-gray-700' :
                  item.priority === 2 ? 'text-gray-500' : 'text-gray-400'
                }`} />
                <div>
                  <p className="font-medium text-gray-800 text-sm">{item.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                </div>
              </div>
            ))}
            {(!summary?.top_priorities || summary.top_priorities.length === 0) && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl text-gray-700">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm">No critical action items</span>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Benchmarking" subtitle="H-34 performance vs literature and registry data" />
        <table className="w-full mt-4">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Metric</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">H-34</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Benchmark</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Source</th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarkRows.map((row, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0">
                <td className="py-3 px-4 text-sm font-medium text-gray-800">{row.metric}</td>
                <td className="py-3 px-4 text-sm text-center font-semibold text-gray-900">{row.studyValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.benchmarkValue}</td>
                <td className="py-3 px-4 text-sm text-center text-gray-500">{row.source}</td>
                <td className="py-3 px-4 text-center">
                  {row.status === 'success' ? (
                    <CheckCircle className="w-5 h-5 text-gray-600 mx-auto" />
                  ) : row.status === 'warning' ? (
                    <TrendingUp className="w-5 h-5 text-gray-500 mx-auto" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-gray-700 mx-auto" />
                  )}
                </td>
              </tr>
            ))}
            {benchmarkRows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500">
                  No benchmark comparisons available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

// Helper to build benchmark table rows from API data
function buildBenchmarkRows(benchmarks: DashboardBenchmarks | undefined): Array<{
  metric: string
  studyValue: string
  benchmarkValue: string
  source: string
  status: 'success' | 'warning' | 'danger'
}> {
  if (!benchmarks?.comparisons) return []

  return benchmarks.comparisons
    .filter(c => c.study_value !== undefined && c.study_value !== null)
    .slice(0, 6) // Limit to 6 rows for UI
    .map(c => {
      // Format metric name for display
      let metricName = c.metric
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())

      // Format study value
      let studyValue: string
      if (c.metric.includes('rate') || c.metric.includes('survival') || c.metric.includes('achievement')) {
        studyValue = `${((c.study_value || 0) * 100).toFixed(1)}%`
      } else if (c.metric.includes('improvement')) {
        studyValue = c.study_value && c.study_value > 0 ? `+${c.study_value.toFixed(1)}` : `${c.study_value?.toFixed(1)}`
      } else {
        studyValue = c.study_value?.toFixed(1) || 'N/A'
      }

      // Format benchmark value
      let benchmarkValue: string
      if (c.benchmark_value !== undefined && c.benchmark_value !== null) {
        if (c.metric.includes('rate') || c.metric.includes('survival')) {
          benchmarkValue = `${((c.benchmark_value || 0) * 100).toFixed(1)}%`
        } else if (c.metric.includes('improvement')) {
          benchmarkValue = c.benchmark_value > 0 ? `+${c.benchmark_value.toFixed(1)}` : c.benchmark_value.toFixed(1)
        } else {
          benchmarkValue = c.benchmark_value.toFixed(1)
        }
        if (c.benchmark_range && c.benchmark_range.length === 2) {
          const [min, max] = c.benchmark_range
          if (c.metric.includes('rate') || c.metric.includes('survival')) {
            benchmarkValue += ` (${(min * 100).toFixed(0)}-${(max * 100).toFixed(0)}%)`
          } else {
            benchmarkValue += ` (${min.toFixed(0)}-${max.toFixed(0)})`
          }
        }
      } else {
        benchmarkValue = 'N/A'
      }

      return {
        metric: metricName,
        studyValue,
        benchmarkValue,
        source: c.source || 'Unknown',
        status: getComparisonStatus(c.comparison_status),
      }
    })
}
