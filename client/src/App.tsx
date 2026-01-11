import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Route, Switch } from 'wouter'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Readiness from './pages/Readiness'
import Safety from './pages/Safety'
import Deviations from './pages/Deviations'
import Risk from './pages/Risk'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/readiness" component={Readiness} />
          <Route path="/safety" component={Safety} />
          <Route path="/deviations" component={Deviations} />
          <Route path="/risk" component={Risk} />
        </Switch>
      </Layout>
    </QueryClientProvider>
  )
}

export default App
