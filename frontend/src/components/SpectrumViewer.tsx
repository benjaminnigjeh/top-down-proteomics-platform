import { useMemo, useState, useEffect } from 'react'
import type { ProteoformResult } from '@/types'

// Monoisotopic residue masses (Da)
const RESIDUE_MASSES: Record<string, number> = {
  A: 71.03711, R: 156.10111, N: 114.04293, D: 115.02694, C: 103.00919,
  E: 129.04259, Q: 128.05858, G: 57.02146, H: 137.05891, I: 113.08406,
  L: 113.08406, K: 128.09496, M: 131.04049, F: 147.06841, P: 97.05276,
  S: 87.03203, T: 101.04768, W: 186.07931, Y: 163.06333, V: 99.06841,
}

interface Fragment {
  mz: number
  label: string
  type: 'b' | 'y'
  intensity: number
}

function generateFragments(seq: string): Fragment[] {
  const clean = seq.replace(/\[.*?\]/g, '')
  const fragments: Fragment[] = []
  const rng = (seed: number) => ((seed * 1664525 + 1013904223) & 0x7fffffff) / 0x7fffffff

  let bMass = 1.00782
  for (let i = 0; i < Math.min(clean.length - 1, 30); i++) {
    bMass += RESIDUE_MASSES[clean[i]] ?? 57.02
    fragments.push({ mz: bMass, label: `b${i + 1}`, type: 'b', intensity: rng(i * 31 + 7) })
  }

  let yMass = 19.01839
  for (let i = clean.length - 1; i > Math.max(0, clean.length - 31); i--) {
    yMass += RESIDUE_MASSES[clean[i]] ?? 57.02
    fragments.push({ mz: yMass, label: `y${clean.length - i}`, type: 'y', intensity: rng(i * 17 + 3) })
  }

  return fragments
}

interface SpectrumViewerProps {
  result: ProteoformResult
}

export function SpectrumViewer({ result }: SpectrumViewerProps) {
  const [PlotComponent, setPlotComponent] = useState<any>(null)

  useEffect(() => {
    import('react-plotly.js').then((m) => setPlotComponent(() => m.default)).catch(() => {})
  }, [])

  const fragments = useMemo(
    () => (result.sequence ? generateFragments(result.sequence) : []),
    [result.sequence]
  )

  if (!result.sequence) {
    return <div className="text-gray-400 text-sm">No sequence data available for spectrum rendering.</div>
  }

  if (!PlotComponent) {
    return (
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="h-48 flex items-center justify-center">
          <div className="text-center">
            <div className="text-gray-400 text-sm">Loading spectrum viewer…</div>
            <div className="mt-2 text-xs text-gray-300">Powered by Plotly.js</div>
          </div>
        </div>
      </div>
    )
  }

  const bIons = fragments.filter((f) => f.type === 'b')
  const yIons = fragments.filter((f) => f.type === 'y')

  const plotData = [
    {
      x: bIons.map((f) => f.mz),
      y: bIons.map((f) => f.intensity),
      type: 'bar' as const,
      name: 'b-ions',
      marker: { color: '#3b82f6' },
      hovertemplate: '%{text}<br>m/z: %{x:.4f}<br>intensity: %{y:.2f}<extra></extra>',
      text: bIons.map((f) => f.label),
    },
    {
      x: yIons.map((f) => f.mz),
      y: yIons.map((f) => -f.intensity),
      type: 'bar' as const,
      name: 'y-ions',
      marker: { color: '#ef4444' },
      hovertemplate: '%{text}<br>m/z: %{x:.4f}<extra></extra>',
      text: yIons.map((f) => f.label),
    },
  ]

  return (
    <div>
      {result.is_demo && (
        <p className="text-xs text-amber-700 mb-2 font-medium">
          ⚠️ DEMO: Fragment ion positions are illustrative only — not real spectral data.
        </p>
      )}
      <PlotComponent
        data={plotData}
        layout={{
          height: 300,
          margin: { t: 20, r: 20, b: 50, l: 60 },
          xaxis: { title: 'm/z', zeroline: false },
          yaxis: { title: 'Relative Intensity', zeroline: true, zerolinecolor: '#e5e7eb' },
          legend: { orientation: 'h' as const, y: -0.25 },
          barmode: 'overlay' as const,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { size: 11 },
        }}
        config={{ displayModeBar: true, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  )
}
