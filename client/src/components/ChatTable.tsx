import React, { useMemo, useState } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { TableConfig, HighlightRule } from '../lib/api'

interface ChatTableProps {
  config: TableConfig
}

type SortDirection = 'asc' | 'desc' | null

function formatCellValue(value: unknown, format: string): string {
  if (value === null || value === undefined) return '-'

  switch (format) {
    case 'percent':
      if (typeof value === 'number') {
        // If value is already a decimal (0-1), multiply by 100
        const pct = value <= 1 && value >= 0 ? value * 100 : value
        return `${pct.toFixed(1)}%`
      }
      return String(value)

    case 'number':
      if (typeof value === 'number') {
        return value.toFixed(2)
      }
      return String(value)

    case 'date':
      if (value instanceof Date) {
        return value.toLocaleDateString()
      }
      if (typeof value === 'string') {
        return new Date(value).toLocaleDateString()
      }
      return String(value)

    case 'text':
    default:
      return String(value)
  }
}

function getCellStyle(
  value: unknown,
  columnKey: string,
  rules?: HighlightRule[]
): string {
  if (!rules) return ''

  for (const rule of rules) {
    if (rule.column !== columnKey) continue

    let matches = false
    switch (rule.condition) {
      case 'equals':
        matches = value === rule.value || String(value).toLowerCase() === String(rule.value).toLowerCase()
        break
      case 'greater_than':
        matches = typeof value === 'number' && value > Number(rule.value)
        break
      case 'less_than':
        matches = typeof value === 'number' && value < Number(rule.value)
        break
      case 'contains':
        matches = String(value).toLowerCase().includes(String(rule.value).toLowerCase())
        break
    }

    if (matches) {
      switch (rule.style) {
        case 'danger':
          return 'bg-red-50 text-red-700'
        case 'warning':
          return 'bg-amber-50 text-amber-700'
        case 'success':
          return 'bg-green-50 text-green-700'
      }
    }
  }

  return ''
}

export function ChatTable({ config }: ChatTableProps) {
  const { title, columns, rows, sortable, highlight_rules } = config
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const sortedRows = useMemo(() => {
    if (!sortColumn || !sortDirection) return rows

    return [...rows].sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]

      if (aVal === bVal) return 0
      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      const comparison = aVal < bVal ? -1 : 1
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [rows, sortColumn, sortDirection])

  const handleSort = (columnKey: string) => {
    if (!sortable) return

    if (sortColumn === columnKey) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="w-3.5 h-3.5 text-gray-600" />
    }
    return <ArrowDown className="w-3.5 h-3.5 text-gray-600" />
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        No data available
      </div>
    )
  }

  return (
    <div className="w-full bg-white rounded-lg border border-gray-200 overflow-hidden">
      {title && (
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
          <h4 className="text-[14px] font-semibold text-gray-800">{title}</h4>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {columns.map(col => (
                <th
                  key={col.key}
                  className={`px-4 py-2.5 text-left font-medium text-gray-600 ${
                    sortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''
                  }`}
                  onClick={() => handleSort(col.key)}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.label}</span>
                    {sortable && getSortIcon(col.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`border-b border-gray-100 ${
                  rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                } hover:bg-gray-50`}
              >
                {columns.map(col => {
                  const cellValue = row[col.key]
                  const cellStyle = getCellStyle(cellValue, col.key, highlight_rules)

                  return (
                    <td
                      key={col.key}
                      className={`px-4 py-2.5 text-gray-700 ${cellStyle}`}
                    >
                      {formatCellValue(cellValue, col.format)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-[11px] text-gray-500">
        {rows.length} row{rows.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}
