import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Dashboard from './Dashboard'

export default function StudyDashboard() {
  // Match both /study/:studyId and /study/:studyId/dashboard
  const [, params1] = useRoute('/study/:studyId')
  const [, params2] = useRoute('/study/:studyId/dashboard')
  const params = params1 || params2
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId}>
      <Dashboard />
    </StudyLayout>
  )
}
