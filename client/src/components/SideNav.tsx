import { Link, useLocation } from 'wouter'
import { useQuery } from '@tanstack/react-query'
import { LayoutDashboard, ClipboardCheck, AlertTriangle, FileWarning, Users, ArrowLeft, FileText, Database, Bot, Dices, Table2, Target, CheckCircle2 } from 'lucide-react'
import { fetchDataTimestamp } from '@/lib/api'

interface SideNavProps {
  studyId: string
  studyName: string
  persona?: string
}

interface NavItem {
  path: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  personas?: string[] // If specified, only show for these personas
}

const mainNavItems: NavItem[] = [
  { path: '', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/readiness', label: 'Readiness', icon: ClipboardCheck },
  { path: '/safety', label: 'Safety Intelligence', icon: AlertTriangle },
  { path: '/risk', label: 'Risk Stratification', icon: Users },
  { path: '/competitive', label: 'Competitive Intel', icon: Target, personas: ['product-manager', 'sales', 'marketing', 'strategy'] },
  { path: '/claims', label: 'Claim Validation', icon: CheckCircle2, personas: ['product-manager', 'marketing'] },
]

const secondaryNavItems: NavItem[] = [
  { path: '/simulation', label: 'Simulation Studio', icon: Dices },
  { path: '/browser', label: 'Data Browser', icon: Table2 },
  { path: '/protocol', label: 'Digital Protocol', icon: FileText },
  { path: '/agents', label: 'AI Agents', icon: Bot },
]

export function SideNav({ studyId, studyName, persona }: SideNavProps) {
  const [location] = useLocation()
  const basePath = `/study/${studyId}`

  const { data: timestampData } = useQuery({
    queryKey: ['data-timestamp'],
    queryFn: fetchDataTimestamp,
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 1,
  })

  // Filter nav items based on persona
  const filterItems = (items: NavItem[]) => {
    return items.filter(item => {
      if (!item.personas) return true // Show if no persona restriction
      if (!persona) return true // Show all if no persona selected
      return item.personas.includes(persona)
    })
  }

  const filteredMainItems = filterItems(mainNavItems)
  const filteredSecondaryItems = filterItems(secondaryNavItems)

  // Format the date for display
  const formatDate = () => {
    if (timestampData?.formatted) {
      return `Data as of ${timestampData.formatted}`
    }
    // Fallback to current date if API fails
    const now = new Date()
    return `Data as of ${now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  }

  return (
    <nav className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="p-6 border-b border-gray-100">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Products
        </Link>
        <h2 className="text-lg font-semibold text-gray-800 tracking-tight">{studyName}</h2>
        <p className="text-sm text-gray-500 mt-1">Clinical Intelligence</p>
      </div>

      <div className="flex-1 py-4">
        {filteredMainItems.map((item) => {
          const fullPath = `${basePath}${item.path}`
          const isActive = location === fullPath || (item.path === '' && location === basePath) || location.startsWith(fullPath + '?')
          const Icon = item.icon

          return (
            <Link
              key={item.path}
              href={fullPath}
              className={`
                flex items-center gap-3 px-6 py-3 text-sm font-medium transition-all duration-150
                ${isActive
                  ? 'bg-gray-100 text-gray-900 border-r-2 border-gray-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </Link>
          )
        })}

        <div className="my-4 mx-6 border-t border-gray-200" />

        {filteredSecondaryItems.map((item) => {
          const fullPath = `${basePath}${item.path}`
          const isActive = location === fullPath
          const Icon = item.icon

          return (
            <Link
              key={item.path}
              href={fullPath}
              className={`
                flex items-center gap-3 px-6 py-3 text-sm font-medium transition-all duration-150
                ${isActive
                  ? 'bg-gray-100 text-gray-900 border-r-2 border-gray-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </Link>
          )
        })}
      </div>

      <div className="p-6 border-t border-gray-100">
        <p className="text-xs text-gray-400">{formatDate()}</p>
      </div>
    </nav>
  )
}
