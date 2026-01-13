import { Search, ChevronDown } from 'lucide-react'

interface NavbarProps {
  userName?: string
}

export function Navbar({ userName = 'Angshuman Deb' }: NavbarProps) {
  const initials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="https://www.saama.com/wp-content/uploads/saama_logo.svg"
            alt="Saama"
            className="h-7"
          />
          <div className="h-6 w-px bg-gray-300" />
          <span className="text-base font-medium text-gray-700 tracking-tight">
            Digital Study Platform
          </span>
        </div>

        <div className="flex-1 max-w-xl mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search sites, protocols, or investigators..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-full text-sm text-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-gray-300 transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {initials}
          </div>
          <span className="text-sm font-medium text-gray-700">{userName}</span>
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </header>
  )
}
