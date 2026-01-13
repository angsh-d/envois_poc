import { useQuery } from '@tanstack/react-query'
import StudyLayout from './StudyLayout'
import { useState } from 'react'
import {
  Check, X, ChevronDown, ChevronRight, Database, GitBranch,
  Target, AlertTriangle, Shield, Pill, TestTube, FlaskConical,
  FileSignature, ClipboardList, Building, CheckCircle, LogOut,
  Scan, Activity, Users, Beaker, FileText, Heart, Stethoscope,
  Clock, Leaf, Syringe, Download
} from 'lucide-react'

interface StudyProtocolProps {
  params: { studyId: string }
}

interface Overview {
  protocol_id: string
  protocol_name: string
  official_title: string
  version: string
  study_type: string
  study_phase: string
  source_document: {
    filename: string
    page_count: number
  }
  extraction_metadata: {
    timestamp: string
    pipeline_version: string
    quality_score: number
    agents_used: number
  }
  soa_summary: {
    total_visits: number
    total_activities: number
    scheduled_instances: number
    footnotes: number
  }
  eligibility_summary: {
    total_criteria: number
    inclusion_count: number
    exclusion_count: number
    atomic_count: number
  }
}

interface VisitInfo {
  id: string
  name: string
}

interface ActivityMatrix {
  activity: string
  category: string
  cdash_domain: string
  visits: Record<string, {
    is_required: boolean
    footnotes: string[]
    condition?: string
  }>
}

interface SOAMatrix {
  visits: VisitInfo[]
  activities: ActivityMatrix[]
  quality_metrics: {
    totalVisits: number
    totalActivities: number
    totalScheduledInstances: number
    footnotesLinked: number
  }
}

interface Footnote {
  marker: string
  text: string
  rule_type: string
  category: string | string[]
  subcategory: string | string[]
  edc_impact: {
    affectsScheduling: boolean
    affectsBranching: boolean
    isInformational: boolean
  }
}

interface ExpressionNode {
  nodeId: string
  nodeType: string
  operator?: string
  operands?: ExpressionNode[]
  atomicText?: string
  omopTable?: string
  clinicalCategory?: string
  queryableStatus?: string
  numericConstraintStructured?: {
    value: number
    operator: string
    unit: string
    parameter: string
  }
  temporalConstraint?: {
    operator: string
    anchor: string
  }
  operand?: ExpressionNode
}

interface Criterion {
  id: string
  original_id: string
  original_text: string
  type: string
  logic_operator: string
  decomposition_strategy: string
  expression: ExpressionNode
  atomic_criteria: Array<{
    atomicId: string
    atomicText: string
    omopTable: string
    strategy: string
    numericConstraintStructured?: {
      value: number
      operator: string
      unit: string
      parameter: string
    }
  }>
  sql_template: string
}

interface EligibilityCriteria {
  protocol_id: string
  summary: {
    totalCriteria: number
    inclusionCount: number
    exclusionCount: number
    atomicCount: number
  }
  inclusion_criteria: Criterion[]
  exclusion_criteria: Criterion[]
}

interface DomainSection {
  id: string
  name: string
  icon: string
  color: string
  description: string
  data: Record<string, unknown>
}

interface ProtocolRulesVisit {
  id: string
  name: string
  target_day: number
  window_minus: number
  window_plus: number
  required_assessments: string[]
  is_primary_endpoint: boolean
}

interface ProtocolRulesEndpoint {
  id: string
  name: string
  timepoint: string
  calculation: string
  success_threshold?: number
  mcid_threshold?: number
  success_criterion?: string
}

interface ProtocolRules {
  protocol: {
    id: string
    version: string
    effective_date: string
    title: string
    sponsor: string
    phase: string
  }
  schedule_of_assessments: {
    reference_point: string
    visits: ProtocolRulesVisit[]
  }
  endpoints: {
    primary: ProtocolRulesEndpoint
    secondary: ProtocolRulesEndpoint[]
  }
  sample_size: {
    target_enrollment: number
    interim_analysis: number
    evaluable_definition: string
    dropout_allowance: number
    power_calculation: {
      expected_improvement: number
      sd: number
      effect_size: number
      power: number
      alpha: number
    }
  }
  safety_thresholds: Record<string, number>
  adverse_events: {
    sae_narrative_required: boolean
    sae_reporting_window_days: number
    device_relationship_required: boolean
    causality_assessment_required: boolean
    classifications: string[]
    severity_grades: string[]
  }
  deviation_classification: {
    minor: { description: string; max_extension_factor: number; action: string }
    major: { description: string; max_extension_factor: number; action: string; requires_explanation: boolean }
    critical: { description: string; action: string; requires_explanation: boolean; requires_pi_notification: boolean }
  }
  ie_criteria: {
    inclusion: string[]
    exclusion: string[]
  }
  data_quality: Record<string, unknown>
}

const API_BASE = '/api/v1'

// Icon mapping for domains
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  GitBranch,
  Target,
  AlertTriangle,
  Shield,
  Pill,
  TestTube,
  FlaskConical,
  FileSignature,
  ClipboardList,
  Database,
  Building,
  CheckCircle,
  LogOut,
  Scan,
  Activity,
}

// Apple-inspired greyscale color mapping for domains
const colorMap: Record<string, { bg: string; text: string; border: string; light: string }> = {
  blue: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  green: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  red: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  orange: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  purple: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  cyan: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  emerald: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  indigo: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  pink: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  slate: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  amber: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  teal: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  rose: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  sky: { bg: 'bg-gray-700', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
  violet: { bg: 'bg-gray-800', text: 'text-gray-700', border: 'border-gray-200', light: 'bg-gray-50' },
}

// Helper to check if a value is empty
const isEmptyValue = (value: unknown): boolean => {
  if (value === null || value === undefined) return true
  if (value === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  if (typeof value === 'object' && Object.keys(value as object).length === 0) return true
  return false
}

// Helper to format display keys
const formatDisplayKey = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/\b\w/g, l => l.toUpperCase())
    .trim()
}

