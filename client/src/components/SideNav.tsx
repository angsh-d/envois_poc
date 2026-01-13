import { Link, useLocation } from 'wouter'
import { LayoutDashboard, ClipboardCheck, AlertTriangle, FileWarning, Users, ArrowLeft, FileText, Database } from 'lucide-react'

interface SideNavProps {
  studyId: string
  studyName: string
}

const navItems = [
  { path: '', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/readiness', label: 'Readiness', icon: ClipboardCheck },
  { path: '/safety', label: 'Safety Signals', icon: AlertTriangle },
  { path: '/deviations', label: 'Deviations', icon: FileWarning },
  { path: '/risk', label: 'Patient Risk', icon: Users },
  { path: '/protocol', label: 'Digital Protocol', icon: FileText },
  { path: '/data-agents', label: 'Data & Agents', icon: Database },
]

export function SideNav({ studyId, studyName }: SideNavProps) {
  const [location] = useLocation()
  const basePath = `/study/${studyId}`

  return (
    <nav className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="p-6 border-b border-gray-100">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Studies
        </Link>
        <h2 className="text-lg font-semibold text-gray-800 tracking-tight">{studyName}</h2>
        <p className="text-sm text-gray-500 mt-1">Clinical Intelligence</p>
      </div>
      
      <div className="flex-1 py-4">
        {navItems.map((item) => {
          const fullPath = `${basePath}${item.path}`
          const isActive = location === fullPath || (item.path === '' && location === basePath)
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
        <p className="text-xs text-gray-400">Data as of Jan 11, 2026</p>
      </div>
    </nav>
  )
}
