import { useParams, Link } from 'react-router-dom'
import { useJob } from '@/hooks/useJobs'
import { useResults, useResultsByEngine } from '@/hooks/useResults'
import { JobStatusPanel } from '@/components/JobStatus'
import { ResultsTable } from '@/components/ResultsTable'
import { VennDiagram } from '@/components/VennDiagram'
import { ExportPanel } from '@/components/ExportPanel'
import { DemoBanner } from '@/components/DemoBanner'
import { Card } from '@/components/ui/Card'
import { useState } from 'react'

type Tab = 'status' | 'results' | 'comparison' | 'export'

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>()
  const { data: job, isLoading } = useJob(jobId!)
  const [tab, setTab] = useState<Tab>('status')
  const [filterEngine, setFilterEngine] = useState<string | undefined>()
  const [maxQvalue, setMaxQvalue] = useState<number | undefined>(0.01)

  const { data: results = [] } = useResults(jobId!, { engine_name: filterEngine, max_qvalue: maxQvalue, page_size: 200 })
  const { data: byEngine = [] } = useResultsByEngine(jobId!)

  if (isLoading) return <div className="text-gray-500 py-8">Loading…</div>
  if (!job) return <div className="text-red-500 py-8">Job not found.</div>

  const hasDemoResults = results.some((r) => r.is_demo)
  const isComplete = job.status === 'completed'

  const tabs: { id: Tab; label: string }[] = [
    { id: 'status', label: 'Status & Logs' },
    { id: 'results', label: `Results (${results.length})` },
    { id: 'comparison', label: 'Engine Comparison' },
    { id: 'export', label: 'Export' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Link to="/jobs" className="hover:text-blue-600">Jobs</Link>
        <span>/</span>
        <span className="text-gray-700 font-medium">{job.name}</span>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">{job.name}</h1>
        <p className="font-mono text-xs text-gray-400">{job.id}</p>
      </div>

      {hasDemoResults && <DemoBanner />}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-1">
          {tabs.map(({ id, label }) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                tab === id
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {label}
            </button>
          ))}
        </nav>
      </div>

      {tab === 'status' && (
        <Card>
          <JobStatusPanel job={job} />
        </Card>
      )}

      {tab === 'results' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <select
              className="input-field max-w-[200px]"
              value={filterEngine ?? ''}
              onChange={(e) => setFilterEngine(e.target.value || undefined)}
            >
              <option value="">All Engines</option>
              {byEngine.map(({ engine }) => (
                <option key={engine} value={engine}>{engine}</option>
              ))}
            </select>
            <select
              className="input-field max-w-[160px]"
              value={maxQvalue ?? ''}
              onChange={(e) => setMaxQvalue(e.target.value ? parseFloat(e.target.value) : undefined)}
            >
              <option value="">Any q-value</option>
              <option value={0.001}>q ≤ 0.001</option>
              <option value={0.01}>q ≤ 0.01</option>
              <option value={0.05}>q ≤ 0.05</option>
            </select>
          </div>

          <Card>
            <ResultsTable results={results} jobId={jobId!} />
          </Card>
        </div>
      )}

      {tab === 'comparison' && (
        <div className="space-y-4">
          <Card title="Results by Engine">
            <div className="space-y-2">
              {byEngine.map(({ engine, count }) => (
                <div key={engine} className="flex items-center gap-3">
                  <span className="font-mono text-sm w-32">{engine}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      className="bg-blue-500 h-3 rounded-full"
                      style={{ width: `${Math.min(100, (count / Math.max(...byEngine.map(e => e.count), 1)) * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-700 w-12 text-right">{count}</span>
                </div>
              ))}
            </div>
          </Card>

          {byEngine.length >= 2 && (
            <Card title="Scan Overlap Between Engines">
              <VennDiagram jobId={jobId!} />
            </Card>
          )}
        </div>
      )}

      {tab === 'export' && (
        <Card title="Export Results">
          <ExportPanel jobId={jobId!} disabled={!isComplete} />
          {!isComplete && (
            <p className="text-sm text-gray-400 mt-4">Exports are available once the job completes.</p>
          )}
        </Card>
      )}
    </div>
  )
}
