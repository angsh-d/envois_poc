import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Safety from './Safety'

export default function StudySafety() {
  const [, params] = useRoute('/study/:studyId/safety')
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId} chatContext="safety">
      <Safety />
    </StudyLayout>
  )
}
