import { useMemo, useState, useEffect, useCallback } from 'react'
import { clsx } from 'clsx'
import type { ProteoformResult } from '@/types'

// ── Mass constants ────────────────────────────────────────────────────────────

const RESIDUE_MASSES: Record<string, number> = {
  A: 71.03711,  R: 156.10111, N: 114.04293, D: 115.02694, C: 103.00919,
  E: 129.04259, Q: 128.05858, G: 57.02146,  H: 137.05891, I: 113.08406,
  L: 113.08406, K: 128.09496, M: 131.04049, F: 147.06841, P: 97.05276,
  S: 87.03203,  T: 101.04768, W: 186.07931, Y: 163.06333, V: 99.06841,
}

const H  = 1.007276
const H2O = 18.010565
const NH3 = 17.026549

// ── Ion color palette (matches publication conventions) ───────────────────────

const ION_COLORS: Record<string, string> = {
  b: '#dc2626',   // red
  y: '#2563eb',   // blue
  a: '#16a34a',   // green
  c: '#7c3aed',   // purple
  z: '#ea580c',   // orange
}

type IonType = 'a' | 'b' | 'c' | 'y' | 'z'

interface Fragment {
  mz: number
  label: string
  type: IonType
  intensity: number  // 0-1
}

// ── Fragment generation ───────────────────────────────────────────────────────

function lcg(seed: number): number {
  return ((seed * 1664525 + 1013904223) >>> 0) / 0x100000000
}

function generateFragments(seq: string, charge = 1): Fragment[] {
  // Strip PTM notation [...]
  const clean = seq.replace(/\[.*?\]/g, '').replace(/[^A-Z]/g, '')
  if (clean.length < 2) return []

  const maxIons = Math.min(clean.length - 1, 28)
  const frags: Fragment[] = []

  // Prefix ions: a, b, c
  let prefix = 0
  for (let i = 0; i < maxIons; i++) {
    prefix += RESIDUE_MASSES[clean[i]] ?? 57.021

    // b-ion: [prefix + H]+
    const bMz = (prefix + H) / charge
    frags.push({ mz: bMz, label: charge > 1 ? `b${i+1}${'+'.repeat(charge)}` : `b${i+1}`, type: 'b', intensity: 0.1 + 0.9 * lcg(i * 31 + 7) })

    // a-ion: b - CO (27.994915)
    frags.push({ mz: bMz - 27.994915 / charge, label: `a${i+1}`, type: 'a', intensity: 0.05 + 0.3 * lcg(i * 13 + 2) })

    // c-ion: b + NH3
    frags.push({ mz: bMz + NH3 / charge, label: `c${i+1}`, type: 'c', intensity: 0.05 + 0.25 * lcg(i * 19 + 11) })
  }

  // Suffix ions: y, z
  let suffix = H2O
  for (let i = clean.length - 1; i > clean.length - 1 - maxIons; i--) {
    suffix += RESIDUE_MASSES[clean[i]] ?? 57.021
    const n = clean.length - i

    // y-ion: [suffix + H]+
    const yMz = (suffix + H) / charge
    frags.push({ mz: yMz, label: `y${n}`, type: 'y', intensity: 0.1 + 0.9 * lcg(i * 17 + 3) })

    // z-ion: y - NH3
    frags.push({ mz: yMz - NH3 / charge, label: `z${n}`, type: 'z', intensity: 0.05 + 0.25 * lcg(i * 23 + 5) })
  }

  // Normalise to 100 (relative intensity %)
  const maxI = Math.max(...frags.map(f => f.intensity))
  frags.forEach(f => { f.intensity = (f.intensity / maxI) * 100 })

  return frags
}

// Synthetic noise baseline peaks (unlabeled)
function generateNoisePeaks(frags: Fragment[]): { mz: number; intensity: number }[] {
  const allMz = new Set(frags.map(f => Math.round(f.mz)))
  const minMz = Math.min(...frags.map(f => f.mz)) - 50
  const maxMz = Math.max(...frags.map(f => f.mz)) + 50
  const noise = []
  let seed = 42
  for (let mz = Math.ceil(minMz / 10) * 10; mz <= maxMz; mz += 10 + Math.floor(lcg(seed++) * 25)) {
    if (!allMz.has(Math.round(mz))) {
      noise.push({ mz: mz + lcg(seed++) * 5, intensity: 1 + lcg(seed++) * 12 })
    }
  }
  return noise
}

