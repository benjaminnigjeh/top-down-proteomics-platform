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

export type EngineCategory = 'search' | 'deconvolution' | 'pipeline' | 'demo'

export interface EngineInfo {
  name: string
  version: string
  category: EngineCategory
  description: string
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

// ── Conversions ───────────────────────────────────────────────────

export interface ConversionTool {
  id: string
  name: string
  category: 'format_conversion' | 'deconvolution'
  description: string
  available: boolean
  version: string | null
  input_formats: string[]
  output_formats: string[]
}

export interface ConversionOptions {
  output_format?: string
  mz_precision?: number
  intensity_precision?: number
  zlib?: boolean
  numpress_linear?: boolean
  numpress_slof?: boolean
  numpress_pic?: boolean
  gzip_output?: boolean
  write_index?: boolean
  sim_as_spectra?: boolean
  srm_as_spectra?: boolean
  combine_ion_mobility?: boolean
  ignore_unknown_instrument?: boolean
  strip_location?: boolean
  strip_version?: boolean
  single_threaded?: boolean
  peak_picking?: string
  peak_picking_ms_levels?: string
  peak_picking_snr?: number | null
  ms_levels?: string | null
  scan_number_range?: string | null
  scan_time_range?: string | null
  mz_window?: string | null
  threshold_type?: string | null
  threshold_value?: number | null
  threshold_orientation?: string
  zero_samples?: string | null
  charge_state_predictor?: boolean
  etd_filter?: boolean
  precursor_recalculation?: boolean
  precursor_refine?: boolean
  metadata_fixer?: boolean
  sort_by_scan_time?: boolean
  ms2_denoise?: boolean
  ms2_deisotope?: boolean
  activation_type?: string | null
  polarity?: string | null
  analyzer?: string | null
  min_peaks?: number | null
  // THRASH
  thrash_min_mass?: number
  thrash_max_mass?: number
  thrash_min_charge?: number
  thrash_max_charge?: number
  thrash_max_fit?: number
  thrash_sn_threshold?: number
  // UniDec
  unidec_min_mass?: number
  unidec_max_mass?: number
  unidec_min_mz?: number
  unidec_max_mz?: number
  // Xtract
  xtract_min_mass?: number
  xtract_max_mass?: number
  xtract_resolution?: number
  xtract_sn?: number
  xtract_fit?: number
}

export interface ConversionCreate {
  name: string
  input_file_id: string
  tool: string
  options: ConversionOptions
}

export interface Conversion {
  id: string
  name: string
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed'
  input_file_id: string
  input_filename: string
  tool: string
  options: Record<string, unknown>
  output_filename: string | null
  output_size_bytes: number | null
  log: string
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}
