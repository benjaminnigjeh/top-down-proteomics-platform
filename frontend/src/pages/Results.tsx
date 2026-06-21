import { useParams, Link } from 'react-router-dom'
import { useResult } from '@/hooks/useResults'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PTMTable } from '@/components/PTMTable'
import { SpectrumViewer } from '@/components/SpectrumViewer'
import { DemoBanner } from '@/components/DemoBanner'
import { ArrowLeft } from 'lucide-react'

export default function ResultDetail() {
  const { jobId, resultId } = useParams<{ jobId: string; resultId: string }>()
  const { data: result, isLoading } = useResult(resultId!)

  if (isLoading) return <div className="text-gray-500 py-8">Loading…</div>
  if (!result) return <div className="text-red-500 py-8">Result not found.</div>

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Link to={`/jobs/${jobId}`} className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to Job
        </Link>
      </div>

      {result.is_demo && <DemoBanner />}

      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-xl font-bold text-gray-900 font-mono">{result.accession}</h1>
        <Badge variant={result.is_demo ? 'demo' : 'info'}>{result.engine_name}</Badge>
        {result.is_demo && <Badge variant="demo">DEMO DATA</Badge>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Identification">
          <dl className="space-y-2 text-sm">
            <Field label="Protein Name" value={result.protein_name} />
            <Field label="Accession" value={result.accession} />
            <Field label="Engine" value={`${result.engine_name} ${result.engine_version || ''}`} />
            <Field label="Scan" value={result.scan_number?.toString()} />
            <Field label="Source File" value={result.source_file} />
          </dl>
        </Card>

        <Card title="Mass & Score">
          <dl className="space-y-2 text-sm">
            <Field label="Observed Mass (Da)" value={result.observed_mass?.toFixed(4)} />
            <Field label="Theoretical Mass (Da)" value={result.theoretical_mass?.toFixed(4)} />
            <Field label="Δ Mass (Da)" value={result.delta_mass?.toFixed(4)} />
            <Field label="Precursor m/z" value={result.precursor_mz?.toFixed(4)} />
            <Field label="Charge State" value={result.charge ? `+${result.charge}` : undefined} />
            <Field label="Score" value={result.score?.toFixed(2)} />
            <Field label="E-value" value={result.evalue?.toExponential(3)} />
            <Field label="q-value" value={result.qvalue?.toExponential(3)} />
            <Field label="FDR" value={result.fdr != null ? `${(result.fdr * 100).toFixed(1)}%` : undefined} />
            <Field label="Matched Fragments" value={result.matched_fragments?.toString()} />
            <Field label="Sequence Coverage" value={result.sequence_coverage != null ? `${(result.sequence_coverage * 100).toFixed(1)}%` : undefined} />
          </dl>
        </Card>
      </div>

      <Card title="Proteoform">
        <div className="font-mono text-sm bg-gray-50 rounded p-4 break-all text-gray-800">
          {result.proteoform_string || result.sequence || '—'}
        </div>
      </Card>

      <Card title="PTM Annotations">
        <PTMTable ptms={result.ptms || []} sequence={result.sequence} />
      </Card>

      <Card title="Spectrum View">
        <SpectrumViewer result={result} />
      </Card>
    </div>
  )
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex gap-2">
      <dt className="font-medium text-gray-500 w-40 flex-shrink-0">{label}</dt>
      <dd className="text-gray-800 font-mono">{value ?? '—'}</dd>
    </div>
  )
}
