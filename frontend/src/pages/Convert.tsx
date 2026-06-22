import { useState } from 'react'
import { clsx } from 'clsx'
import {
  FileText, Zap, ChevronDown, ChevronRight, Download,
  CheckCircle, XCircle, Loader2, Trash2, RefreshCw, Info,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { uploadFile, getConversionDownloadUrl } from '@/api/client'
import { useConversionTools, useConversions, useCreateConversion, useDeleteConversion, useConversion } from '@/hooks/useConversions'
import type { ConversionOptions, Conversion, ConversionTool } from '@/types'

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  pending:   'bg-gray-100 text-gray-600',
  queued:    'bg-blue-100 text-blue-700',
  running:   'bg-amber-100 text-amber-700',
  completed: 'bg-green-100 text-green-700',
  failed:    'bg-red-100 text-red-700',
}

function Chip({ label, color }: { label: string; color: string }) {
  return <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', color)}>{label}</span>
}

function SectionHeader({ title, open, onToggle }: { title: string; open: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex items-center gap-2 w-full text-left text-sm font-semibold text-gray-700 hover:text-gray-900 py-1"
    >
      {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      {title}
    </button>
  )
}

function Field({ label, tip, children }: { label: string; tip?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-44 shrink-0">
        <div className="text-xs font-medium text-gray-700 leading-5">{label}</div>
        {tip && <div className="text-xs text-gray-400 leading-4">{tip}</div>}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  )
}

function Select({ value, onChange, options }: {
  value: string; onChange: (v: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:ring-1 focus:ring-blue-400"
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer select-none">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={clsx(
          'relative w-8 h-4 rounded-full transition-colors',
          checked ? 'bg-blue-500' : 'bg-gray-300'
        )}
      >
        <span className={clsx(
          'absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-4' : 'translate-x-0.5'
        )} />
      </button>
      <span className="text-sm text-gray-700">{label}</span>
    </label>
  )
}

function NumInput({ value, onChange, min, max, step, placeholder }: {
  value: number | string; onChange: (v: string) => void
  min?: number; max?: number; step?: number; placeholder?: string
}) {
  return (
    <input
      type="number"
      value={value}
      onChange={e => onChange(e.target.value)}
      min={min} max={max} step={step}
      placeholder={placeholder}
      className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:ring-1 focus:ring-blue-400"
    />
  )
}

function TextInput({ value, onChange, placeholder }: {
  value: string; onChange: (v: string) => void; placeholder?: string
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:ring-1 focus:ring-blue-400"
    />
  )
}

// ──────────────────────────────────────────────────────────────────────────────
// Options panels per tool
// ──────────────────────────────────────────────────────────────────────────────

