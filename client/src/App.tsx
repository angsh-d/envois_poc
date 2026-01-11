import { Route, Switch } from 'wouter'
import Landing from './pages/Landing'
import StudyDashboard from './pages/StudyDashboard'
import StudyReadiness from './pages/StudyReadiness'
import StudySafety from './pages/StudySafety'
import StudyDeviations from './pages/StudyDeviations'
import StudyRisk from './pages/StudyRisk'

function App() {
  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/study/:studyId" component={StudyDashboard} />
      <Route path="/study/:studyId/readiness" component={StudyReadiness} />
      <Route path="/study/:studyId/safety" component={StudySafety} />
      <Route path="/study/:studyId/deviations" component={StudyDeviations} />
      <Route path="/study/:studyId/risk" component={StudyRisk} />
    </Switch>
  )
}

export default App
