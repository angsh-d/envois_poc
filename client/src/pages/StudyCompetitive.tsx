import { useRoute, useSearch } from 'wouter'
import { useMemo } from 'react'
import StudyLayout from './StudyLayout'
import Competitive from './Competitive'

export default function StudyCompetitive() {
  const [, params] = useRoute('/study/:studyId/competitive')
  const studyId = params?.studyId || 'h34-delta'
  const searchString = useSearch()

  const persona = useMemo(() => {
    const params = new URLSearchParams(searchString)
    return params.get('persona') || undefined
  }, [searchString])

  return (
    <StudyLayout studyId={studyId} chatContext="competitive" persona={persona}>
      <Competitive studyId={studyId} />
    </StudyLayout>
  )
}
