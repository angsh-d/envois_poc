import React, { useMemo } from 'react'
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2, Info, Globe, BarChart3, Shield } from 'lucide-react'

interface ResponseDisplayProps {
  content: string
  isExpanded?: boolean
}

// Content block types - enhanced for new registry data
type BlockType = 'text' | 'metric' | 'comparison' | 'table' | 'list' | 'alert' | 'highlight' | 'threshold' | 'registry' | 'revision'

interface ContentBlock {
  type: BlockType
  content: string
  data?: Record<string, unknown>
}

// Pattern matchers for smart formatting
const METRIC_PATTERN = /(\d+(?:\.\d+)?%?)\s*(revision rate|survival|mcid|mortality|infection|dislocation|fracture|hazard ratio|hr|risk)/gi
const COMPARISON_PATTERN = /(higher|lower|above|below|exceeds?|within|compared to|versus|vs\.?)\s+([^,.]+(?:\s+(?:benchmark|threshold|rate|target))?)/gi
const ALERT_KEYWORDS = ['exceeds', 'concern', 'warning', 'risk threshold', 'critical', 'elevated', 'signal']
const SUCCESS_KEYWORDS = ['within', 'acceptable', 'meets', 'achieved', 'good', 'excellent']
const PERCENTAGE_VALUE_PATTERN = /(\d+(?:\.\d+)?)\s*%/g
const HR_PATTERN = /(?:hr|hazard ratio)[:\s]+(\d+(?:\.\d+)?)/gi

// New patterns for enhanced registry data
const THRESHOLD_KEYWORDS = ['threshold', 'approaching', 'near threshold', 'proximity', 'within 20%', 'close to']
const REGISTRY_KEYWORDS = ['aoanjrr', 'njr', 'shar', 'ajrr', 'cjrr', 'registry', 'registries', 'international', 'pooled']
const REVISION_KEYWORDS = ['aseptic loosening', 'infection', 'instability', 'pain', 'fracture', 'revision reason', 'cause of revision']

// Parse content into structured blocks
function parseContent(content: string): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const lines = content.split('\n')
  let currentTextBlock = ''

  for (const line of lines) {
    const trimmedLine = line.trim()

    // Skip empty lines
    if (!trimmedLine) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      continue
    }

    // Detect list items
    if (/^[-•*]\s/.test(trimmedLine) || /^\d+\.\s/.test(trimmedLine)) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'list', content: trimmedLine.replace(/^[-•*\d.]\s*/, '') })
      continue
    }

    // Detect tables (lines with | separators)
    if (trimmedLine.includes('|') && trimmedLine.split('|').length >= 3) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'table', content: trimmedLine })
      continue
    }

    // Check for threshold proximity patterns (highest priority for safety)
    const hasThreshold = THRESHOLD_KEYWORDS.some(kw => trimmedLine.toLowerCase().includes(kw))
    if (hasThreshold) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'threshold', content: trimmedLine })
      continue
    }

    // Check for registry comparison patterns
    const hasRegistry = REGISTRY_KEYWORDS.some(kw => trimmedLine.toLowerCase().includes(kw))
    if (hasRegistry && trimmedLine.includes('%')) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'registry', content: trimmedLine })
      continue
    }

    // Check for revision reason patterns
    const hasRevision = REVISION_KEYWORDS.some(kw => trimmedLine.toLowerCase().includes(kw))
    if (hasRevision) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'revision', content: trimmedLine })
      continue
    }

    // Check for alert patterns
    const hasAlert = ALERT_KEYWORDS.some(kw => trimmedLine.toLowerCase().includes(kw))
    const hasSuccess = SUCCESS_KEYWORDS.some(kw => trimmedLine.toLowerCase().includes(kw))

    if (hasAlert) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'alert', content: trimmedLine })
      continue
    }

    if (hasSuccess) {
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'highlight', content: trimmedLine })
      continue
    }

    // Check for metric patterns
    if (METRIC_PATTERN.test(trimmedLine)) {
      METRIC_PATTERN.lastIndex = 0 // Reset regex
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'metric', content: trimmedLine })
      continue
    }

    // Check for comparison patterns
    if (COMPARISON_PATTERN.test(trimmedLine)) {
      COMPARISON_PATTERN.lastIndex = 0 // Reset regex
      if (currentTextBlock) {
        blocks.push({ type: 'text', content: currentTextBlock.trim() })
        currentTextBlock = ''
      }
      blocks.push({ type: 'comparison', content: trimmedLine })
      continue
    }

    // Regular text
    currentTextBlock += (currentTextBlock ? ' ' : '') + trimmedLine
  }

  // Don't forget remaining text
  if (currentTextBlock) {
    blocks.push({ type: 'text', content: currentTextBlock.trim() })
  }

  return blocks
}

