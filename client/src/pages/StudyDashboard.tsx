import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Dashboard from './Dashboard'

export default function StudyDashboard() {
  const [, params] = useRoute('/study/:studyId')
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId}>
      <Dashboard />
    </StudyLayout>
  )
}
