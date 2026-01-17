import { ReactNode, useState, useCallback, useMemo } from 'react'
import { useSearch } from 'wouter'
import { SideNav } from '@/components/SideNav'
import { ChatPanel } from '@/components/ChatPanel'
import { Navbar } from '@/components/Navbar'
import { SafetyAlertBanner } from '@/components/SafetyAlertBanner'
import { SafetyAlert } from '@/lib/api'

interface StudyLayoutProps {
  studyId: string
  children: ReactNode
  chatContext?: string
  persona?: string
}

const studyNames: Record<string, string> = {
  'h34-delta': 'DELTA Revision Cup',
}

export default function StudyLayout({ studyId, children, chatContext = 'dashboard', persona: propPersona }: StudyLayoutProps) {
  const [chatOpen, setChatOpen] = useState(false)
  const studyName = studyNames[studyId] || studyId
  const searchString = useSearch()

  // Parse persona from URL query param or use prop
  const persona = useMemo(() => {
    if (propPersona) return propPersona
    const params = new URLSearchParams(searchString)
    return params.get('persona') || undefined
  }, [searchString, propPersona])

  // Handle alert clicks by opening chat panel with context
  const handleAlertClick = useCallback((alert: SafetyAlert) => {
    // Open chat panel when an alert is clicked
    setChatOpen(true)
    // The chat panel will show the alert details
    console.log('Alert clicked:', alert.title)
  }, [])

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navbar />
      {/* Safety Alert Banner - appears below navbar when there are active alerts */}
      <SafetyAlertBanner studyId={studyId} onAlertClick={handleAlertClick} />
      <div className="flex flex-1">
        <SideNav studyId={studyId} studyName={studyName} persona={persona} />
        <main className="flex-1 overflow-auto">
          <div className="p-8">
            {children}
          </div>
        </main>
        <ChatPanel
          studyId={studyId}
          context={chatContext}
          isOpen={chatOpen}
          onToggle={() => setChatOpen(!chatOpen)}
        />
      </div>
    </div>
  )
}
