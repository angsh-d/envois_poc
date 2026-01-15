import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Readiness from './Readiness'

export default function StudyReadiness() {
  const [, params] = useRoute('/study/:studyId/readiness')
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId} chatContext="readiness">
      <Readiness />
    </StudyLayout>
  )
}
