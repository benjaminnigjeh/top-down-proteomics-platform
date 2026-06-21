import { useQuery } from '@tanstack/react-query'
import { getResults, getResultCount, getResultsByEngine, getVennData, getResult } from '@/api/client'

export function useResults(jobId: string, filters?: {
  engine_name?: string
  max_qvalue?: number
  min_score?: number
  accession?: string
  page?: number
  page_size?: number
}) {
  return useQuery({
    queryKey: ['results', jobId, filters],
    queryFn: () => getResults(jobId, filters),
    enabled: !!jobId,
  })
}

export function useResultCount(jobId: string) {
  return useQuery({
    queryKey: ['result-count', jobId],
    queryFn: () => getResultCount(jobId),
    enabled: !!jobId,
  })
}

export function useResultsByEngine(jobId: string) {
  return useQuery({
    queryKey: ['results-by-engine', jobId],
    queryFn: () => getResultsByEngine(jobId),
    enabled: !!jobId,
  })
}

export function useVennData(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['venn', jobId],
    queryFn: () => getVennData(jobId),
    enabled: enabled && !!jobId,
  })
}

export function useResult(resultId: string) {
  return useQuery({
    queryKey: ['result', resultId],
    queryFn: () => getResult(resultId),
    enabled: !!resultId,
  })
}
