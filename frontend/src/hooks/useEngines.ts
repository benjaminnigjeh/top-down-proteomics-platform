import { useQuery } from '@tanstack/react-query'
import { listEngines } from '@/api/client'

export function useEngines() {
  return useQuery({ queryKey: ['engines'], queryFn: listEngines, staleTime: 60_000 })
}
