import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, StatusBadge } from '@/components/ui/Badge'
import type { ProteoformResult } from '@/types'
import { clsx } from 'clsx'

interface ResultsTableProps {
  results: ProteoformResult[]
  jobId: string
}

export function ResultsTable({ results, jobId }: ResultsTableProps) {
  const [sortKey, setSortKey] = useState<keyof ProteoformResult>('qvalue')
  const [sortAsc, setSortAsc] = useState(true)

  const sorted = [...results].sort((a, b) => {
    const av = a[sortKey] ?? (sortAsc ? Infinity : -Infinity)
    const bv = b[sortKey] ?? (sortAsc ? Infinity : -Infinity)
    if (av < bv) return sortAsc ? -1 : 1
    if (av > bv) return sortAsc ? 1 : -1
    return 0
  })

  const Col = ({ k, label }: { k: keyof ProteoformResult; label: string }) => (
    <th
      className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
      onClick={() => { if (sortKey === k) setSortAsc(!sortAsc); else { setSortKey(k); setSortAsc(true) } }}
    >
      {label}
      {sortKey === k && <span className="ml-1">{sortAsc ? '↑' : '↓'}</span>}
    </th>
  )

  if (results.length === 0) {
    return <div className="text-center py-12 text-gray-400">No results to display.</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <Col k="scan_number" label="Scan" />
            <Col k="engine_name" label="Engine" />
            <Col k="accession" label="Accession" />
            <Col k="proteoform_string" label="Proteoform" />
            <Col k="observed_mass" label="Mass (Da)" />
            <Col k="delta_mass" label="ΔMass" />
            <Col k="score" label="Score" />
            <Col k="qvalue" label="q-value" />
            <Col k="sequence_coverage" label="Cov%" />
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase">PTMs</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {sorted.map((r) => (
            <tr key={r.id} className={clsx('hover:bg-gray-50', r.is_demo && 'bg-amber-50/40')}>
              <td className="px-3 py-2 font-mono text-xs text-gray-600">{r.scan_number}</td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-xs">{r.engine_name}</span>
                  {r.is_demo && <Badge variant="demo">DEMO</Badge>}
                </div>
              </td>
              <td className="px-3 py-2">
                <Link to={`/jobs/${jobId}/results/${r.id}`} className="text-blue-600 hover:underline font-mono text-xs">
                  {r.accession}
                </Link>
              </td>
              <td className="px-3 py-2 max-w-xs truncate font-mono text-xs text-gray-700" title={r.proteoform_string ?? ''}>
                {r.proteoform_string}
              </td>
              <td className="px-3 py-2 font-mono text-xs">{r.observed_mass?.toFixed(2)}</td>
              <td className="px-3 py-2 font-mono text-xs">
                <span className={clsx((r.delta_mass ?? 0) > 1 ? 'text-orange-600' : 'text-gray-600')}>
                  {r.delta_mass != null ? (r.delta_mass > 0 ? '+' : '') + r.delta_mass.toFixed(2) : '—'}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-xs">{r.score?.toFixed(1)}</td>
              <td className="px-3 py-2">
                <QValueCell qvalue={r.qvalue} />
              </td>
              <td className="px-3 py-2 font-mono text-xs">
                {r.sequence_coverage != null ? `${(r.sequence_coverage * 100).toFixed(1)}%` : '—'}
              </td>
              <td className="px-3 py-2">
                {r.ptms?.length > 0 ? (
                  <span className="text-xs text-purple-700 font-medium">{r.ptms.length} PTM{r.ptms.length > 1 ? 's' : ''}</span>
                ) : <span className="text-gray-300">—</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function QValueCell({ qvalue }: { qvalue: number | null }) {
  if (qvalue == null) return <span className="text-gray-400 text-xs">—</span>
  const color = qvalue <= 0.01 ? 'text-green-700' : qvalue <= 0.05 ? 'text-yellow-700' : 'text-red-600'
  return <span className={clsx('font-mono text-xs font-medium', color)}>{qvalue.toExponential(2)}</span>
}
