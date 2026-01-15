import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Deviations from './Deviations'

export default function StudyDeviations() {
  const [, params] = useRoute('/study/:studyId/deviations')
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId} chatContext="deviations">
      <Deviations />
    </StudyLayout>
  )
}
