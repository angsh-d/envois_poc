import { useState, useCallback, useEffect } from 'react'
import { CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { RecommendationCard, RegistryItem, PaperItem } from './RecommendationCard'

interface WhyExplanationData {
  summary: string
  key_reasons: string[]
  unique_value: string
  inclusions?: Array<{ name: string; reason: string }>
  exclusions?: Array<{ name: string; reason: string }>
  selection_criteria?: string[]
  data_sources?: Array<{ name: string; description: string }>
}

interface DataSource {
  id: string
  type: 'clinical' | 'registry' | 'literature' | 'fda'
  name: string
  selected: boolean
  enabled_insights: string[]
  preview?: string
  data?: Record<string, unknown>
  whyExplanation?: WhyExplanationData
  confidence?: Record<string, unknown>
}

interface RegistryData {
  name: string
  region: string
  selected: boolean
  data_years?: string
  relevance?: string
  n_procedures?: number
  exclusion_reason?: string
}

interface PaperData {
  title: string
  journal: string
  year: number
  insight: string
  relevance_score?: number
  pmid?: string
  url?: string
}

interface DataSourceSelectorProps {
  recommendations: Record<string, unknown>
  onSelectionChange: (selectedSources: string[]) => void
  onRegistrySelectionChange?: (registrySelections: Record<string, boolean>) => void
  onPaperSelectionChange?: (paperSelections: Record<string, boolean>) => void
}

export function DataSourceSelector({
  recommendations,
  onSelectionChange,
  onRegistrySelectionChange,
  onPaperSelectionChange,
}: DataSourceSelectorProps) {
  // Parse recommendations into structured data sources
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [registrySelections, setRegistrySelections] = useState<Record<string, boolean>>({})
  const [paperSelections, setPaperSelections] = useState<Record<string, boolean>>({})

  // Initialize data sources from recommendations
  useEffect(() => {
    const sources: DataSource[] = []
    const regSelections: Record<string, boolean> = {}
    const papSelections: Record<string, boolean> = {}

    // Get why_explanations from recommendations (if available at top level)
    const whyExplanations = (recommendations?.why_explanations || {}) as Record<string, WhyExplanationData>

    // Clinical Study
    if (recommendations?.clinical_study) {
      const clinical = recommendations.clinical_study as Record<string, unknown>
      sources.push({
        id: 'clinical_study',
        type: 'clinical',
        name: (clinical.source as string) || 'Clinical Study Database',
        selected: true,
        enabled_insights: (clinical.enabled_insights as string[]) || [],
        preview: clinical.data_preview as string,
        data: clinical,
        whyExplanation: (clinical.why_explanation as WhyExplanationData) || whyExplanations.clinical_study,
        confidence: clinical.confidence as Record<string, unknown>,
      })
    }

    // Registries
    if (recommendations?.registries) {
      const registries = recommendations.registries as RegistryData[]
      const registriesWhyExplanation = (recommendations.registries_why_explanation as WhyExplanationData) || whyExplanations.registries
      sources.push({
        id: 'registries',
        type: 'registry',
        name: 'Registry Benchmarks',
        selected: true,
        enabled_insights: [
          'Benchmark comparison for revision rates',
          'Percentile ranking vs. global population',
          'Competitive positioning statements',
        ],
        data: { registries },
        whyExplanation: registriesWhyExplanation,
        confidence: recommendations.registries_confidence as Record<string, unknown>,
      })

      // Initialize individual registry selections
      registries.forEach((reg, i) => {
        const key = reg.name || `registry_${i}`
        regSelections[key] = reg.selected !== false && !reg.exclusion_reason
      })
    }

    // Literature
    if (recommendations?.literature) {
      const literature = recommendations.literature as Record<string, unknown>
      sources.push({
        id: 'literature',
        type: 'literature',
        name: 'Literature Knowledge Base',
        selected: true,
        enabled_insights: (literature.enabled_insights as string[]) || [],
        preview: `AI discovered ${(literature.total_papers as number) || 0} relevant publications`,
        data: literature,
        whyExplanation: (literature.why_explanation as WhyExplanationData) || whyExplanations.literature,
        confidence: literature.confidence as Record<string, unknown>,
      })

      // Initialize individual paper selections
      const papers = (literature.top_papers as PaperData[]) || []
      papers.forEach((paper, i) => {
        const key = paper.pmid || `paper_${i}`
        papSelections[key] = true
      })
    }

    // FDA Surveillance
    if (recommendations?.fda_surveillance) {
      const fda = recommendations.fda_surveillance as Record<string, unknown>
      sources.push({
        id: 'fda_surveillance',
        type: 'fda',
        name: 'FDA Surveillance',
        selected: true,
        enabled_insights: (fda.enabled_insights as string[]) || [],
        preview: fda.preview as string,
        data: fda,
        whyExplanation: (fda.why_explanation as WhyExplanationData) || whyExplanations.fda_surveillance,
        confidence: fda.confidence as Record<string, unknown>,
      })
    }

    setDataSources(sources)
    setRegistrySelections(regSelections)
    setPaperSelections(papSelections)
  }, [recommendations])

  // Notify parent of selection changes
  useEffect(() => {
    const selected = dataSources.filter(s => s.selected).map(s => s.id)
    onSelectionChange(selected)
  }, [dataSources, onSelectionChange])

  useEffect(() => {
    onRegistrySelectionChange?.(registrySelections)
  }, [registrySelections, onRegistrySelectionChange])

  useEffect(() => {
    onPaperSelectionChange?.(paperSelections)
  }, [paperSelections, onPaperSelectionChange])

  // Toggle data source selection
  const handleToggleSource = useCallback((sourceId: string, selected: boolean) => {
    setDataSources(prev =>
      prev.map(s => s.id === sourceId ? { ...s, selected } : s)
    )
  }, [])

  // Toggle individual registry selection
  const handleToggleRegistry = useCallback((registryName: string, selected: boolean) => {
    setRegistrySelections(prev => ({ ...prev, [registryName]: selected }))
  }, [])

  // Toggle individual paper selection
  const handleTogglePaper = useCallback((paperId: string, selected: boolean) => {
    setPaperSelections(prev => ({ ...prev, [paperId]: selected }))
  }, [])

  // Calculate selection summary
  const selectedCount = dataSources.filter(s => s.selected).length
  const totalCount = dataSources.length
  const selectedRegistries = Object.values(registrySelections).filter(Boolean).length
  const totalRegistries = Object.keys(registrySelections).length
  const selectedPapers = Object.values(paperSelections).filter(Boolean).length
  const totalPapers = Object.keys(paperSelections).length

  return (
    <div className="space-y-4">
      {/* Selection Summary */}
      <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-100 rounded-lg">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600" />
          <span className="text-sm text-blue-900">
            <strong>{selectedCount}</strong> of {totalCount} data sources selected
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-blue-700">
          {totalRegistries > 0 && (
            <span>{selectedRegistries}/{totalRegistries} registries</span>
          )}
          {totalPapers > 0 && (
            <span>{selectedPapers}/{totalPapers} papers</span>
          )}
        </div>
      </div>

      {/* Data Source Cards */}
      {dataSources.map(source => (
        <DataSourceCard
          key={source.id}
          source={source}
          onToggle={(selected) => handleToggleSource(source.id, selected)}
          registrySelections={registrySelections}
          onToggleRegistry={handleToggleRegistry}
          paperSelections={paperSelections}
          onTogglePaper={handleTogglePaper}
        />
      ))}

      {/* Minimum Selection Warning */}
      {selectedCount === 0 && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-amber-600" />
          <span className="text-sm text-amber-800">
            Please select at least one data source to continue.
          </span>
        </div>
      )}
    </div>
  )
}

