/**
 * Intelligent Caching Service
 *
 * Two-tier caching with memory (fast) + localStorage (persistent)
 * - Memory cache: Session-scoped, instant access
 * - localStorage: Persistent across page reloads with TTL
 */

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

// Default TTL values in milliseconds
// All data is cached for 48 hours for optimal performance
export const CACHE_TTL = {
  SHORT: 4 * 60 * 60 * 1000,       // 4 hours - for frequently accessed data
  MEDIUM: 12 * 60 * 60 * 1000,     // 12 hours - for most API data
  LONG: 24 * 60 * 60 * 1000,       // 24 hours - for stable data
  EXTENDED: 48 * 60 * 60 * 1000,   // 48 hours - for reference data (default)
} as const

// Cache keys for type safety
export const CACHE_KEYS = {
  READINESS: 'cip_readiness',
  SAFETY: 'cip_safety',
  RISK: 'cip_risk',
  COMPETITIVE_LANDSCAPE: 'cip_competitive_landscape',
  COMPETITIVE_BENCHMARKS: 'cip_competitive_benchmarks',
  BATTLE_CARD: 'cip_battle_card',
  DIFFERENTIATORS: 'cip_differentiators',
  TALKING_POINTS: 'cip_talking_points',
  DASHBOARD_SUMMARY: 'cip_dashboard_summary',
  DASHBOARD_PROGRESS: 'cip_dashboard_progress',
  DASHBOARD_BENCHMARKS: 'cip_dashboard_benchmarks',
  PORTFOLIO_STATS: 'cip_portfolio_stats',
} as const

type CacheKey = typeof CACHE_KEYS[keyof typeof CACHE_KEYS]

// In-memory cache for instant access
const memoryCache = new Map<string, CacheEntry<unknown>>()

/**
 * Set a value in the cache
 */
export function setCache<T>(key: CacheKey, data: T, ttl: number = CACHE_TTL.MEDIUM): void {
  const entry: CacheEntry<T> = {
    data,
    timestamp: Date.now(),
    ttl,
  }

  // Set in memory cache
  memoryCache.set(key, entry)

  // Persist to localStorage
  try {
    localStorage.setItem(key, JSON.stringify(entry))
  } catch (e) {
    console.warn('Failed to persist cache to localStorage:', e)
  }
}

/**
 * Get a value from the cache
 * Returns null if not found or expired
 */
export function getCache<T>(key: CacheKey): T | null {
  // First check memory cache (fastest)
  const memEntry = memoryCache.get(key) as CacheEntry<T> | undefined
  if (memEntry) {
    const age = Date.now() - memEntry.timestamp
    if (age < memEntry.ttl) {
      return memEntry.data
    }
    // Expired - remove from memory
    memoryCache.delete(key)
  }

  // Fall back to localStorage
  try {
    const stored = localStorage.getItem(key)
    if (stored) {
      const entry: CacheEntry<T> = JSON.parse(stored)
      const age = Date.now() - entry.timestamp
      if (age < entry.ttl) {
        // Restore to memory cache for faster subsequent access
        memoryCache.set(key, entry)
        return entry.data
      }
      // Expired - remove from localStorage
      localStorage.removeItem(key)
    }
  } catch (e) {
    console.warn('Failed to read cache from localStorage:', e)
  }

  return null
}

/**
 * Clear a specific cache entry
 */
export function clearCache(key: CacheKey): void {
  memoryCache.delete(key)
  try {
    localStorage.removeItem(key)
  } catch (e) {
    console.warn('Failed to clear localStorage cache:', e)
  }
}

/**
 * Clear all cache entries
 */
export function clearAllCache(): void {
  memoryCache.clear()
  try {
    Object.values(CACHE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
  } catch (e) {
    console.warn('Failed to clear all localStorage cache:', e)
  }
}

/**
 * Get cache status for debugging
 */
export function getCacheStatus(): Record<string, { valid: boolean; age: number | null }> {
  const status: Record<string, { valid: boolean; age: number | null }> = {}

  Object.values(CACHE_KEYS).forEach(key => {
    const memEntry = memoryCache.get(key)
    if (memEntry) {
      const age = Date.now() - memEntry.timestamp
      status[key] = { valid: age < memEntry.ttl, age }
    } else {
      try {
        const stored = localStorage.getItem(key)
        if (stored) {
          const entry = JSON.parse(stored)
          const age = Date.now() - entry.timestamp
          status[key] = { valid: age < entry.ttl, age }
        } else {
          status[key] = { valid: false, age: null }
        }
      } catch {
        status[key] = { valid: false, age: null }
      }
    }
  })

  return status
}

/**
 * Cached fetch wrapper - fetches data with automatic caching
 */
export async function cachedFetch<T>(
  key: CacheKey,
  fetcher: () => Promise<T>,
  ttl: number = CACHE_TTL.MEDIUM,
  forceRefresh: boolean = false
): Promise<T> {
  // Check cache first (unless force refresh)
  if (!forceRefresh) {
    const cached = getCache<T>(key)
    if (cached !== null) {
      return cached
    }
  }

  // Fetch fresh data
  const data = await fetcher()

  // Cache the result
  setCache(key, data, ttl)

  return data
}

/**
 * Prefetch multiple cache entries in parallel
 * Useful for preloading data on app init
 */
export async function prefetchCache(
  entries: Array<{ key: CacheKey; fetcher: () => Promise<unknown>; ttl?: number }>
): Promise<void> {
  await Promise.allSettled(
    entries.map(async ({ key, fetcher, ttl }) => {
      const cached = getCache(key)
      if (cached === null) {
        try {
          const data = await fetcher()
          setCache(key, data, ttl ?? CACHE_TTL.MEDIUM)
        } catch (e) {
          console.warn(`Failed to prefetch ${key}:`, e)
        }
      }
    })
  )
}

/**
 * Subscribe to cache updates (for React components)
 */
type CacheListener = (key: CacheKey, data: unknown) => void
const listeners = new Set<CacheListener>()

export function subscribeToCacheUpdates(listener: CacheListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

// Notify listeners when cache is updated
function notifyListeners(key: CacheKey, data: unknown): void {
  listeners.forEach(listener => listener(key, data))
}

// Enhanced setCache that notifies listeners
export function setCacheWithNotify<T>(key: CacheKey, data: T, ttl: number = CACHE_TTL.MEDIUM): void {
  setCache(key, data, ttl)
  notifyListeners(key, data)
}