function MsconvertOptions({ opts, setOpts }: { opts: ConversionOptions; setOpts: (o: ConversionOptions) => void }) {
  const [open, setOpen] = useState<Record<string, boolean>>({
    format: true, precision: false, compression: false,
    peak: false, msfilter: false, scans: false, mz: false,
    threshold: false, zeros: false, etd: false, charge: false,
    precursor: false, ms2: false, activation: false, misc: false,
  })
  const tog = (k: string) => setOpen(p => ({ ...p, [k]: !p[k] }))
  const set = (patch: Partial<ConversionOptions>) => setOpts({ ...opts, ...patch })

  return (
    <div className="space-y-3">
      {/* Format */}
      <div>
        <SectionHeader title="Output Format" open={open.format} onToggle={() => tog('format')} />
        {open.format && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Format">
              <Select value={opts.output_format ?? 'mzML'} onChange={v => set({ output_format: v })}
                options={[
                  { value: 'mzML', label: 'mzML (recommended)' },
                  { value: 'mzXML', label: 'mzXML' },
                  { value: 'mgf', label: 'MGF (Mascot Generic)' },
                  { value: 'ms2', label: 'MS2' },
                  { value: 'mz5', label: 'mz5 (HDF5)' },
                  { value: 'cms2', label: 'CMS2 (compressed)' },
                ]} />
            </Field>
            <Field label="Write index" tip="Speeds up random access">
              <Toggle checked={opts.write_index ?? true} onChange={v => set({ write_index: v })} label="" />
            </Field>
            <Field label="Gzip output" tip="Adds .gz suffix">
              <Toggle checked={opts.gzip_output ?? false} onChange={v => set({ gzip_output: v })} label="" />
            </Field>
          </div>
        )}
      </div>

      {/* Precision */}
      <div>
        <SectionHeader title="Binary Precision" open={open.precision} onToggle={() => tog('precision')} />
        {open.precision && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="m/z precision" tip="64-bit default">
              <Select value={String(opts.mz_precision ?? 64)} onChange={v => set({ mz_precision: Number(v) })}
                options={[{ value: '64', label: '64-bit (default)' }, { value: '32', label: '32-bit (smaller)' }]} />
            </Field>
            <Field label="Intensity precision" tip="32-bit default">
              <Select value={String(opts.intensity_precision ?? 32)} onChange={v => set({ intensity_precision: Number(v) })}
                options={[{ value: '32', label: '32-bit (default)' }, { value: '64', label: '64-bit (max accuracy)' }]} />
            </Field>
          </div>
        )}
      </div>

      {/* Compression */}
      <div>
        <SectionHeader title="Compression" open={open.compression} onToggle={() => tog('compression')} />
        {open.compression && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.zlib ?? false} onChange={v => set({ zlib: v })} label="zlib compression" />
            <Toggle checked={opts.numpress_linear ?? false} onChange={v => set({ numpress_linear: v })} label="Numpress linear (m/z + RT)" />
            <Toggle checked={opts.numpress_slof ?? false} onChange={v => set({ numpress_slof: v })} label="Numpress SLOF (intensities)" />
            <Toggle checked={opts.numpress_pic ?? false} onChange={v => set({ numpress_pic: v })} label="Numpress PIC (integer intensities)" />
          </div>
        )}
      </div>

      {/* Peak picking */}
      <div>
        <SectionHeader title="Peak Picking" open={open.peak} onToggle={() => tog('peak')} />
        {open.peak && (
          <div className="mt-2 pl-6 space-y-2">
            <div className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1 border border-amber-200">
              Peak picking must be the first filter. When using "vendor" mode, vendor DLLs are required.
            </div>
            <Field label="Algorithm">
              <Select value={opts.peak_picking ?? 'none'} onChange={v => set({ peak_picking: v })}
                options={[
                  { value: 'none', label: 'None (keep profile data)' },
                  { value: 'vendor', label: 'Vendor (uses instrument DLLs)' },
                  { value: 'cwt', label: 'CWT wavelet (cross-platform)' },
                ]} />
            </Field>
            {opts.peak_picking !== 'none' && (
              <>
                <Field label="MS levels" tip="e.g. 1- or 1-2">
                  <TextInput value={opts.peak_picking_ms_levels ?? '1-'} onChange={v => set({ peak_picking_ms_levels: v })} placeholder="1-" />
                </Field>
                {opts.peak_picking === 'cwt' && (
                  <Field label="SNR threshold">
                    <NumInput value={opts.peak_picking_snr ?? 1.0} onChange={v => set({ peak_picking_snr: Number(v) })} min={0} step={0.1} placeholder="1.0" />
                  </Field>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* MS level filter */}
      <div>
        <SectionHeader title="MS Level Filter" open={open.msfilter} onToggle={() => tog('msfilter')} />
        {open.msfilter && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Keep MS levels" tip="int_set, e.g. 1-2 or 2">
              <TextInput value={opts.ms_levels ?? ''} onChange={v => set({ ms_levels: v || undefined })} placeholder="1- (all levels)" />
            </Field>
          </div>
        )}
      </div>

      {/* Scan range */}
      <div>
        <SectionHeader title="Scan Range" open={open.scans} onToggle={() => tog('scans')} />
        {open.scans && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Scan numbers" tip="e.g. 1-5000">
              <TextInput value={opts.scan_number_range ?? ''} onChange={v => set({ scan_number_range: v || undefined })} placeholder="1-5000" />
            </Field>
            <Field label="Scan time (s)" tip="e.g. [0,3600]">
              <TextInput value={opts.scan_time_range ?? ''} onChange={v => set({ scan_time_range: v || undefined })} placeholder="[60,3600]" />
            </Field>
          </div>
        )}
      </div>

      {/* m/z window */}
      <div>
        <SectionHeader title="m/z Window" open={open.mz} onToggle={() => tog('mz')} />
        {open.mz && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="m/z range" tip="e.g. [200,2000]">
              <TextInput value={opts.mz_window ?? ''} onChange={v => set({ mz_window: v || undefined })} placeholder="[200,2000]" />
            </Field>
          </div>
        )}
      </div>

      {/* Intensity threshold */}
      <div>
        <SectionHeader title="Intensity Threshold" open={open.threshold} onToggle={() => tog('threshold')} />
        {open.threshold && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Type">
              <Select value={opts.threshold_type ?? ''} onChange={v => set({ threshold_type: v || undefined })}
                options={[
                  { value: '', label: 'None' },
                  { value: 'absolute', label: 'Absolute' },
                  { value: 'bpi-relative', label: 'BPI-relative (0–1)' },
                  { value: 'tic-relative', label: 'TIC-relative (0–1)' },
                  { value: 'count', label: 'Peak count (n most intense)' },
                  { value: 'tic-cutoff', label: 'TIC cutoff' },
                ]} />
            </Field>
            {opts.threshold_type && (
              <>
                <Field label="Value">
                  <NumInput value={opts.threshold_value ?? ''} onChange={v => set({ threshold_value: Number(v) })} step={0.01} placeholder="e.g. 100 or 0.01" />
                </Field>
                <Field label="Orientation">
                  <Select value={opts.threshold_orientation ?? 'most-intense'} onChange={v => set({ threshold_orientation: v })}
                    options={[
                      { value: 'most-intense', label: 'Keep most intense' },
                      { value: 'least-intense', label: 'Keep least intense' },
                    ]} />
                </Field>
              </>
            )}
          </div>
        )}
      </div>

      {/* Zero samples */}
      <div>
        <SectionHeader title="Zero Samples" open={open.zeros} onToggle={() => tog('zeros')} />
        {open.zeros && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Mode" tip="Profile data only">
              <Select value={opts.zero_samples ?? ''} onChange={v => set({ zero_samples: v || undefined })}
                options={[
                  { value: '', label: 'None' },
                  { value: 'removeExtra', label: 'Remove extra zeros' },
                  { value: 'addMissing', label: 'Add missing zeros' },
                  { value: 'addMissing=5', label: 'Add missing (5 flanking)' },
                ]} />
            </Field>
          </div>
        )}
      </div>

      {/* ETD filter */}
      <div>
        <SectionHeader title="ETD Filter" open={open.etd} onToggle={() => tog('etd')} />
        {open.etd && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.etd_filter ?? false} onChange={v => set({ etd_filter: v })} label="Apply ETD filter" />
          </div>
        )}
      </div>

      {/* Charge state predictor */}
      <div>
        <SectionHeader title="Charge State Predictor" open={open.charge} onToggle={() => tog('charge')} />
        {open.charge && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.charge_state_predictor ?? false} onChange={v => set({ charge_state_predictor: v })} label="Predict charge states" />
          </div>
        )}
      </div>

      {/* Precursor */}
      <div>
        <SectionHeader title="Precursor" open={open.precursor} onToggle={() => tog('precursor')} />
        {open.precursor && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.precursor_recalculation ?? false} onChange={v => set({ precursor_recalculation: v })} label="Precursor recalculation (Orbitrap/FT)" />
            <Toggle checked={opts.precursor_refine ?? false} onChange={v => set({ precursor_refine: v })} label="Precursor refinement (Orbitrap/FT/TOF)" />
          </div>
        )}
      </div>

      {/* MS2 */}
      <div>
        <SectionHeader title="MS2 Processing" open={open.ms2} onToggle={() => tog('ms2')} />
        {open.ms2 && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.ms2_denoise ?? false} onChange={v => set({ ms2_denoise: v })} label="MS2 noise removal" />
            <Toggle checked={opts.ms2_deisotope ?? false} onChange={v => set({ ms2_deisotope: v })} label="MS2 deisotoping" />
            <Toggle checked={opts.sort_by_scan_time ?? false} onChange={v => set({ sort_by_scan_time: v })} label="Sort by scan time" />
            <Toggle checked={opts.metadata_fixer ?? false} onChange={v => set({ metadata_fixer: v })} label="Metadata fixer (TIC/BPI after peak picking)" />
          </div>
        )}
      </div>

      {/* Activation / analyzer / polarity */}
      <div>
        <SectionHeader title="Activation / Analyzer / Polarity" open={open.activation} onToggle={() => tog('activation')} />
        {open.activation && (
          <div className="mt-2 pl-6 space-y-2">
            <Field label="Activation type" tip="Keep only this type">
              <Select value={opts.activation_type ?? ''} onChange={v => set({ activation_type: v || undefined })}
                options={[
                  { value: '', label: 'All' },
                  { value: 'ETD', label: 'ETD' },
                  { value: 'CID', label: 'CID' },
                  { value: 'HCD', label: 'HCD' },
                  { value: 'ECD', label: 'ECD' },
                  { value: 'IRMPD', label: 'IRMPD' },
                  { value: 'SA', label: 'SA (Supplemental activation)' },
                ]} />
            </Field>
            <Field label="Analyzer">
              <Select value={opts.analyzer ?? ''} onChange={v => set({ analyzer: v || undefined })}
                options={[
                  { value: '', label: 'All' },
                  { value: 'orbi', label: 'Orbitrap' },
                  { value: 'FT', label: 'FT' },
                  { value: 'IT', label: 'Ion Trap' },
                  { value: 'quad', label: 'Quadrupole' },
                  { value: 'TOF', label: 'TOF' },
                ]} />
            </Field>
            <Field label="Polarity">
              <Select value={opts.polarity ?? ''} onChange={v => set({ polarity: v || undefined })}
                options={[
                  { value: '', label: 'Both' },
                  { value: 'positive', label: 'Positive' },
                  { value: 'negative', label: 'Negative' },
                ]} />
            </Field>
          </div>
        )}
      </div>

      {/* Misc */}
      <div>
        <SectionHeader title="Miscellaneous" open={open.misc} onToggle={() => tog('misc')} />
        {open.misc && (
          <div className="mt-2 pl-6 space-y-2">
            <Toggle checked={opts.sim_as_spectra ?? false} onChange={v => set({ sim_as_spectra: v })} label="SIM as spectra (not chromatograms)" />
            <Toggle checked={opts.srm_as_spectra ?? false} onChange={v => set({ srm_as_spectra: v })} label="SRM as spectra (not chromatograms)" />
            <Toggle checked={opts.combine_ion_mobility ?? false} onChange={v => set({ combine_ion_mobility: v })} label="Combine ion mobility scans" />
            <Toggle checked={opts.ignore_unknown_instrument ?? false} onChange={v => set({ ignore_unknown_instrument: v })} label="Ignore unknown instrument error" />
            <Toggle checked={opts.strip_location ?? false} onChange={v => set({ strip_location: v })} label="Strip file location from source metadata" />
            <Toggle checked={opts.strip_version ?? false} onChange={v => set({ strip_version: v })} label="Strip software version from metadata" />
            <Toggle checked={opts.single_threaded ?? false} onChange={v => set({ single_threaded: v })} label="Single-threaded mode" />
            <Field label="Remove sparse spectra" tip="Keep only spectra with ≥ N peaks">
              <NumInput value={opts.min_peaks ?? ''} onChange={v => set({ min_peaks: v ? Number(v) : undefined })} min={0} placeholder="disabled" />
            </Field>
          </div>
        )}
      </div>
    </div>
  )
}

