import { Link, useLocation } from 'wouter'
import { cn } from '../lib/utils'

const navItems = [
  { path: '/', label: 'Overview' },
  { path: '/readiness', label: 'Readiness' },
  { path: '/safety', label: 'Safety' },
  { path: '/deviations', label: 'Deviations' },
  { path: '/risk', label: 'Risk' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation()

  return (
    <div className="min-h-screen">
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-black/[0.08]">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-12">
            <Link href="/">
              <span className="text-[15px] font-semibold tracking-tight text-neutral-900 cursor-pointer">
                Clinical Intelligence
              </span>
            </Link>

            <div className="flex items-center">
              <div className="flex items-center bg-black/[0.06] rounded-full p-1 gap-0.5">
                {navItems.map((item) => {
                  const isActive = location === item.path
                  return (
                    <Link key={item.path} href={item.path}>
                      <button
                        className={cn(
                          'px-5 py-1.5 rounded-full text-[13px] font-medium transition-all duration-200 whitespace-nowrap',
                          isActive
                            ? 'bg-white text-neutral-900 shadow-[0_1px_3px_rgba(0,0,0,0.1)]'
                            : 'text-neutral-500 hover:text-neutral-900'
                        )}
                      >
                        {item.label}
                      </button>
                    </Link>
                  )
                })}
              </div>
            </div>

            <div className="w-[120px]" />
          </div>
        </div>
      </nav>

      <main className="pt-12">
        {children}
      </main>
    </div>
  )
}
