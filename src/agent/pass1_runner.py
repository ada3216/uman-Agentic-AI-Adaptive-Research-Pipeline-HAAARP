"""
Pass 1 Runner — blind analysis, no researcher lens.

Writes pass1_output and pass1_anchor. Prompts for OSF deposit after completion.
anchor_type starts as "local" and MUST be upgraded to osf_doi before Pass 2 runs.

Exit codes: 0 success, 3 on sequencing/hash errors
See docs/error_codes.md
"""
import sys
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _sha256_file(path: str) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pass1(deid_path: str, config: dict) -> dict:
    """
    Runs blind analysis — NO researcher lens, NO theoretical framing in prompt.
    Calls local model at config['model']['api_base'] via POST /api/generate.
    Reads system prompt from src/prompts/pass1_system_prompt.txt.

    strand field is REQUIRED in output — read from config['study']['strand'].

    Writes:
        artifacts/pass1_output_[dataset_id].json
        artifacts/pass1_anchor_[dataset_id].json

    Returns: { "pass1_output_path": str, "pass1_hash": str, "anchor_path": str }
    """
    dataset_id = str(uuid.uuid4())[:8]
    strand = config.get("study", {}).get("strand")
    if not strand:
        print("[ERR_STRAND_MISSING] strand not set in config/defaults.yaml")
        print("Action: Set study.strand to: IPA | PDA | TA | quant | mixed")
        sys.exit(5)

    # ── Path setup so sibling src/ packages are importable ────────────────────
    _src = Path(__file__).parent.parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from modules.ollama_client import call_generate  # noqa: E402

    # ── Load system prompt ─────────────────────────────────────────────────────
    prompt_path = _src / "prompts" / "pass1_system_prompt.txt"
    if not prompt_path.exists():
        print("[ERR_PREFLIGHT_MISSING] src/prompts/pass1_system_prompt.txt not found.")
        print("Action: Ensure pass1_system_prompt.txt exists in src/prompts/")
        sys.exit(1)
    system_prompt = prompt_path.read_text()

    # ── Load de-identified data ────────────────────────────────────────────────
    with open(deid_path) as f:
        data_content = json.load(f)
    user_prompt = f"Dataset strand: {strand}\n\nData:\n{json.dumps(data_content, indent=2)}"

    # ── Call local model ───────────────────────────────────────────────────────
    model_cfg = config.get("model", {})
    raw_response = call_generate(
        api_base=model_cfg.get("api_base", "http://localhost:11434"),
        model=model_cfg.get("model_name", "qwen2.5-27b-instruct"),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=model_cfg.get("temperature", 0.3),
    )

    # ── Parse LLM output ───────────────────────────────────────────────────────
    try:
        llm_output = json.loads(raw_response)
    except json.JSONDecodeError:
        llm_output = {}
    pass1_themes = llm_output.get("pass1_themes", [])

    # ── Write pass1_output ─────────────────────────────────────────────────────
    output_path = f"artifacts/pass1_output_{dataset_id}.json"
    Path("artifacts").mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "dataset_id": dataset_id,
            "strand": strand,
            "run_label": "pass1_blind",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "pass1_themes": pass1_themes,
        }, f, indent=2)

    pass1_hash = _sha256_file(output_path)
    prereg_doi = config.get("pre_registration_doi")
    if not prereg_doi:
        print("[WARN_PREREG_MISSING] pre_registration_doi is null.")
        print("Warning: Consider pre-registering at https://osf.io before Pass 1.")

    anchor = {
        "pass1_hash": pass1_hash,
        "artifact_path": output_path,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operator_id": config.get("operator_id", "unknown"),
        "pre_registration_doi": prereg_doi,
        "strand": strand,
        "anchor_type": "local",  # MUST be upgraded to osf_doi before Pass 2
        "anchor_value": None,  # filled by osf_uploader.py after deposit
    }
    anchor_path = f"artifacts/pass1_anchor_{dataset_id}.json"
    with open(anchor_path, "w") as f:
        json.dump(anchor, f, indent=2)

    prompt_osf_deposit(anchor_path)
    return {"pass1_output_path": output_path, "pass1_hash": pass1_hash, "anchor_path": anchor_path}


def prompt_osf_deposit(anchor_path: str) -> None:
    """
    Prints OSF deposit instructions and blocks until researcher confirms.
    This step is REQUIRED before Pass 2 can run.
    """
    print("\n" + "=" * 60)
    print("PASS 1 COMPLETE — OSF DEPOSIT REQUIRED BEFORE PASS 2")
    print("=" * 60)
    print(f"\nAnchor file created: {anchor_path}")
    print("\nTo proceed to Pass 2 you must deposit the Pass 1 output to OSF:")
    print("  1. Go to https://osf.io (or your institutional repository)")
    print("  2. Upload the pass1_output file listed in the anchor")
    print("  3. Copy the DOI or accession number")
    print("  4. Run: python src/modules/osf_uploader.py --anchor", anchor_path, "--doi [DOI]")
    print("\nThis upgrades anchor_type from 'local' to 'osf_doi' — required for Pass 2.")
    print("\nPress Enter to acknowledge (you can complete deposit later before running Pass 2).")
    input()
