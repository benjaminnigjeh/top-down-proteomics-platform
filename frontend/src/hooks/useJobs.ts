import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createJob, submitJob, listJobs, getJob, getJobStatus, deleteJob, getEngineLog } from '@/api/client'

export function useJobs() {
  return useQuery({ queryKey: ['jobs'], queryFn: listJobs, refetchInterval: 5000 })
}

export function useJob(jobId: string) {
  return useQuery({ queryKey: ['job', jobId], queryFn: () => getJob(jobId), enabled: !!jobId })
}

export function useJobStatus(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['job-status', jobId],
    queryFn: () => getJobStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'running' || status === 'queued') return 2000
      return false
    },
  })
}

export function useEngineLog(jobId: string, engineName: string, enabled: boolean) {
  return useQuery({
    queryKey: ['engine-log', jobId, engineName],
    queryFn: () => getEngineLog(jobId, engineName),
    enabled: enabled && !!jobId && !!engineName,
    refetchInterval: 3000,
  })
}

export function useCreateJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useSubmitJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: submitJob,
    onSuccess: (_, jobId) => {
      qc.invalidateQueries({ queryKey: ['job', jobId] })
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}

export function useDeleteJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}
