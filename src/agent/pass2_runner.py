"""
Pass 2 Runner — positioned analysis with researcher lens.

Hard prerequisites (all must pass before any analysis runs):
  (a) pass1_anchor exists
  (b) pass1_hash matches file SHA256
  (c) anchor_type is NOT "local" (osf_doi or repo_accession required)
  (d) lens exists and locked == True
  (e) lens researcher_signature is non-null
  (f) if special_category: dpia_signed.json exists

Runs 4 stability passes: seed 42, 99, 123 + deterministic.
Writes individual output files and stability_report.

Exit codes: see docs/error_codes.md
"""
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _gate_check(deid_path: str, lens_path: str, pass1_hash: str,
                dataset_id: str, config: dict) -> None:
    """Run all precondition checks. Exit with correct code on any failure."""

    # (a) anchor exists
    default_anchor_path = Path("artifacts") / f"pass1_anchor_{dataset_id}.json"
    lens_anchor_path = Path(lens_path).parent / f"pass1_anchor_{dataset_id}.json"
    anchor_path = lens_anchor_path if lens_anchor_path.exists() else default_anchor_path
    if not anchor_path.exists():
        print(f"[ERR_PASS1_ANCHOR_MISSING] {anchor_path} not found.")
        print("Action: Run pass1_runner.py first, deposit to OSF, then retry Pass 2.")
        sys.exit(3)

    with open(anchor_path) as f:
        anchor = json.load(f)

    # (b) hash matches
    actual_hash = _sha256_file(anchor["artifact_path"])
    if actual_hash != anchor["pass1_hash"]:
        print("[ERR_PASS1_HASH_MISMATCH] SHA256 of pass1_output does not match stored hash.")
        print("Action: File may have been modified. Restore from OSF deposit or re-run Pass 1.")
        sys.exit(3)

    # (c) anchor not local
    if anchor.get("anchor_type") == "local":
        print("[ERR_PASS1_ANCHOR_LOCAL] anchor_type is 'local'. External deposit required.")
        print("Action: Run osf_uploader.py --anchor", anchor_path, "--doi [DOI]")
        print("        This upgrades anchor_type to osf_doi.")
        sys.exit(3)

    # (d) lens locked
    if not Path(lens_path).exists():
        print(f"[ERR_LENS_NOT_LOCKED] Lens file not found: {lens_path}")
        print("Action: Run lens_dialogue.py first.")
        sys.exit(4)
    with open(lens_path) as f:
        lens = json.load(f)
    if not lens.get("locked"):
        print("[ERR_LENS_NOT_LOCKED] lens locked != true.")
        print("Action: python src/modules/lens_dialogue.py --lock --run-id [id] --researcher-id [orcid]")
        sys.exit(4)

    # (e) signature non-null
    if not lens.get("researcher_signature"):
        print("[ERR_LENS_SIGNATURE_MISSING] researcher_signature is null.")
        print("Action: Re-run lock_lens() with your ORCID or institutional username.")
        sys.exit(4)

    # (f) DPIA for special_category
    if config.get("sensitivity") == "special_category":
        if not Path("artifacts/dpia_signed.json").exists():
            print("[ERR_DPIA_MISSING] artifacts/dpia_signed.json not found.")
            print("Action: Complete DPIA, obtain DPO sign-off, save to artifacts/dpia_signed.json.")
            sys.exit(2)


def run_pass2(deid_path: str, lens_path: str, pass1_hash: str,
              dataset_id: str, config: dict) -> dict:
    """
    Runs 4 stability passes after gate checks pass.
    Returns paths to primary output and stability report.
    """
    _gate_check(deid_path, lens_path, pass1_hash, dataset_id, config)

    # TODO: load pass2_system_prompt.txt
    # TODO: inject lens_summary from lens JSON
    # TODO: run 4 passes via Ollama REST API

    outputs = []
    for label, seed in [("seed42", 42), ("seed99", 99), ("seed123", 123), ("deterministic", None)]:
        out_path = f"artifacts/pass2_output_{label}_{dataset_id}.json"
        # TODO: actual LLM call with seed / temperature=0 for deterministic
        with open(out_path, "w") as f:
            json.dump({
                "dataset_id": dataset_id,
                "strand": config.get("study", {}).get("strand"),
                "run_label": label,
                "seed": seed,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "claims": [],  # TODO: fill from LLM output
            }, f, indent=2)
        outputs.append(out_path)

    stability = compute_stability_metrics(outputs)
    stability_path = f"artifacts/stability_report_{dataset_id}.json"
    with open(stability_path, "w") as f:
        json.dump(stability, f, indent=2)

    print(f"\nPass 2 complete. Primary output: artifacts/pass2_output_seed42_{dataset_id}.json")
    print(f"Stability report: {stability_path}")
    print(f"Theme stability score: {stability['theme_stability_score']}")
    print(f"Jaccard mean: {stability['jaccard_mean']}")
    sys.exit(0)


def compute_stability_metrics(output_paths: list) -> dict:
    """
    Computes theme stability, Jaccard overlap, lens amplification index.
    TODO: implement comparison logic across 4 output files.
    """
    return {
        "theme_stability_score": None,  # TODO: proportion of themes stable across >=2/3 runs
        "jaccard_mean": None,  # TODO: mean |A∩B|/|A∪B| across run pairs
        "jaccard_pairs": [],  # TODO: per-pair scores
        "lens_amplification_index": None,  # TODO: new Pass2 obs supported only by lens vocab
        "unstable_themes": [],  # TODO: themes in <2/3 runs; labelled provisional
    }
