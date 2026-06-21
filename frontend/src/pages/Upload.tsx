import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, FileText, Database, Dna } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { EngineSelector } from '@/components/EngineSelector'
import { ParameterForm } from '@/components/ParameterForm'
import { uploadFile, createJob, submitJob } from '@/api/client'
import type { SearchParameters } from '@/types'

type Step = 'files' | 'engines' | 'params' | 'review'

export default function UploadPage() {
  const nav = useNavigate()
  const [step, setStep] = useState<Step>('files')
  const [mzmlFile, setMzmlFile] = useState<File | null>(null)
  const [fastaFile, setFastaFile] = useState<File | null>(null)
  const [ptmFile, setPtmFile] = useState<File | null>(null)
  const [engines, setEngines] = useState<string[]>([])
  const [params, setParams] = useState<Partial<SearchParameters>>({})
  const [jobName, setJobName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const steps: Step[] = ['files', 'engines', 'params', 'review']
  const stepIdx = steps.indexOf(step)

  const handleSubmit = async () => {
    if (!mzmlFile || !fastaFile || engines.length === 0) return
    setLoading(true)
    setError('')
    try {
      const [mzmlUpload, fastaUpload] = await Promise.all([
        uploadFile(mzmlFile),
        uploadFile(fastaFile),
      ])
      const ptmUpload = ptmFile ? await uploadFile(ptmFile) : null

      const job = await createJob({
        name: jobName || `Job_${new Date().toISOString().slice(0, 16)}`,
        mzml_file_id: mzmlUpload.id,
        fasta_file_id: fastaUpload.id,
        ptm_file_id: ptmUpload?.id,
        engines,
        parameters: params,
      })
      await submitJob(job.id)
      nav(`/jobs/${job.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">New Analysis Job</h1>
        <p className="text-sm text-gray-500 mt-1">Upload your MS data and configure search parameters</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
              i < stepIdx ? 'bg-green-500 text-white' :
              i === stepIdx ? 'bg-blue-600 text-white' :
              'bg-gray-200 text-gray-500'
            }`}>
              {i < stepIdx ? '✓' : i + 1}
            </div>
            <span className={`text-sm capitalize ${i === stepIdx ? 'font-semibold text-blue-700' : 'text-gray-400'}`}>
              {s}
            </span>
            {i < steps.length - 1 && <div className="flex-1 h-px bg-gray-200 min-w-[20px]" />}
          </div>
        ))}
      </div>

      {/* Step: Files */}
      {step === 'files' && (
        <Card title="Upload Files">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Name (optional)</label>
              <input
                type="text"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="My proteomics run"
                className="input-field"
              />
            </div>
            <FileDropzone label="mzML File *" icon={Database} accept=".mzml,.mzxml" file={mzmlFile} onFile={setMzmlFile}
              hint="Top-down MS data in mzML or mzXML format" />
            <FileDropzone label="FASTA Database *" icon={Dna} accept=".fasta,.fa" file={fastaFile} onFile={setFastaFile}
              hint="Protein sequence database for searching" />
            <FileDropzone label="PTM Config (optional)" icon={FileText} accept=".xml,.json,.csv" file={ptmFile} onFile={setPtmFile}
              hint="PTM configuration file (XML/JSON/CSV)" />
          </div>
          <div className="mt-6 flex justify-end">
            <Button onClick={() => setStep('engines')} disabled={!mzmlFile || !fastaFile}>
              Next: Select Engines
            </Button>
          </div>
        </Card>
      )}

      {/* Step: Engines */}
      {step === 'engines' && (
        <Card title="Select Search Engines">
          <EngineSelector selected={engines} onChange={setEngines} />
          <div className="mt-6 flex justify-between">
            <Button variant="secondary" onClick={() => setStep('files')}>Back</Button>
            <Button onClick={() => setStep('params')} disabled={engines.length === 0}>
              Next: Parameters
            </Button>
          </div>
        </Card>
      )}

      {/* Step: Parameters */}
      {step === 'params' && (
        <Card title="Search Parameters">
          <ParameterForm value={params} onChange={setParams} />
          <div className="mt-6 flex justify-between">
            <Button variant="secondary" onClick={() => setStep('engines')}>Back</Button>
            <Button onClick={() => setStep('review')}>Review & Submit</Button>
          </div>
        </Card>
      )}

      {/* Step: Review */}
      {step === 'review' && (
        <Card title="Review & Submit">
          <div className="space-y-3 text-sm">
            <Row label="mzML File" value={mzmlFile?.name} />
            <Row label="FASTA Database" value={fastaFile?.name} />
            <Row label="PTM Config" value={ptmFile?.name ?? 'None'} />
            <Row label="Engines" value={engines.join(', ')} />
            {engines.includes('demo') && (
              <div className="bg-amber-50 border border-amber-300 rounded p-3 text-amber-800 text-xs font-medium">
                ⚠️ Demo engine selected — results will be synthetic. Remove "demo" for real analysis.
              </div>
            )}
          </div>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
          <div className="mt-6 flex justify-between">
            <Button variant="secondary" onClick={() => setStep('params')}>Back</Button>
            <Button onClick={handleSubmit} loading={loading}>Submit Job</Button>
          </div>
        </Card>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex gap-2">
      <span className="font-medium text-gray-600 w-32 flex-shrink-0">{label}:</span>
      <span className="text-gray-800">{value || '—'}</span>
    </div>
  )
}

function FileDropzone({ label, icon: Icon, accept, file, onFile, hint }: {
  label: string; icon: any; accept: string; file: File | null
  onFile: (f: File | null) => void; hint: string
}) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div
        onClick={() => ref.current?.click()}
        className={`border-2 border-dashed rounded-lg p-4 cursor-pointer transition-colors ${
          file ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:border-blue-400 bg-gray-50'
        }`}
      >
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${file ? 'text-green-600' : 'text-gray-400'}`} />
          {file ? (
            <div>
              <p className="text-sm font-medium text-green-700">{file.name}</p>
              <p className="text-xs text-green-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600">Click to select file</p>
              <p className="text-xs text-gray-400">{hint}</p>
            </div>
          )}
          {file && (
            <button className="ml-auto text-xs text-gray-400 hover:text-red-500"
              onClick={(e) => { e.stopPropagation(); onFile(null) }}>✕</button>
          )}
        </div>
      </div>
      <input ref={ref} type="file" accept={accept} className="hidden"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
    </div>
  )
}
