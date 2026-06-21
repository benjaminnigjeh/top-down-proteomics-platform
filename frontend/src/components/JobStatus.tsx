import { useJobStatus, useEngineLog } from '@/hooks/useJobs'
import { Progress } from '@/components/ui/Progress'
import { StatusBadge } from '@/components/ui/Badge'
import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { Job } from '@/types'

interface JobStatusProps {
  job: Job
}

export function JobStatusPanel({ job }: JobStatusProps) {
  const isActive = job.status === 'running' || job.status === 'queued'
  const { data: status } = useJobStatus(job.id, isActive)
  const [expandedEngine, setExpandedEngine] = useState<string | null>(null)

  const progress = status?.progress_percent ?? (job.status === 'completed' ? 100 : 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <StatusBadge status={job.status} />
        {isActive && <span className="text-sm text-gray-500 animate-pulse">Processing…</span>}
      </div>

      <Progress value={progress} label={`Progress: ${status?.total_results ?? 0} results`} />

      <div className="space-y-2">
        {job.engine_runs.map((er) => (
          <div key={er.engine_name} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-left"
              onClick={() => setExpandedEngine(expandedEngine === er.engine_name ? null : er.engine_name)}
            >
              {expandedEngine === er.engine_name ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span className="font-mono text-sm font-semibold">{er.engine_name}</span>
              <StatusBadge status={er.status} />
              <span className="ml-auto text-xs text-gray-500">{er.result_count} results</span>
            </button>
            {expandedEngine === er.engine_name && (
              <LogViewer jobId={job.id} engineName={er.engine_name} active={isActive} initialLog={er.log} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function LogViewer({ jobId, engineName, active, initialLog }: {
  jobId: string; engineName: string; active: boolean; initialLog: string
}) {
  const { data } = useEngineLog(jobId, engineName, active)
  const log = data?.log || initialLog || ''
  const lines = log.split('\n').filter(Boolean)

  return (
    <div className="bg-gray-900 text-gray-100 font-mono text-xs p-4 max-h-48 overflow-y-auto">
      {lines.length === 0 ? (
        <span className="text-gray-500">No log output yet.</span>
      ) : (
        lines.map((line, i) => (
          <div key={i} className={line.includes('ERROR') ? 'text-red-400' : line.includes('DEMO') ? 'text-amber-400' : ''}>
            {line}
          </div>
        ))
      )}
    </div>
  )
}
