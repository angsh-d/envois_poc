import { useRoute } from 'wouter'
import StudyLayout from './StudyLayout'
import Risk from './Risk'

export default function StudyRisk() {
  const [, params] = useRoute('/study/:studyId/risk')
  const studyId = params?.studyId || 'h34-delta'
  
  return (
    <StudyLayout studyId={studyId}>
      <Risk />
    </StudyLayout>
  )
}