// Extract metrics from text - only extract well-formed metric statements
function extractMetrics(text: string): Array<{ value: string; label: string; trend?: 'up' | 'down' | 'neutral' }> {
  const metrics: Array<{ value: string; label: string; trend?: 'up' | 'down' | 'neutral' }> = []
  const seenValues = new Set<string>()

  // Extract percentages with meaningful context (must have a noun/label after)
  // Pattern: percentage followed by a descriptive word (rate, survival, etc.)
  const percentMatches = text.matchAll(/(\d+(?:\.\d+)?%)\s+(revision rate|survival rate|infection rate|dislocation rate|fracture rate|mortality rate|mcid achievement|hazard ratio|risk|improvement)/gi)
  for (const match of percentMatches) {
    const value = match[1]
    const label = match[2].trim()

    // Skip duplicates
    const key = `${value}-${label.toLowerCase()}`
    if (seenValues.has(key)) continue
    seenValues.add(key)

    let trend: 'up' | 'down' | 'neutral' = 'neutral'
    // For rates like revision/infection/fracture, lower is better
    if (/revision|infection|dislocation|fracture|mortality/i.test(label)) {
      trend = 'neutral' // Don't assume trend without context
    }

    metrics.push({ value, label, trend })
  }

  // Extract hazard ratios with clean labels
  const hrMatches = text.matchAll(/(?:hr|hazard ratio)[:\s]+(\d+(?:\.\d+)?)\s*(?:\([^)]+\))?\s*(?:for\s+)?(\w+(?:\s+\w+)?)?/gi)
  for (const match of hrMatches) {
    const value = `HR ${match[1]}`
    const label = match[2]?.trim() || 'Hazard Ratio'

    // Skip if label looks like a number or truncated text
    if (/^\d|^to\s|^CI|^\[/.test(label)) continue

    const key = `${value}-${label.toLowerCase()}`
    if (seenValues.has(key)) continue
    seenValues.add(key)

    metrics.push({
      value,
      label,
      trend: parseFloat(match[1]) > 1.5 ? 'up' : 'neutral'
    })
  }

  return metrics
}

// Metric Card Component
function MetricCard({ value, label, trend }: { value: string; label: string; trend?: 'up' | 'down' | 'neutral' }) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? 'text-gray-600' : trend === 'down' ? 'text-gray-500' : 'text-gray-400'

  return (
    <div className="inline-flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
      <span className="text-[15px] font-semibold text-gray-800">{value}</span>
      <span className="text-[11px] text-gray-500 max-w-[100px] truncate">{label}</span>
      <TrendIcon className={`w-3.5 h-3.5 ${trendColor}`} />
    </div>
  )
}

// Alert Box Component
function AlertBox({ content, type }: { content: string; type: 'warning' | 'success' | 'info' }) {
  const config = {
    warning: {
      bg: 'bg-gray-100',
      border: 'border-gray-300',
      icon: AlertTriangle,
      iconColor: 'text-gray-600'
    },
    success: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: CheckCircle2,
      iconColor: 'text-gray-600'
    },
    info: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: Info,
      iconColor: 'text-gray-600'
    }
  }

  const { bg, border, icon: Icon, iconColor } = config[type]

  return (
    <div className={`flex items-start gap-2 ${bg} ${border} border rounded-lg px-3 py-2`}>
      <Icon className={`w-4 h-4 ${iconColor} flex-shrink-0 mt-0.5`} />
      <p className="text-[13px] text-gray-700 leading-relaxed">{content}</p>
    </div>
  )
}