function ThrashOptions({ opts, setOpts }: { opts: ConversionOptions; setOpts: (o: ConversionOptions) => void }) {
  const set = (p: Partial<ConversionOptions>) => setOpts({ ...opts, ...p })
  return (
    <div className="space-y-2">
      <Field label="Mass range (Da)" tip="Min – Max neutral mass">
        <div className="flex gap-2">
          <NumInput value={opts.thrash_min_mass ?? 400} onChange={v => set({ thrash_min_mass: Number(v) })} min={0} placeholder="400" />
          <span className="self-center text-gray-400">–</span>
          <NumInput value={opts.thrash_max_mass ?? 200000} onChange={v => set({ thrash_max_mass: Number(v) })} min={0} placeholder="200000" />
        </div>
      </Field>
      <Field label="Charge range" tip="Min – Max charge state">
        <div className="flex gap-2">
          <NumInput value={opts.thrash_min_charge ?? 1} onChange={v => set({ thrash_min_charge: Number(v) })} min={1} placeholder="1" />
          <span className="self-center text-gray-400">–</span>
          <NumInput value={opts.thrash_max_charge ?? 60} onChange={v => set({ thrash_max_charge: Number(v) })} min={1} placeholder="60" />
        </div>
      </Field>
      <Field label="Max fit score" tip="Lower = stricter isotope fit (0–1)">
        <NumInput value={opts.thrash_max_fit ?? 0.25} onChange={v => set({ thrash_max_fit: Number(v) })} min={0} max={1} step={0.01} placeholder="0.25" />
      </Field>
      <Field label="S/N threshold">
        <NumInput value={opts.thrash_sn_threshold ?? 3.0} onChange={v => set({ thrash_sn_threshold: Number(v) })} min={0} step={0.5} placeholder="3.0" />
      </Field>
    </div>
  )
}

