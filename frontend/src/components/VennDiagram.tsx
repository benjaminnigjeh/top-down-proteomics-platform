import { useVennData } from '@/hooks/useResults'
import { Card } from '@/components/ui/Card'

interface VennDiagramProps {
  jobId: string
}

export function VennDiagram({ jobId }: VennDiagramProps) {
  const { data, isLoading } = useVennData(jobId, true)

  if (isLoading) return <div className="text-gray-400 text-sm">Loading overlap data…</div>
  if (!data) return null

  const { engines, sets, overlaps } = data

  if (engines.length === 0) return <div className="text-gray-400 text-sm">No engine overlap data available.</div>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {engines.map((e) => (
          <div key={e} className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
            <div className="font-mono text-xs font-bold text-blue-800">{e}</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{sets[e] ?? 0}</div>
            <div className="text-xs text-blue-500">unique scans</div>
          </div>
        ))}
      </div>

      {Object.entries(overlaps).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Pairwise Overlaps</h4>
          <div className="space-y-1">
            {Object.entries(overlaps).map(([key, count]) => (
              <div key={key} className="flex items-center gap-3 text-sm">
                <span className="font-mono text-xs text-gray-600 min-w-[160px]">{key}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 bg-purple-500 rounded-full"
                    style={{
                      width: `${Math.min(100, (count / Math.max(...Object.values(sets), 1)) * 100)}%`
                    }}
                  />
                </div>
                <span className="text-xs font-medium text-purple-700 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
