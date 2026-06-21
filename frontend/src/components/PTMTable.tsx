import type { PTM } from '@/types'

interface PTMTableProps {
  ptms: PTM[]
  sequence?: string | null
}

export function PTMTable({ ptms, sequence }: PTMTableProps) {
  if (!ptms || ptms.length === 0) {
    return <p className="text-sm text-gray-400">No PTMs detected for this proteoform.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Position</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Residue</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Modification</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Mass Shift (Da)</th>
            {sequence && <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Context</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {ptms.map((ptm, i) => (
            <tr key={i} className="hover:bg-gray-50">
              <td className="px-4 py-2 font-mono text-xs">{ptm.position}</td>
              <td className="px-4 py-2 font-mono text-xs font-bold text-blue-700">{ptm.residue}</td>
              <td className="px-4 py-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-xs font-medium">
                  {ptm.modification}
                </span>
              </td>
              <td className="px-4 py-2 font-mono text-xs text-gray-600">
                {ptm.mass_shift != null ? (ptm.mass_shift > 0 ? '+' : '') + ptm.mass_shift.toFixed(3) : '—'}
              </td>
              {sequence && (
                <td className="px-4 py-2 font-mono text-xs text-gray-500">
                  {getContext(sequence, (ptm.position ?? 1) - 1, 3)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getContext(seq: string, pos: number, radius: number): string {
  const start = Math.max(0, pos - radius)
  const end = Math.min(seq.length, pos + radius + 1)
  const before = seq.slice(start, pos)
  const residue = seq[pos] || '?'
  const after = seq.slice(pos + 1, end)
  return `${before}[${residue}]${after}`
}
