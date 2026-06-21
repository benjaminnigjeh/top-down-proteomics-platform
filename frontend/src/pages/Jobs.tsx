import { Link } from 'react-router-dom'
import { useJobs, useDeleteJob } from '@/hooks/useJobs'
import { StatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { format } from 'date-fns'
import { Trash2, ExternalLink } from 'lucide-react'

export default function Jobs() {
  const { data: jobs = [], isLoading } = useJobs()
  const deleteMutation = useDeleteJob()

  if (isLoading) return <div className="text-gray-500">Loading jobs…</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Jobs</h1>
        <Link to="/upload">
          <Button>New Job</Button>
        </Link>
      </div>

      {jobs.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-400 text-lg">No jobs yet.</p>
          <Link to="/upload" className="mt-4 inline-block">
            <Button>Submit Your First Job</Button>
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {jobs.map((job) => (
          <div key={job.id} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Link to={`/jobs/${job.id}`} className="font-semibold text-gray-900 hover:text-blue-600 truncate">
                    {job.name}
                  </Link>
                  <StatusBadge status={job.status} />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {format(new Date(job.created_at), 'yyyy-MM-dd HH:mm')} &bull;{' '}
                  Engines: <span className="font-mono">{job.engines_requested.join(', ')}</span>
                </p>
                <div className="flex gap-3 mt-2">
                  {job.engine_runs.map((er) => (
                    <span key={er.engine_name} className="text-xs text-gray-500">
                      <span className="font-mono">{er.engine_name}</span>:{' '}
                      <StatusBadge status={er.status} />
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Link to={`/jobs/${job.id}`}>
                  <Button variant="secondary" size="sm">
                    <ExternalLink className="w-3.5 h-3.5 mr-1" /> View
                  </Button>
                </Link>
                <Button
                  variant="ghost" size="sm"
                  onClick={() => confirm('Delete this job?') && deleteMutation.mutate(job.id)}
                >
                  <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-500" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