// Threshold Proximity Alert - specifically for safety threshold warnings
function ThresholdAlert({ content }: { content: string }) {
  return (
    <div className="flex items-start gap-2 bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 shadow-sm">
      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center">
        <AlertTriangle className="w-3 h-3 text-gray-600" />
      </div>
      <div>
        <span className="text-[11px] font-medium text-gray-700 uppercase tracking-wide">Threshold Alert</span>
        <HighlightedText text={content} />
      </div>
    </div>
  )
}

// Registry Comparison Card - for international registry data
function RegistryCard({ content }: { content: string }) {
  // Extract registry name if present
  const registryMatch = content.match(/\b(AOANJRR|NJR|SHAR|AJRR|CJRR)\b/i)
  const registryName = registryMatch ? registryMatch[1].toUpperCase() : null

  return (
    <div className="flex items-start gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
      <Globe className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        {registryName && (
          <span className="inline-block text-[10px] font-semibold text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded mb-1">
            {registryName}
          </span>
        )}
        <HighlightedText text={content} />
      </div>
    </div>
  )
}

// Revision Reason Card - for revision cause breakdowns
function RevisionCard({ content }: { content: string }) {
  // Highlight revision reason keywords
  const highlightedContent = content
    .replace(/(aseptic loosening|infection|instability|pain|fracture)/gi,
      '<strong class="text-gray-800">$1</strong>')

  return (
    <div className="flex items-start gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
      <BarChart3 className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
      <p
        className="text-[13px] text-gray-700 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: highlightedContent }}
      />
    </div>
  )
}

// Comparison Badge Component
function ComparisonBadge({ content }: { content: string }) {
  const isHigher = /higher|above|exceeds/i.test(content)
  const isLower = /lower|below/i.test(content)

  return (
    <div className="flex items-center gap-2">
      {isHigher && <TrendingUp className="w-3.5 h-3.5 text-gray-600" />}
      {isLower && <TrendingDown className="w-3.5 h-3.5 text-gray-500" />}
      <p className="text-[13px] text-gray-700 leading-relaxed">{content}</p>
    </div>
  )
}

