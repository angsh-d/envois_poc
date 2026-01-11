import { Link, useLocation } from 'wouter'
import { Activity, Shield, AlertTriangle, Users, LayoutDashboard, Search } from 'lucide-react'
import { cn } from '../lib/utils'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/readiness', label: 'Readiness', icon: Activity },
  { path: '/safety', label: 'Safety', icon: Shield },
  { path: '/deviations', label: 'Deviations', icon: AlertTriangle },
  { path: '/risk', label: 'Risk', icon: Users },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation()

  return (
    <div className="min-h-screen bg-white">
      <nav className="bg-white px-6 py-3 sticky top-0 z-50 shadow-sm border-b border-gray-200">
        <div className="max-w-full mx-auto flex items-center justify-between gap-8">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div className="w-px h-8 bg-gray-300 flex-shrink-0"></div>
            <span className="text-gray-600 font-light text-xl leading-none">
              Clinical Intelligence
            </span>
          </div>

          <div className="hidden lg:flex flex-1 max-w-2xl mx-8">
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="w-5 h-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-full bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent text-sm"
                placeholder="Search patients, signals, deviations..."
              />
            </div>
          </div>

          <div className="flex items-center gap-6">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location === item.path
              return (
                <Link key={item.path} href={item.path}>
                  <button
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                      isActive
                        ? 'bg-black text-white'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden xl:inline">{item.label}</span>
                  </button>
                </Link>
              )
            })}
          </div>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-xs">H34</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="min-h-[calc(100vh-52px)]">
        {children}
      </main>
    </div>
  )
}
