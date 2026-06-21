import { Card } from '@/components/ui/Card'
import { AlertTriangle } from 'lucide-react'

const engines = [
  { name: 'TopPIC Suite (TopFD + TopPIC)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'TopPIC Suite (TopMG)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'TopLib', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'MSPathFinderT', status: 'Supported', license: 'Apache 2.0', url: 'https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics' },
  { name: 'FLASHDeconv', status: 'Supported', license: 'BSD', url: 'https://github.com/OpenMS/OpenMS' },
  { name: 'ProteoID (ProteoBio AI)', status: 'Placeholder', license: 'TBD', url: '' },
  { name: 'TruncNet (ProteoBio AI)', status: 'Placeholder', license: 'TBD', url: '' },
  { name: 'PTMNet (ProteoBio AI)', status: 'Placeholder', license: 'TBD', url: '' },
  { name: 'MassFlowNet (ProteoBio AI)', status: 'Placeholder', license: 'TBD', url: '' },
  { name: 'ProteoEngine (ProteoBio AI)', status: 'Placeholder', license: 'TBD', url: '' },
]

export default function About() {
  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">About TDPortal-OS</h1>

      <div className="bg-amber-50 border border-amber-400 rounded-lg p-4 flex gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
        <div className="text-sm text-amber-800">
          <strong>Disclaimer:</strong> TDPortal-OS is an independent open-source project. It is NOT affiliated with,
          endorsed by, or derived from the official TDPortal (University of Illinois at Urbana-Champaign) or ProSight
          software suite. No proprietary source code has been used.
        </div>
      </div>

      <Card title="Purpose">
        <p className="text-sm text-gray-700">
          TDPortal-OS provides a web-based interface for top-down proteomics data analysis using real open-source
          search engines. It supports uploading mzML data and running multiple engines in parallel, then comparing
          results across engines with standardized output formats.
        </p>
      </Card>

      <Card title="Supported Engines">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 uppercase border-b">
                <th className="pb-2 pr-4">Engine</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">License</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {engines.map((e) => (
                <tr key={e.name}>
                  <td className="py-2 pr-4">
                    {e.url ? (
                      <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {e.name}
                      </a>
                    ) : (
                      <span className="text-gray-600">{e.name}</span>
                    )}
                  </td>
                  <td className="py-2 pr-4">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      e.status === 'Supported' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {e.status}
                    </span>
                  </td>
                  <td className="py-2 text-xs text-gray-500">{e.license}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Demo Mode">
        <p className="text-sm text-gray-700">
          When no real search engines are installed, the "Demo" engine is available for testing the UI workflow.
          Demo results are entirely fabricated synthetic data. They are always labeled with a prominent warning
          banner and the <code className="bg-gray-100 px-1 rounded">is_demo=true</code> flag in the database.
          Never use demo results for any research purpose.
        </p>
      </Card>

      <Card title="Adding a Custom Engine">
        <div className="text-sm text-gray-700 space-y-2">
          <p>Implement <code className="bg-gray-100 px-1 rounded">SearchEngineAdapter</code> in <code className="bg-gray-100 px-1 rounded">backend/app/engines/</code>:</p>
          <pre className="bg-gray-900 text-gray-100 rounded p-3 text-xs overflow-x-auto">{`from app.engines.base import SearchEngineAdapter, ProteoformResult

class MyEngine(SearchEngineAdapter):
    name = "myengine"
    version = "1.0"
    input_formats = [".mzml"]
    output_formats = [".tsv"]

    def validate_installation(self) -> bool: ...
    def prepare_database(self, fasta, ptm_config, out_dir): ...
    def run_search(self, inputs, db, params, out_dir, log_cb=None): ...
    def parse_results(self, out_dir) -> list[ProteoformResult]: ...`}</pre>
          <p>Then register it in <code className="bg-gray-100 px-1 rounded">app/engines/registry.py</code>.</p>
        </div>
      </Card>
    </div>
  )
}
