"""
Export utilities for standardized result formats.

Formats:
- CSV / TSV
- JSON
- mzIdentML-like XML
- ProForma strings list
- PTM library XML
- Annotated FASTA
- Engine-specific raw output ZIP
- Consensus result table
"""
import csv
import json
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.dom import minidom


_RESULT_FIELDS = [
    "id", "job_id", "job_engine_id", "engine_name", "engine_version",
    "spectrum_id", "scan_number", "source_file",
    "precursor_mz", "charge", "observed_mass", "theoretical_mass", "delta_mass",
    "accession", "protein_name", "sequence", "proteoform_string", "proteoform_mass",
    "score", "evalue", "qvalue", "fdr",
    "matched_fragments", "sequence_coverage", "ptms", "localization_confidence", "is_demo",
]


def _to_dict(r) -> dict:
    """Convert either a SQLAlchemy ORM result or a dataclass ProteoformResult to dict."""
    import dataclasses
    if dataclasses.is_dataclass(r) and not isinstance(r, type):
        row = dataclasses.asdict(r)
    else:
        row = {f: getattr(r, f, None) for f in _RESULT_FIELDS}
    row["ptms"] = json.dumps(row.get("ptms") or [])
    return row


def export_csv(results: list, output_path: Path, delimiter: str = ",") -> Path:
    if not results:
        output_path.write_text("")
        return output_path
    fields = [f for f in _RESULT_FIELDS if f != "raw_engine_output_path"]
    with open(output_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=delimiter, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({k: _to_dict(r).get(k) for k in fields})
    return output_path


def export_json(results: list, output_path: Path) -> Path:
    data = [_to_dict(r) for r in results]
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path


def export_mzidentml(results: list, output_path: Path, job_id: str) -> Path:
    root = ET.Element("MzIdentML", {
        "xmlns": "http://psidev.info/psi/pi/mzIdentML/1.2",
        "id": f"tdportal_job_{job_id}",
        "version": "1.2.0",
    })
    inputs = ET.SubElement(root, "Inputs")
    sir = ET.SubElement(root, "SequenceIdentificationResults")

    for i, r in enumerate(results):
        sii = ET.SubElement(sir, "SpectrumIdentificationResult", {
            "id": f"SIR_{i}",
            "spectrumID": r.spectrum_id or f"scan={r.scan_number}",
        })
        sii_item = ET.SubElement(sii, "SpectrumIdentificationItem", {
            "id": f"SII_{i}",
            "chargeState": str(r.charge or ""),
            "experimentalMassToCharge": str(r.precursor_mz or ""),
            "calculatedMassToCharge": str(r.theoretical_mass or ""),
            "rank": "1",
            "passThreshold": "true" if (r.qvalue or 1) < 0.01 else "false",
        })
        if r.score is not None:
            cv = ET.SubElement(sii_item, "cvParam", {
                "accession": "MS:1001171",
                "name": "Mascot:score",
                "value": str(r.score),
            })
        for ptm in (r.ptms or []):
            mod = ET.SubElement(sii_item, "Modification", {
                "location": str(ptm.get("position", "")),
                "residues": ptm.get("residue", ""),
                "monoisotopicMassDelta": str(ptm.get("mass_shift", "")),
            })
            ET.SubElement(mod, "cvParam", {"name": ptm.get("modification", ""), "accession": "MOD:unknown"})

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    output_path.write_text(xml_str)
    return output_path


def export_proforma(results: list, output_path: Path) -> Path:
    lines = []
    for r in results:
        pf = r.proteoform_string or r.sequence or ""
        lines.append(pf)
    output_path.write_text("\n".join(lines))
    return output_path


def export_ptm_library_xml(results: list, output_path: Path) -> Path:
    root = ET.Element("PTMLibrary")
    seen = set()
    for r in results:
        for ptm in (r.ptms or []):
            key = (ptm.get("modification"), ptm.get("residue"))
            if key not in seen:
                seen.add(key)
                entry = ET.SubElement(root, "PTM", {
                    "name": ptm.get("modification", ""),
                    "residue": ptm.get("residue", ""),
                    "monoisotopicMassDelta": str(ptm.get("mass_shift", "")),
                })
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    output_path.write_text(xml_str)
    return output_path


def export_annotated_fasta(results: list, output_path: Path) -> Path:
    seen = set()
    lines = []
    for r in results:
        acc = r.accession or "unknown"
        if acc in seen:
            continue
        seen.add(acc)
        header = f">{acc} {r.protein_name or ''} | proteoform: {r.proteoform_string or ''}"
        seq = r.sequence or ""
        lines.append(header)
        lines.extend([seq[i:i+60] for i in range(0, len(seq), 60)] if seq else [""])
    output_path.write_text("\n".join(lines))
    return output_path


def export_raw_zip(raw_dirs: list[Path], output_path: Path) -> Path:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for raw_dir in raw_dirs:
            if raw_dir.exists():
                for f in raw_dir.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(raw_dir.parent))
    return output_path


def export_consensus(results: list, output_path: Path) -> Path:
    """Build a consensus table: rows where multiple engines agree (same scan, similar mass)."""
    by_scan: dict[int, list] = {}
    for r in results:
        k = r.scan_number or 0
        by_scan.setdefault(k, []).append(r)

    consensus = []
    for scan, group in by_scan.items():
        if len(group) < 2:
            continue
        engines = sorted({r.engine_name for r in group})
        best = min(group, key=lambda x: (x.qvalue or 1.0))
        row = {
            "scan_number": scan,
            "engines_agreed": ",".join(engines),
            "n_engines": len(engines),
            "accession": best.accession,
            "proteoform_string": best.proteoform_string,
            "observed_mass": best.observed_mass,
            "best_qvalue": best.qvalue,
            "best_score": best.score,
        }
        consensus.append(row)

    if not consensus:
        output_path.write_text("scan_number\tengines_agreed\tn_engines\taccession\tproteoform_string\tobserved_mass\tbest_qvalue\tbest_score\n")
        return output_path

    with open(output_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(consensus[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(consensus)
    return output_path
