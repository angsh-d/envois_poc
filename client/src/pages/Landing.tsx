import { Link } from 'wouter'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Sparkles,
  Network,
  Database,
  Zap,
  Activity,
  Circle,
  Loader2,
} from 'lucide-react'
import { Card } from '@/components/Card'
import { Navbar } from '@/components/Navbar'
import { fetchProducts, type Product, type ProductStatus } from '@/lib/api'

const capabilities = [
  { icon: Network, label: 'Protocol-as-Code' },
  { icon: Database, label: 'Unified Data Layer' },
  { icon: Zap, label: 'Real-time RAG' },
  { icon: Sparkles, label: 'LLM Synthesis' },
]

const getStatusBadge = (status: ProductStatus) => {
  switch (status) {
    case 'active':
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-gray-900 rounded-full text-xs">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-white"></span>
          </span>
          <span className="text-white font-medium">Active</span>
        </div>
      )
    case 'configured':
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-gray-100 border border-gray-200 rounded-full text-xs">
          <Circle className="w-1.5 h-1.5 fill-gray-600 text-gray-600" />
          <span className="text-gray-700 font-medium">Ready</span>
        </div>
      )
    case 'pending':
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-gray-50 border border-gray-200 rounded-full text-xs">
          <Circle className="w-1.5 h-1.5 text-gray-400" />
          <span className="text-gray-500 font-medium">Setup Required</span>
        </div>
      )
  }
}

export default function Landing() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })

  const products = data?.products || []
  const activeCount = products.filter(p => p.status === 'active').length
  const configuredCount = products.filter(p => p.status === 'configured').length

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <Navbar />

      <main>
        {/* Hero Section */}
        <section className="py-16 px-6 bg-white">
          <div className="max-w-5xl mx-auto text-center">
            <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-500">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Multi-Agent AI</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 rounded-full text-sm">
                <Activity className="w-3.5 h-3.5 text-white" />
                <span className="text-white font-medium">
                  {isLoading ? '...' : `${activeCount + configuredCount} Products Active`}
                </span>
              </div>
            </div>

            <h1 className="text-4xl md:text-5xl font-semibold text-gray-900 tracking-tight leading-tight">
              Clinical Intelligence Platform
            </h1>

            <p className="mt-5 text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
              AI-native platform unifying clinical data, registries, and literature
              into actionable intelligence across your{' '}
              <span className="text-gray-900 font-medium">Enovis product portfolio</span>.
            </p>

            {/* Product Stats */}
            <div className="mt-8 flex justify-center gap-8">
              <div className="text-center">
                <div className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : products.length}
                </div>
                <div className="text-sm text-gray-400">Products</div>
              </div>
              <div className="w-px bg-gray-200" />
              <div className="text-center">
                <div className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : activeCount}
                </div>
                <div className="text-sm text-gray-400">Active Studies</div>
              </div>
              <div className="w-px bg-gray-200" />
              <div className="text-center">
                <div className="text-2xl font-semibold text-gray-700">
                  {isLoading ? '-' : configuredCount}
                </div>
                <div className="text-sm text-gray-400">Ready</div>
              </div>
            </div>

            {/* Capabilities */}
            <div className="mt-10 flex flex-wrap justify-center gap-2">
              {capabilities.map((cap) => (
                <div key={cap.label} className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500">
                  <cap.icon className="w-4 h-4 text-gray-400" />
                  <span>{cap.label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Product Selection Section */}
        <section className="py-12 px-6 pb-24">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-2xl font-semibold text-gray-900 tracking-tight">Select a Product</h2>
              <p className="mt-2 text-gray-500">Choose a product to access its intelligence dashboard</p>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="text-center py-20 text-gray-500">
                <p>Unable to load products. Please check the backend is running.</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.map((product: Product, i: number) => {
                  const isClickable = product.status !== 'pending'

                  return isClickable ? (
                    <Link key={product.id} href={`/product/${product.id}`}>
                      <div className={`animate-fade-in-up stagger-${i + 1} opacity-0 h-full`}>
                        <Card
                          hoverable
                          className="h-full flex flex-col group transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50"
                        >
                          {/* Header */}
                          <div className="flex items-start justify-between gap-2 mb-3">
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{product.category}</p>
                              <h3 className="text-base font-semibold text-gray-900 leading-tight">
                                {product.name}
                              </h3>
                            </div>
                            {getStatusBadge(product.status)}
                          </div>

                          {/* Description */}
                          <p className="text-sm text-gray-500 leading-relaxed flex-1 mb-4">
                            {product.description}
                          </p>

                          {/* Meta */}
                          <div className="flex flex-wrap gap-2 mb-4">
                            <span className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                              {product.indication}
                            </span>
                            {product.study_phase && (
                              <span className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                                {product.study_phase}
                              </span>
                            )}
                          </div>

                          {/* CTA */}
                          <div className="pt-3 border-t border-gray-100 mt-auto">
                            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-900 group-hover:text-gray-600 transition-colors">
                              Open Dashboard
                              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                            </span>
                          </div>
                        </Card>
                      </div>
                    </Link>
                  ) : (
                    <div key={product.id} className={`animate-fade-in-up stagger-${i + 1} opacity-0 h-full`}>
                      <Card className="h-full flex flex-col opacity-60 cursor-not-allowed">
                        {/* Header */}
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{product.category}</p>
                            <h3 className="text-base font-semibold text-gray-500 leading-tight">
                              {product.name}
                            </h3>
                          </div>
                          {getStatusBadge(product.status)}
                        </div>

                        {/* Description */}
                        <p className="text-sm text-gray-400 leading-relaxed flex-1 mb-4">
                          {product.description}
                        </p>

                        {/* Meta */}
                        <div className="flex flex-wrap gap-2 mb-4">
                          <span className="px-2 py-0.5 bg-gray-50 rounded text-xs text-gray-400">
                            {product.indication}
                          </span>
                        </div>

                        {/* CTA */}
                        <div className="pt-3 border-t border-gray-100 mt-auto">
                          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-400">
                            Configuration Required
                          </span>
                        </div>
                      </Card>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Bottom note */}
            <div className="mt-12 text-center">
              <p className="text-xs text-gray-400">
                Powered by multi-agent AI with reasoning chains and investigation mode
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