// Individual data source card with granular selection
interface DataSourceCardProps {
  source: DataSource
  onToggle: (selected: boolean) => void
  registrySelections: Record<string, boolean>
  onToggleRegistry: (name: string, selected: boolean) => void
  paperSelections: Record<string, boolean>
  onTogglePaper: (id: string, selected: boolean) => void
}

function DataSourceCard({
  source,
  onToggle,
  registrySelections,
  onToggleRegistry,
  paperSelections,
  onTogglePaper,
}: DataSourceCardProps) {
  // Render children based on source type
  const renderChildren = () => {
    if (source.type === 'registry' && source.data?.registries) {
      const registries = source.data.registries as RegistryData[]
      return (
        <div className="mt-3 space-y-2">
          {registries.map((reg, i) => {
            const key = reg.name || `registry_${i}`
            const isExcluded = !!reg.exclusion_reason
            const isSelected = registrySelections[key] ?? (reg.selected !== false && !isExcluded)

            return (
              <SelectableRegistryItem
                key={key}
                name={reg.name}
                region={reg.region}
                selected={isSelected}
                dataYears={reg.data_years}
                relevance={reg.relevance}
                nProcedures={reg.n_procedures}
                excluded={isExcluded}
                exclusionReason={reg.exclusion_reason}
                onToggle={(selected) => onToggleRegistry(key, selected)}
                disabled={isExcluded}
              />
            )
          })}
        </div>
      )
    }

    if (source.type === 'literature' && source.data?.top_papers) {
      const papers = source.data.top_papers as PaperData[]
      return (
        <div className="mt-3 space-y-2">
          {papers.slice(0, 5).map((paper, i) => {
            const key = paper.pmid || `paper_${i}`
            const isSelected = paperSelections[key] ?? true

            return (
              <SelectablePaperItem
                key={key}
                title={paper.title}
                journal={paper.journal}
                year={paper.year}
                insight={paper.insight}
                relevanceScore={paper.relevance_score}
                pmid={paper.pmid}
                url={paper.url}
                selected={isSelected}
                onToggle={(selected) => onTogglePaper(key, selected)}
              />
            )
          })}
        </div>
      )
    }

    return null
  }

  return (
    <RecommendationCard
      title={source.name}
      type={source.type}
      selected={source.selected}
      onToggle={onToggle}
      enabledInsights={source.enabled_insights}
      preview={source.preview}
      whyExplanation={source.whyExplanation}
      confidence={source.confidence as { overall_score: number; level: 'HIGH' | 'MODERATE' | 'LOW' | 'INSUFFICIENT'; factors?: Record<string, number>; explanation?: string } | undefined}
    >
      {renderChildren()}
    </RecommendationCard>
  )
}

