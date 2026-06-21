import { Download } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { getExportUrl } from '@/api/client'
import type { ExportFormat } from '@/types'

const FORMATS: { id: ExportFormat; label: string; description: string }[] = [
  { id: 'csv', label: 'CSV', description: 'Comma-separated values — all results' },
  { id: 'tsv', label: 'TSV', description: 'Tab-separated values — all results' },
  { id: 'json', label: 'JSON', description: 'Full result objects in JSON format' },
  { id: 'mzidentml', label: 'mzIdentML', description: 'PSI-MI mzIdentML-like XML' },
  { id: 'proforma', label: 'ProForma', description: 'ProForma proteoform strings' },
  { id: 'ptm_xml', label: 'PTM Library XML', description: 'Detected PTMs as XML library' },
  { id: 'fasta', label: 'Annotated FASTA', description: 'FASTA with proteoform headers' },
  { id: 'raw_zip', label: 'Raw Engine Output', description: 'ZIP of all raw engine output files' },
  { id: 'consensus', label: 'Consensus Table', description: 'Cross-engine consensus TSV' },
]

interface ExportPanelProps {
  jobId: string
  disabled?: boolean
}

export function ExportPanel({ jobId, disabled }: ExportPanelProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {FORMATS.map(({ id, label, description }) => (
        <a
          key={id}
          href={disabled ? undefined : getExportUrl(jobId, id)}
          download
          onClick={(e) => disabled && e.preventDefault()}
          className="block"
        >
          <div className={`border rounded-lg p-3 flex items-start gap-2 transition-colors ${
            disabled
              ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
              : 'border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50 cursor-pointer'
          }`}>
            <Download className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-sm font-semibold text-gray-800">{label}</div>
              <div className="text-xs text-gray-500">{description}</div>
            </div>
          </div>
        </a>
      ))}
    </div>
  )
}
