import { useRoute, useSearch } from 'wouter'
import { useMemo } from 'react'
import StudyLayout from './StudyLayout'
import Dashboard from './Dashboard'
import { PersonaLanding } from '@/components/PersonaLanding'

export default function StudyDashboard() {
  // Match both /study/:studyId and /study/:studyId/dashboard
  const [, params1] = useRoute('/study/:studyId')
  const [, params2] = useRoute('/study/:studyId/dashboard')
  const params = params1 || params2
  const studyId = params?.studyId || 'h34-delta'
  const searchString = useSearch()

  // Parse persona from URL query param
  const persona = useMemo(() => {
    const params = new URLSearchParams(searchString)
    return params.get('persona') || undefined
  }, [searchString])

  return (
    <StudyLayout studyId={studyId} persona={persona}>
      {persona ? (
        <PersonaLanding studyId={studyId} persona={persona} />
      ) : (
        <Dashboard />
      )}
    </StudyLayout>
  )
}
