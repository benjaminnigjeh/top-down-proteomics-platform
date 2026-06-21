import { Link } from 'react-router-dom'
import { Dna, Upload, Cpu, BarChart3, GitCompare, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/Button'

const features = [
  { icon: Upload, title: 'Multi-File Upload', desc: 'Upload mzML, FASTA, and PTM config files for analysis' },
  { icon: Cpu, title: 'Multiple Search Engines', desc: 'TopPIC, MSPathFinderT, FLASHDeconv, TopLib, and custom adapters' },
  { icon: BarChart3, title: 'Real Results Only', desc: 'No fake data — engines run real algorithms on your data' },
  { icon: GitCompare, title: 'Cross-Engine Comparison', desc: 'Compare results across engines, view overlaps and consensus' },
]

export default function Home() {
  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="text-center py-12 bg-gradient-to-br from-blue-900 to-blue-700 rounded-2xl text-white px-6">
        <div className="flex justify-center mb-4">
          <Dna className="w-14 h-14 text-blue-200" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight">TDPortal-OS</h1>
        <p className="text-blue-200 text-lg mt-2">Open-Source Top-Down Proteomics Search Platform</p>
        <p className="text-blue-300 text-sm mt-1">Not affiliated with official TDPortal or ProSight</p>
        <div className="flex justify-center gap-4 mt-6">
          <Link to="/upload">
            <Button size="lg" className="bg-white text-blue-700 hover:bg-blue-50">Start New Job</Button>
          </Link>
          <Link to="/jobs">
            <Button size="lg" variant="secondary" className="bg-blue-800 text-white border-blue-600 hover:bg-blue-700">
              View Jobs
            </Button>
          </Link>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 flex gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800">
          <strong>About Demo Mode:</strong> If no real search engines are installed, the platform will offer a "Demo"
          engine that produces entirely <strong>synthetic, fabricated data</strong> for interface testing only.
          Demo results are always clearly labeled. Real research requires real engine binaries (TopPIC, MSPathFinderT, etc.).
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="bg-white rounded-xl border border-gray-200 p-6 flex gap-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Icon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500 mt-1">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Workflow */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow</h2>
        <div className="flex flex-col sm:flex-row gap-2">
          {['1. Upload Files', '2. Select Engines', '3. Configure Params', '4. Submit Job', '5. View Results', '6. Export'].map((step, i) => (
            <div key={i} className="flex-1 text-center">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center mx-auto mb-2">
                {i + 1}
              </div>
              <p className="text-xs text-gray-600">{step.replace(/^\d+\.\s/, '')}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
