import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listConversionTools, createConversion, listConversions,
  getConversion, deleteConversion,
} from '@/api/client'
import type { ConversionCreate } from '@/types'

export function useConversionTools() {
  return useQuery({ queryKey: ['conversion-tools'], queryFn: listConversionTools, staleTime: 60_000 })
}

export function useConversions() {
  return useQuery({ queryKey: ['conversions'], queryFn: listConversions, refetchInterval: 4000 })
}

export function useConversion(id: string, active: boolean) {
  return useQuery({
    queryKey: ['conversion', id],
    queryFn: () => getConversion(id),
    enabled: active && !!id,
    refetchInterval: (q) => {
      const s = q.state.data?.status
      return s === 'running' || s === 'queued' ? 2000 : false
    },
  })
}

export function useCreateConversion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ConversionCreate) => createConversion(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversions'] }),
  })
}

export function useDeleteConversion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteConversion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversions'] }),
  })
}