// Selectable registry item
interface SelectableRegistryItemProps {
  name: string
  region: string
  selected: boolean
  dataYears?: string
  relevance?: string
  nProcedures?: number
  excluded?: boolean
  exclusionReason?: string
  onToggle: (selected: boolean) => void
  disabled?: boolean
}

function SelectableRegistryItem({
  name,
  region,
  selected,
  dataYears,
  relevance,
  nProcedures,
  excluded,
  exclusionReason,
  onToggle,
  disabled,
}: SelectableRegistryItemProps) {
  const [showWhyTooltip, setShowWhyTooltip] = useState(false)

  return (
    <div className={`
      flex items-center gap-3 p-2.5 rounded-lg transition-colors
      ${excluded ? 'bg-gray-50 opacity-60' : selected ? 'bg-white border border-emerald-100 hover:border-emerald-200' : 'bg-gray-50 hover:bg-gray-100'}
      ${!disabled ? 'cursor-pointer' : 'cursor-not-allowed'}
    `}
    onClick={() => !disabled && onToggle(!selected)}
    >
      <button
        type="button"
        disabled={disabled}
        className={`
          w-5 h-5 rounded border-2 flex items-center justify-center transition-colors flex-shrink-0
          ${selected && !excluded ? 'border-emerald-500 bg-emerald-50' : 'border-gray-300 bg-white'}
          ${disabled ? 'opacity-50' : 'hover:border-emerald-400'}
        `}
        onClick={(e) => {
          e.stopPropagation()
          if (!disabled) onToggle(!selected)
        }}
      >
        {selected && !excluded && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />}
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-sm font-medium ${excluded ? 'text-gray-500' : 'text-gray-900'}`}>{name}</span>
          <span className="text-xs text-gray-400">({region})</span>
          {nProcedures && (
            <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              {nProcedures.toLocaleString()} procedures
            </span>
          )}
        </div>
        {dataYears && (
          <span className="text-xs text-gray-500 block">{dataYears}</span>
        )}
        {relevance && !excluded && (
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-blue-600">{relevance}</span>
            <div className="relative">
              <button
                type="button"
                onMouseEnter={() => setShowWhyTooltip(true)}
                onMouseLeave={() => setShowWhyTooltip(false)}
                onClick={(e) => e.stopPropagation()}
                className="text-xs text-gray-400 hover:text-blue-600"
              >
                Why?
              </button>
              {showWhyTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
                  <span className="font-medium">Included because:</span> {relevance}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
                </div>
              )}
            </div>
          </div>
        )}
        {excluded && exclusionReason && (
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-amber-600">{exclusionReason}</span>
            <div className="relative">
              <button
                type="button"
                onMouseEnter={() => setShowWhyTooltip(true)}
                onMouseLeave={() => setShowWhyTooltip(false)}
                onClick={(e) => e.stopPropagation()}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Why excluded?
              </button>
              {showWhyTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
                  <span className="font-medium">Excluded:</span> {exclusionReason}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Selectable paper item
interface SelectablePaperItemProps {
  title: string
  journal: string
  year: number
  insight: string
  relevanceScore?: number
  pmid?: string
  url?: string
  selected: boolean
  onToggle: (selected: boolean) => void
}

function SelectablePaperItem({
  title,
  journal,
  year,
  insight,
  relevanceScore,
  pmid,
  url,
  selected,
  onToggle,
}: SelectablePaperItemProps) {
  const [showWhyTooltip, setShowWhyTooltip] = useState(false)

  return (
    <div
      className={`
        p-3 rounded-lg border transition-colors cursor-pointer
        ${selected ? 'bg-white border-gray-200 hover:border-emerald-300' : 'bg-gray-50 border-gray-100 hover:bg-gray-100'}
      `}
      onClick={() => onToggle(!selected)}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          className={`
            w-4 h-4 rounded border-2 flex items-center justify-center transition-colors flex-shrink-0 mt-0.5
            ${selected ? 'border-emerald-500 bg-emerald-50' : 'border-gray-300 bg-white hover:border-emerald-400'}
          `}
          onClick={(e) => {
            e.stopPropagation()
            onToggle(!selected)
          }}
        >
          {selected && <CheckCircle2 className="w-3 h-3 text-emerald-500" />}
        </button>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium line-clamp-2 ${selected ? 'text-gray-900' : 'text-gray-500'}`}>
            {title}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">{journal}, {year}</p>
          <div className="flex items-center gap-2 mt-1">
            <p className={`text-xs ${selected ? 'text-blue-600' : 'text-gray-400'}`}>{insight}</p>
            <div className="relative">
              <button
                type="button"
                onMouseEnter={() => setShowWhyTooltip(true)}
                onMouseLeave={() => setShowWhyTooltip(false)}
                onClick={(e) => e.stopPropagation()}
                className="text-xs text-gray-400 hover:text-blue-600"
              >
                Why?
              </button>
              {showWhyTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2 bg-gray-800 text-white text-xs rounded shadow-lg">
                  <span className="font-medium">Selected because:</span> {insight}
                  {relevanceScore && (
                    <p className="mt-1 text-gray-300">Relevance score: {Math.round(relevanceScore * 100)}%</p>
                  )}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45" />
                </div>
              )}
            </div>
          </div>
          {pmid && (
            <a
              href={url || `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-xs text-gray-400 hover:text-blue-600 mt-1 inline-block"
            >
              PMID: {pmid}
            </a>
          )}
        </div>
        {relevanceScore !== undefined && (
          <div className={`
            flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium
            ${relevanceScore >= 0.8 ? 'bg-emerald-50 text-emerald-700' :
              relevanceScore >= 0.6 ? 'bg-blue-50 text-blue-700' :
              selected ? 'bg-gray-100 text-gray-600' : 'bg-gray-100 text-gray-500'}
          `}>
            {Math.round(relevanceScore * 100)}%
          </div>
        )}
      </div>
    </div>
  )
}

// Export types for use in parent components
export type { DataSource, RegistryData, PaperData }
