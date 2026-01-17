/**
 * Cached API Layer
 *
 * Wraps all API calls with intelligent caching for optimal performance
 * and reduced API load. Provides cached versions of all core API functions.
 */

import {
  fetchReadiness,
  fetchSafetySignals,
  fetchRiskSummary,
  fetchCompetitiveLandscape,
  fetchCompetitiveBenchmarking,
  fetchBattleCard,
  fetchDifferentiators,
  fetchTalkingPoints,
  fetchDashboardExecutiveSummary,
  fetchDashboardStudyProgress,
  fetchDashboardBenchmarks,
  ReadinessResponse,
  SafetyResponse,
  RiskSummaryResponse,
  CompetitiveLandscapeResponse,
  BenchmarkingResponse,
  BattleCardResponse,
  DashboardExecutiveSummary,
  DashboardStudyProgress,
  DashboardBenchmarks,
} from './api'

import {
  cachedFetch,
  CACHE_KEYS,
  CACHE_TTL,
  prefetchCache,
  getCache,
  clearCache,
  clearAllCache,
} from './cache'

// ============================================================================
// Cached Core Data APIs
// ============================================================================

export async function getCachedReadiness(forceRefresh = false): Promise<ReadinessResponse> {
  return cachedFetch(
    CACHE_KEYS.READINESS,
    fetchReadiness,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedSafety(forceRefresh = false): Promise<SafetyResponse> {
  return cachedFetch(
    CACHE_KEYS.SAFETY,
    fetchSafetySignals,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedRisk(forceRefresh = false): Promise<RiskSummaryResponse> {
  return cachedFetch(
    CACHE_KEYS.RISK,
    fetchRiskSummary,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

// ============================================================================
// Cached Competitive Intelligence APIs
// ============================================================================

export async function getCachedCompetitiveLandscape(forceRefresh = false): Promise<CompetitiveLandscapeResponse> {
  return cachedFetch(
    CACHE_KEYS.COMPETITIVE_LANDSCAPE,
    fetchCompetitiveLandscape,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedBenchmarking(forceRefresh = false): Promise<BenchmarkingResponse> {
  return cachedFetch(
    CACHE_KEYS.COMPETITIVE_BENCHMARKS,
    fetchCompetitiveBenchmarking,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedBattleCard(forceRefresh = false): Promise<BattleCardResponse> {
  return cachedFetch(
    CACHE_KEYS.BATTLE_CARD,
    fetchBattleCard,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedDifferentiators(forceRefresh = false): Promise<{
  success: boolean
  generated_at: string
  product: string
  differentiators: Array<{ category: string; differentiator: string; evidence: string }>
  sources: Array<Record<string, unknown>>
}> {
  return cachedFetch(
    CACHE_KEYS.DIFFERENTIATORS,
    fetchDifferentiators,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedTalkingPoints(forceRefresh = false): Promise<{
  success: boolean
  generated_at: string
  product: string
  talking_points: string[]
  quick_stats: Array<{ stat: string; value: string; context: string }>
  sources: Array<Record<string, unknown>>
}> {
  return cachedFetch(
    CACHE_KEYS.TALKING_POINTS,
    fetchTalkingPoints,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

// ============================================================================
// Cached Dashboard APIs
// ============================================================================

export async function getCachedDashboardSummary(forceRefresh = false): Promise<DashboardExecutiveSummary> {
  return cachedFetch(
    CACHE_KEYS.DASHBOARD_SUMMARY,
    fetchDashboardExecutiveSummary,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedDashboardProgress(forceRefresh = false): Promise<DashboardStudyProgress> {
  return cachedFetch(
    CACHE_KEYS.DASHBOARD_PROGRESS,
    fetchDashboardStudyProgress,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

export async function getCachedDashboardBenchmarks(forceRefresh = false): Promise<DashboardBenchmarks> {
  return cachedFetch(
    CACHE_KEYS.DASHBOARD_BENCHMARKS,
    fetchDashboardBenchmarks,
    CACHE_TTL.EXTENDED,
    forceRefresh
  )
}

// ============================================================================
// Portfolio Stats (Composite data for Landing Page)
// ============================================================================

export interface PortfolioStats {
  studyCount: number
  safetySignals: number
  criticalAlerts: number
  readinessScore: number
  overallStatus: 'healthy' | 'attention' | 'critical'
  lastUpdated: string
}

export async function getCachedPortfolioStats(forceRefresh = false): Promise<PortfolioStats> {
  const cacheKey = CACHE_KEYS.PORTFOLIO_STATS

  if (!forceRefresh) {
    const cached = getCache<PortfolioStats>(cacheKey)
    if (cached) return cached
  }

  // Aggregate data from multiple sources
  const [readiness, safety, risk] = await Promise.allSettled([
    getCachedReadiness(forceRefresh),
    getCachedSafety(forceRefresh),
    getCachedRisk(forceRefresh),
  ])

  const readinessData = readiness.status === 'fulfilled' ? readiness.value : null
  const safetyData = safety.status === 'fulfilled' ? safety.value : null
  const riskData = risk.status === 'fulfilled' ? risk.value : null

  // Calculate composite readiness score
  let readinessScore = 0
  if (readinessData) {
    readinessScore = Math.round(
      (readinessData.enrollment.percent_complete * 0.3 +
        readinessData.data_completeness.completion_rate * 0.3 +
        (readinessData.compliance.deviation_rate < 5 ? 100 : readinessData.compliance.deviation_rate < 10 ? 80 : 60) * 0.2 +
        (readinessData.safety.n_signals === 0 ? 100 : readinessData.safety.n_signals <= 2 ? 80 : 60) * 0.2)
    )
  }

  // Determine overall status
  const safetySignals = safetyData?.n_signals ?? 0
  const highRiskPct = riskData?.high_risk_pct ?? 0
  const criticalAlerts = safetyData?.high_priority.length ?? 0

  let overallStatus: 'healthy' | 'attention' | 'critical' = 'healthy'
  if (criticalAlerts > 0 || highRiskPct > 20) {
    overallStatus = 'critical'
  } else if (safetySignals > 0 || highRiskPct > 10 || readinessScore < 70) {
    overallStatus = 'attention'
  }

  const stats: PortfolioStats = {
    studyCount: 1, // Currently single study
    safetySignals,
    criticalAlerts,
    readinessScore,
    overallStatus,
    lastUpdated: new Date().toISOString(),
  }

  // Cache with short TTL since it's composite
  cachedFetch(
    cacheKey,
    async () => stats,
    CACHE_TTL.SHORT,
    true
  )

  return stats
}

// ============================================================================
// Prefetch Utilities
// ============================================================================

/**
 * Prefetch all essential data for the dashboard experience
 * Call this on app init or when entering study context
 */
export async function prefetchDashboardData(): Promise<void> {
  await prefetchCache([
    { key: CACHE_KEYS.READINESS, fetcher: fetchReadiness, ttl: CACHE_TTL.EXTENDED },
    { key: CACHE_KEYS.SAFETY, fetcher: fetchSafetySignals, ttl: CACHE_TTL.EXTENDED },
    { key: CACHE_KEYS.RISK, fetcher: fetchRiskSummary, ttl: CACHE_TTL.EXTENDED },
    { key: CACHE_KEYS.DASHBOARD_SUMMARY, fetcher: fetchDashboardExecutiveSummary, ttl: CACHE_TTL.EXTENDED },
  ])
}

/**
 * Prefetch competitive intelligence data
 * Call this when entering competitive modules
 */
export async function prefetchCompetitiveData(): Promise<void> {
  await prefetchCache([
    { key: CACHE_KEYS.COMPETITIVE_LANDSCAPE, fetcher: fetchCompetitiveLandscape, ttl: CACHE_TTL.EXTENDED },
    { key: CACHE_KEYS.COMPETITIVE_BENCHMARKS, fetcher: fetchCompetitiveBenchmarking, ttl: CACHE_TTL.EXTENDED },
    { key: CACHE_KEYS.BATTLE_CARD, fetcher: fetchBattleCard, ttl: CACHE_TTL.EXTENDED },
  ])
}

/**
 * Refresh all cached data (for pull-to-refresh or manual refresh)
 */
export async function refreshAllData(): Promise<void> {
  clearAllCache()
  await prefetchDashboardData()
}

/**
 * Refresh specific module data
 */
export async function refreshModuleData(module: 'readiness' | 'safety' | 'risk' | 'competitive' | 'dashboard'): Promise<void> {
  switch (module) {
    case 'readiness':
      clearCache(CACHE_KEYS.READINESS)
      await getCachedReadiness(true)
      break
    case 'safety':
      clearCache(CACHE_KEYS.SAFETY)
      await getCachedSafety(true)
      break
    case 'risk':
      clearCache(CACHE_KEYS.RISK)
      await getCachedRisk(true)
      break
    case 'competitive':
      clearCache(CACHE_KEYS.COMPETITIVE_LANDSCAPE)
      clearCache(CACHE_KEYS.COMPETITIVE_BENCHMARKS)
      clearCache(CACHE_KEYS.BATTLE_CARD)
      await prefetchCompetitiveData()
      break
    case 'dashboard':
      clearCache(CACHE_KEYS.DASHBOARD_SUMMARY)
      clearCache(CACHE_KEYS.DASHBOARD_PROGRESS)
      clearCache(CACHE_KEYS.DASHBOARD_BENCHMARKS)
      await Promise.all([
        getCachedDashboardSummary(true),
        getCachedDashboardProgress(true),
        getCachedDashboardBenchmarks(true),
      ])
      break
  }
}

// Re-export cache utilities for convenience
export { clearCache, clearAllCache, getCache } from './cache'
