export interface Upload {
  id: string
  original_filename: string
  file_type: string
  size_bytes: number
  checksum_md5: string
  created_at: string
}

export interface SearchParameters {
  precursor_tolerance_ppm: number
  fragment_tolerance_ppm: number
  fixed_modifications: string[]
  variable_modifications: string[]
  max_unexpected_mass_shift: number
  fdr_threshold: number
  protease: string
  min_score: number
  max_ptm_count: number
  deconvolution_engine: string
  search_engine: string
}

export interface JobEngineRun {
  id: string
  engine_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  log: string
  result_count: number
  started_at: string | null
  completed_at: string | null
}

export interface Job {
  id: string
  name: string
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  mzml_file_id: string
  fasta_file_id: string
  ptm_file_id: string | null
  parameters: Partial<SearchParameters>
  engines_requested: string[]
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  engine_runs: JobEngineRun[]
}

export interface JobStatus {
  job_id: string
  status: string
  progress_percent: number
  engine_statuses: Record<string, string>
  total_results: number
}

export interface PTM {
  modification: string
  residue: string
  position: number
  mass_shift?: number
  source?: string
}

export interface ProteoformResult {
  id: string
  job_id: string
  job_engine_id: string
  engine_name: string
  engine_version: string | null

  spectrum_id: string | null
  scan_number: number | null
  source_file: string | null

  precursor_mz: number | null
  charge: number | null
  observed_mass: number | null
  theoretical_mass: number | null
  delta_mass: number | null

  accession: string | null
  protein_name: string | null
  sequence: string | null
  proteoform_string: string | null
  proteoform_mass: number | null

  score: number | null
  evalue: number | null
  qvalue: number | null
  fdr: number | null

  matched_fragments: number | null
  sequence_coverage: number | null

  ptms: PTM[]
  localization_confidence: number | null
  is_demo: boolean
}

export interface EngineInfo {
  name: string
  version: string
  input_formats: string[]
  output_formats: string[]
  available: boolean
}

export interface VennData {
  engines: string[]
  sets: Record<string, number>
  overlaps: Record<string, number>
}

export type ExportFormat = 'csv' | 'tsv' | 'json' | 'mzidentml' | 'proforma' | 'ptm_xml' | 'fasta' | 'raw_zip' | 'consensus'
