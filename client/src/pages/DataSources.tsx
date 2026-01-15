import { useState } from 'react'
import StudyLayout from './StudyLayout'
import {
  Database,
  FileText,
  BookOpen,
  Globe,
  CheckCircle,
  Beaker,
  Sparkles,
  Info,
  GitBranch
} from 'lucide-react'

interface DataSourcesProps {
  params: { studyId: string }
}

type DataSubTab = 'real' | 'synthetic' | 'models' | 'lineage'

export default function DataSources({ params }: DataSourcesProps) {
  const [dataSubTab, setDataSubTab] = useState<DataSubTab>('real')

  const dataSubTabs = [
    { id: 'real' as const, label: 'Real Data', icon: CheckCircle },
    { id: 'synthetic' as const, label: 'Synthetic Data', icon: Beaker },
    { id: 'models' as const, label: 'AI & ML Models', icon: Sparkles },
    { id: 'lineage' as const, label: 'Data Lineage', icon: GitBranch },
  ]

  return (
    <StudyLayout studyId={params.studyId} chatContext="data-sources">
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Data Sources</h1>
          <p className="text-gray-500 mt-1">Clinical data, literature, and registry benchmarks</p>
        </div>

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
              </div>
            </div>
          </div>
        )}

        {dataSubTab === 'synthetic' && (
          <div className="space-y-6">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Beaker className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">Synthetic Data</h3>
              </div>
              <p className="text-sm text-amber-800">These data sources were generated synthetically for demonstration, testing, or when real data was not available. They are clearly marked and not used for actual clinical decisions.</p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">Synthetic Data Summary</h3>
                  <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded">SYNTHETIC</span>
                </div>
              </div>
              <div className="p-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 text-gray-500 font-medium">Data Source</th>
                      <th className="text-center py-2 text-gray-500 font-medium">Type</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-800">Safety Signals</td>
                      <td className="py-2 text-center"><span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">SYNTHETIC</span></td>
                      <td className="py-2 text-gray-600">Simulated adverse event patterns</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-800">Protocol Deviations</td>
                      <td className="py-2 text-center"><span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">SYNTHETIC</span></td>
                      <td className="py-2 text-gray-600">Example protocol deviation scenarios</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-800">Risk Predictions</td>
                      <td className="py-2 text-center"><span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">SYNTHETIC</span></td>
                      <td className="py-2 text-gray-600">Model outputs based on synthetic patient features</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {dataSubTab === 'models' && (
          <div className="space-y-6">
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-900">AI & ML Models</h3>
              </div>
              <p className="text-sm text-gray-600">Overview of language models, machine learning models, and AI capabilities used in the platform.</p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">Foundation Models (LLMs)</h3>
              </div>
              <div className="p-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 text-gray-500 font-medium">Model</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Provider</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Use Case</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-800">Gemini 2.5 Pro</td>
                      <td className="py-2 text-gray-600">Google</td>
                      <td className="py-2 text-gray-600">Document extraction, complex reasoning, synthesis</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-800">text-embedding-004</td>
                      <td className="py-2 text-gray-600">Google</td>
                      <td className="py-2 text-gray-600">Semantic search, vector embeddings</td>
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
│  H-34 Excel (37 pts)  │  Literature PDFs (4)   │  Registry YAML (9)     │
│         ↓             │          ↓              │         ↓              │
│    Excel Loader       │    PDF Extractor        │    YAML Loader         │
│         ↓             │          ↓              │         ↓              │
│  Unified Schema       │   Vector Store          │  Registry Agent        │
│  (Pydantic)           │   (pgvector)            │                        │
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
│                           USER INTERFACES                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Executive Dashboard │ Readiness │ Safety │ Deviations │ Risk │ Chat   │
└─────────────────────────────────────────────────────────────────────────┘`}</pre>
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
                      <th className="text-left py-2 text-gray-500 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-800">literature_benchmarks.yaml</td>
                      <td className="py-2 text-gray-600">/data/processed/document_as_code/</td>
                      <td className="py-2 text-gray-600">Literature benchmarks with provenance</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-800">registry_norms.yaml</td>
                      <td className="py-2 text-gray-600">/data/processed/document_as_code/</td>
                      <td className="py-2 text-gray-600">Registry benchmarks (9 registries)</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-800">protocol_rules.yaml</td>
                      <td className="py-2 text-gray-600">/data/processed/document_as_code/</td>
                      <td className="py-2 text-gray-600">Protocol-as-code rules</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </StudyLayout>
  )
}