// Simple Table Component
function SimpleTable({ rows }: { rows: string[][] }) {
  if (rows.length === 0) return null

  const header = rows[0]
  const body = rows.slice(1).filter(row => !row.every(cell => cell.match(/^[-:]+$/)))

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="bg-gray-50">
            {header.map((cell, i) => (
              <th key={i} className="px-3 py-2 text-left font-medium text-gray-600 border-b border-gray-200">
                {cell.trim()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-gray-700 border-b border-gray-100">
                  {cell.trim()}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Convert markdown to React elements
function parseMarkdown(text: string): React.ReactNode[] {
  const elements: React.ReactNode[] = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Check for bold (**text**)
    const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/)
    if (boldMatch) {
      elements.push(<strong key={key++} className="font-semibold">{boldMatch[1]}</strong>)
      remaining = remaining.slice(boldMatch[0].length)
      continue
    }

    // Check for italic (*text*)
    const italicMatch = remaining.match(/^\*([^*]+)\*/)
    if (italicMatch) {
      elements.push(<em key={key++} className="italic">{italicMatch[1]}</em>)
      remaining = remaining.slice(italicMatch[0].length)
      continue
    }

    // Check for percentage values
    const percentMatch = remaining.match(/^(\d+(?:\.\d+)?%)/)
    if (percentMatch) {
      elements.push(
        <span key={key++} className="font-semibold text-gray-800 bg-gray-100 px-1 rounded">
          {percentMatch[1]}
        </span>
      )
      remaining = remaining.slice(percentMatch[0].length)
      continue
    }

    // Check for hazard ratios
    const hrMatch = remaining.match(/^(HR\s*\d+(?:\.\d+)?)/i)
    if (hrMatch) {
      elements.push(
        <span key={key++} className="font-semibold text-purple-600 bg-purple-50 px-1 rounded">
          {hrMatch[1]}
        </span>
      )
      remaining = remaining.slice(hrMatch[0].length)
      continue
    }

    // Find the next special pattern
    const nextSpecial = remaining.search(/\*\*|\*(?=[^*])|\d+(?:\.\d+)?%|HR\s*\d+/i)
    if (nextSpecial === -1) {
      // No more special patterns, add the rest as plain text
      elements.push(remaining)
      break
    } else if (nextSpecial === 0) {
      // Edge case: pattern didn't match above, move one character forward
      elements.push(remaining[0])
      remaining = remaining.slice(1)
    } else {
      // Add plain text up to the next special pattern
      elements.push(remaining.slice(0, nextSpecial))
      remaining = remaining.slice(nextSpecial)
    }
  }

  return elements
}

// Highlighted text with inline metrics and markdown support
function HighlightedText({ text }: { text: string }) {
  const elements = parseMarkdown(text)

  return (
    <p className="text-[14px] leading-relaxed text-gray-800">
      {elements}
    </p>
  )
}

export function ResponseDisplay({ content, isExpanded = false }: ResponseDisplayProps) {
  const blocks = useMemo(() => parseContent(content), [content])

  // Collect table rows if consecutive table blocks
  const processedBlocks = useMemo(() => {
    const result: Array<ContentBlock | { type: 'tableGroup'; rows: string[][] }> = []
    let tableRows: string[][] = []

    for (const block of blocks) {
      if (block.type === 'table') {
        const cells = block.content.split('|').map(c => c.trim()).filter(c => c)
        tableRows.push(cells)
      } else {
        if (tableRows.length > 0) {
          result.push({ type: 'tableGroup', rows: tableRows })
          tableRows = []
        }
        result.push(block)
      }
    }

    if (tableRows.length > 0) {
      result.push({ type: 'tableGroup', rows: tableRows })
    }

    return result
  }, [blocks])

  // Collect list items if consecutive
  const finalBlocks = useMemo(() => {
    const result: Array<ContentBlock | { type: 'tableGroup'; rows: string[][] } | { type: 'listGroup'; items: string[] }> = []
    let listItems: string[] = []

    for (const block of processedBlocks) {
      if (block.type === 'list') {
        listItems.push(block.content)
      } else {
        if (listItems.length > 0) {
          result.push({ type: 'listGroup', items: listItems })
          listItems = []
        }
        result.push(block)
      }
    }

    if (listItems.length > 0) {
      result.push({ type: 'listGroup', items: listItems })
    }

    return result
  }, [processedBlocks])

  // Extract top-level metrics for expanded view
  const topMetrics = useMemo(() => {
    if (!isExpanded) return []
    return extractMetrics(content).slice(0, 4)
  }, [content, isExpanded])

  return (
    <div className="space-y-3">
      {/* Top metrics bar in expanded mode */}
      {isExpanded && topMetrics.length > 0 && (
        <div className="flex flex-wrap gap-2 pb-2 border-b border-gray-100">
          {topMetrics.map((metric, i) => (
            <MetricCard key={i} {...metric} />
          ))}
        </div>
      )}

      {/* Render blocks */}
      {finalBlocks.map((block, i) => {
        if (block.type === 'tableGroup' && 'rows' in block) {
          return <SimpleTable key={i} rows={block.rows} />
        }

        if (block.type === 'listGroup' && 'items' in block) {
          return (
            <ul key={i} className="space-y-1 ml-1">
              {block.items.map((item, j) => (
                <li key={j} className="flex items-start gap-2 text-[13px] text-gray-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#007aff] mt-2 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )
        }

        switch (block.type) {
          case 'threshold':
            return <ThresholdAlert key={i} content={block.content} />

          case 'registry':
            return <RegistryCard key={i} content={block.content} />

          case 'revision':
            return <RevisionCard key={i} content={block.content} />

          case 'alert':
            return <AlertBox key={i} content={block.content} type="warning" />

          case 'highlight':
            return <AlertBox key={i} content={block.content} type="success" />

          case 'metric':
            return <HighlightedText key={i} text={block.content} />

          case 'comparison':
            return <ComparisonBadge key={i} content={block.content} />

          case 'text':
          default:
            return <HighlightedText key={i} text={block.content} />
        }
      })}
    </div>
  )
}
