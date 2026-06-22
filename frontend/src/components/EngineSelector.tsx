import { clsx } from 'clsx'
import { CheckCircle, XCircle, Search, Zap, GitMerge, FlaskConical } from 'lucide-react'
import type { EngineInfo, EngineCategory } from '@/types'
import { useEngines } from '@/hooks/useEngines'

const CATEGORY_META: Record<EngineCategory, { label: string; color: string; icon: React.ElementType; note?: string }> = {
  search:        { label: 'Search Engines',               color: 'blue',   icon: Search },
  deconvolution: { label: 'Deconvolution / Preprocessing', color: 'teal',   icon: Zap,    note: 'These tools process raw spectra but do not search a protein database. Use standalone to inspect deconvolved masses, or as part of a pipeline.' },
  pipeline:      { label: 'Pipelines',                    color: 'purple', icon: GitMerge, note: 'End-to-end workflows combining deconvolution + database search.' },
  demo:          { label: 'Demo',                         color: 'amber',  icon: FlaskConical, note: 'Produces entirely synthetic data for UI testing only. Never use for real research.' },
}

const COLOR_CLASSES: Record<string, { header: string; badge: string; ring: string }> = {
  blue:   { header: 'text-blue-700 border-blue-200 bg-blue-50',   badge: 'bg-blue-100 text-blue-700',   ring: 'border-blue-500 bg-blue-50' },
  teal:   { header: 'text-teal-700 border-teal-200 bg-teal-50',   badge: 'bg-teal-100 text-teal-700',   ring: 'border-teal-500 bg-teal-50' },
  purple: { header: 'text-purple-700 border-purple-200 bg-purple-50', badge: 'bg-purple-100 text-purple-700', ring: 'border-purple-500 bg-purple-50' },
  amber:  { header: 'text-amber-700 border-amber-200 bg-amber-50', badge: 'bg-amber-100 text-amber-700', ring: 'border-amber-400 bg-amber-50' },
  gray:   { header: 'text-gray-500 border-gray-200 bg-gray-50',   badge: 'bg-gray-100 text-gray-500',   ring: 'border-gray-300 bg-gray-50' },
}

interface EngineSelectorProps {
  selected: string[]
  onChange: (engines: string[]) => void
}

// Search engines that run TopFD internally — selecting topfd alongside these is redundant
const TOPFD_INTERNAL = new Set(['toppic', 'topmg', 'topdiff'])

export function EngineSelector({ selected, onChange }: EngineSelectorProps) {
  const { data: engines = [], isLoading } = useEngines()

  const toggle = (name: string) => {
    onChange(selected.includes(name) ? selected.filter(e => e !== name) : [...selected, name])
  }

  const redundantTopFD =
    selected.includes('topfd') && selected.some(e => TOPFD_INTERNAL.has(e))

  if (isLoading) return <div className="text-gray-500 text-sm py-4">Loading engines…</div>
  if (engines.length === 0) return <p className="text-sm text-gray-500">No engines reported by the server.</p>

  const byCategory = engines.reduce<Record<string, EngineInfo[]>>((acc, e) => {
    const cat = e.category || 'search'
    ;(acc[cat] = acc[cat] || []).push(e)
    return acc
  }, {})

  const categoryOrder: EngineCategory[] = ['search', 'deconvolution', 'pipeline', 'demo']

  return (
    <div className="space-y-6">
      {redundantTopFD && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg px-3 py-2 text-xs text-amber-800">
          <strong>Note:</strong> TopPIC / TopMG / TopDiff already run TopFD internally.
          Selecting <code className="bg-amber-100 px-0.5 rounded">topfd</code> alongside them
          will run deconvolution twice. Remove <code className="bg-amber-100 px-0.5 rounded">topfd</code> unless
          you only want the raw msalign output.
        </div>
      )}
      {categoryOrder.map(cat => {
        const items = byCategory[cat]
        if (!items || items.length === 0) return null
        const meta = CATEGORY_META[cat]
        const colors = COLOR_CLASSES[meta.color]
        const Icon = meta.icon
        return (
          <div key={cat}>
            <div className={clsx('flex items-center gap-2 px-3 py-2 rounded-lg border mb-2', colors.header)}>
              <Icon className="w-4 h-4" />
              <span className="text-sm font-semibold">{meta.label}</span>
              <span className={clsx('ml-auto text-xs px-1.5 py-0.5 rounded-full font-medium', colors.badge)}>
                {items.filter(e => e.available).length}/{items.length} available
              </span>
            </div>
            {meta.note && (
              <p className="text-xs text-gray-500 px-1 mb-2 italic">{meta.note}</p>
            )}
            <div className="space-y-2">
              {items.map(engine => (
                <EngineCard
                  key={engine.name}
                  engine={engine}
                  selected={selected.includes(engine.name)}
                  onToggle={() => toggle(engine.name)}
                  disabled={!engine.available}
                  ringColor={colors.ring}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function EngineCard({ engine, selected, onToggle, disabled, ringColor }: {
  engine: EngineInfo
  selected: boolean
  onToggle: () => void
  disabled?: boolean
  ringColor: string
}) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onToggle}
      disabled={disabled}
      className={clsx(
        'w-full text-left px-4 py-3 rounded-lg border-2 transition-all',
        selected ? ringColor : 'border-gray-200 bg-white hover:border-gray-300',
        disabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-gray-800">{engine.name}</span>
            {engine.version !== 'unknown' && engine.version !== 'placeholder' && (
              <span className="text-xs text-gray-400">v{engine.version}</span>
            )}
            {engine.available
              ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              : <XCircle className="w-4 h-4 text-gray-300 flex-shrink-0" />}
          </div>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{engine.description}</p>
          <p className="text-xs text-gray-400 mt-0.5">Accepts: {engine.input_formats.join(', ')}</p>
        </div>
        <div className={clsx(
          'w-5 h-5 rounded border-2 mt-0.5 flex-shrink-0 flex items-center justify-center',
          selected ? 'border-blue-500 bg-blue-500' : 'border-gray-300 bg-white'
        )}>
          {selected && (
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
      </div>
    </button>
  )
}
