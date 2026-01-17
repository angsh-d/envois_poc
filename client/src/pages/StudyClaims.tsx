import { useRoute, useSearch } from 'wouter'
import { useMemo } from 'react'
import StudyLayout from './StudyLayout'
import Claims from './Claims'

export default function StudyClaims() {
  const [, params] = useRoute('/study/:studyId/claims')
  const studyId = params?.studyId || 'h34-delta'
  const searchString = useSearch()

  const persona = useMemo(() => {
    const params = new URLSearchParams(searchString)
    return params.get('persona') || undefined
  }, [searchString])

  return (
    <StudyLayout studyId={studyId} chatContext="claims" persona={persona}>
      <Claims studyId={studyId} />
    </StudyLayout>
  )
}
