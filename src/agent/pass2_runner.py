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

    # ── Path setup so sibling src/ packages are importable ────────────────────
    import sys as _sys
    _src = Path(__file__).parent.parent
    if str(_src) not in _sys.path:
        _sys.path.insert(0, str(_src))
    from modules.ollama_client import call_generate  # noqa: E402

    # ── Load system prompt ─────────────────────────────────────────────────────
    prompt_path = _src / "prompts" / "pass2_system_prompt.txt"
    if not prompt_path.exists():
        print("[ERR_PREFLIGHT_MISSING] src/prompts/pass2_system_prompt.txt not found.")
        print("Action: Ensure pass2_system_prompt.txt exists in src/prompts/")
        sys.exit(1)
    system_prompt = prompt_path.read_text()

    # ── Inject lens_summary from locked lens JSON ──────────────────────────────
    with open(lens_path) as f:
        lens = json.load(f)
    lens_summary = lens.get("lens_summary", "")
    strand = config.get("study", {}).get("strand") or lens.get("strand", "")

    # ── Load de-identified data ────────────────────────────────────────────────
    with open(deid_path) as f:
        data_content = json.load(f)

    model_cfg = config.get("model", {})
    determ_temp = config.get("stability_testing", {}).get(
        "deterministic_temperature",
        model_cfg.get("deterministic_temperature", 0.0),
    )

    # ── Run 4 stability passes ─────────────────────────────────────────────────
    outputs = []
    for label, seed, temp in [
        ("seed42", 42, model_cfg.get("temperature", 0.3)),
        ("seed99", 99, model_cfg.get("temperature", 0.3)),
        ("seed123", 123, model_cfg.get("temperature", 0.3)),
        ("deterministic", None, determ_temp),
    ]:
        user_prompt = (
            f"Researcher Lens Summary:\n{lens_summary}\n\n"
            f"Dataset strand: {strand}\n\n"
            f"Data:\n{json.dumps(data_content, indent=2)}"
        )
        raw_response = call_generate(
            api_base=model_cfg.get("api_base", "http://localhost:11434"),
            model=model_cfg.get("model_name", "qwen2.5-27b-instruct"),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temp,
            seed=seed,
        )
        try:
            llm_output = json.loads(raw_response)
        except json.JSONDecodeError:
            llm_output = {}

        out_path = f"artifacts/pass2_output_{label}_{dataset_id}.json"
        with open(out_path, "w") as f:
            json.dump({
                "dataset_id": dataset_id,
                "strand": strand,
                "run_label": label,
                "seed": seed,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "claims": llm_output.get("claims", []),
            }, f, indent=2)
        outputs.append(out_path)

    stability = compute_stability_metrics(outputs)

    # ── Lens amplification index: proportion of pass2 claims using lens vocab ──
    lens_vocab = [v.lower() for v in lens.get("lens_vocabulary", [])]
    if lens_vocab and outputs:
        # Use the seed42 (primary) output for this measure
        with open(outputs[0]) as f:
            primary = json.load(f)
        claims = primary.get("claims", [])
        if claims:
            lens_supported = sum(
                1 for c in claims
                if any(v in c.get("claim_text", "").lower() for v in lens_vocab)
            )
            stability["lens_amplification_index"] = round(lens_supported / len(claims), 4)

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

    theme_stability_score = proportion of distinct themes appearing in >= 2/3 of runs.
    jaccard_mean          = mean |A∩B|/|A∪B| across all run pairs.
    lens_amplification_index is not computable here (no lens vocab available);
    it is filled by pass2_runner.run_pass2() if a lens is present.
    """
    loaded = []
    for path in output_paths:
        if Path(path).exists():
            with open(path) as f:
                loaded.append(json.load(f))

    if len(loaded) < 2:
        return {
            "theme_stability_score": None,
            "jaccard_mean": None,
            "jaccard_pairs": [],
            "lens_amplification_index": None,
            "unstable_themes": [],
        }

    def _claim_keys(output: dict) -> set:
        """Extract a set of short, normalised keys from claims or themes."""
        items = output.get("claims", []) or output.get("pass2_themes", [])
        keys = set()
        for item in items:
            label = (item.get("label") or item.get("claim_text") or "").strip()
            if label:
                keys.add(label[:80].lower())
        return keys

    label_sets = [_claim_keys(o) for o in loaded]

    # ── Pairwise Jaccard scores ────────────────────────────────────────────────
    pairs = []
    for i in range(len(label_sets)):
        for j in range(i + 1, len(label_sets)):
            a, b = label_sets[i], label_sets[j]
            if not a and not b:
                score = 1.0
            elif not a or not b:
                score = 0.0
            else:
                score = len(a & b) / len(a | b)
            pairs.append({
                "run_a": loaded[i].get("run_label", f"run_{i}"),
                "run_b": loaded[j].get("run_label", f"run_{j}"),
                "jaccard": round(score, 4),
            })

    jaccard_mean = round(
        sum(p["jaccard"] for p in pairs) / len(pairs), 4
    ) if pairs else None

    # ── Theme stability ────────────────────────────────────────────────────────
    all_labels: set = set()
    for ls in label_sets:
        all_labels |= ls

    stability_threshold = max(2, round(len(label_sets) * 2 / 3))
    stable = []
    unstable = []
    for label in sorted(all_labels):
        count = sum(1 for ls in label_sets if label in ls)
        (stable if count >= stability_threshold else unstable).append(label)

    theme_stability_score = (
        round(len(stable) / len(all_labels), 4) if all_labels else None
    )

    return {
        "theme_stability_score": theme_stability_score,
        "jaccard_mean": jaccard_mean,
        "jaccard_pairs": pairs,
        "lens_amplification_index": None,  # filled by run_pass2 if lens vocab present
        "unstable_themes": unstable,
    }