// ── Build Plotly stick traces ─────────────────────────────────────────────────
// Each peak = 3 points: (mz,0) → (mz,intensity) → (mz,NaN)
// This draws individual vertical lines without connecting horizontally.

function stickTrace(
  ions: Fragment[],
  color: string,
  name: string,
  showLabel: boolean,
): object {
  const x: (number | null)[] = []
  const y: (number | null)[] = []
  const texts: string[] = []

  for (const ion of ions) {
    x.push(ion.mz, ion.mz, null)
    y.push(0, ion.intensity, null)
    texts.push('', ion.label, '')
  }

  return {
    x,
    y,
    mode: 'lines+text',
    type: 'scatter',
    name,
    line: { color, width: 1.5 },
    text: showLabel ? texts : texts.map(() => ''),
    textposition: 'top center',
    textfont: { size: 9, color },
    hovertemplate:
      ions.map(ion => [`m/z ${ion.mz.toFixed(4)}<br>${ion.label}<br>Int: ${ion.intensity.toFixed(1)}%`, '', '']).flat()
        .map((t, i) => i % 3 === 0 ? t : '<extra></extra>').join('') || '<extra></extra>',
    hoveron: 'points',
    connectgaps: false,
    showlegend: true,
  }
}

function noiseTrace(peaks: { mz: number; intensity: number }[]): object {
  const x: (number | null)[] = []
  const y: (number | null)[] = []
  for (const p of peaks) {
    x.push(p.mz, p.mz, null)
    y.push(0, p.intensity, null)
  }
  return {
    x, y,
    mode: 'lines',
    type: 'scatter',
    name: 'noise',
    line: { color: '#9ca3af', width: 0.8 },
    hoverinfo: 'skip',
    showlegend: false,
    connectgaps: false,
  }
}

// ── Per-ion hover template (correct tooltip per peak) ────────────────────────

function buildHoverTexts(ions: Fragment[]): string[] {
  return ions.flatMap(ion => [
    `<b>${ion.label}</b><br>m/z: ${ion.mz.toFixed(4)}<br>Intensity: ${ion.intensity.toFixed(1)}%<extra></extra>`,
    `<b>${ion.label}</b><br>m/z: ${ion.mz.toFixed(4)}<br>Intensity: ${ion.intensity.toFixed(1)}%<extra></extra>`,
    '<extra></extra>',
  ])
}

function stickTraceV2(ions: Fragment[], color: string, name: string): object {
  const x: (number | null)[] = []
  const y: (number | null)[] = []
  const text: string[] = []
  const hovertext: string[] = []

  for (const ion of ions) {
    x.push(ion.mz, ion.mz, null)
    y.push(0, ion.intensity, null)
    text.push('', ion.label, '')
    hovertext.push('', `<b>${ion.label}</b><br>m/z: ${ion.mz.toFixed(4)}<br>${ion.intensity.toFixed(1)}%`, '')
  }

  return {
    x, y, text, hovertext,
    mode: 'lines+text',
    type: 'scatter',
    name,
    line: { color, width: 1.6 },
    textposition: 'top center',
    textfont: { size: 9.5, color, family: 'Arial, sans-serif' },
    hovertemplate: '%{hovertext}<extra></extra>',
    hoveron: 'points',
    connectgaps: false,
    showlegend: true,
  }
}

// ── Ion type selector ─────────────────────────────────────────────────────────

const ION_ORDER: IonType[] = ['b', 'y', 'a', 'c', 'z']
const ION_LABELS: Record<IonType, string> = { b: 'b ions', y: 'y ions', a: 'a ions', c: 'c ions', z: 'z ions' }

const ION_BG: Record<IonType, string> = {
  b: 'bg-red-100 border-red-400 text-red-700',
  y: 'bg-blue-100 border-blue-400 text-blue-700',
  a: 'bg-green-100 border-green-400 text-green-700',
  c: 'bg-purple-100 border-purple-400 text-purple-700',
  z: 'bg-orange-100 border-orange-400 text-orange-700',
}
const ION_BG_OFF = 'bg-gray-100 border-gray-300 text-gray-400 line-through'

