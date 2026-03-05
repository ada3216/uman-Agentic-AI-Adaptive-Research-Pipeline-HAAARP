"""
Ingest and De-identification Module.

Copies raw data to archive and replaces personal identifiers with participant codes.
Analysis agents ONLY receive files named: deidentified_[participant_code]_[session].json
This naming pattern is enforced — analysis modules reject files not matching it.

Exit codes: 0 success, 1 on configuration errors
"""
import sys
import json
import uuid
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path


def ingest(raw_path: str) -> dict:
    """
    Copies raw file to artifacts/raw_archive/ with timestamp prefix.
    Returns: { "archive_path": str, "dataset_id": str, "sha256": str, "timestamp_utc": str }
    """
    raw = Path(raw_path)
    if not raw.exists():
        print(f"[ERR_PREFLIGHT_MISSING] Raw data file not found: {raw_path}")
        print("Action: Check the file path and ensure the file exists.")
        sys.exit(1)

    archive_dir = Path("artifacts/raw_archive")
    archive_dir.mkdir(parents=True, exist_ok=True)

    dataset_id = str(uuid.uuid4())[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = archive_dir / f"{ts}_{dataset_id}_{raw.name}"
    shutil.copy2(raw_path, archive_path)

    sha256 = _sha256_file(str(archive_path))
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    return {
        "archive_path": str(archive_path),
        "dataset_id": dataset_id,
        "sha256": sha256,
        "timestamp_utc": timestamp_utc,
    }


def deidentify(archive_path: str, participant_code_map: dict,
               participant_code: str, session_label: str) -> dict:
    """
    Replaces real names, locations, dates, organisations with participant codes.
    participant_code_map: { "real_name": "P01", ... } — stored separately, never in AI inputs.

    Output MUST be named: deidentified_[participant_code]_[session].json
    This naming pattern is the enforcement mechanism — analysis agents reject other names.

    Returns: { "deid_path": str, "sha256": str, "replacements_count": int }
    """
    with open(archive_path) as f:
        content = f.read()

    replacements_count = 0
    for real, code in participant_code_map.items():
        if real in content:
            content = content.replace(real, code)
            replacements_count += content.count(code)  # approximate

    # TODO: more sophisticated NER-based de-identification using local model

    output_path = Path("artifacts") / f"deidentified_{participant_code}_{session_label}.json"
    Path("artifacts").mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)

    sha256 = _sha256_file(str(output_path))
    return {
        "deid_path": str(output_path),
        "sha256": sha256,
        "replacements_count": replacements_count,
    }


def spot_check_prompt(deid_path: str) -> None:
    """
    Prints spot-check reminder and blocks until researcher acknowledges.
    Automated de-identification is imperfect — manual check is required.
    """
    print("\n" + "="*60)
    print("DE-IDENTIFICATION SPOT CHECK REQUIRED")
    print("="*60)
    print(f"\nDe-identified file: {deid_path}")
    print("\nBefore analysis begins, manually review a sample of the")
    print("de-identified transcript to verify no personal identifiers remain.")
    print("\nCheck especially: names, locations, dates, organisation names,")
    print("role descriptions that could identify individuals, and any")
    print("unusual or distinctive phrases that might identify a participant.")
    print("\nType 'confirmed' and press Enter when spot check is complete:")
    while True:
        response = input().strip().lower()
        if response == "confirmed":
            break
        print("Please type 'confirmed' to acknowledge the spot check.")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
