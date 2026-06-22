import hashlib
import shutil
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".mzml", ".mzxml", ".fasta", ".fa", ".xml", ".json", ".csv", ".tsv",
    ".raw", ".d", ".wiff", ".ms1", ".ms2", ".mgf", ".mz5",
}


def validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{suffix}' is not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    return suffix


def determine_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".mzml": "mzml",
        ".mzxml": "mzxml",
        ".fasta": "fasta",
        ".fa": "fasta",
        ".xml": "xml",
        ".json": "json",
        ".csv": "csv",
        ".tsv": "tsv",
        ".raw": "raw",
        ".d": "raw",
        ".wiff": "raw",
        ".ms1": "ms1",
        ".ms2": "ms2",
        ".mgf": "mgf",
        ".mz5": "mz5",
    }
    return mapping.get(ext, "unknown")


def compute_md5(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def save_upload(content: bytes, original_filename: str, upload_dir: Path) -> tuple[str, str]:
    """Save bytes to disk with a UUID-based filename. Returns (stored_filename, md5)."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_filename).suffix.lower()
    stored = f"{uuid.uuid4()}{ext}"
    dest = upload_dir / stored
    dest.write_bytes(content)
    md5 = compute_md5(dest)
    return stored, md5


def safe_zip_directory(source_dir: Path, output_path: Path) -> Path:
    """Zip a directory to output_path.zip. Returns the zip path."""
    shutil.make_archive(str(output_path.with_suffix("")), "zip", source_dir)
    return output_path.with_suffix(".zip")
