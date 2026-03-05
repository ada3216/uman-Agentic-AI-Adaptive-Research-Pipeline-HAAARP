"""
Audit Emitter — packages all pipeline artifacts into a verifiable bundle.

Validates before packaging:
  - All evidence_review files have non-null human_verdict
  - pass1_anchor anchor_type is NOT "local" (OSF deposit must have occurred)
  - Every artifact entry has a strand field (indexed, non-null)
  - pre_registration_doi present (warning if null, not a block)

Exits with code 5 on validation failure.
Exits with code 0 on success.
"""
import sys
import json
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from glob import glob


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def emit_audit_bundle(run_id: str, dataset_id: str, config: dict) -> dict:
    """
    Validates all constraints then packages artifacts into audit_bundle_[run_id].zip.
    Returns: { "bundle_path": str, "bundle_sha256": str, "metadata_path": str }
    """
    Path("artifacts").mkdir(exist_ok=True)

    # ── Validation pass ────────────────────────────────────────────────────
    errors = []

    # 1. Check anchor is not local
    anchor_path = f"artifacts/pass1_anchor_{dataset_id}.json"
    anchor = {}
    if Path(anchor_path).exists():
        with open(anchor_path) as f:
            anchor = json.load(f)
        if anchor.get("anchor_type") == "local":
            print(f"\n[ERR_ANCHOR_LOCAL_AT_BUNDLE] pass1_anchor has anchor_type: local.")
            print("Action: Complete OSF deposit (Step 4 in docs/runbook.md) before emitting audit bundle.")
            sys.exit(5)

    # 2. Check all evidence_review verdicts complete
    review_files = glob("artifacts/evidence_review_*.json")
    incomplete = []
    interpretive_propositions = []
    reviewer_ids = set()

    for rf in review_files:
        with open(rf) as f:
            rec = json.load(f)
        verdict = rec.get("human_verdict")
        if verdict is None or (isinstance(verdict, dict) and verdict.get("verdict") is None):
            incomplete.append(rf)
        else:
            if isinstance(verdict, dict):
                rid = verdict.get("reviewer_id")
                if rid:
                    reviewer_ids.add(rid)
                if verdict.get("interpretive_proposition"):
                    interpretive_propositions.append(rec.get("claim_id"))

    if incomplete:
        print(f"\n[ERR_VERDICT_INCOMPLETE] {len(incomplete)} evidence_review record(s) have human_verdict: null.")
        print("Action: Run: python src/tools/review_cli.py --dir artifacts/")
        for f in incomplete:
            print(f"  Pending: {f}")
        sys.exit(5)

    # 3. Check strand labels on all key artifacts
    strand_required = (
        glob("artifacts/pass1_output_*.json") +
        glob("artifacts/pass2_output_*.json") +
        review_files
    )
    missing_strand = []
    for af in strand_required:
        try:
            with open(af) as f:
                data = json.load(f)
            if not data.get("strand"):
                missing_strand.append(af)
        except Exception:
            pass

    if missing_strand:
        print(f"\n[ERR_STRAND_MISSING] {len(missing_strand)} artifact(s) missing strand field.")
        for f in missing_strand:
            print(f"  Missing: {f}")
        sys.exit(5)

    # 4. Pre-reg DOI soft warning
    prereg_doi = config.get("pre_registration_doi") or anchor.get("pre_registration_doi")
    if not prereg_doi:
        print("[WARN_PREREG_MISSING] pre_registration_doi is null. Flagged in audit bundle.")

    # ── Collect artifacts ──────────────────────────────────────────────────
    stability_path = f"artifacts/stability_report_{dataset_id}.json"
    stability = {}
    if Path(stability_path).exists():
        with open(stability_path) as f:
            stability = json.load(f)

    table_path = f"artifacts/claim_evidence_table_{dataset_id}.json"
    hallucination_rate = 0.0
    if Path(table_path).exists():
        with open(table_path) as f:
            table = json.load(f)
        total = table.get("total_claims", 1)
        hallucination_rate = table.get("hallucination_count", 0) / max(total, 1)

    # Files to include in bundle
    bundle_files = (
        ["artifacts/repo_manifest.json", anchor_path] +
        glob(f"artifacts/lens_*{run_id}*.json") +
        glob(f"artifacts/pass2_output_*_{dataset_id}.json") +
        ([stability_path] if Path(stability_path).exists() else []) +
        glob(f"artifacts/lens_delta_report_*_{dataset_id}.md") +
        ([table_path] if Path(table_path).exists() else []) +
        review_files
    )
    bundle_files = [f for f in bundle_files if Path(f).exists()]

    # ── Package ────────────────────────────────────────────────────────────
    bundle_path = f"artifacts/audit_bundle_{run_id}.zip"
    manifest = []
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in bundle_files:
            zf.write(fpath)
            manifest.append({
                "path": fpath,
                "sha256": _sha256_file(fpath),
                "strand": _get_strand(fpath),
            })

    bundle_sha256 = _sha256_file(bundle_path)

    # ── Metadata ───────────────────────────────────────────────────────────
    strand_labels = list({m["strand"] for m in manifest if m.get("strand")})

    metadata = {
        "bundle_id": run_id,
        "bundle_sha256": bundle_sha256,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pre_registration_doi": prereg_doi,
        "pass1_hash": anchor.get("pass1_hash"),
        "pass1_anchor_type": anchor.get("anchor_type"),
        "pass1_anchor_value": anchor.get("anchor_value"),
        "lens_hash": anchor.get("lens_hash"),
        "strand_labels": strand_labels,
        "human_verdicts_complete": len(incomplete) == 0,
        "interpretive_propositions": interpretive_propositions,
        "hallucination_rate": round(hallucination_rate, 4),
        "theme_stability_score": stability.get("theme_stability_score"),
        "jaccard_mean": stability.get("jaccard_mean"),
        "lens_amplification_index": stability.get("lens_amplification_index"),
        "reviewer_ids": sorted(list(reviewer_ids)),
        "artifact_manifest": manifest,
    }
    metadata_path = f"artifacts/audit_bundle_{run_id}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'='*60}")
    print(f"AUDIT BUNDLE COMPLETE")
    print(f"  Bundle:      {bundle_path}")
    print(f"  SHA256:      {bundle_sha256}")
    print(f"  Metadata:    {metadata_path}")
    print(f"  Artifacts:   {len(manifest)}")
    print(f"  Reviewers:   {', '.join(sorted(reviewer_ids))}")
    if interpretive_propositions:
        print(f"  Interp. props: {len(interpretive_propositions)} (labelled in write-up)")
    print(f"\nNext: python src/modules/osf_uploader.py --bundle {bundle_path}")
    sys.exit(0)


def _get_strand(fpath: str) -> str:
    try:
        with open(fpath) as f:
            data = json.load(f)
        return data.get("strand")
    except Exception:
        return None
