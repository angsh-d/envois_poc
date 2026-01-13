import type { CSSProperties } from 'react'

interface SkeletonProps {
  className?: string
  style?: CSSProperties
}

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-gray-100',
        className
      )}
    />
  )
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div className={cn('bg-white rounded-2xl border border-gray-100 p-6', className)}>
      <Skeleton className="h-4 w-1/3 mb-4" />
      <Skeleton className="h-8 w-2/3 mb-2" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  )
}

export function SkeletonMetricCard({ className }: SkeletonProps) {
  return (
    <div className={cn('bg-white rounded-2xl border border-gray-100 p-5', className)}>
      <div className="flex items-start justify-between mb-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-8 w-20 mb-1" />
      <Skeleton className="h-3 w-16" />
    </div>
  )
}

export function SkeletonTable({ rows = 5, className }: { rows?: number } & SkeletonProps) {
  return (
    <div className={cn('bg-white rounded-2xl border border-gray-100 overflow-hidden', className)}>
      <div className="p-4 border-b border-gray-50">
        <Skeleton className="h-5 w-32" />
      </div>
      <div className="p-4">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 py-3 border-b border-gray-50 last:border-0">
            <Skeleton className="h-4 w-8" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function SkeletonChart({ className }: SkeletonProps) {
  return (
    <div className={cn('bg-white rounded-2xl border border-gray-100 p-6', className)}>
      <Skeleton className="h-5 w-40 mb-4" />
      <div className="flex items-end gap-2 h-40">
        {Array.from({ length: 8 }).map((_, i) => (
          <div 
            key={i} 
            className="flex-1 animate-pulse rounded-lg bg-gray-100"
            style={{ height: `${30 + (i * 8) + 10}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center gap-3 mb-6">
        <Skeleton className="h-8 w-8 rounded-lg" />
        <div>
          <Skeleton className="h-6 w-48 mb-1" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SkeletonMetricCard />
        <SkeletonMetricCard />
        <SkeletonMetricCard />
        <SkeletonMetricCard />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonTable rows={4} />
        <SkeletonChart />
      </div>
      
      <SkeletonCard className="h-32" />
    </div>
  )
}

export function LoadingMessage({ message = 'Loading data...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="relative mb-4">
        <div className="w-10 h-10 border-2 border-gray-200 rounded-full" />
        <div className="absolute inset-0 w-10 h-10 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
      </div>
      <p className="text-sm text-gray-500">{message}</p>
      <p className="text-xs text-gray-400 mt-1">This may take a moment on first load</p>
    </div>
  )
}
