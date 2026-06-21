# TDPortal-OS

**Open-Source Top-Down Proteomics Web Platform**

> ⚠️ **Disclaimer**: TDPortal-OS is an independent open-source project. It is **not** affiliated with, endorsed by, or derived from the official [TDPortal](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5036929/) (University of Illinois at Urbana-Champaign) or [ProSight](https://prosightptm.scs.illinois.edu/) software suite. No proprietary source code is used.

---

## Overview

TDPortal-OS provides a web interface for top-down proteomics data analysis using real open-source search engines. Users can upload mzML files and FASTA databases, select one or more search engines, configure parameters, submit jobs, and compare results across engines with standardized output formats.

**Key principle: No fake results.** The system runs real engine binaries when installed. A clearly-labeled Demo mode generates synthetic data for UI testing only — it is never mixed with real results.

---

## Supported Engines

| Engine | Description | Status | License |
|--------|-------------|--------|---------|
| **TopPIC** (`toppic`) | TopFD + TopPIC: deconvolution + proteoform ID | Supported | MIT |
| **TopMG** (`topmg`) | TopFD + TopMG: proteogenomics/large shifts | Supported | MIT |
| **TopLib** (`toplib`) | Spectral library search | Supported | MIT |
| **MSPathFinderT** (`mspathfindert`) | Informed Proteomics PNNL | Supported | Apache 2.0 |
| **FLASHDeconv** (`flashdeconv`) | OpenMS ultrafast deconvolution | Supported | BSD |
| **FLASHDeconv+TopPIC** (`flashdeconv_toppic`) | Combined pipeline | Supported | Mixed |
| **Demo** (`demo`) | ⚠️ SYNTHETIC DATA ONLY — UI testing | Always on | N/A |
| **ProteoID** (`proteoid`) | ProteoBio AI engine | Placeholder | TBD |
| **TruncNet** (`truncnet`) | AI truncation detection | Placeholder | TBD |
| **PTMNet** (`ptmnet`) | AI PTM localization | Placeholder | TBD |
| **MassFlowNet** (`massflownet`) | AI mass shift flow | Placeholder | TBD |
| **ProteoEngine** (`proteoengine`) | Integrated AI search | Placeholder | TBD |

---

## Quick Start (Docker Compose)

### Requirements
- Docker 24+
- Docker Compose 2.20+

### 1. Clone and Configure

```bash
git clone <your-repo-url> tdportal-os
cd tdportal-os
cp .env.example .env
```

### 2. Start the Platform

```bash
docker compose up -d
```

- **Frontend**: http://localhost (or http://localhost:3000)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Install Real Engines (Optional)

Without real engines, only Demo mode is available. To install TopPIC:

```bash
# Option A: During Docker build
INSTALL_TOPPIC=1 docker compose build worker
docker compose up -d worker

# Option B: On your host machine
bash scripts/install_toppic.sh
```

See [scripts/](scripts/) for all engine install scripts.

---

## Local Development (No Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Start Redis (required for Celery)
docker run -d -p 6379:6379 redis:7-alpine

# Set environment
export DATABASE_URL=sqlite:///./dev.db
export DEMO_MODE_ENABLED=true
export UPLOAD_DIR=./data/uploads
export JOB_DIR=./data/jobs
mkdir -p ./data/uploads ./data/jobs

# Start API
uvicorn app.main:app --reload

# In another terminal: start worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 and proxies `/api/` to the backend.

---

## Example Workflow

1. **Upload** your mzML and FASTA files
2. **Select** search engines (e.g., `toppic` + `demo` for testing)
3. **Configure** parameters (tolerance, FDR, modifications)
4. **Submit** — the job is queued to the Celery worker
5. **Monitor** progress in real-time via the Status tab
6. **Browse** results, filter by engine/q-value/accession/PTM
7. **Compare** engines in the Comparison tab (Venn overlap)
8. **Export** in CSV, JSON, mzIdentML, ProForma, or ZIP

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/uploads` | Upload a file |
| `GET` | `/api/v1/uploads/{id}` | Get upload info |
| `GET` | `/api/v1/engines` | List all engines and availability |
| `POST` | `/api/v1/jobs` | Create a job |
| `POST` | `/api/v1/jobs/{id}/submit` | Queue a job |
| `GET` | `/api/v1/jobs` | List jobs |
| `GET` | `/api/v1/jobs/{id}` | Get job details |
| `GET` | `/api/v1/jobs/{id}/status` | Get live status |
| `GET` | `/api/v1/jobs/{id}/logs/{engine}` | Get engine log |
| `DELETE` | `/api/v1/jobs/{id}` | Delete job |
| `GET` | `/api/v1/results/job/{id}` | Query results (filterable) |
| `GET` | `/api/v1/results/job/{id}/by-engine` | Results per engine |
| `GET` | `/api/v1/results/job/{id}/venn` | Scan overlap data |
| `GET` | `/api/v1/results/{result_id}` | Get single result |
| `GET` | `/api/v1/exports/job/{id}/{format}` | Download export |
| `GET` | `/api/v1/health` | Health check |

---

## Export Formats

| Format | Description |
|--------|-------------|
| `csv` | Comma-separated values |
| `tsv` | Tab-separated values |
| `json` | Full result objects |
| `mzidentml` | PSI-MI mzIdentML-like XML |
| `proforma` | ProForma proteoform strings |
| `ptm_xml` | PTM library XML |
| `fasta` | Annotated FASTA |
| `raw_zip` | All raw engine output files (ZIP) |
| `consensus` | Cross-engine consensus table |

---

## Adding a New Engine

1. Create `backend/app/engines/myengine.py`:

```python
from app.engines.base import SearchEngineAdapter, ProteoformResult
from pathlib import Path
from typing import Any, Optional

class MyEngineAdapter(SearchEngineAdapter):
    name = "myengine"
    version = "1.0"
    input_formats = [".mzml"]
    output_formats = [".tsv"]

    def validate_installation(self) -> bool:
        from shutil import which
        return bool(which("myengine"))

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        return fasta_path  # or build an index

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        # run subprocess, capture logs
        ...

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        results = []
        # parse your engine's output files
        return results
```

2. Register in `backend/app/engines/registry.py`:

```python
from app.engines.myengine import MyEngineAdapter
_ADAPTERS["myengine"] = MyEngineAdapter()
```

3. The engine will automatically appear in the UI after restart.

---

## Engine-Specific Notes

### TopPIC Suite
- Install from: https://github.com/toppic-suite/toppic-suite/releases
- Requires binaries on PATH: `topfd`, `toppic`, `topmg`
- Tested with TopPIC Suite >= 1.6
- Set `TOPPIC_BIN` / `TOPFD_BIN` in `.env` for non-PATH installs

### MSPathFinderT
- Requires .NET 6+ runtime
- Install: `bash scripts/install_mspathfinder.sh`
- Works on Linux/macOS. Windows: use native installer
- License: Apache 2.0 (PNNL)

### FLASHDeconv
- Part of OpenMS >= 3.0
- Install: `conda install -c conda-forge -c bioconda openms`
- Or: `bash scripts/install_flashdeconv.sh`
- License: BSD 3-Clause

### TopLib
- Bundled with TopPIC Suite
- Requires a `.splib` spectral library file

### Demo Engine
- Always available — no installation needed
- Produces **100% synthetic fabricated data**
- `is_demo=true` on all results in DB and API
- Prominent warning banner in UI
- **Never use for research**

---

## Testing

```bash
cd backend
pytest tests/ -v                   # all tests
pytest tests/test_engines.py -v    # engine adapter tests
pytest tests/test_exports.py -v    # export format tests
pytest tests/test_jobs.py -v       # API + job lifecycle
```

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

Third-party tools have their own licenses:
- TopPIC Suite: MIT
- MSPathFinderT / Informed Proteomics: Apache 2.0
- OpenMS / FLASHDeconv: BSD 3-Clause

TDPortal-OS does not redistribute binaries for any third-party tool. Engines must be installed separately.
