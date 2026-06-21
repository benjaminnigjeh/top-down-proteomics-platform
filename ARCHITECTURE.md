# Architecture — TDPortal-OS

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│   React + TypeScript + Vite (Tailwind CSS, React Query, Plotly)  │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP /api/v1/...
┌───────────────────────────▼──────────────────────────────────────┐
│                    Nginx Reverse Proxy                            │
│              (serves frontend SPA + proxies /api/)               │
└─────────┬─────────────────────────────────────────────┬──────────┘
          │                                             │
┌─────────▼────────────┐                   ┌───────────▼──────────┐
│   FastAPI Backend     │                   │    Celery Worker      │
│   (Uvicorn)           │                   │                       │
│                       │  Celery tasks     │  Engine Adapters:     │
│  Routes:              │◄──────────────────┤  - TopPICAdapter      │
│  /uploads             │                   │  - MSPathFinderT      │
│  /jobs                │                   │  - FLASHDeconv        │
│  /results             │                   │  - TopLib             │
│  /engines             │                   │  - DemoAdapter        │
│  /exports             │                   │  - ProteoBio AI       │
│                       │                   │    (placeholders)     │
└──────────┬────────────┘                   └──────────┬───────────┘
           │                                           │
           │        ┌──────────────┐                  │
           └───────►│   SQLite /   │◄─────────────────┘
                    │  PostgreSQL  │
                    └──────────────┘
           ┌───────►│    Redis     │◄─────────────────┐
           │        └──────────────┘                  │
     (broker/backend)                          (task queue)
           │                                          │
┌──────────┴──────────┐                   ┌──────────┴───────────┐
│   Shared Volume:     │                   │  Shared Volume:       │
│   /data/uploads/     │                   │  /data/jobs/{id}/     │
│   (user files)       │                   │  (engine outputs)     │
└──────────────────────┘                   └──────────────────────┘
```

## Component Breakdown

### Frontend (React/TypeScript)
- **Pages**: Home, Upload (wizard), Jobs list, Job detail, Result detail, About
- **State**: TanStack Query for server state; React useState for UI state
- **Upload Wizard**: 4-step: files → engine selection → parameters → review
- **Job Detail Tabs**: Status/Logs, Results table, Engine comparison, Export
- **Spectrum Viewer**: Plotly.js bar chart with b/y ion annotations
- **Venn Diagram**: Custom bar-chart overlap visualization
- **Export Panel**: Links to `/api/v1/exports/job/{id}/{format}`

### Backend (FastAPI)
- **SQLAlchemy 2.0** ORM with SQLite (default) or PostgreSQL
- **Pydantic v2** for request/response validation
- **Async file upload** via `python-multipart` + `aiofiles`
- **Job lifecycle**: `pending → queued → running → completed/failed`
- **Results**: stored in `proteoform_results` table with standardized schema

### Worker (Celery + Redis)
- One Celery task per job (`run_job`)
- Iterates through requested engines sequentially within the task
- Each engine runs in isolated directory: `/data/jobs/{job_id}/{engine_name}/`
- Logs captured line-by-line and persisted to DB for real-time streaming
- Raw engine outputs preserved at `/data/jobs/{job_id}/{engine_name}/output/`

### Engine Adapter Interface

```python
class SearchEngineAdapter(ABC):
    name: str
    version: str
    input_formats: list[str]
    output_formats: list[str]

    def validate_installation(self) -> bool: ...
    def prepare_database(self, fasta_path, ptm_config, output_dir): ...
    def run_search(self, input_files, database_path, params, output_dir, log_callback=None): ...
    def parse_results(self, output_dir) -> list[ProteoformResult]: ...
    def estimate_fdr(self, results) -> list[ProteoformResult]: ...    # optional
    def export_standardized(self, results, output_dir) -> Path: ...   # optional
    def get_info(self) -> dict: ...
```

### Standardized Result Schema (`ProteoformResult`)

Every engine's output is normalized into this schema:
- **Identification**: engine_name, engine_version, job_id
- **Spectrum**: spectrum_id, scan_number, source_file
- **Mass**: precursor_mz, charge, observed_mass, theoretical_mass, delta_mass
- **Protein**: accession, protein_name, sequence, proteoform_string, proteoform_mass
- **Score**: score, evalue, qvalue, fdr
- **Annotation**: matched_fragments, sequence_coverage, ptms, localization_confidence
- **Provenance**: raw_engine_output_path, is_demo

## Database Schema

```
uploads
  id, original_filename, stored_filename, file_type, size_bytes, checksum_md5, created_at

jobs
  id, name, status, mzml_file_id, fasta_file_id, ptm_file_id,
  parameters (JSON), engines_requested (JSON),
  created_at, started_at, completed_at, celery_task_id, error_message

job_engines
  id, job_id (FK), engine_name, status, log (TEXT), output_dir,
  result_count, started_at, completed_at

proteoform_results
  id, job_id (FK), job_engine_id (FK), engine_name, engine_version,
  spectrum_id, scan_number, source_file,
  precursor_mz, charge, observed_mass, theoretical_mass, delta_mass,
  accession, protein_name, sequence, proteoform_string, proteoform_mass,
  score, evalue, qvalue, fdr,
  matched_fragments, sequence_coverage, ptms (JSON), localization_confidence,
  raw_engine_output_path, is_demo
```

## Security Considerations

- File uploads validated by extension whitelist (no executables)
- File size limit enforced (default 2 GB)
- MD5 checksum stored for integrity verification
- Engine binaries run in worker container (isolated from API container)
- No shell injection: all subprocess calls use list form (not `shell=True`)
- CORS restricted to configured origins

## Scaling

- Worker concurrency: set `--concurrency=N` in Celery
- Multiple worker containers: scale via `docker compose scale worker=N`
- PostgreSQL: change `DATABASE_URL` for production
- For very large datasets, consider S3/GCS for `/data/` volume

## Adding ProteoBio AI Engines

When ProteoID, TruncNet, etc. become available:

1. Open the corresponding placeholder file in `app/engines/proteo_ai/`
2. Replace `NotImplementedError` with real inference code
3. Set `validate_installation()` to check for model weights/runtime
4. The adapter is already registered in `registry.py` and will appear in the UI
