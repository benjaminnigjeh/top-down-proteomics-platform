import type { SearchParameters } from '@/types'

const DEFAULTS: SearchParameters = {
  precursor_tolerance_ppm: 10,
  fragment_tolerance_ppm: 15,
  fixed_modifications: [],
  variable_modifications: [],
  max_unexpected_mass_shift: 500,
  fdr_threshold: 0.01,
  protease: 'no_cleavage',
  min_score: 0,
  max_ptm_count: 5,
  deconvolution_engine: 'topfd',
  search_engine: 'toppic',
}

const COMMON_MODS = [
  'C57', // Cys carbamidomethyl
  'Phospho(ST)',
  'Phospho(Y)',
  'Acetyl(N-term)',
  'Oxidation(M)',
  'Methyl(K)',
  'Dimethyl(R)',
]

interface ParameterFormProps {
  value: Partial<SearchParameters>
  onChange: (params: Partial<SearchParameters>) => void
}

export function ParameterForm({ value, onChange }: ParameterFormProps) {
  const params = { ...DEFAULTS, ...value }

  const set = (key: keyof SearchParameters, v: unknown) =>
    onChange({ ...value, [key]: v })

  const toggleMod = (mods: string[], mod: string) =>
    mods.includes(mod) ? mods.filter((m) => m !== mod) : [...mods, mod]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Precursor Tolerance (ppm)">
          <input type="number" value={params.precursor_tolerance_ppm} step="0.5" min="0"
            onChange={(e) => set('precursor_tolerance_ppm', parseFloat(e.target.value))}
            className="input-field" />
        </Field>
        <Field label="Fragment Tolerance (ppm)">
          <input type="number" value={params.fragment_tolerance_ppm} step="0.5" min="0"
            onChange={(e) => set('fragment_tolerance_ppm', parseFloat(e.target.value))}
            className="input-field" />
        </Field>
        <Field label="FDR Threshold">
          <select value={params.fdr_threshold} onChange={(e) => set('fdr_threshold', parseFloat(e.target.value))} className="input-field">
            <option value={0.001}>0.1%</option>
            <option value={0.01}>1%</option>
            <option value={0.05}>5%</option>
          </select>
        </Field>
        <Field label="Max Unexpected Mass Shift (Da)">
          <input type="number" value={params.max_unexpected_mass_shift} step="50" min="0"
            onChange={(e) => set('max_unexpected_mass_shift', parseFloat(e.target.value))}
            className="input-field" />
        </Field>
        <Field label="Max PTM Count">
          <input type="number" value={params.max_ptm_count} step="1" min="0" max="20"
            onChange={(e) => set('max_ptm_count', parseInt(e.target.value))}
            className="input-field" />
        </Field>
        <Field label="Protease">
          <select value={params.protease} onChange={(e) => set('protease', e.target.value)} className="input-field">
            <option value="no_cleavage">No Cleavage (Top-Down)</option>
            <option value="trypsin">Trypsin</option>
            <option value="lys_c">Lys-C</option>
          </select>
        </Field>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Fixed Modifications</label>
        <div className="flex flex-wrap gap-2">
          {COMMON_MODS.slice(0, 3).map((mod) => (
            <ModToggle
              key={mod}
              mod={mod}
              active={params.fixed_modifications.includes(mod)}
              onClick={() => set('fixed_modifications', toggleMod(params.fixed_modifications, mod))}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Variable Modifications</label>
        <div className="flex flex-wrap gap-2">
          {COMMON_MODS.slice(1).map((mod) => (
            <ModToggle
              key={mod}
              mod={mod}
              active={params.variable_modifications.includes(mod)}
              onClick={() => set('variable_modifications', toggleMod(params.variable_modifications, mod))}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>
      {children}
    </label>
  )
}

function ModToggle({ mod, active, onClick }: { mod: string; active: boolean; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
        active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
      }`}>
      {mod}
    </button>
  )
}
