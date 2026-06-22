"""
DEMO ENGINE - FOR UI TESTING ONLY.

*** THIS ENGINE PRODUCES FABRICATED DATA. ***
*** NEVER USE FOR REAL RESEARCH. ***

Demo results are always flagged with is_demo=True in the database and API.
The UI clearly labels all demo results with a warning banner.
This engine is only active when DEMO_MODE_ENABLED=True in settings.
"""
import time
import random
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


_DEMO_PROTEINS = [
    ("P62988", "Ubiquitin", "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"),
    ("P0DTD1", "Histone H4", "SGRGKGGKGLGKGGAKRHRKVLRDNIQGITKPAIRRLARRGGVKRISGLIYEETRGVLKVFLENVIRDAVTYTEHAKRKTVTAMDVVYALKRQGRTLYGFGG"),
    ("P68871", "Hemoglobin HBB", "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"),
    ("P01857", "IGHG1 Fc", "ASTKGPSVFPLAPSSKSTSGGTAALGCLVKDYFPEPVTVSWNSGALTSGVHTFPAVLQSSGLYSLSSVVTVPSSSLGTQTYICNVNHKPSNTKVDKKVEPKSCDKTHTCPPCPAPELLGGPSVFLFPPKPKDTLMISRTPEVTCVVVDVSHEDPEVKFNWYVDGVEVHNAKTKPREEQYNSTYRVVSVLTVLHQDWLNGKEYKCKVSNKALPAPIEKTISKAKGQPREPQVYTLPPSREEMTKNQVSLTCLVKGFYPSDIAVEWESNGQPENNYKTTPPVLDSDGSFFLYSKLTVDKSRWQQGNVFSCSVMHEALHNHYTQKSLSLSPGK"),
    ("P05067", "APP", "MLPGLALLLLAAWTARALEVPTDGNAGLLAEPQIAMFCGRLNMHMNVQNGKWDSDPSGTKTCIDTKEGILQYCQEVYPELQITNVVEANQPVTIQNWCKRGRKQCKTHPHFVIPYRCLVGEFVSDALLVPDKCKFLHQERMDVCETHLHWHTVAKETCSEKSTNLHDYGMLLPCGIDKFRGVEFVCCPLAEESDNVDSADAEEDDSDVWWGGADTDYADGSEDKVVEVAEEEEVAEVEEEEADDDEDDDEDDDDDEEDDSEDDDSVWWGGADTDYADGSEDKVVEVAEEEEVAEVEEEEADDDEDDDEDDDDDEEDDSEDDD"),
]

_MODIFICATIONS = [
    {"modification": "Phospho", "residue": "S", "mass_shift": 79.966},
    {"modification": "Phospho", "residue": "T", "mass_shift": 79.966},
    {"modification": "Acetyl", "residue": "K", "mass_shift": 42.011},
    {"modification": "Methyl", "residue": "R", "mass_shift": 14.016},
    {"modification": "Oxidation", "residue": "M", "mass_shift": 15.995},
]


class DemoAdapter(SearchEngineAdapter):
    """DEMO ONLY — produces synthetic data for UI/workflow testing."""
    name = "demo"
    category = "demo"
    description = "⚠️ DEMO ONLY — Generates 50 synthetic proteoform identifications for UI testing. All results are fabricated and clearly labeled."
    version = "1.0.0-demo"
    input_formats = [".mzml", ".mzxml", ".fasta"]
    output_formats = [".tsv"]

    def validate_installation(self) -> bool:
        from app.config import settings
        return settings.DEMO_MODE_ENABLED

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        return fasta_path

    def run_search(
        self,
        input_files: list[Path],
        database_path: Path,
        params: dict[str, Any],
        output_dir: Path,
        log_callback=None,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        steps = [
            "[DEMO] *** DEMO MODE — results are synthetic ***",
            "[DEMO] Loading spectral data...",
            "[DEMO] Running simulated deconvolution...",
            "[DEMO] Executing simulated database search...",
            "[DEMO] Estimating FDR...",
            "[DEMO] Done. WARNING: These are fabricated results for UI testing only.",
        ]
        for step in steps:
            if log_callback:
                log_callback(step)
            time.sleep(0.2)

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        random.seed(42)
        results = []
        for scan in range(1, 51):
            protein = random.choice(_DEMO_PROTEINS)
            accession, name, seq = protein
            n_ptms = random.randint(0, 3)
            ptms = []
            for _ in range(n_ptms):
                mod = random.choice(_MODIFICATIONS)
                pos = random.randint(1, len(seq))
                ptms.append({**mod, "position": pos})

            mass = random.uniform(8000, 80000)
            delta = random.gauss(0, 0.5)
            score = random.uniform(10, 200)
            evalue = 10 ** random.uniform(-20, -3)
            qvalue = min(random.uniform(0, 0.05), 1.0)

            results.append(ProteoformResult(
                engine_name=self.name,
                engine_version=self.version,
                spectrum_id=f"scan={scan}",
                scan_number=scan,
                source_file="demo_data.mzML",
                precursor_mz=round((mass + 1.007276) / random.randint(5, 30), 4),
                charge=random.randint(5, 30),
                observed_mass=round(mass, 4),
                theoretical_mass=round(mass - delta, 4),
                delta_mass=round(delta, 4),
                accession=accession,
                protein_name=name,
                sequence=seq,
                proteoform_string=_build_proforma(seq, ptms),
                proteoform_mass=round(mass - delta, 4),
                score=round(score, 2),
                evalue=round(evalue, 6),
                qvalue=round(qvalue, 4),
                fdr=round(qvalue, 4),
                matched_fragments=random.randint(5, 80),
                sequence_coverage=round(random.uniform(0.3, 1.0), 3),
                ptms=ptms,
                localization_confidence=round(random.uniform(0.5, 1.0), 3),
                raw_engine_output_path=str(output_dir / "demo_output.tsv"),
                is_demo=True,
            ))
        return results


def _build_proforma(seq: str, ptms: list[dict]) -> str:
    """Build a simplified ProForma-style string."""
    if not ptms:
        return seq
    mods_by_pos = {}
    for ptm in ptms:
        pos = ptm.get("position", 1)
        mods_by_pos.setdefault(pos - 1, []).append(ptm["modification"])
    result = []
    for i, aa in enumerate(seq):
        result.append(aa)
        if i in mods_by_pos:
            for mod in mods_by_pos[i]:
                result.append(f"[{mod}]")
    return "".join(result)
