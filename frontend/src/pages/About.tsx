import { Card } from '@/components/ui/Card'
import { AlertTriangle } from 'lucide-react'

const engines = [
  { name: 'TopPIC (TopPIC Suite via Docker)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'TopMG (TopPIC Suite via Docker)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'TopFD (TopPIC Suite via Docker)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'TopDiff (TopPIC Suite via Docker)', status: 'Supported', license: 'MIT', url: 'https://github.com/toppic-suite/toppic-suite' },
  { name: 'MSPathFinderT (Informed Proteomics)', status: 'Supported', license: 'Apache 2.0', url: 'https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics' },
  { name: 'pTop (ICT Beijing)', status: 'Install required', license: 'Academic', url: 'http://pfind.ict.ac.cn' },
  { name: 'Protein Prospector (UCSF)', status: 'Web API', license: 'UCSF TOS', url: 'https://prospector.ucsf.edu' },
  { name: 'MetaMorpheus (Smith Lab)', status: 'Install required', license: 'MIT', url: 'https://github.com/smith-chem-wisc/MetaMorpheus' },
  { name: 'Proteoform Suite (Smith Lab)', status: 'GUI only', license: 'MIT', url: 'https://github.com/smith-chem-wisc/ProteoformSuite' },
  { name: 'FLASHDeconv (OpenMS)', status: 'Supported', license: 'BSD', url: 'https://github.com/OpenMS/OpenMS' },
  { name: 'ProMex (Informed Proteomics)', status: 'Supported', license: 'Apache 2.0', url: 'https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics' },
  { name: 'PeakPickerHiRes (OpenMS)', status: 'Supported', license: 'BSD', url: 'https://github.com/OpenMS/OpenMS' },
  { name: 'Decharger (OpenMS)', status: 'Supported', license: 'BSD', url: 'https://github.com/OpenMS/OpenMS' },
  { name: 'FeatureFinderCentroided (OpenMS)', status: 'Supported', license: 'BSD', url: 'https://github.com/OpenMS/OpenMS' },
  { name: 'THRASH (DeconTools, PNNL)', status: 'Supported', license: 'Apache 2.0', url: 'https://github.com/PNNL-Comp-Mass-Spec/DeconTools' },
  { name: 'UniDec (Marty Lab)', status: 'Install required', license: 'MIT', url: 'https://github.com/michaelmarty/UniDec' },
  { name: 'Xtract (Thermo)', status: 'Install required', license: 'Proprietary', url: '' },
  { name: 'modformPro (NRTDP)', status: 'Supported', license: 'MIT', url: 'https://github.com/NRTDP/modformPro' },
  { name: 'TDCD_FDR_Calculator (NRTDP)', status: 'Supported', license: 'MIT', url: 'https://github.com/NRTDP/TDCD_FDR_Calculator' },
  { name: 'tdReport → mzIdentML (NRTDP)', status: 'Supported', license: 'MIT', url: 'https://github.com/NRTDP/tdReport-to-mzIdentML' },
]

const statusColor: Record<string, string> = {
  'Supported':       'bg-green-100 text-green-800',
  'Web API':         'bg-blue-100 text-blue-800',
  'Install required':'bg-amber-100 text-amber-800',
  'GUI only':        'bg-purple-100 text-purple-800',
}

export default function About() {
  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">About Proteoformer Pipeline</h1>

      <div className="bg-amber-50 border border-amber-400 rounded-lg p-4 flex gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
        <div className="text-sm text-amber-800">
          <strong>Disclaimer:</strong> Proteoformer Pipeline is an independent open-source project. It is NOT affiliated with,
          endorsed by, or derived from the official TDPortal (University of Illinois) or ProSight suite.
          No proprietary source code has been used. Third-party engines retain their own licenses.
        </div>
      </div>

      <Card title="Purpose">
        <p className="text-sm text-gray-700">
          Proteoformer Pipeline provides a unified web interface for top-down proteomics data analysis using real
          open-source and academic search engines. Upload mzML/FASTA data, run multiple engines in parallel (including
          TopPIC Suite via Docker, MSPathFinderT, OpenMS tools, and web-based services), then compare and export results
          in standardized formats.
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
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor[e.status] ?? 'bg-gray-100 text-gray-600'}`}>
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

      <Card title="Quick-Start: TopPIC Suite (Docker)">
        <div className="text-sm text-gray-700 space-y-1">
          <p>TopPIC, TopMG, TopFD, and TopDiff run inside the official Docker image — no local installation needed:</p>
          <pre className="bg-gray-900 text-gray-100 rounded p-3 text-xs overflow-x-auto">docker pull toppicsuite/toppic</pre>
          <p className="text-gray-500">Docker Desktop must be running when you submit a job.</p>
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
    category = "search"
    description = "My custom engine"
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
