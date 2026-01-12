import { ReactNode, useState } from 'react'
import { SideNav } from '@/components/SideNav'
import { ChatPanel } from '@/components/ChatPanel'
import { Navbar } from '@/components/Navbar'

interface StudyLayoutProps {
  studyId: string
  children: ReactNode
  chatContext?: string
}

const studyNames: Record<string, string> = {
  'h34-delta': 'H-34 DELTA Revision Cup',
}

export default function StudyLayout({ studyId, children, chatContext = 'dashboard' }: StudyLayoutProps) {
  const [chatOpen, setChatOpen] = useState(false)
  const studyName = studyNames[studyId] || studyId

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex flex-1">
        <SideNav studyId={studyId} studyName={studyName} />
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
