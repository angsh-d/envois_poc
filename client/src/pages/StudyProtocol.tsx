import { useQuery } from '@tanstack/react-query'
import StudyLayout from './StudyLayout'
import { useState } from 'react'
import {
  Check, X, ChevronDown, ChevronRight, Database, GitBranch,
  Target, AlertTriangle, Shield, Pill, TestTube, FlaskConical,
  FileSignature, ClipboardList, Building, CheckCircle, LogOut,
  Scan, Activity, Users, Beaker, FileText, Heart, Stethoscope
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

// Color mapping for domains
const colorMap: Record<string, { bg: string; text: string; border: string; light: string }> = {
  blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-200', light: 'bg-blue-50' },
  green: { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-200', light: 'bg-green-50' },
  red: { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200', light: 'bg-red-50' },
  orange: { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200', light: 'bg-orange-50' },
  purple: { bg: 'bg-purple-500', text: 'text-purple-600', border: 'border-purple-200', light: 'bg-purple-50' },
  cyan: { bg: 'bg-cyan-500', text: 'text-cyan-600', border: 'border-cyan-200', light: 'bg-cyan-50' },
  emerald: { bg: 'bg-emerald-500', text: 'text-emerald-600', border: 'border-emerald-200', light: 'bg-emerald-50' },
  indigo: { bg: 'bg-indigo-500', text: 'text-indigo-600', border: 'border-indigo-200', light: 'bg-indigo-50' },
  pink: { bg: 'bg-pink-500', text: 'text-pink-600', border: 'border-pink-200', light: 'bg-pink-50' },
  slate: { bg: 'bg-slate-500', text: 'text-slate-600', border: 'border-slate-200', light: 'bg-slate-50' },
  amber: { bg: 'bg-amber-500', text: 'text-amber-600', border: 'border-amber-200', light: 'bg-amber-50' },
  teal: { bg: 'bg-teal-500', text: 'text-teal-600', border: 'border-teal-200', light: 'bg-teal-50' },
  rose: { bg: 'bg-rose-500', text: 'text-rose-600', border: 'border-rose-200', light: 'bg-rose-50' },
  sky: { bg: 'bg-sky-500', text: 'text-sky-600', border: 'border-sky-200', light: 'bg-sky-50' },
  violet: { bg: 'bg-violet-500', text: 'text-violet-600', border: 'border-violet-200', light: 'bg-violet-50' },
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
    }
  })

  const { data: soaMatrix, isLoading: soaMatrixLoading } = useQuery<SOAMatrix>({
    queryKey: ['protocol-soa-matrix'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/soa/matrix`)
      if (!res.ok) throw new Error('Failed to fetch SOA matrix')
      return res.json()
    },
    enabled: activeTab === 'soa'
  })

  const { data: footnotes, isLoading: footnotesLoading } = useQuery<Footnote[]>({
    queryKey: ['protocol-footnotes'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/soa/footnotes`)
      if (!res.ok) throw new Error('Failed to fetch footnotes')
      return res.json()
    },
    enabled: activeTab === 'soa'
  })

  const { data: eligibility, isLoading: eligibilityLoading } = useQuery<EligibilityCriteria>({
    queryKey: ['protocol-eligibility'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/eligibility`)
      if (!res.ok) throw new Error('Failed to fetch eligibility')
      return res.json()
    },
    enabled: activeTab === 'eligibility'
  })

  const { data: domains, isLoading: domainsLoading } = useQuery<DomainSection[]>({
    queryKey: ['protocol-domains'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/domains`)
      if (!res.ok) throw new Error('Failed to fetch domains')
      return res.json()
    },
    enabled: activeTab === 'domains'
  })

  const { data: protocolRules, isLoading: rulesLoading } = useQuery<ProtocolRules>({
    queryKey: ['protocol-rules'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/protocol/rules`)
      if (!res.ok) throw new Error('Failed to fetch protocol rules')
      return res.json()
    },
    enabled: activeTab === 'rules'
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
      case 'person': return 'bg-blue-100 text-blue-800'
      case 'observation': return 'bg-green-100 text-green-800'
      case 'procedure_occurrence': return 'bg-purple-100 text-purple-800'
      case 'condition_occurrence': return 'bg-red-100 text-red-800'
      case 'drug_exposure': return 'bg-yellow-100 text-yellow-800'
      case 'measurement': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getQueryableStatusColor = (status: string) => {
    switch (status) {
      case 'fully_queryable': return 'bg-green-100 text-green-800'
      case 'partially_queryable': return 'bg-yellow-100 text-yellow-800'
      case 'requires_manual': return 'bg-orange-100 text-orange-800'
      case 'screening_only': return 'bg-red-100 text-red-800'
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
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-red-600 font-bold text-sm">PDF</span>
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
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Schedule of Assessments</h3>
            <p className="text-sm text-gray-500 mt-1">Activities and visit schedule matrix</p>
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
    const arms = (data.studyArms as Array<{ name: string; description: string }>) || []
    const epochs = (data.studyEpochs as Array<{ name: string; type: string }>) || []

    return (
      <div className="space-y-6">
        {/* Study Arms */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4" />
            Study Arms ({arms.length})
          </h4>
          <div className="space-y-2">
            {arms.map((arm, i) => (
              <div key={i} className="bg-gradient-to-r from-blue-50 to-white p-4 rounded-lg border border-blue-100">
                <p className="font-medium text-gray-900">{arm.name}</p>
                {arm.description && (
                  <p className="text-sm text-gray-600 mt-1">{arm.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Study Epochs */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Study Epochs ({epochs.length})
          </h4>
          <div className="flex gap-2 flex-wrap">
            {epochs.map((epoch, i) => (
              <div key={i} className="bg-gradient-to-r from-indigo-50 to-white px-4 py-3 rounded-lg border border-indigo-100">
                <p className="font-medium text-gray-900">{epoch.name}</p>
                {epoch.type && (
                  <p className="text-xs text-indigo-600 mt-1">{epoch.type}</p>
                )}
              </div>
            ))}
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
                <div key={i} className="bg-gradient-to-r from-green-50 to-white p-4 rounded-lg border border-green-100">
                  <p className="font-medium text-gray-900">{obj.name || obj}</p>
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
                    <p className="font-medium text-gray-900">{ep.name || ep.outcome_measure || ep}</p>
                    {ep.level && (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        ep.level === 'PRIMARY' ? 'bg-green-100 text-green-800' :
                        ep.level === 'SECONDARY' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {ep.level}
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
                <div key={i} className="bg-gradient-to-r from-purple-50 to-white p-4 rounded-lg border border-purple-100">
                  <p className="font-medium text-gray-900">{est.name || est}</p>
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
            <div className="bg-gradient-to-r from-red-50 to-white p-4 rounded-lg border border-red-100">
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
            <div className="bg-gradient-to-r from-orange-50 to-white p-4 rounded-lg border border-orange-100">
              {saeCriteria.regulatory_criteria && Array.isArray(saeCriteria.regulatory_criteria) && (
                <ul className="space-y-1">
                  {(saeCriteria.regulatory_criteria as string[]).map((c, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-orange-500 mt-1">•</span>
                      {c}
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
    const prohibited = (data.prohibited_medications as Array<{ drug_class?: string; examples?: string[]; reason?: string }>) || []
    const restricted = (data.restricted_medications as Array<{ drug_class?: string; restriction?: string }>) || []
    const required = (data.required_medications as Array<{ medication?: string; indication?: string }>) || []

    return (
      <div className="space-y-6">
        {/* Prohibited */}
        {prohibited.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <X className="w-4 h-4 text-red-500" />
              Prohibited Medications ({prohibited.length})
            </h4>
            <div className="space-y-2">
              {prohibited.map((med, i) => (
                <div key={i} className="bg-gradient-to-r from-red-50 to-white p-4 rounded-lg border border-red-100">
                  <p className="font-medium text-gray-900">{med.drug_class || med}</p>
                  {med.reason && <p className="text-sm text-red-600 mt-1">{med.reason}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Restricted */}
        {restricted.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              Restricted Medications ({restricted.length})
            </h4>
            <div className="space-y-2">
              {restricted.map((med, i) => (
                <div key={i} className="bg-gradient-to-r from-yellow-50 to-white p-4 rounded-lg border border-yellow-100">
                  <p className="font-medium text-gray-900">{med.drug_class || med}</p>
                  {med.restriction && <p className="text-sm text-yellow-700 mt-1">{med.restriction}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Required */}
        {required.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              Required Medications ({required.length})
            </h4>
            <div className="space-y-2">
              {required.map((med, i) => (
                <div key={i} className="bg-gradient-to-r from-green-50 to-white p-4 rounded-lg border border-green-100">
                  <p className="font-medium text-gray-900">{med.medication || med}</p>
                  {med.indication && <p className="text-sm text-green-700 mt-1">{med.indication}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderLaboratory = (data: Record<string, unknown>) => {
    const panels = (data.discovered_panels as string[]) || []
    const tests = (data.laboratory_tests as Array<{ test_name?: string; panel?: string; frequency?: string }>) || []

    return (
      <div className="space-y-6">
        {/* Lab Panels */}
        {panels.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Beaker className="w-4 h-4" />
              Laboratory Panels ({panels.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {panels.map((panel, i) => (
                <span key={i} className="px-3 py-2 bg-gradient-to-r from-emerald-50 to-white rounded-lg border border-emerald-100 text-sm font-medium text-gray-900">
                  {panel}
                </span>
              ))}
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
                    <p className="font-medium text-gray-900">{test.test_name || test}</p>
                    {test.panel && <p className="text-xs text-gray-500">{test.panel}</p>}
                  </div>
                  {test.frequency && (
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">{test.frequency}</span>
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
            <div className="bg-gradient-to-r from-indigo-50 to-white p-4 rounded-lg border border-indigo-100">
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
            <div className="bg-gradient-to-r from-red-50 to-white p-4 rounded-lg border border-red-100">
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
            <div className="bg-gradient-to-r from-green-50 to-white p-4 rounded-lg border border-green-100">
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
            <div key={i} className="bg-gradient-to-r from-pink-50 to-white p-4 rounded-lg border border-pink-100">
              <p className="font-medium text-gray-900">{inst.name || inst.full_name || inst}</p>
              {inst.domains && Array.isArray(inst.domains) && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {inst.domains.map((d, j) => (
                    <span key={j} className="text-xs bg-pink-100 text-pink-700 px-2 py-0.5 rounded">{d}</span>
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
                <div key={i} className="bg-gradient-to-r from-sky-50 to-white p-4 rounded-lg border border-sky-100">
                  <p className="font-medium text-gray-900">{mod.modality_type || mod}</p>
                  {mod.anatomical_region && (
                    <p className="text-sm text-gray-600 mt-1">Region: {mod.anatomical_region}</p>
                  )}
                  {mod.frequency && (
                    <span className="inline-block mt-2 text-xs bg-sky-100 text-sky-700 px-2 py-0.5 rounded">
                      {mod.frequency}
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
                <div key={i} className="bg-gradient-to-r from-rose-50 to-white p-4 rounded-lg border border-rose-100">
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

  const renderGenericDomain = (data: Record<string, unknown>) => {
    // For domains without custom renderers, show a beautiful card-based view
    const entries = Object.entries(data).filter(([key]) =>
      !['id', 'instanceType', 'name', 'provenance', 'extraction_statistics'].includes(key)
    )

    if (entries.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No displayable data available</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {entries.map(([key, value]) => {
          const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

          // Handle arrays
          if (Array.isArray(value) && value.length > 0) {
            return (
              <div key={key}>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">{displayKey} ({value.length})</h4>
                <div className="space-y-2">
                  {value.slice(0, 5).map((item, i) => (
                    <div key={i} className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                      {typeof item === 'object' ? (
                        <pre className="text-xs text-gray-600 overflow-x-auto">
                          {JSON.stringify(item, null, 2)}
                        </pre>
                      ) : (
                        <p className="text-sm text-gray-700">{String(item)}</p>
                      )}
                    </div>
                  ))}
                  {value.length > 5 && (
                    <p className="text-xs text-gray-500 italic">...and {value.length - 5} more</p>
                  )}
                </div>
              </div>
            )
          }

          // Handle objects
          if (typeof value === 'object' && value !== null) {
            return (
              <div key={key}>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">{displayKey}</h4>
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <pre className="text-xs text-gray-600 overflow-x-auto">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              </div>
            )
          }

          // Handle primitives
          return (
            <div key={key} className="flex items-baseline gap-2">
              <span className="text-sm font-medium text-gray-600">{displayKey}:</span>
              <span className="text-sm text-gray-900">{String(value)}</span>
            </div>
          )
        })}
      </div>
    )
  }

  const renderDomains = () => {
    if (domainsLoading || !domains) {
      return <div className="animate-pulse h-48 bg-gray-100 rounded-lg" />
    }

    return (
      <div className="space-y-6">
        {/* Domain Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {domains.map((domain) => {
            const Icon = iconMap[domain.icon] || Database
            const colors = colorMap[domain.color] || colorMap.slate
            const isExpanded = expandedDomain === domain.id
            const hasData = domain.data && Object.keys(domain.data).length > 0

            return (
              <button
                key={domain.id}
                onClick={() => setExpandedDomain(isExpanded ? null : domain.id)}
                className={`
                  relative p-4 rounded-xl border-2 transition-all duration-200 text-left
                  ${isExpanded
                    ? `${colors.border} ${colors.light} shadow-lg scale-[1.02]`
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                  }
                  ${!hasData ? 'opacity-50' : ''}
                `}
                disabled={!hasData}
              >
                <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center mb-3`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm leading-tight">{domain.name}</h3>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{domain.description}</p>
                {isExpanded && (
                  <div className={`absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-4 h-4 rotate-45 ${colors.light} border-b-2 border-r-2 ${colors.border}`} />
                )}
              </button>
            )
          })}
        </div>

        {/* Expanded Domain Content */}
        {expandedDomain && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-lg">
            {(() => {
              const domain = domains.find(d => d.id === expandedDomain)
              if (!domain) return null
              const Icon = iconMap[domain.icon] || Database
              const colors = colorMap[domain.color] || colorMap.slate

              return (
                <>
                  <div className={`p-4 ${colors.light} border-b ${colors.border} flex items-center justify-between`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{domain.name}</h3>
                        <p className="text-sm text-gray-600">{domain.description}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setExpandedDomain(null)}
                      className="text-gray-400 hover:text-gray-600 p-2"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="p-6">
                    {renderDomainContent(domain)}
                  </div>
                </>
              )
            })()}
          </div>
        )}
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
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
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
            <div className="bg-gradient-to-r from-green-50 to-white p-4 rounded-lg border border-green-200">
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
