import React from 'react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import { ChartConfig, ChartDataPoint } from '../lib/api'

interface ChatChartProps {
  config: ChartConfig
}

// Transform series data for Recharts format
function transformData(config: ChartConfig): Record<string, unknown>[] {
  const { series } = config
  if (!series || series.length === 0) return []

  // Get all unique x values across series
  const xValues = new Set<string | number>()
  series.forEach(s => {
    s.data.forEach(d => xValues.add(d.x))
  })

  // Create data points for each x value
  return Array.from(xValues).map(x => {
    const point: Record<string, unknown> = { x }
    series.forEach(s => {
      const match = s.data.find(d => d.x === x)
      if (match) {
        point[s.name] = match.y
        if (match.ci_lower !== undefined) {
          point[`${s.name}_ci_lower`] = match.ci_lower
        }
        if (match.ci_upper !== undefined) {
          point[`${s.name}_ci_upper`] = match.ci_upper
        }
      }
    })
    return point
  })
}

// Default colors if not specified
const DEFAULT_COLORS = [
  '#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2'
]

export function ChatChart({ config }: ChatChartProps) {
  const {
    chart_type,
    title,
    x_label,
    y_label,
    series,
    reference_lines,
    y_domain,
    show_legend = true,
    show_grid = true
  } = config

  const data = transformData(config)

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data available for chart
      </div>
    )
  }

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 10, right: 30, left: 10, bottom: 10 }
    }

    const axisProps = {
      xAxis: (
        <XAxis
          dataKey="x"
          tick={{ fontSize: 11, fill: '#6b7280' }}
          label={x_label ? { value: x_label, position: 'insideBottom', offset: -5, fontSize: 11, fill: '#374151' } : undefined}
        />
      ),
      yAxis: (
        <YAxis
          domain={y_domain || ['auto', 'auto']}
          tick={{ fontSize: 11, fill: '#6b7280' }}
          label={y_label ? { value: y_label, angle: -90, position: 'insideLeft', fontSize: 11, fill: '#374151' } : undefined}
        />
      )
    }

    const referenceLineElements = reference_lines?.map((ref, i) => (
      <ReferenceLine
        key={i}
        y={ref.y}
        stroke={ref.color || '#9ca3af'}
        strokeDasharray={ref.strokeDasharray || '3 3'}
        label={{ value: ref.label, position: 'right', fontSize: 10, fill: '#6b7280' }}
      />
    ))

    switch (chart_type) {
      case 'line':
      case 'kaplan_meier':
        return (
          <LineChart {...commonProps}>
            {show_grid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {axisProps.xAxis}
            {axisProps.yAxis}
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            />
            {show_legend && <Legend wrapperStyle={{ fontSize: 11 }} />}
            {series.map((s, i) => (
              <Line
                key={s.name}
                type={chart_type === 'kaplan_meier' ? 'stepAfter' : 'monotone'}
                dataKey={s.name}
                stroke={s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
            {referenceLineElements}
          </LineChart>
        )

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {show_grid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {axisProps.xAxis}
            {axisProps.yAxis}
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            />
            {show_legend && <Legend wrapperStyle={{ fontSize: 11 }} />}
            {series.map((s, i) => (
              <Bar
                key={s.name}
                dataKey={s.name}
                fill={s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
            {referenceLineElements}
          </BarChart>
        )

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {show_grid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {axisProps.xAxis}
            {axisProps.yAxis}
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            />
            {show_legend && <Legend wrapperStyle={{ fontSize: 11 }} />}
            {series.map((s, i) => (
              <Area
                key={s.name}
                type="monotone"
                dataKey={s.name}
                stroke={s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
                fill={s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
                fillOpacity={0.3}
              />
            ))}
            {referenceLineElements}
          </AreaChart>
        )

      default:
        return (
          <LineChart {...commonProps}>
            {show_grid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
            {axisProps.xAxis}
            {axisProps.yAxis}
            <Tooltip />
            {show_legend && <Legend />}
            {series.map((s, i) => (
              <Line
                key={s.name}
                type="monotone"
                dataKey={s.name}
                stroke={s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
              />
            ))}
          </LineChart>
        )
    }
  }

  return (
    <div className="w-full bg-white rounded-lg border border-gray-200 p-4">
      {title && (
        <h4 className="text-[14px] font-semibold text-gray-800 mb-3">{title}</h4>
      )}
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
