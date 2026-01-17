import { useState, useEffect, useCallback } from 'react'
import { AlertTriangle, X, ChevronDown, ChevronUp, Check, ExternalLink } from 'lucide-react'
import { fetchSafetyAlerts, acknowledgeAlert, SafetyAlert, AlertSeverity } from '@/lib/api'

interface SafetyAlertBannerProps {
  studyId?: string
  onAlertClick?: (alert: SafetyAlert) => void
}

export function SafetyAlertBanner({ onAlertClick }: SafetyAlertBannerProps) {
  const [alerts, setAlerts] = useState<SafetyAlert[]>([])
  const [criticalCount, setCriticalCount] = useState(0)
  const [warningCount, setWarningCount] = useState(0)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isDismissed, setIsDismissed] = useState(false)
  const [proactiveInsights, setProactiveInsights] = useState<string[]>([])

  const loadAlerts = useCallback(async () => {
    try {
      setIsLoading(true)
      const summary = await fetchSafetyAlerts(undefined, false)
      setAlerts(summary.alerts)
      setCriticalCount(summary.critical_count)
      setWarningCount(summary.warning_count)
      setProactiveInsights(summary.proactive_insights)
    } catch (error) {
      console.error('Failed to load safety alerts:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
    // Refresh alerts every 60 seconds
    const interval = setInterval(loadAlerts, 60000)
    return () => clearInterval(interval)
  }, [loadAlerts])

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId)
      // Refresh alerts after acknowledging
      await loadAlerts()
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const getSeverityStyles = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-gray-100',
          border: 'border-gray-300',
          text: 'text-gray-900',
          badge: 'bg-gray-800 text-white',
          icon: 'text-gray-800'
        }
      case 'warning':
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-800',
          badge: 'bg-gray-200 text-gray-700',
          icon: 'text-gray-600'
        }
      case 'info':
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          badge: 'bg-gray-100 text-gray-600',
          icon: 'text-gray-500'
        }
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-800',
          badge: 'bg-gray-100 text-gray-700',
          icon: 'text-gray-600'
        }
    }
  }

  // Don't render if no alerts or dismissed
  if (isLoading || alerts.length === 0 || isDismissed) {
    return null
  }

  const totalAlerts = alerts.length
  const hasCritical = criticalCount > 0

  return (
    <div className={`w-full ${hasCritical ? 'bg-gray-100 border-gray-300' : 'bg-gray-50 border-gray-200'} border-b`}>
      {/* Header Bar */}
      <div className="px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 ${hasCritical ? 'text-gray-800' : 'text-gray-700'}`}>
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium text-sm">Safety Alerts</span>
          </div>

          {/* Alert counts */}
          <div className="flex items-center gap-2">
            {criticalCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-gray-800 text-white rounded-full">
                {criticalCount} critical
              </span>
            )}
            {warningCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-gray-200 text-gray-700 rounded-full">
                {warningCount} warning
              </span>
            )}
          </div>

          {/* Proactive insight preview */}
          {proactiveInsights.length > 0 && !isExpanded && (
            <span className="text-xs text-gray-600 hidden md:block truncate max-w-[300px]">
              {proactiveInsights[0]}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded ${
              hasCritical ? 'text-gray-800 hover:bg-gray-200' : 'text-gray-700 hover:bg-gray-100'
            } transition-colors`}
          >
            {isExpanded ? 'Hide Details' : 'View Details'}
            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <button
            onClick={() => setIsDismissed(true)}
            className={`p-1 rounded ${
              hasCritical ? 'text-gray-500 hover:text-gray-700 hover:bg-gray-200' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            } transition-colors`}
            title="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Expanded Alert List */}
      {isExpanded && (
        <div className="px-4 pb-3 space-y-2">
          {/* Proactive Insights Section */}
          {proactiveInsights.length > 0 && (
            <div className="mb-3 p-3 bg-white/60 rounded-lg border border-gray-200">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Proactive Insights</h4>
              <ul className="space-y-1">
                {proactiveInsights.map((insight, idx) => (
                  <li key={idx} className="text-xs text-gray-600 flex items-start gap-2">
                    <span className="w-1 h-1 rounded-full bg-gray-400 mt-1.5 flex-shrink-0" />
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Alert Cards */}
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
            {alerts.slice(0, 6).map((alert) => {
              const styles = getSeverityStyles(alert.severity)
              return (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border ${styles.bg} ${styles.border} cursor-pointer hover:shadow-sm transition-shadow`}
                  onClick={() => onAlertClick?.(alert)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${styles.badge}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="text-[10px] text-gray-500">{alert.metric_name}</span>
                      </div>
                      <h5 className={`text-sm font-medium ${styles.text} truncate`}>{alert.title}</h5>
                      <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">{alert.description}</p>

                      {/* Values */}
                      <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-500">
                        <span>Current: <strong className={styles.text}>{alert.current_value.toFixed(1)}%</strong></span>
                        {alert.threshold_value && (
                          <span>Threshold: {alert.threshold_value.toFixed(1)}%</span>
                        )}
                        {alert.trend_direction && (
                          <span className={alert.trend_direction === 'increasing' ? 'text-gray-800' : 'text-gray-500'}>
                            {alert.trend_direction === 'increasing' ? '↑' : alert.trend_direction === 'decreasing' ? '↓' : '→'}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleAcknowledge(alert.id)
                        }}
                        className={`p-1 rounded ${styles.badge} hover:opacity-80 transition-opacity`}
                        title="Acknowledge alert"
                      >
                        <Check className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onAlertClick?.(alert)
                        }}
                        className={`p-1 rounded ${styles.badge} hover:opacity-80 transition-opacity`}
                        title="View details"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Recommendations preview */}
                  {alert.recommendations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200/50">
                      <p className="text-[10px] text-gray-500 truncate">
                        Recommendation: {alert.recommendations[0]}
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {alerts.length > 6 && (
            <div className="text-center">
              <span className="text-xs text-gray-500">
                + {alerts.length - 6} more alerts
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
