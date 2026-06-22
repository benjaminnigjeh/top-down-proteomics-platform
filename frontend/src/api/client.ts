import axios from 'axios'
import type { Upload, Job, JobStatus, ProteoformResult, EngineInfo, VennData, ExportFormat, ConversionTool, Conversion, ConversionCreate } from '@/types'

const BASE = '/api/v1'

const api = axios.create({ baseURL: BASE })

// ── Uploads ──────────────────────────────────────────────────────

export async function uploadFile(file: File): Promise<Upload> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<Upload>('/uploads', form)
  return data
}

export async function getUpload(id: string): Promise<Upload> {
  const { data } = await api.get<Upload>(`/uploads/${id}`)
  return data
}

// ── Engines ──────────────────────────────────────────────────────

export async function listEngines(): Promise<EngineInfo[]> {
  const { data } = await api.get<EngineInfo[]>('/engines')
  return data
}

// ── Jobs ─────────────────────────────────────────────────────────

export async function createJob(payload: {
  name: string
  mzml_file_id: string
  fasta_file_id: string
  ptm_file_id?: string
  engines: string[]
  parameters?: Partial<import('@/types').SearchParameters>
}): Promise<Job> {
  const { data } = await api.post<Job>('/jobs', payload)
  return data
}

export async function submitJob(jobId: string): Promise<Job> {
  const { data } = await api.post<Job>(`/jobs/${jobId}/submit`)
  return data
}

export async function listJobs(): Promise<Job[]> {
  const { data } = await api.get<Job[]>('/jobs')
  return data
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/jobs/${jobId}`)
  return data
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data } = await api.get<JobStatus>(`/jobs/${jobId}/status`)
  return data
}

export async function getEngineLog(jobId: string, engineName: string): Promise<{ log: string; status: string }> {
  const { data } = await api.get(`/jobs/${jobId}/logs/${engineName}`)
  return data
}

export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/jobs/${jobId}`)
}

// ── Results ──────────────────────────────────────────────────────

export async function getResults(
  jobId: string,
  params?: {
    engine_name?: string
    max_qvalue?: number
    min_score?: number
    accession?: string
    page?: number
    page_size?: number
  }
): Promise<ProteoformResult[]> {
  const { data } = await api.get<ProteoformResult[]>(`/results/job/${jobId}`, { params })
  return data
}

export async function getResultCount(jobId: string): Promise<{ count: number }> {
  const { data } = await api.get(`/results/job/${jobId}/count`)
  return data
}

export async function getResultsByEngine(jobId: string): Promise<{ engine: string; count: number }[]> {
  const { data } = await api.get(`/results/job/${jobId}/by-engine`)
  return data
}

export async function getVennData(jobId: string): Promise<VennData> {
  const { data } = await api.get<VennData>(`/results/job/${jobId}/venn`)
  return data
}

export async function getResult(resultId: string): Promise<ProteoformResult> {
  const { data } = await api.get<ProteoformResult>(`/results/${resultId}`)
  return data
}

// ── Exports ──────────────────────────────────────────────────────

export function getExportUrl(jobId: string, format: ExportFormat): string {
  return `${BASE}/exports/job/${jobId}/${format}`
}

// ── Conversions ───────────────────────────────────────────────────

export async function listConversionTools(): Promise<ConversionTool[]> {
  const { data } = await api.get<ConversionTool[]>('/conversions/tools')
  return data
}

export async function createConversion(payload: ConversionCreate): Promise<Conversion> {
  const { data } = await api.post<Conversion>('/conversions', payload)
  return data
}

export async function listConversions(): Promise<Conversion[]> {
  const { data } = await api.get<Conversion[]>('/conversions')
  return data
}

export async function getConversion(id: string): Promise<Conversion> {
  const { data } = await api.get<Conversion>(`/conversions/${id}`)
  return data
}

export async function deleteConversion(id: string): Promise<void> {
  await api.delete(`/conversions/${id}`)
}

export function getConversionDownloadUrl(id: string): string {
  return `${BASE}/conversions/${id}/download`
}