function IonTypeSelector({
  active,
  onChange,
}: {
  active: Set<IonType>
  onChange: (t: IonType) => void
}) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className="text-xs text-gray-500 font-medium mr-1">Show ions:</span>
      {ION_ORDER.map(t => {
        const on = active.has(t)
        return (
          <button
            key={t}
            type="button"
            onClick={() => onChange(t)}
            title={on ? `Hide ${ION_LABELS[t]}` : `Show ${ION_LABELS[t]}`}
            className={clsx(
              'px-2.5 py-0.5 rounded border text-xs font-mono font-semibold transition-all select-none',
              on ? ION_BG[t] : ION_BG_OFF,
            )}
          >
            {t}
          </button>
        )
      })}
      <button
        type="button"
        onClick={() => ION_ORDER.forEach(t => !active.has(t) && onChange(t))}
        className="px-2 py-0.5 rounded border border-gray-300 text-xs text-gray-500 hover:bg-gray-100 transition-colors"
      >
        all
      </button>
      <button
        type="button"
        onClick={() => ION_ORDER.forEach(t => active.has(t) && onChange(t))}
        className="px-2 py-0.5 rounded border border-gray-300 text-xs text-gray-500 hover:bg-gray-100 transition-colors"
      >
        none
      </button>
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

interface SpectrumViewerProps {
  result: ProteoformResult
}

export function SpectrumViewer({ result }: SpectrumViewerProps) {
  const [Plotly, setPlotly] = useState<any>(null)
  const [activeIons, setActiveIons] = useState<Set<IonType>>(new Set(['b', 'y', 'a', 'c', 'z']))
  const [showNoise, setShowNoise] = useState(true)

  useEffect(() => {
    import('react-plotly.js').then(m => setPlotly(() => m.default)).catch(() => {})
  }, [])

  const toggleIon = useCallback((t: IonType) => {
    setActiveIons(prev => {
      const next = new Set(prev)
      next.has(t) ? next.delete(t) : next.add(t)
      return next
    })
  }, [])

  const { fragments, noise } = useMemo(() => {
    const seq = result.sequence ?? ''
    if (!seq) return { fragments: [], noise: [] }
    const frags = generateFragments(seq)
    return { fragments: frags, noise: generateNoisePeaks(frags) }
  }, [result.sequence])

  const traces = useMemo(() => {
    const byType = Object.fromEntries(
      ION_ORDER.map(t => [t, fragments.filter(f => f.type === t)])
    ) as Record<IonType, Fragment[]>

    return [
      ...(showNoise ? [noiseTrace(noise)] : []),
      ...ION_ORDER
        .filter(t => activeIons.has(t) && byType[t].length > 0)
        .map(t => stickTraceV2(byType[t], ION_COLORS[t], ION_LABELS[t])),
    ]
  }, [fragments, noise, activeIons, showNoise])

  if (!result.sequence) {
    return <p className="text-gray-400 text-sm">No sequence data available for spectrum rendering.</p>
  }

  if (!Plotly) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
        Loading spectrum viewer…
      </div>
    )
  }

  const allMz = fragments.map(f => f.mz)
  const xMin = Math.min(...allMz) - 60
  const xMax = Math.max(...allMz) + 80

  return (
    <div className="space-y-2">
      {result.is_demo && (
        <p className="text-xs text-amber-700 font-medium">
          ⚠️ DEMO: Fragment ion positions are illustrative only — not real spectral data.
        </p>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <IonTypeSelector active={activeIons} onChange={toggleIon} />
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showNoise}
            onChange={e => setShowNoise(e.target.checked)}
            className="rounded border-gray-300 text-gray-500"
          />
          <span className="text-xs text-gray-500">Show noise</span>
        </label>
      </div>

      <Plotly
        data={traces}
        layout={{
          height: 420,
          margin: { t: 24, r: 24, b: 56, l: 72 },
          xaxis: {
            title: { text: 'm/z', font: { size: 13 } },
            range: [xMin, xMax],
            zeroline: false,
            showgrid: false,
            ticks: 'outside',
            ticklen: 5,
          },
          yaxis: {
            title: { text: 'Relative Intensity (%)', font: { size: 13 } },
            range: [0, 118],
            zeroline: true,
            zerolinecolor: '#374151',
            zerolinewidth: 1.5,
            showgrid: false,
            ticks: 'outside',
            ticklen: 5,
          },
          legend: {
            x: 1,
            xanchor: 'right',
            y: 1,
            yanchor: 'top',
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#d1d5db',
            borderwidth: 1,
            font: { size: 11 },
          },
          paper_bgcolor: 'white',
          plot_bgcolor: 'white',
          font: { family: 'Arial, sans-serif', size: 11 },
          hovermode: 'closest',
        }}
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: ['select2d', 'lasso2d'],
          responsive: true,
          toImageButtonOptions: { format: 'svg', filename: 'spectrum' },
        }}
        style={{ width: '100%' }}
      />
    </div>
  )
}