export default function StudyProtocol({ params }: StudyProtocolProps) {
  const { studyId } = params
  const [activeTab, setActiveTab] = useState<'overview' | 'soa' | 'eligibility' | 'domains' | 'rules'>('overview')
  const [expandedCriteria, setExpandedCriteria] = useState<Set<string>>(new Set())
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)

  const { data: overview, isLoading: overviewLoading } = useQuery<Overview>({
    queryKey: ['protocol-overview'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/overview`)
      if (!res.ok) throw new Error('Failed to fetch overview')
      return res.json()
    },
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: soaMatrix, isLoading: soaMatrixLoading } = useQuery<SOAMatrix>({
    queryKey: ['protocol-soa-matrix'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/soa/matrix`)
      if (!res.ok) throw new Error('Failed to fetch SOA matrix')
      return res.json()
    },
    enabled: activeTab === 'soa',
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: footnotes, isLoading: footnotesLoading } = useQuery<Footnote[]>({
    queryKey: ['protocol-footnotes'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/soa/footnotes`)
      if (!res.ok) throw new Error('Failed to fetch footnotes')
      return res.json()
    },
    enabled: activeTab === 'soa',
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: eligibility, isLoading: eligibilityLoading } = useQuery<EligibilityCriteria>({
    queryKey: ['protocol-eligibility'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/eligibility`)
      if (!res.ok) throw new Error('Failed to fetch eligibility')
      return res.json()
    },
    enabled: activeTab === 'eligibility',
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60 * 24,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  })

  const { data: domains, isLoading: domainsLoading } = useQuery<DomainSection[]>({
    queryKey: ['protocol-domains'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/domains`)
      if (!res.ok) throw new Error('Failed to fetch domains')
      return res.json()
    },
    enabled: activeTab === 'domains',
    staleTime: 1000 * 60 * 30,
    gcTime: 1000 * 60 * 60,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    retry: 2,
  })

  const { data: protocolRules, isLoading: rulesLoading } = useQuery<ProtocolRules>({
    queryKey: ['protocol-rules'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/rules`)
      if (!res.ok) throw new Error('Failed to fetch protocol rules')
      return res.json()
    },
    enabled: activeTab === 'rules',
    staleTime: 1000 * 60 * 30,
    gcTime: 1000 * 60 * 60,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    retry: 2,
  })

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'soa', label: 'Schedule of Assessments' },
    { id: 'eligibility', label: 'Eligibility Criteria' },
    { id: 'domains', label: 'Protocol Domains' },
    { id: 'rules', label: 'Protocol Rules' },
  ] as const

  const toggleCriterion = (id: string) => {
    setExpandedCriteria(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const getOMOPTableColor = (table: string) => {
    switch (table) {
      case 'person': return 'bg-gray-100 text-gray-800'
      case 'observation': return 'bg-gray-100 text-gray-800'
      case 'procedure_occurrence': return 'bg-gray-100 text-gray-800'
      case 'condition_occurrence': return 'bg-gray-100 text-gray-800'
      case 'drug_exposure': return 'bg-gray-100 text-gray-800'
      case 'measurement': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getQueryableStatusColor = (status: string) => {
    switch (status) {
      case 'fully_queryable': return 'bg-gray-100 text-gray-800'
      case 'partially_queryable': return 'bg-gray-100 text-gray-800'
      case 'requires_manual': return 'bg-gray-100 text-gray-800'
      case 'screening_only': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const renderOverview = () => {
    if (overviewLoading || !overview) {
      return <div className="animate-pulse h-48 bg-gray-100 rounded-lg" />
    }

    return (
      <div className="space-y-6">
        {/* Study Info Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Protocol Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Protocol ID</p>
              <p className="text-sm font-medium text-gray-900">{overview.protocol_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Version</p>
              <p className="text-sm font-medium text-gray-900">{overview.version}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Study Type</p>
              <p className="text-sm font-medium text-gray-900">{overview.study_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Study Phase</p>
              <p className="text-sm font-medium text-gray-900">{overview.study_phase}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-sm text-gray-500">Official Title</p>
            <p className="text-sm font-medium text-gray-900">{overview.official_title}</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Extraction Quality</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {(overview.extraction_metadata.quality_score * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {overview.extraction_metadata.agents_used} agents used
            </p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Schedule of Assessments</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {overview.soa_summary.total_visits} visits
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {overview.soa_summary.total_activities} activities
            </p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Scheduled Instances</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {overview.soa_summary.scheduled_instances}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {overview.soa_summary.footnotes} footnotes
            </p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Eligibility Criteria</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {overview.eligibility_summary.total_criteria}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {overview.eligibility_summary.inclusion_count} Inc / {overview.eligibility_summary.exclusion_count} Exc
            </p>
          </div>
        </div>

        {/* Source Document */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Source Document</h3>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              <span className="text-gray-700 font-bold text-sm">PDF</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{overview.source_document.filename}</p>
              <p className="text-xs text-gray-500">{overview.source_document.page_count} pages</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderSOAMatrix = () => {
    if (soaMatrixLoading || footnotesLoading || !soaMatrix) {
      return <div className="animate-pulse h-48 bg-gray-100 rounded-lg" />
    }

    const { visits, activities } = soaMatrix

    // Collect all unique footnotes per activity (to display next to activity name)
    const getActivityFootnotes = (activity: ActivityMatrix): string[] => {
      const allFootnotes = new Set<string>()
      Object.values(activity.visits).forEach(instance => {
        if (instance?.footnotes) {
          instance.footnotes.forEach(fn => allFootnotes.add(fn))
        }
      })
      // Sort: letters (a-z) first, then numbers
      return Array.from(allFootnotes).sort((a, b) => {
        const aIsLetter = /^[a-z]$/i.test(a)
        const bIsLetter = /^[a-z]$/i.test(b)
        if (aIsLetter && !bIsLetter) return -1
        if (!aIsLetter && bIsLetter) return 1
        return a.localeCompare(b)
      })
    }

    return (
      <div className="space-y-6">
        {/* SOA Matrix Table - Like PDF page 53 */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Schedule of Assessments</h3>
              <p className="text-sm text-gray-500 mt-1">Activities and visit schedule matrix</p>
            </div>
            <a
              href="/api/v1/protocol/download/soa-usdm"
              download
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
            >
              <Download className="w-4 h-4" />
              Download SOA USDM JSON
            </a>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 z-10 min-w-[250px]">
                    Activity
                  </th>
                  <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    CDASH
                  </th>
                  {visits.map(visit => (
                    <th key={visit.id} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                      {visit.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {activities.map((activity, idx) => {
                  const activityFootnotes = getActivityFootnotes(activity)
                  return (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900 sticky left-0 bg-white z-10">
                        {activity.activity}
                        {activityFootnotes.length > 0 && (
                          <sup className="ml-1 text-xs text-blue-600 font-medium">
                            {activityFootnotes.join(',')}
                          </sup>
                        )}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          activity.category === 'QUESTIONNAIRE' ? 'bg-yellow-100 text-yellow-800' :
                          activity.category === 'IMAGING' ? 'bg-blue-100 text-blue-800' :
                          activity.category === 'SAFETY' ? 'bg-red-100 text-red-800' :
                          activity.category === 'LABORATORY' ? 'bg-green-100 text-green-800' :
                          activity.category === 'VITAL_SIGNS' ? 'bg-purple-100 text-purple-800' :
                          activity.category === 'PHYSICAL_EXAM' ? 'bg-pink-100 text-pink-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {activity.cdash_domain}
                        </span>
                      </td>
                      {visits.map(visit => {
                        const instance = activity.visits[visit.id]
                        return (
                          <td key={visit.id} className="px-4 py-3 text-center">
                            {instance ? (
                              instance.is_required ? (
                                <Check className="w-4 h-4 text-green-600 mx-auto" />
                              ) : (
                                <X className="w-4 h-4 text-gray-300 mx-auto" />
                              )
                            ) : (
                              <span className="text-gray-300">–</span>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footnotes */}
        {footnotes && footnotes.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Footnotes</h3>
            <div className="space-y-3">
              {footnotes.map((footnote, idx) => (
                <div key={idx} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-0">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">
                    {footnote.marker}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{footnote.text}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        footnote.rule_type === 'visit_window' || footnote.rule_type === 'frequency' ? 'bg-blue-100 text-blue-800' :
                        footnote.rule_type === 'conditional' ? 'bg-yellow-100 text-yellow-800' :
                        footnote.rule_type === 'timing_modifier' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {footnote.rule_type}
                      </span>
                      {footnote.edc_impact?.affectsScheduling && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Affects Scheduling
                        </span>
                      )}
                      {footnote.edc_impact?.affectsBranching && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                          Affects Branching
                        </span>
                      )}
                      {footnote.edc_impact?.isInformational && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          Informational
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderExpressionNode = (node: ExpressionNode, depth: number = 0): JSX.Element => {
    const indent = depth * 16

    if (node.nodeType === 'operator') {
      return (
        <div style={{ marginLeft: indent }}>
          <div className="flex items-center gap-2 py-1">
            <GitBranch className="w-4 h-4 text-gray-400" />
            <span className="font-mono text-sm font-medium text-purple-600">{node.operator}</span>
          </div>
          <div className="border-l-2 border-purple-200 ml-2">
            {node.operands?.map((operand, i) => (
              <div key={operand.nodeId || i}>
                {renderExpressionNode(operand, depth + 1)}
              </div>
            ))}
          </div>
        </div>
      )
    }

    if (node.nodeType === 'temporal') {
      return (
        <div style={{ marginLeft: indent }}>
          <div className="flex items-center gap-2 py-1">
            <span className="px-2 py-0.5 bg-amber-100 text-amber-800 text-xs font-medium rounded">
              {node.temporalConstraint?.operator} {node.temporalConstraint?.anchor}
            </span>
          </div>
          {node.operand && (
            <div className="border-l-2 border-amber-200 ml-2">
              {renderExpressionNode(node.operand, depth + 1)}
            </div>
          )}
        </div>
      )
    }

    // Atomic node
    return (
      <div style={{ marginLeft: indent }} className="py-2">
        <div className="bg-gray-50 rounded-lg p-3 space-y-2">
          <p className="text-sm text-gray-900">{node.atomicText}</p>
          <div className="flex flex-wrap gap-2">
            {node.omopTable && (
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${getOMOPTableColor(node.omopTable)}`}>
                <Database className="w-3 h-3" />
                {node.omopTable}
              </span>
            )}
            {node.clinicalCategory && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                {node.clinicalCategory}
              </span>
            )}
            {node.queryableStatus && (
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getQueryableStatusColor(node.queryableStatus)}`}>
                {node.queryableStatus.replace(/_/g, ' ')}
              </span>
            )}
          </div>
          {node.numericConstraintStructured && (
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span className="font-mono bg-gray-200 px-2 py-0.5 rounded">
                {node.numericConstraintStructured.parameter} {node.numericConstraintStructured.operator} {node.numericConstraintStructured.value} {node.numericConstraintStructured.unit}
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderEligibility = () => {
    if (eligibilityLoading || !eligibility) {
      return <div className="animate-pulse h-48 bg-gray-100 rounded-lg" />
    }

    const renderCriterion = (criterion: Criterion) => {
      const isExpanded = expandedCriteria.has(criterion.id)

      return (
        <div key={criterion.id} className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleCriterion(criterion.id)}
            className="w-full flex items-start gap-3 p-4 hover:bg-gray-50 text-left"
          >
            <span className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-bold text-gray-600">
              {criterion.original_id}
            </span>
            <div className="flex-1">
              <p className="text-sm text-gray-900">{criterion.original_text}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                  {criterion.logic_operator}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {criterion.atomic_criteria?.length || 0} atomic criteria
                </span>
              </div>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
            )}
          </button>

          {isExpanded && (
            <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-4">
              {/* Decomposition Strategy */}
              {criterion.decomposition_strategy && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase mb-1">Decomposition Strategy</p>
                  <p className="text-sm text-gray-700">{criterion.decomposition_strategy}</p>
                </div>
              )}

              {/* Expression Tree */}
              {criterion.expression && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">Expression Tree</p>
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    {renderExpressionNode(criterion.expression)}
                  </div>
                </div>
              )}

              {/* Atomic Criteria with OMOP Tables */}
              {criterion.atomic_criteria && criterion.atomic_criteria.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">OMOP CDM Mappings</p>
                  <div className="space-y-2">
                    {criterion.atomic_criteria.map((atomic, i) => (
                      <div key={i} className="bg-white rounded-lg p-3 border border-gray-200">
                        <div className="flex items-start gap-2">
                          <span className="flex-shrink-0 text-xs font-mono text-gray-400">{atomic.atomicId}</span>
                          <div className="flex-1">
                            <p className="text-sm text-gray-900">{atomic.atomicText}</p>
                            <div className="flex flex-wrap gap-2 mt-2">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${getOMOPTableColor(atomic.omopTable)}`}>
                                <Database className="w-3 h-3" />
                                {atomic.omopTable}
                              </span>
                              {atomic.numericConstraintStructured && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-700 font-mono">
                                  {atomic.numericConstraintStructured.parameter} {atomic.numericConstraintStructured.operator} {atomic.numericConstraintStructured.value} {atomic.numericConstraintStructured.unit}
                                </span>
                              )}
                            </div>
                            {atomic.strategy && (
                              <p className="text-xs text-gray-500 mt-2 italic">{atomic.strategy}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SQL Template */}
              {criterion.sql_template && (
                <details className="mt-3">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 font-medium">
                    View SQL Template
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-900 text-green-400 text-xs rounded overflow-x-auto">
                    {criterion.sql_template}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {/* Download Button */}
        <div className="flex justify-end">
          <a
            href="/api/v1/protocol/download/eligibility"
            download
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download Eligibility Criteria JSON
          </a>
        </div>

        {/* Summary */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Eligibility Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{eligibility.summary.totalCriteria}</p>
              <p className="text-sm text-gray-500">Total Criteria</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{eligibility.summary.inclusionCount}</p>
              <p className="text-sm text-gray-500">Inclusion</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{eligibility.summary.exclusionCount}</p>
              <p className="text-sm text-gray-500">Exclusion</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{eligibility.summary.atomicCount}</p>
              <p className="text-sm text-gray-500">Atomic Criteria</p>
            </div>
          </div>
        </div>

        {/* OMOP Table Legend */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs font-medium text-gray-500 uppercase mb-2">OMOP CDM Table Mappings</p>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
              <Database className="w-3 h-3" /> person
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
              <Database className="w-3 h-3" /> observation
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
              <Database className="w-3 h-3" /> procedure_occurrence
            </span>
          </div>
        </div>

        {/* Inclusion Criteria */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Inclusion Criteria ({eligibility.inclusion_criteria.length})
          </h3>
          <div className="space-y-3">
            {eligibility.inclusion_criteria.map(c => renderCriterion(c))}
          </div>
        </div>

        {/* Exclusion Criteria */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-red-500 rounded-full"></span>
            Exclusion Criteria ({eligibility.exclusion_criteria.length})
          </h3>
          <div className="space-y-3">
            {eligibility.exclusion_criteria.map(c => renderCriterion(c))}
          </div>
        </div>
      </div>
    )
  }

  // Helper to render domain-specific content beautifully
  const renderDomainContent = (domain: DomainSection) => {
    const data = domain.data as Record<string, unknown>
    if (!data || Object.keys(data).length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No data extracted for this domain</p>
        </div>
      )
    }

    // Custom renderers for specific domains
    switch (domain.id) {
      case 'studyDesign':
        return renderStudyDesign(data)
      case 'endpointsEstimandsSAP':
        return renderEndpoints(data)
      case 'adverseEvents':
        return renderAdverseEvents(data)
      case 'concomitantMedications':
        return renderConcomitantMeds(data)
      case 'laboratorySpecifications':
        return renderLaboratory(data)
      case 'informedConsent':
        return renderInformedConsent(data)
      case 'proSpecifications':
        return renderPRO(data)
      case 'imagingCentralReading':
        return renderImaging(data)
      case 'withdrawalProcedures':
        return renderWithdrawal(data)
      default:
        return renderGenericDomain(data)
    }
  }

  const renderStudyDesign = (data: Record<string, unknown>) => {
    interface StudyArm {
      id?: string
      name: string
      label?: string
      description?: string
      plannedSubjects?: number
      armType?: { decode?: string }
      interventions?: Array<{
        name: string
        type?: string
        manufacturer?: string
        isBlinded?: boolean
      }>
    }
    interface StudyEpoch {
      id?: string
      name: string
      description?: string
      sequenceInStudy?: number
      epochType?: { decode?: string }
    }
    
    const arms = (data.studyArms as StudyArm[]) || []
    const epochs = (data.studyEpochs as StudyEpoch[]) || []

    return (
      <div className="space-y-8">
        {/* Study Arms - Premium Cards */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Study Arms</h4>
            <span className="text-xs text-gray-400">{arms.length} arm{arms.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="grid gap-4">
            {arms.map((arm, i) => (
              <div key={i} className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-100 overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center">
                        <Users className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h5 className="font-semibold text-gray-900">{arm.name}</h5>
                        {arm.label && <p className="text-xs text-gray-500">{arm.label}</p>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {arm.armType?.decode && (
                        <span className="px-2.5 py-1 bg-gray-900 text-white text-xs font-medium rounded-lg">
                          {arm.armType.decode}
                        </span>
                      )}
                      {arm.plannedSubjects && (
                        <span className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg">
                          n={arm.plannedSubjects}
                        </span>
                      )}
                    </div>
                  </div>
                  {arm.description && (
                    <p className="text-sm text-gray-600 leading-relaxed mb-4">{arm.description}</p>
                  )}
                  {/* Interventions */}
                  {arm.interventions && arm.interventions.length > 0 && (
                    <div className="pt-4 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Interventions</p>
                      <div className="flex flex-wrap gap-2">
                        {arm.interventions.map((int, j) => (
                          <div key={j} className="inline-flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-xl">
                            <Stethoscope className="w-3.5 h-3.5 text-gray-400" />
                            <span className="text-sm font-medium text-gray-700">{int.name}</span>
                            {int.type && (
                              <span className="text-xs text-gray-400">({int.type})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Study Epochs - Visual Timeline */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Study Timeline</h4>
            <span className="text-xs text-gray-400">{epochs.length} epoch{epochs.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="relative">
            {/* Timeline Track */}
            <div className="absolute top-6 left-0 right-0 h-0.5 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded-full" />
            
            {/* Epoch Cards */}
            <div className="relative grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {epochs.map((epoch, i) => (
                <div key={i} className="relative pt-10">
                  {/* Timeline Node */}
                  <div className="absolute top-3.5 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-gray-900 border-4 border-white shadow-sm z-10 flex items-center justify-center">
                    <span className="text-[9px] font-bold text-white">{epoch.sequenceInStudy || i + 1}</span>
                  </div>
                  
                  {/* Epoch Card */}
                  <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-shadow">
                    <h5 className="font-semibold text-gray-900 text-sm mb-1">{epoch.name}</h5>
                    {epoch.epochType?.decode && (
                      <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-md mb-2">
                        {epoch.epochType.decode}
                      </span>
                    )}
                    {epoch.description && (
                      <p className="text-xs text-gray-500 leading-relaxed line-clamp-3">{epoch.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderEndpoints = (data: Record<string, unknown>) => {
    const endpoints = data.protocol_endpoints as Record<string, unknown> || {}
    const objectives = (endpoints.objectives as Array<{ name: string; description?: string }>) || []
    const endpointsList = (endpoints.endpoints as Array<{ name: string; outcome_measure?: string; level?: string }>) || []
    const estimands = (endpoints.estimands as Array<{ name: string; description?: string }>) || []

    return (
      <div className="space-y-6">
        {/* Objectives */}
        {objectives.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Objectives ({objectives.length})
            </h4>
            <div className="space-y-2">
              {objectives.map((obj, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <p className="font-medium text-gray-900">{safeRenderValue(obj.name || obj)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Endpoints */}
        {endpointsList.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Endpoints ({endpointsList.length})
            </h4>
            <div className="grid gap-3">
              {endpointsList.map((ep, i) => (
                <div key={i} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                  <div className="flex items-start justify-between">
                    <p className="font-medium text-gray-900">{safeRenderValue(ep.name || ep.outcome_measure || ep)}</p>
                    {ep.level && (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        ep.level === 'PRIMARY' ? 'bg-green-100 text-green-800' :
                        ep.level === 'SECONDARY' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {safeRenderValue(ep.level)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Estimands */}
        {estimands.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Estimands ({estimands.length})</h4>
            <div className="space-y-2">
              {estimands.map((est, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <p className="font-medium text-gray-900">{safeRenderValue(est.name || est)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderAdverseEvents = (data: Record<string, unknown>) => {
    const aeDef = data.ae_definitions as Record<string, unknown> || {}
    const saeCriteria = data.sae_criteria as Record<string, unknown> || {}
    const gradingSystem = data.grading_system as { name?: string; version?: string } || {}

    return (
      <div className="space-y-6">
        {/* AE Definition */}
        {Object.keys(aeDef).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              AE Definition
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              {aeDef.definition && (
                <p className="text-sm text-gray-700">{String(aeDef.definition)}</p>
              )}
            </div>
          </div>
        )}

        {/* SAE Criteria */}
        {Object.keys(saeCriteria).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              SAE Criteria
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              {saeCriteria.regulatory_criteria && Array.isArray(saeCriteria.regulatory_criteria) && (
                <ul className="space-y-1">
                  {(saeCriteria.regulatory_criteria as unknown[]).map((c, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-gray-500 mt-1">•</span>
                      {safeRenderValue(c)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        {/* Grading System */}
        {gradingSystem.name && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Grading System</h4>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="font-medium text-gray-900">{gradingSystem.name}</p>
              {gradingSystem.version && (
                <p className="text-sm text-gray-500 mt-1">Version: {gradingSystem.version}</p>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderConcomitantMeds = (data: Record<string, unknown>) => {
    const prohibited = (data.prohibited_medications as Array<Record<string, unknown>>) || []
    const restricted = (data.restricted_medications as Array<Record<string, unknown>>) || []
    const required = (data.required_medications as Array<Record<string, unknown>>) || []
    const rescue = (data.rescue_medications as Array<Record<string, unknown>>) || []
    const allowed = (data.allowed_medications as Array<Record<string, unknown>>) || []
    const washout = (data.washout_requirements as Array<Record<string, unknown>>) || []
    const interactions = (data.drug_interactions as Array<Record<string, unknown>>) || []
    const herbalPolicy = data.herbal_supplements_policy as Record<string, unknown> || {}
    const vaccinePolicy = data.vaccine_policy as Record<string, unknown> || {}

    const renderMedCard = (med: Record<string, unknown>, colorClass: string = 'text-gray-600') => {
      const name = med.medication_name || med.medication_class || med.drug_class || med.name
      const purpose = med.purpose || med.indication || med.reason || med.restriction
      const timing = med.timing as Record<string, unknown> | undefined
      const dosing = med.dosing as Record<string, unknown> | undefined
      const concept = med.biomedicalConcept as Record<string, unknown> | undefined
      const impactOnEndpoints = med.impact_on_endpoints as string | undefined
      const dosingInstructions = med.dosing_instructions as string | undefined
      
      return (
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-start justify-between mb-2">
            <p className="font-semibold text-gray-900">{safeRenderValue(name)}</p>
            {concept?.conceptName && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {safeRenderValue(concept.conceptName)}
              </span>
            )}
          </div>
          {purpose && (
            <p className={`text-sm ${colorClass} mb-2`}>{safeRenderValue(purpose)}</p>
          )}
          {timing?.timing_description && (
            <div className="text-xs text-gray-500 flex items-center gap-1 mb-1">
              <Clock className="w-3 h-3" />
              {safeRenderValue(timing.timing_description)}
            </div>
          )}
          {timing?.relative_to && !timing?.timing_description && (
            <div className="text-xs text-gray-500 flex items-center gap-1 mb-1">
              <Clock className="w-3 h-3" />
              Relative to: {safeRenderValue(timing.relative_to)}
            </div>
          )}
          {dosingInstructions && (
            <div className="text-xs text-gray-500 mb-1">
              <span className="font-medium">Dosing:</span> {safeRenderValue(dosingInstructions)}
            </div>
          )}
          {dosing?.route?.decode && dosing.route.decode !== 'not_specified' && (
            <div className="text-xs text-gray-500 mb-1">
              <span className="font-medium">Route:</span> {safeRenderValue(dosing.route)}
            </div>
          )}
          {impactOnEndpoints && (
            <div className="text-xs text-gray-500 mt-2 p-2 bg-gray-50 rounded">
              <span className="font-medium">Impact on Endpoints:</span> {safeRenderValue(impactOnEndpoints)}
            </div>
          )}
        </div>
      )
    }

    const hasNoData = prohibited.length === 0 && restricted.length === 0 && required.length === 0 && 
                      rescue.length === 0 && allowed.length === 0 && Object.keys(herbalPolicy).length <= 1

    if (hasNoData) {
      return (
        <div className="text-center py-8 text-gray-400">
          <Pill className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No medication restrictions specified for this study</p>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {/* Required Medications */}
        {required.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Check className="w-4 h-4 text-gray-600" />
              Required Medications ({required.length})
            </h4>
            <div className="space-y-3">
              {required.map((med, i) => (
                <div key={i}>{renderMedCard(med, 'text-gray-700')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Rescue Medications */}
        {rescue.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Pill className="w-4 h-4 text-gray-600" />
              Rescue/Supportive Medications ({rescue.length})
            </h4>
            <div className="space-y-3">
              {rescue.map((med, i) => (
                <div key={i}>{renderMedCard(med, 'text-gray-600')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Allowed Medications */}
        {allowed.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Check className="w-4 h-4 text-gray-500" />
              Allowed Medications ({allowed.length})
            </h4>
            <div className="space-y-3">
              {allowed.map((med, i) => (
                <div key={i}>{renderMedCard(med, 'text-gray-600')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Prohibited Medications */}
        {prohibited.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <X className="w-4 h-4 text-gray-600" />
              Prohibited Medications ({prohibited.length})
            </h4>
            <div className="space-y-3">
              {prohibited.map((med, i) => (
                <div key={i}>{renderMedCard(med, 'text-gray-700')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Restricted Medications */}
        {restricted.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-gray-500" />
              Restricted Medications ({restricted.length})
            </h4>
            <div className="space-y-3">
              {restricted.map((med, i) => (
                <div key={i}>{renderMedCard(med, 'text-gray-600')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Washout Requirements */}
        {washout.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              Washout Requirements ({washout.length})
            </h4>
            <div className="space-y-3">
              {washout.map((req, i) => (
                <div key={i}>{renderMedCard(req, 'text-gray-600')}</div>
              ))}
            </div>
          </div>
        )}

        {/* Drug Interactions */}
        {interactions.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-gray-500" />
              Drug Interactions ({interactions.length})
            </h4>
            <div className="space-y-3">
              {interactions.map((int, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <p className="font-medium text-gray-900">{safeRenderValue(int.name || int)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Herbal Supplements Policy */}
        {Object.keys(herbalPolicy).length > 1 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Leaf className="w-4 h-4 text-gray-500" />
              Herbal Supplements Policy
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              {herbalPolicy.provenance && (
                <p className="text-sm text-gray-700">
                  {safeRenderValue((herbalPolicy.provenance as Record<string, unknown>)?.text_snippet)}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Vaccine Policy */}
        {Object.keys(vaccinePolicy).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Syringe className="w-4 h-4 text-gray-500" />
              Vaccine Policy
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              {renderObjectAsTable(vaccinePolicy)}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderLaboratory = (data: Record<string, unknown>) => {
    const panels = (data.discovered_panels as Array<Record<string, unknown>>) || []
    const tests = (data.laboratory_tests as Array<Record<string, unknown>>) || []

    return (
      <div className="space-y-6">
        {/* Lab Panels */}
        {panels.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Beaker className="w-4 h-4" />
              Laboratory Panels ({panels.length})
            </h4>
            <div className="grid gap-3">
              {panels.map((panel, i) => {
                const name = panel.panel_name || panel.name
                const description = panel.panel_description || panel.description
                const category = panel.panel_category
                const concept = panel.biomedicalConcept as Record<string, unknown> | undefined
                
                return (
                  <div key={i} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                    <div className="flex items-start justify-between mb-2">
                      <p className="font-semibold text-gray-900">{safeRenderValue(name)}</p>
                      {category && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded capitalize">
                          {safeRenderValue(category)}
                        </span>
                      )}
                    </div>
                    {description && (
                      <p className="text-sm text-gray-600 mb-2">{safeRenderValue(description)}</p>
                    )}
                    {concept?.conceptName && (
                      <div className="text-xs text-gray-500">
                        CDISC: {safeRenderValue(concept.conceptName)} ({safeRenderValue(concept.cdiscCode)})
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Lab Tests */}
        {tests.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <FlaskConical className="w-4 h-4" />
              Laboratory Tests ({tests.length})
            </h4>
            <div className="grid gap-2">
              {tests.map((test, i) => (
                <div key={i} className="bg-white p-3 rounded-lg border border-gray-200 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{safeRenderValue(test.test_name || test.name || test)}</p>
                    {test.panel && <p className="text-xs text-gray-500">{safeRenderValue(test.panel)}</p>}
                  </div>
                  {test.frequency && (
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">{safeRenderValue(test.frequency)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderInformedConsent = (data: Record<string, unknown>) => {
    const overview = data.study_overview as { study_title?: string; study_purpose?: string; duration?: string } || {}
    const risks = data.risks as { general_risks?: string[] } || {}
    const benefits = data.benefits as { potential_benefits?: string[] } || {}

    return (
      <div className="space-y-6">
        {/* Study Overview */}
        {overview.study_purpose && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Study Purpose
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <p className="text-sm text-gray-700">{overview.study_purpose}</p>
            </div>
          </div>
        )}

        {/* Risks */}
        {risks.general_risks && Array.isArray(risks.general_risks) && risks.general_risks.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Risks
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <ul className="space-y-1">
                {risks.general_risks.map((risk, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-red-500 mt-1">•</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Benefits */}
        {benefits.potential_benefits && Array.isArray(benefits.potential_benefits) && benefits.potential_benefits.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Heart className="w-4 h-4 text-green-500" />
              Potential Benefits
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <ul className="space-y-1">
                {benefits.potential_benefits.map((benefit, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-green-500 mt-1">•</span>
                    {benefit}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderPRO = (data: Record<string, unknown>) => {
    const instruments = (data.pro_instruments as Array<{ name?: string; full_name?: string; domains?: string[] }>) || []

    return (
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <ClipboardList className="w-4 h-4" />
          PRO Instruments ({instruments.length})
        </h4>
        <div className="grid gap-3">
          {instruments.map((inst, i) => (
            <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <p className="font-medium text-gray-900">{safeRenderValue(inst.name || inst.full_name || inst)}</p>
              {inst.domains && Array.isArray(inst.domains) && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {inst.domains.map((d, j) => (
                    <span key={j} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">{safeRenderValue(d)}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderImaging = (data: Record<string, unknown>) => {
    const modalities = (data.imaging_modalities as Array<{ modality_type?: string; anatomical_region?: string; frequency?: string }>) || []
    const schedule = data.assessment_schedule as { timing?: string[] } || {}

    return (
      <div className="space-y-6">
        {/* Modalities */}
        {modalities.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Scan className="w-4 h-4" />
              Imaging Modalities ({modalities.length})
            </h4>
            <div className="grid gap-3">
              {modalities.map((mod, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <p className="font-medium text-gray-900">{safeRenderValue(mod.modality_type || mod)}</p>
                  {mod.anatomical_region && (
                    <p className="text-sm text-gray-600 mt-1">Region: {safeRenderValue(mod.anatomical_region)}</p>
                  )}
                  {mod.frequency && (
                    <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                      {safeRenderValue(mod.frequency)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Schedule */}
        {schedule.timing && Array.isArray(schedule.timing) && schedule.timing.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Assessment Schedule</h4>
            <div className="flex flex-wrap gap-2">
              {schedule.timing.map((t, i) => (
                <span key={i} className="px-3 py-1 bg-sky-100 text-sky-800 rounded-full text-sm">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderWithdrawal = (data: Record<string, unknown>) => {
    const types = (data.discontinuation_types as Array<{ type?: string; definition?: string }>) || []
    const followup = data.post_discontinuation_followup as { description?: string; procedures?: string[] } || {}

    return (
      <div className="space-y-6">
        {/* Discontinuation Types */}
        {types.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <LogOut className="w-4 h-4" />
              Discontinuation Types ({types.length})
            </h4>
            <div className="space-y-2">
              {types.map((dt, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <p className="font-medium text-gray-900">{dt.type || 'Withdrawal'}</p>
                  {dt.definition && (
                    <p className="text-sm text-gray-600 mt-1">{dt.definition}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Post-Discontinuation Follow-up */}
        {(followup.description || (followup.procedures && followup.procedures.length > 0)) && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Post-Discontinuation Follow-up</h4>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              {followup.description && (
                <p className="text-sm text-gray-700">{followup.description}</p>
              )}
              {followup.procedures && Array.isArray(followup.procedures) && (
                <ul className="mt-2 space-y-1">
                  {followup.procedures.map((p, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-rose-500 mt-1">•</span>
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Helper to detect code objects (medical terminology) and format them as strings
  const isCodeObject = (value: unknown): value is Record<string, unknown> => {
    if (typeof value !== 'object' || value === null) return false
    const keys = Object.keys(value)
    return keys.includes('code') || keys.includes('decode') || keys.includes('codeSystem')
  }

  const formatCodeObject = (obj: Record<string, unknown>): string => {
    const decode = obj.decode || obj.code || ''
    const code = obj.code && obj.decode ? ` (${obj.code})` : ''
    return `${decode}${code}`
  }

  // Safe value renderer that handles code objects and any non-primitive values
  const safeRenderValue = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    if (typeof value === 'string') return value
    if (typeof value === 'number' || typeof value === 'boolean') return String(value)
    if (isCodeObject(value)) return formatCodeObject(value as Record<string, unknown>)
    if (Array.isArray(value)) return value.map(v => safeRenderValue(v)).join(', ')
    if (typeof value === 'object') {
      // Check for common text properties
      const obj = value as Record<string, unknown>
      if (obj.name) return safeRenderValue(obj.name)
      if (obj.text) return safeRenderValue(obj.text)
      if (obj.description) return safeRenderValue(obj.description)
      if (obj.value) return safeRenderValue(obj.value)
      return JSON.stringify(value)
    }
    return String(value)
  }

  const renderObjectAsTable = (obj: Record<string, unknown>, depth: number = 0): React.ReactNode => {
    // Check if this is a code object - format it as a string
    if (isCodeObject(obj)) {
      return <span className="text-sm text-gray-800">{formatCodeObject(obj)}</span>
    }

    const entries = Object.entries(obj).filter(([key, value]) => 
      !isEmptyValue(value) && !['id', 'instanceType', 'provenance'].includes(key)
    )
    
    if (entries.length === 0) return null

    return (
      <div className={depth > 0 ? 'ml-4' : ''}>
        {entries.map(([key, value]) => {
          const displayKey = formatDisplayKey(key)
          
          // Check if value is a code object
          if (isCodeObject(value)) {
            return (
              <div key={key} className="py-2 border-b border-gray-50 last:border-0">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{displayKey}</span>
                <p className="text-sm text-gray-800 mt-0.5">{formatCodeObject(value as Record<string, unknown>)}</p>
              </div>
            )
          }
          
          if (typeof value === 'boolean') {
            return (
              <div key={key} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-500">{displayKey}</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${value ? 'bg-gray-100 text-gray-700' : 'bg-gray-50 text-gray-400'}`}>
                  {value ? 'Yes' : 'No'}
                </span>
              </div>
            )
          }
          
          if (typeof value === 'number') {
            return (
              <div key={key} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-500">{displayKey}</span>
                <span className="text-sm font-medium text-gray-900">{value}</span>
              </div>
            )
          }
          
          if (typeof value === 'string') {
            return (
              <div key={key} className="py-2 border-b border-gray-50 last:border-0">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{displayKey}</span>
                <p className="text-sm text-gray-800 mt-0.5">{value}</p>
              </div>
            )
          }
          
          if (Array.isArray(value) && value.length > 0) {
            if (typeof value[0] === 'string') {
              return (
                <div key={key} className="py-3 border-b border-gray-50 last:border-0">
                  <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{displayKey}</span>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {value.map((item, i) => (
                      <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-md">{String(item)}</span>
                    ))}
                  </div>
                </div>
              )
            }
            return (
              <div key={key} className="py-3 border-b border-gray-50 last:border-0">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2 block">{displayKey} ({value.length})</span>
                <div className="space-y-2">
                  {value.slice(0, 8).map((item, i) => (
                    <div key={i} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                      {typeof item === 'object' && item !== null ? (
                        renderObjectAsTable(item as Record<string, unknown>, depth + 1)
                      ) : (
                        <p className="text-sm text-gray-700">{String(item)}</p>
                      )}
                    </div>
                  ))}
                  {value.length > 8 && (
                    <p className="text-xs text-gray-400 pt-1">+ {value.length - 8} more items</p>
                  )}
                </div>
              </div>
            )
          }
          
          if (typeof value === 'object' && value !== null) {
            return (
              <div key={key} className="py-3 border-b border-gray-50 last:border-0">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2 block">{displayKey}</span>
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  {renderObjectAsTable(value as Record<string, unknown>, depth + 1)}
                </div>
              </div>
            )
          }
          
          return null
        })}
      </div>
    )
  }

  const renderGenericDomain = (data: Record<string, unknown>) => {
    const entries = Object.entries(data).filter(([key, value]) =>
      !['id', 'instanceType', 'name', 'provenance', 'extraction_statistics'].includes(key) && !isEmptyValue(value)
    )

    if (entries.length === 0) {
      return (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">No data available for this domain</p>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {entries.map(([key, value]) => {
          const displayKey = formatDisplayKey(key)

          if (Array.isArray(value) && value.length > 0) {
            if (typeof value[0] === 'string') {
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{displayKey}</h4>
                    <span className="text-xs text-gray-400">{value.length} item{value.length !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {value.map((item, i) => (
                      <span key={i} className="text-sm bg-white border border-gray-200 text-gray-700 px-3 py-2 rounded-xl shadow-sm">{String(item)}</span>
                    ))}
                  </div>
                </div>
              )
            }
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{displayKey}</h4>
                  <span className="text-xs text-gray-400">{value.length} item{value.length !== 1 ? 's' : ''}</span>
                </div>
                <div className="grid gap-3">
                  {value.slice(0, 10).map((item, i) => (
                    <div key={i} className="bg-white rounded-xl p-5 border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                      {typeof item === 'object' && item !== null ? (
                        renderObjectAsTable(item as Record<string, unknown>)
                      ) : (
                        <p className="text-sm text-gray-700">{String(item)}</p>
                      )}
                    </div>
                  ))}
                  {value.length > 10 && (
                    <div className="text-center py-3">
                      <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1.5 rounded-lg">+ {value.length - 10} more items</span>
                    </div>
                  )}
                </div>
              </div>
            )
          }

          if (typeof value === 'object' && value !== null) {
            return (
              <div key={key}>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{displayKey}</h4>
                <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                  {renderObjectAsTable(value as Record<string, unknown>)}
                </div>
              </div>
            )
          }

          if (typeof value === 'boolean') {
            return (
              <div key={key} className="flex items-center justify-between py-3 px-4 bg-white rounded-xl border border-gray-100">
                <span className="text-sm text-gray-700 font-medium">{displayKey}</span>
                <span className={`text-xs font-semibold px-3 py-1.5 rounded-lg ${value ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  {value ? 'Yes' : 'No'}
                </span>
              </div>
            )
          }

          return (
            <div key={key} className="flex items-center justify-between py-3 px-4 bg-white rounded-xl border border-gray-100">
              <span className="text-sm text-gray-500">{displayKey}</span>
              <span className="text-sm font-semibold text-gray-900">{String(value)}</span>
            </div>
          )
        })}
      </div>
    )
  }

  const renderDomains = () => {
    if (domainsLoading || !domains) {
      return (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse bg-gray-100 rounded-xl h-20" />
          ))}
        </div>
      )
    }

    const domainsWithData = domains.filter(domain => {
      if (!domain.data || typeof domain.data !== 'object') return false
      const dataEntries = Object.entries(domain.data).filter(([key, value]) =>
        !['id', 'instanceType', 'name', 'provenance', 'extraction_statistics'].includes(key) && !isEmptyValue(value)
      )
      return dataEntries.length > 0
    })

    if (domainsWithData.length === 0) {
      return (
        <div className="text-center py-16">
          <Database className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No domain data available</p>
        </div>
      )
    }

    const getDomainInsights = (domain: DomainSection): Array<{ label: string; value: string | number }> => {
      const data = domain.data as Record<string, unknown>
      const insights: Array<{ label: string; value: string | number }> = []
      
      switch (domain.id) {
        case 'studyDesign': {
          const arms = (data.studyArms as unknown[]) || []
          const epochs = (data.studyEpochs as unknown[]) || []
          if (arms.length) insights.push({ label: 'Arms', value: arms.length })
          if (epochs.length) insights.push({ label: 'Epochs', value: epochs.length })
          break
        }
        case 'endpointsEstimandsSAP': {
          const endpoints = data.protocol_endpoints as Record<string, unknown> || {}
          const ep = (endpoints.endpoints as unknown[]) || []
          const obj = (endpoints.objectives as unknown[]) || []
          if (ep.length) insights.push({ label: 'Endpoints', value: ep.length })
          if (obj.length) insights.push({ label: 'Objectives', value: obj.length })
          break
        }
        case 'adverseEvents': {
          const aeDef = data.ae_definitions as Record<string, unknown> || {}
          const saeCriteria = data.sae_criteria as Record<string, unknown> || {}
          const reportingReqs = data.reporting_requirements as unknown[] || []
          if (Object.keys(aeDef).length > 0) insights.push({ label: 'AE Defined', value: 'Yes' })
          if (Object.keys(saeCriteria).length > 0) insights.push({ label: 'SAE Criteria', value: 'Yes' })
          if (reportingReqs.length > 0) insights.push({ label: 'Reporting', value: reportingReqs.length })
          break
        }
        case 'concomitantMedications': {
          const prohibited = (data.prohibited_medications as unknown[]) || []
          const required = (data.required_medications as unknown[]) || []
          if (prohibited.length) insights.push({ label: 'Prohibited', value: prohibited.length })
          if (required.length) insights.push({ label: 'Required', value: required.length })
          break
        }
        case 'laboratorySpecifications': {
          const panels = (data.required_tests as unknown[]) || (data.panels as unknown[]) || []
          if (panels.length) insights.push({ label: 'Tests', value: panels.length })
          break
        }
        default: {
          const entries = Object.entries(data).filter(([key, value]) =>
            !['id', 'instanceType', 'name', 'provenance', 'extraction_statistics'].includes(key) && 
            !isEmptyValue(value)
          )
          if (entries.length) insights.push({ label: 'Fields', value: entries.length })
        }
      }
      return insights
    }

    return (
      <div className="space-y-6">
        {/* Header with Download */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">
              {domainsWithData.length} domain{domainsWithData.length !== 1 ? 's' : ''} extracted from protocol
            </p>
          </div>
          <a
            href="/api/v1/protocol/download/usdm"
            download
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 transition-all shadow-sm"
          >
            <Download className="w-4 h-4" />
            Download USDM 4.0
          </a>
        </div>
        
        {/* Domain Cards Grid */}
        <div className="space-y-3">
          {domainsWithData.map((domain) => {
            const Icon = iconMap[domain.icon] || Database
            const isExpanded = expandedDomain === domain.id
            const insights = getDomainInsights(domain)

            return (
              <div 
                key={domain.id} 
                className={`bg-white rounded-2xl border overflow-hidden transition-all duration-200 ${
                  isExpanded 
                    ? 'border-gray-200 shadow-[0_4px_20px_rgba(0,0,0,0.08)]' 
                    : 'border-gray-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)] hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)]'
                }`}
              >
                <button
                  onClick={() => setExpandedDomain(isExpanded ? null : domain.id)}
                  className="w-full p-5 flex items-center justify-between text-left transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors ${
                      isExpanded ? 'bg-gray-900' : 'bg-gray-100'
                    }`}>
                      <Icon className={`w-5 h-5 transition-colors ${isExpanded ? 'text-white' : 'text-gray-600'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="font-semibold text-gray-900">{domain.name}</h3>
                        {/* Insight Pills */}
                        <div className="hidden sm:flex items-center gap-2">
                          {insights.map((insight, idx) => (
                            <span 
                              key={idx}
                              className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-lg"
                            >
                              <span className="text-gray-900 font-semibold mr-1">{insight.value}</span>
                              {insight.label}
                            </span>
                          ))}
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 truncate">{domain.description}</p>
                    </div>
                  </div>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                    isExpanded ? 'bg-gray-100 rotate-180' : 'bg-transparent'
                  }`}>
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  </div>
                </button>
                
                {isExpanded && (
                  <div className="border-t border-gray-100 bg-gradient-to-b from-gray-50/50 to-white p-6">
                    {renderDomainContent(domain)}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderRules = () => {
    if (rulesLoading || !protocolRules) {
      return <div className="animate-pulse h-48 bg-gray-100 rounded-lg" />
    }

    const formatDay = (day: number) => {
      if (day === 0) return 'Day 0 (Surgery)'
      if (day < 0) return `Day ${day}`
      if (day < 30) return `Day +${day}`
      if (day < 365) return `${Math.round(day / 30)} months`
      return `${(day / 365).toFixed(0)} year${day >= 730 ? 's' : ''}`
    }

    const formatAssessment = (assessment: string) => {
      return assessment
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
        .replace('Hhs', 'HHS')
        .replace('Ohs', 'OHS')
        .replace('Ie', 'I/E')
        .replace('Ae', 'AE')
    }

    return (
      <div className="space-y-6">
        {/* Protocol Header */}
        <div className="bg-gray-900 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">{protocolRules.protocol.title}</h2>
              <p className="text-indigo-100">Document-as-Code Protocol Rules</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-indigo-200 text-xs">Protocol ID</p>
              <p className="font-semibold">{protocolRules.protocol.id}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-indigo-200 text-xs">Version</p>
              <p className="font-semibold">{protocolRules.protocol.version}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-indigo-200 text-xs">Phase</p>
              <p className="font-semibold">{protocolRules.protocol.phase}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-indigo-200 text-xs">Effective Date</p>
              <p className="font-semibold">{protocolRules.protocol.effective_date}</p>
            </div>
          </div>
        </div>

        {/* Visit Windows Timeline */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Visit Windows Timeline
          </h3>
          <p className="text-sm text-gray-500 mb-4">Reference point: {protocolRules.schedule_of_assessments.reference_point.replace('_', ' ')}</p>

          <div className="space-y-4">
            {protocolRules.schedule_of_assessments.visits.map((visit, idx) => (
              <div
                key={visit.id}
                className={`relative flex items-start gap-4 p-4 rounded-lg border ${
                  visit.is_primary_endpoint
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-100 bg-gray-50'
                }`}
              >
                {/* Timeline connector */}
                {idx < protocolRules.schedule_of_assessments.visits.length - 1 && (
                  <div className="absolute left-8 top-16 w-0.5 h-8 bg-gray-200" />
                )}

                {/* Visit number */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  visit.is_primary_endpoint
                    ? 'bg-green-600 text-white'
                    : 'bg-blue-600 text-white'
                }`}>
                  {idx + 1}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-gray-900">{visit.name}</h4>
                    {visit.is_primary_endpoint && (
                      <span className="px-2 py-0.5 bg-green-600 text-white text-xs rounded-full">
                        Primary Endpoint
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3 text-sm mb-2">
                    <span className="text-gray-600">
                      <span className="font-medium">Target:</span> {formatDay(visit.target_day)}
                    </span>
                    <span className="text-gray-600">
                      <span className="font-medium">Window:</span> -{visit.window_minus} / +{visit.window_plus} days
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1 mt-2">
                    {visit.required_assessments.map(assessment => (
                      <span
                        key={assessment}
                        className="px-2 py-0.5 bg-white border border-gray-200 rounded text-xs text-gray-600"
                      >
                        {formatAssessment(assessment)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Endpoints */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-green-600" />
            Study Endpoints
          </h3>

          {/* Primary Endpoint */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2 py-0.5 bg-green-600 text-white text-xs font-medium rounded">PRIMARY</span>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h4 className="font-semibold text-gray-900">{protocolRules.endpoints.primary.name}</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                <div>
                  <p className="text-gray-500">Timepoint</p>
                  <p className="font-medium text-gray-900">{protocolRules.endpoints.primary.timepoint}</p>
                </div>
                <div>
                  <p className="text-gray-500">Calculation</p>
                  <p className="font-medium text-gray-900 font-mono text-xs">{protocolRules.endpoints.primary.calculation}</p>
                </div>
                {protocolRules.endpoints.primary.mcid_threshold && (
                  <div>
                    <p className="text-gray-500">MCID Threshold</p>
                    <p className="font-medium text-gray-900">{protocolRules.endpoints.primary.mcid_threshold} points</p>
                  </div>
                )}
                {protocolRules.endpoints.primary.success_threshold && (
                  <div>
                    <p className="text-gray-500">Success Threshold</p>
                    <p className="font-medium text-gray-900">{protocolRules.endpoints.primary.success_threshold} points</p>
                  </div>
                )}
              </div>
              {protocolRules.endpoints.primary.success_criterion && (
                <p className="mt-3 text-sm text-green-700 bg-green-100 p-2 rounded">
                  {protocolRules.endpoints.primary.success_criterion}
                </p>
              )}
            </div>
          </div>

          {/* Secondary Endpoints */}
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 bg-blue-600 text-white text-xs font-medium rounded">SECONDARY</span>
          </div>
          <div className="grid gap-3">
            {protocolRules.endpoints.secondary.map((endpoint) => (
              <div key={endpoint.id} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-900">{endpoint.name}</h4>
                <div className="flex flex-wrap gap-4 mt-2 text-sm">
                  <span className="text-gray-600">
                    <span className="font-medium">Timepoint:</span> {endpoint.timepoint}
                  </span>
                  <span className="text-gray-600">
                    <span className="font-medium">Method:</span>{' '}
                    <code className="bg-gray-200 px-1 rounded text-xs">{endpoint.calculation}</code>
                  </span>
                  {endpoint.success_threshold && (
                    <span className="text-gray-600">
                      <span className="font-medium">Threshold:</span> {endpoint.success_threshold}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sample Size & Safety Thresholds */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Sample Size */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              Sample Size
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                <span className="text-gray-600">Target Enrollment</span>
                <span className="font-bold text-purple-600 text-xl">{protocolRules.sample_size.target_enrollment}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Interim Analysis</span>
                <span className="font-medium text-gray-900">{protocolRules.sample_size.interim_analysis} patients</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Dropout Allowance</span>
                <span className="font-medium text-gray-900">{(protocolRules.sample_size.dropout_allowance * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                <p className="text-xs text-gray-500 uppercase mb-2">Power Calculation</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-500">Power:</span> <span className="font-medium">{(protocolRules.sample_size.power_calculation.power * 100)}%</span></div>
                  <div><span className="text-gray-500">Alpha:</span> <span className="font-medium">{protocolRules.sample_size.power_calculation.alpha}</span></div>
                  <div><span className="text-gray-500">Effect Size:</span> <span className="font-medium">{protocolRules.sample_size.power_calculation.effect_size}</span></div>
                  <div><span className="text-gray-500">Expected Δ:</span> <span className="font-medium">{protocolRules.sample_size.power_calculation.expected_improvement}</span></div>
                </div>
              </div>
            </div>
          </div>

          {/* Safety Thresholds */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-red-600" />
              Safety Thresholds
            </h3>
            <p className="text-sm text-gray-500 mb-3">Rates above these trigger review/escalation</p>
            <div className="space-y-2">
              {Object.entries(protocolRules.safety_thresholds).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                  <span className="text-sm text-gray-700">
                    {key.replace(/_/g, ' ').replace('rate concern', '').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-sm font-medium ${
                    value >= 0.1 ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'
                  }`}>
                    {(value * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Deviation Classification */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            Deviation Classification Rules
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            {/* Minor */}
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 bg-yellow-400 text-yellow-900 text-xs font-bold rounded">MINOR</span>
              </div>
              <p className="text-sm text-gray-700 mb-2">{protocolRules.deviation_classification.minor.description}</p>
              <p className="text-xs text-gray-500 italic">{protocolRules.deviation_classification.minor.action}</p>
            </div>

            {/* Major */}
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 bg-orange-500 text-white text-xs font-bold rounded">MAJOR</span>
              </div>
              <p className="text-sm text-gray-700 mb-2">{protocolRules.deviation_classification.major.description}</p>
              <p className="text-xs text-gray-500 italic">{protocolRules.deviation_classification.major.action}</p>
            </div>

            {/* Critical */}
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 bg-red-600 text-white text-xs font-bold rounded">CRITICAL</span>
              </div>
              <p className="text-sm text-gray-700 mb-2">{protocolRules.deviation_classification.critical.description}</p>
              <p className="text-xs text-gray-500 italic">{protocolRules.deviation_classification.critical.action}</p>
            </div>
          </div>
        </div>

        {/* Adverse Events */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-red-600" />
            Adverse Event Handling
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Requirements</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {protocolRules.adverse_events.sae_narrative_required ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <X className="w-4 h-4 text-red-600" />
                  )}
                  <span className="text-sm text-gray-700">SAE Narrative Required</span>
                </div>
                <div className="flex items-center gap-2">
                  {protocolRules.adverse_events.device_relationship_required ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <X className="w-4 h-4 text-red-600" />
                  )}
                  <span className="text-sm text-gray-700">Device Relationship Assessment</span>
                </div>
                <div className="flex items-center gap-2">
                  {protocolRules.adverse_events.causality_assessment_required ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <X className="w-4 h-4 text-red-600" />
                  )}
                  <span className="text-sm text-gray-700">Causality Assessment</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-red-50 rounded mt-2">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span className="text-sm text-red-700 font-medium">
                    SAE Reporting Window: {protocolRules.adverse_events.sae_reporting_window_days * 24} hours
                  </span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Classifications</h4>
              <div className="space-y-2">
                {protocolRules.adverse_events.classifications.map((c) => (
                  <span key={c} className="inline-block mr-2 px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                    {c}
                  </span>
                ))}
              </div>
              <h4 className="text-sm font-semibold text-gray-700 mt-4 mb-3">Severity Grades</h4>
              <div className="flex gap-2">
                {protocolRules.adverse_events.severity_grades.map((grade, idx) => (
                  <span
                    key={grade}
                    className={`px-3 py-1 text-sm rounded-full ${
                      idx === 0 ? 'bg-yellow-100 text-yellow-800' :
                      idx === 1 ? 'bg-orange-100 text-orange-800' :
                      'bg-red-100 text-red-800'
                    }`}
                  >
                    {grade}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* I/E Criteria */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-indigo-600" />
            Inclusion/Exclusion Criteria
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Inclusion */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <h4 className="font-semibold text-gray-700">Inclusion ({protocolRules.ie_criteria.inclusion.length})</h4>
              </div>
              <ul className="space-y-2">
                {protocolRules.ie_criteria.inclusion.map((criterion, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                    <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    {criterion}
                  </li>
                ))}
              </ul>
            </div>

            {/* Exclusion */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                <h4 className="font-semibold text-gray-700">Exclusion ({protocolRules.ie_criteria.exclusion.length})</h4>
              </div>
              <ul className="space-y-2">
                {protocolRules.ie_criteria.exclusion.map((criterion, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                    <X className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                    {criterion}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <StudyLayout studyId={studyId} chatContext="protocol">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Digitized Protocol</h1>
          <p className="text-gray-600 mt-1">
            AI-extracted protocol content with USDM 4.0 structure and OMOP mappings
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-3 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'soa' && renderSOAMatrix()}
        {activeTab === 'eligibility' && renderEligibility()}
        {activeTab === 'domains' && renderDomains()}
        {activeTab === 'rules' && renderRules()}
      </div>
    </StudyLayout>
  )
}
