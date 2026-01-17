import { Download, ExternalLink, CheckCircle2, Database, BookOpen, Shield, FileText } from 'lucide-react'

interface IntelligenceBriefProps {
  productName: string
  protocolId: string
  category: string
  indication: string
  dataSources: {
    clinical_db?: { patients: number; configured: boolean }
    registries?: { count: number; configured: boolean }
    fda_surveillance?: { configured: boolean }
  }
  knowledgeBase: {
    publications: number
    ifu_labeling: boolean
    protocol: boolean
  }
  generatedReports: Array<{ name: string; pages: number; status: string }>
  enabledModules: string[]
}

export function IntelligenceBrief({
  productName,
  protocolId,
  category,
  indication,
  dataSources,
  knowledgeBase,
  generatedReports,
  enabledModules,
}: IntelligenceBriefProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-4">
        <div className="flex items-center gap-2 text-white/80 text-sm mb-1">
          <CheckCircle2 className="w-4 h-4" />
          Configuration Complete
        </div>
        <h2 className="text-xl font-bold text-white">{productName}</h2>
        <p className="text-emerald-100 text-sm mt-1">
          Protocol {protocolId} | {category} | {indication}
        </p>
      </div>

      {/* Content Grid */}
      <div className="p-6 grid grid-cols-2 gap-6">
        {/* Data Sources */}
        <div>
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Data Sources</h3>
          <ul className="space-y-2">
            {dataSources.clinical_db?.configured && (
              <li className="flex items-center gap-2 text-sm text-gray-700">
                <Database className="w-4 h-4 text-gray-400" />
                Clinical DB (n={dataSources.clinical_db.patients})
              </li>
            )}
            {dataSources.registries?.configured && (
              <li className="flex items-center gap-2 text-sm text-gray-700">
                <Database className="w-4 h-4 text-gray-400" />
                {dataSources.registries.count} registries
              </li>
            )}
            {dataSources.fda_surveillance?.configured && (
              <li className="flex items-center gap-2 text-sm text-gray-700">
                <Shield className="w-4 h-4 text-gray-400" />
                FDA MAUDE
              </li>
            )}
          </ul>
        </div>

        {/* Knowledge Base */}
        <div>
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Knowledge Base</h3>
          <ul className="space-y-2">
            <li className="flex items-center gap-2 text-sm text-gray-700">
              <BookOpen className="w-4 h-4 text-gray-400" />
              {knowledgeBase.publications} key publications
            </li>
            {knowledgeBase.ifu_labeling && (
              <li className="flex items-center gap-2 text-sm text-gray-700">
                <FileText className="w-4 h-4 text-gray-400" />
                IFU & labeling
              </li>
            )}
            {knowledgeBase.protocol && (
              <li className="flex items-center gap-2 text-sm text-gray-700">
                <FileText className="w-4 h-4 text-gray-400" />
                Protocol {protocolId}
              </li>
            )}
          </ul>
        </div>
      </div>

      {/* Generated Reports */}
      <div className="px-6 pb-6">
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Generated Reports</h3>
        <div className="grid grid-cols-3 gap-3">
          {generatedReports.map((report, i) => (
            <div key={i} className="bg-gray-50 border border-gray-100 rounded-lg p-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{report.name}</p>
                  <p className="text-xs text-gray-500">{report.pages} pages</p>
                </div>
                <button className="p-1.5 hover:bg-gray-200 rounded transition-colors">
                  <Download className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Enabled Modules */}
      <div className="px-6 pb-6">
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Enabled Modules</h3>
        <div className="flex flex-wrap gap-2">
          {enabledModules.map((module, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 border border-emerald-100 rounded-lg text-sm text-emerald-700"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {module}
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex gap-3">
        <button className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors">
          <Download className="w-4 h-4" />
          Download Intelligence Brief
        </button>
        <button className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors">
          Go to Product Dashboard
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