function UniDecOpts({ opts, setOpts }: { opts: ConversionOptions; setOpts: (o: ConversionOptions) => void }) {
  const set = (p: Partial<ConversionOptions>) => setOpts({ ...opts, ...p })
  return (
    <div className="space-y-2">
      <Field label="Mass range (Da)">
        <div className="flex gap-2">
          <NumInput value={opts.unidec_min_mass ?? 1000} onChange={v => set({ unidec_min_mass: Number(v) })} min={0} placeholder="1000" />
          <span className="self-center text-gray-400">–</span>
          <NumInput value={opts.unidec_max_mass ?? 200000} onChange={v => set({ unidec_max_mass: Number(v) })} min={0} placeholder="200000" />
        </div>
      </Field>
      <Field label="m/z range">
        <div className="flex gap-2">
          <NumInput value={opts.unidec_min_mz ?? 200} onChange={v => set({ unidec_min_mz: Number(v) })} min={0} placeholder="200" />
          <span className="self-center text-gray-400">–</span>
          <NumInput value={opts.unidec_max_mz ?? 8000} onChange={v => set({ unidec_max_mz: Number(v) })} min={0} placeholder="8000" />
        </div>
      </Field>
    </div>
  )
}

function XtractOpts({ opts, setOpts }: { opts: ConversionOptions; setOpts: (o: ConversionOptions) => void }) {
  const set = (p: Partial<ConversionOptions>) => setOpts({ ...opts, ...p })
  return (
    <div className="space-y-2">
      <Field label="Mass range (Da)">
        <div className="flex gap-2">
          <NumInput value={opts.xtract_min_mass ?? 400} onChange={v => set({ xtract_min_mass: Number(v) })} min={0} placeholder="400" />
          <span className="self-center text-gray-400">–</span>
          <NumInput value={opts.xtract_max_mass ?? 100000} onChange={v => set({ xtract_max_mass: Number(v) })} min={0} placeholder="100000" />
        </div>
      </Field>
      <Field label="Resolution" tip="at 400 m/z">
        <NumInput value={opts.xtract_resolution ?? 60000} onChange={v => set({ xtract_resolution: Number(v) })} min={1000} step={5000} placeholder="60000" />
      </Field>
      <Field label="S/N threshold">
        <NumInput value={opts.xtract_sn ?? 3} onChange={v => set({ xtract_sn: Number(v) })} min={0} step={0.5} placeholder="3" />
      </Field>
      <Field label="Min fit (%)">
        <NumInput value={opts.xtract_fit ?? 44} onChange={v => set({ xtract_fit: Number(v) })} min={0} max={100} step={1} placeholder="44" />
      </Field>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────────
// Conversion history row
// ──────────────────────────────────────────────────────────────────────────────

function ConversionRow({ c, onDelete }: { c: Conversion; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const { data: live } = useConversion(c.id, c.status === 'running' || c.status === 'queued')
  const item = live ?? c
  const downloadUrl = getConversionDownloadUrl(item.id)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(e => !e)}
      >
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm text-gray-900 truncate">{item.name}</div>
          <div className="text-xs text-gray-500">{item.input_filename} → {item.tool}</div>
        </div>
        <Chip label={item.status} color={STATUS_COLOR[item.status] ?? 'bg-gray-100 text-gray-600'} />
        {item.status === 'running' && <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />}
        {item.status === 'completed' && item.output_filename && (
          <a
            href={downloadUrl}
            download={item.output_filename}
            onClick={e => e.stopPropagation()}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
          >
            <Download className="w-4 h-4" />
            {item.output_filename}
            {item.output_size_bytes ? ` (${(item.output_size_bytes / 1024 / 1024).toFixed(1)} MB)` : ''}
          </a>
        )}
        <button
          type="button"
          onClick={e => { e.stopPropagation(); onDelete() }}
          className="p-1 text-gray-400 hover:text-red-500"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      {expanded && (
        <div className="px-4 pb-3 border-t border-gray-100 bg-gray-50">
          {item.error_message && (
            <div className="mt-2 text-xs text-red-700 bg-red-50 rounded p-2 border border-red-200">{item.error_message}</div>
          )}
          {item.log && (
            <pre className="mt-2 text-xs text-gray-600 bg-white border border-gray-200 rounded p-2 max-h-48 overflow-y-auto whitespace-pre-wrap font-mono">
              {item.log}
            </pre>
          )}
          {!item.log && !item.error_message && (
            <p className="mt-2 text-xs text-gray-400 italic">No log yet.</p>
          )}
        </div>
      )}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────────
// Main page
// ──────────────────────────────────────────────────────────────────────────────

const TOOL_ICON: Record<string, React.ElementType> = {
  format_conversion: FileText,
  deconvolution: Zap,
}

export default function ConvertPage() {
  const { data: tools = [] } = useConversionTools()
  const { data: conversions = [] } = useConversions()
  const createMut = useCreateConversion()
  const deleteMut = useDeleteConversion()

  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadedId, setUploadedId] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState('')

  const [selectedTool, setSelectedTool] = useState('msconvert')
  const [jobName, setJobName] = useState('')
  const [opts, setOpts] = useState<ConversionOptions>({})
  const [submitError, setSubmitError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleFileChange = async (f: File) => {
    setFile(f)
    setUploadedId(null)
    setUploadError('')
    setUploading(true)
    try {
      const up = await uploadFile(f)
      setUploadedId(up.id)
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || err?.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async () => {
    if (!uploadedId) return
    setSubmitting(true)
    setSubmitError('')
    try {
      await createMut.mutateAsync({
        name: jobName || `${file?.name ?? 'file'}_${selectedTool}_${new Date().toISOString().slice(0, 16)}`,
        input_file_id: uploadedId,
        tool: selectedTool,
        options: opts,
      })
      // Reset
      setFile(null)
      setUploadedId(null)
      setJobName('')
      setOpts({})
    } catch (err: any) {
      setSubmitError(err?.response?.data?.detail || err?.message || 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const toolMeta = tools.find(t => t.id === selectedTool)
  const formatTools = tools.filter(t => t.category === 'format_conversion')
  const deconvTools = tools.filter(t => t.category === 'deconvolution')

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">File Conversion & Deconvolution</h1>
        <p className="text-sm text-gray-500 mt-1">
          Convert vendor instrument files to open formats, or deconvolve charge states to neutral masses.
        </p>
      </div>

      {/* Tool selector */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Select Tool</h2>
        <div className="space-y-3">
          {/* Format conversion group */}
          {formatTools.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 mb-1.5 uppercase tracking-wide">
                <FileText className="w-3.5 h-3.5" /> Format Conversion
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {formatTools.map(t => <ToolCard key={t.id} tool={t} selected={selectedTool === t.id} onSelect={() => setSelectedTool(t.id)} />)}
              </div>
            </div>
          )}
          {/* Deconvolution group */}
          {deconvTools.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-700 mb-1.5 uppercase tracking-wide">
                <Zap className="w-3.5 h-3.5" /> Deconvolution
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {deconvTools.map(t => <ToolCard key={t.id} tool={t} selected={selectedTool === t.id} onSelect={() => setSelectedTool(t.id)} />)}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* File upload */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Input File</h2>
        {toolMeta && (
          <p className="text-xs text-gray-500 mb-2">
            Accepted: <span className="font-mono">{toolMeta.input_formats.join(', ')}</span>
          </p>
        )}
        <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg px-4 py-6 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
          <FileText className="w-8 h-8 text-gray-400 mb-1" />
          <span className="text-sm text-gray-600">{file ? file.name : 'Click or drag a file here'}</span>
          {file && <span className="text-xs text-gray-400 mt-0.5">{(file.size / 1024 / 1024).toFixed(1)} MB</span>}
          <input type="file" className="hidden" onChange={e => e.target.files?.[0] && handleFileChange(e.target.files[0])} />
        </label>
        {uploading && <p className="text-xs text-blue-600 mt-2 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Uploading…</p>}
        {uploadedId && !uploading && <p className="text-xs text-green-600 mt-2 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Uploaded successfully</p>}
        {uploadError && <p className="text-xs text-red-600 mt-2">{uploadError}</p>}
      </Card>

      {/* Options */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Options</h2>
        <div className="space-y-2">
          <Field label="Job name">
            <TextInput value={jobName} onChange={setJobName} placeholder="Auto-generated if blank" />
          </Field>
        </div>
        <div className="mt-4">
          {selectedTool === 'msconvert' && <MsconvertOptions opts={opts} setOpts={setOpts} />}
          {selectedTool === 'thermoparser' && (
            <div className="space-y-2">
              <Field label="Output format">
                <Select value={(opts as any).thermo_output_format ?? 'mzML'} onChange={v => setOpts({ ...opts, thermo_output_format: v } as any)}
                  options={[
                    { value: 'mzML', label: 'mzML' },
                    { value: 'mzXML', label: 'mzXML' },
                    { value: 'mgf', label: 'MGF' },
                    { value: 'parquet', label: 'Parquet' },
                  ]} />
              </Field>
            </div>
          )}
          {selectedTool === 'thrash' && <ThrashOptions opts={opts} setOpts={setOpts} />}
          {selectedTool === 'unidec' && <UniDecOpts opts={opts} setOpts={setOpts} />}
          {selectedTool === 'xtract' && <XtractOpts opts={opts} setOpts={setOpts} />}
        </div>
      </Card>

      {/* Submit */}
      <div className="flex items-center gap-3">
        <Button
          onClick={handleSubmit}
          disabled={!uploadedId || submitting || uploading}
          loading={submitting}
        >
          Start Conversion
        </Button>
        {submitError && <span className="text-sm text-red-600">{submitError}</span>}
      </div>

      {/* History */}
      {conversions.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Conversion History</h2>
          <div className="space-y-2">
            {conversions.map(c => (
              <ConversionRow
                key={c.id}
                c={c}
                onDelete={() => deleteMut.mutate(c.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ToolCard({ tool, selected, onSelect }: { tool: ConversionTool; selected: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={clsx(
        'text-left p-3 rounded-lg border-2 transition-all',
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-gray-300',
        !tool.available && 'opacity-50',
      )}
    >
      <div className="flex items-center gap-2">
        <span className="font-medium text-sm text-gray-900">{tool.name}</span>
        {tool.available
          ? <CheckCircle className="w-3.5 h-3.5 text-green-500 ml-auto" />
          : <XCircle className="w-3.5 h-3.5 text-gray-300 ml-auto" />}
      </div>
      <p className="text-xs text-gray-500 mt-1 leading-relaxed line-clamp-2">{tool.description}</p>
      {tool.version && <span className="text-xs text-gray-400">v{tool.version}</span>}
    </button>
  )
}
