import { clsx } from 'clsx'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import type { EngineInfo } from '@/types'
import { useEngines } from '@/hooks/useEngines'

const ENGINE_DESCRIPTIONS: Record<string, string> = {
  toppic: 'TopFD + TopPIC — Full top-down pipeline: deconvolution + proteoform identification',
  topmg: 'TopFD + TopMG — Proteogenomics and large unexpected modifications',
  mspathfindert: 'MSPathFinderT (Informed Proteomics) — Bottom-up tolerant top-down search',
  toplib: 'TopLib — Spectral library search for top-down MS',
  flashdeconv: 'FLASHDeconv — Ultrafast deconvolution (OpenMS)',
  flashdeconv_toppic: 'FLASHDeconv + TopPIC — Alternative deconvolution pipeline',
  demo: '⚠️ DEMO ONLY — Produces synthetic data for UI testing',
  proteoid: 'ProteoID (ProteoBio AI) — AI proteoform identification [placeholder]',
  truncnet: 'TruncNet (ProteoBio AI) — N/C-terminal truncation detection [placeholder]',
  ptmnet: 'PTMNet (ProteoBio AI) — AI PTM localization [placeholder]',
  massflownet: 'MassFlowNet (ProteoBio AI) — Mass shift flow network [placeholder]',
  proteoengine: 'ProteoEngine (ProteoBio AI) — Integrated AI search [placeholder]',
}

interface EngineSelectorProps {
  selected: string[]
  onChange: (engines: string[]) => void
}

export function EngineSelector({ selected, onChange }: EngineSelectorProps) {
  const { data: engines = [], isLoading } = useEngines()

  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter((e) => e !== name))
    } else {
      onChange([...selected, name])
    }
  }

  if (isLoading) return <div className="text-gray-500 text-sm">Loading engines…</div>

  const available = engines.filter((e) => e.available)
  const unavailable = engines.filter((e) => !e.available)

  return (
    <div className="space-y-4">
      {available.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Available Engines</h4>
          <div className="space-y-2">
            {available.map((engine) => (
              <EngineCard key={engine.name} engine={engine} selected={selected.includes(engine.name)} onToggle={() => toggle(engine.name)} />
            ))}
          </div>
        </div>
      )}

      {unavailable.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 mb-2">Not Installed</h4>
          <div className="space-y-2">
            {unavailable.map((engine) => (
              <EngineCard key={engine.name} engine={engine} selected={false} onToggle={() => {}} disabled />
            ))}
          </div>
        </div>
      )}

      {engines.length === 0 && (
        <p className="text-sm text-gray-500">No engines reported by the server.</p>
      )}
    </div>
  )
}

function EngineCard({ engine, selected, onToggle, disabled }: {
  engine: EngineInfo
  selected: boolean
  onToggle: () => void
  disabled?: boolean
}) {
  const isDemo = engine.name === 'demo'
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={clsx(
        'w-full text-left px-4 py-3 rounded-lg border-2 transition-all',
        selected && !disabled
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 bg-white hover:border-gray-300',
        disabled && 'opacity-50 cursor-not-allowed',
        isDemo && 'border-amber-300 bg-amber-50'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-semibold text-gray-800">{engine.name}</span>
            {engine.version !== 'unknown' && (
              <span className="text-xs text-gray-400">v{engine.version}</span>
            )}
            {isDemo && <span className="text-xs font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">DEMO</span>}
            {engine.available ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <XCircle className="w-4 h-4 text-gray-400" />
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">{ENGINE_DESCRIPTIONS[engine.name] || 'Custom engine adapter'}</p>
          <p className="text-xs text-gray-400 mt-0.5">Formats: {engine.input_formats.join(', ')}</p>
        </div>
        <div className={clsx('w-5 h-5 rounded border-2 mt-1 flex-shrink-0 flex items-center justify-center',
          selected ? 'border-blue-500 bg-blue-500' : 'border-gray-300 bg-white'
        )}>
          {selected && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
        </div>
      </div>
    </button>
  )
}
