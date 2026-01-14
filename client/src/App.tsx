import { Route, Switch } from 'wouter'
import Landing from './pages/Landing'
import StudySelect from './pages/StudySelect'
import StudyDashboard from './pages/StudyDashboard'
import StudyReadiness from './pages/StudyReadiness'
import StudySafety from './pages/StudySafety'
import StudyDeviations from './pages/StudyDeviations'
import StudyRisk from './pages/StudyRisk'
import StudyProtocol from './pages/StudyProtocol'
import DataSources from './pages/DataSources'
import Agents from './pages/Agents'
import SimulationStudio from './pages/SimulationStudio'

function App() {
  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/role/clinical-strategy-analyst" component={StudySelect} />
      <Route path="/study/:studyId" component={StudyDashboard} />
      <Route path="/study/:studyId/dashboard" component={StudyDashboard} />
      <Route path="/study/:studyId/readiness" component={StudyReadiness} />
      <Route path="/study/:studyId/safety" component={StudySafety} />
      <Route path="/study/:studyId/deviations" component={StudyDeviations} />
      <Route path="/study/:studyId/risk" component={StudyRisk} />
      <Route path="/study/:studyId/protocol" component={StudyProtocol} />
      <Route path="/study/:studyId/simulation">{(params) => <SimulationStudio params={params} />}</Route>
      <Route path="/study/:studyId/data">{(params) => <DataSources params={params} />}</Route>
      <Route path="/study/:studyId/agents">{(params) => <Agents params={params} />}</Route>
    </Switch>
  )
}

export default App
