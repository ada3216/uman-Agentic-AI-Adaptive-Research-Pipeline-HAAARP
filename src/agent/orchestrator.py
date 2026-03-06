"""
Orchestrator — main pipeline sequencer.

Enforces stage ordering. Does NOT run analysis directly.
Calls each runner/module in sequence and checks preconditions before each step.

Exit codes: see docs/error_codes.md
"""
import sys
import json
from pathlib import Path

# Allow sibling src/ packages to be imported when run from repo root
_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


ERROR_CODES = {
    "ERR_PREFLIGHT_MISSING": 1,
    "ERR_SENSITIVITY_UNKNOWN": 1,
    "ERR_DPIA_MISSING": 2,
    "ERR_DPIA_INVALID": 2,
    "ERR_PASS1_ANCHOR_MISSING": 3,
    "ERR_PASS1_HASH_MISMATCH": 3,
    "ERR_PASS1_ANCHOR_LOCAL": 3,
    "ERR_LENS_NOT_LOCKED": 4,
    "ERR_LENS_SIGNATURE_MISSING": 4,
    "ERR_VERDICT_INCOMPLETE": 5,
    "ERR_STRAND_MISSING": 5,
    "ERR_ANCHOR_LOCAL_AT_BUNDLE": 5,
}


def pipeline_error(code: str, message: str, action: str) -> None:
    """Print structured error and exit with correct code."""
    exit_code = ERROR_CODES.get(code, 1)
    print(f"\n[{code}] {message}")
    print(f"Action: {action}\n")
    sys.exit(exit_code)


class Orchestrator:
    def __init__(self, config_path: str = "config/defaults.yaml"):
        try:
            import yaml
            with open(config_path) as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"[WARN] Config file not found: {config_path}. Proceeding with empty config.")
            self.config = {}
        self.config_path = config_path

    def check_preflight(self) -> None:
        """Validate all required pre-flight documents exist."""
        required = [
            ("docs/workflow.md", "main pipeline spec"),
            ("docs/lens.md", "lens dialogue questions"),
            ("artifacts/audit_schema.json", "audit metadata schema"),
            ("artifacts/dpia_checklist.md", "DPIA template"),
            ("artifacts/consent_snippets.md", "consent language"),
        ]
        for path, desc in required:
            if not Path(path).exists():
                pipeline_error(
                    "ERR_PREFLIGHT_MISSING",
                    f"Required document not found: {path} ({desc})",
                    f"Provide this file before running the pipeline.\n"
                    f"If HTML version exists: pandoc {path.replace('.md', '.html')} -o {path}"
                )

    def check_sensitivity(self, sensitivity: str) -> None:
        """Validate sensitivity value and gate DPIA if special_category."""
        valid = {"public_text", "personal_non_sensitive", "special_category"}
        if sensitivity not in valid:
            pipeline_error(
                "ERR_SENSITIVITY_UNKNOWN",
                f"Sensitivity value '{sensitivity}' is not recognised.",
                "Set sensitivity in config/defaults.yaml to one of:\n"
                "  public_text | personal_non_sensitive | special_category\n"
                "The value 'normal' is not valid."
            )
        if sensitivity == "special_category":
            self._check_dpia()

    def _check_dpia(self) -> None:
        """Hard block if DPIA not signed."""
        dpia_path = Path("artifacts/dpia_signed.json")
        if not dpia_path.exists():
            pipeline_error(
                "ERR_DPIA_MISSING",
                "artifacts/dpia_signed.json not found.",
                "Complete artifacts/dpia_checklist.md, obtain DPO sign-off,\n"
                "and save to artifacts/dpia_signed.json.\n"
                "See examples/dpia_signed.json for required format."
            )
        with open(dpia_path) as f:
            dpia = json.load(f)
        if not (
            dpia.get("dpia_complete")
            and dpia.get("dpo_sign_off", {}).get("decision") == "approved"
        ):
            pipeline_error(
                "ERR_DPIA_INVALID",
                "dpia_signed.json is missing required fields.",
                "Ensure dpia_signed.json contains dpo_sign_off.decision == 'approved'\n"
                "and dpia_complete == true."
            )

    def run_pipeline(self, dataset_path: str) -> None:
        """Run the full pipeline in sequence. Each step is a hard gate.

        Stage order:
          0 — preflight         check required documents exist
          1 — sensitivity       gate DPIA if special_category
          2 — ingest + deid     archive raw data, apply de-identification
          3 — Pass 1            blind analysis, write anchor, prompt OSF deposit
          4 — lens dialogue     researcher reflexivity interview (interactive)
            [pipeline pauses — researcher locks lens, upgrades OSF anchor]
          5 — Pass 2            lens-informed analysis, 4 stability runs
          6 — grounding check   verify claim citations against transcript
          7 — human review      researcher sets verdicts via review_cli
          8 — audit bundle      emit signed audit package

        Stages 5–8 require a separate invocation after the researcher has:
          - locked the lens:   python src/modules/lens_dialogue.py --lock ...
          - upgraded anchor:   python src/modules/osf_uploader.py --anchor ... --doi ...
        """
        from modules.ingest_and_deid import ingest, deidentify, spot_check_prompt
        from agent.pass1_runner import run_pass1
        from modules.lens_dialogue import run_lens_dialogue

        # Stage 0 — preflight
        print("\n[Stage 0] Preflight checks...")
        self.check_preflight()

        # Stage 1 — sensitivity + DPIA gate
        sensitivity = self.config.get("sensitivity", "")
        print(f"[Stage 1] Sensitivity: {sensitivity or '(not set)'}")
        self.check_sensitivity(sensitivity)

        # Stage 2 — ingest + de-id
        print(f"\n[Stage 2] Ingesting: {dataset_path}")
        ingest_result = ingest(dataset_path)
        archive_path = ingest_result["archive_path"]
        dataset_id = ingest_result["dataset_id"]

        # De-identification: participant_code_map from config (or empty — researcher fills later)
        participant_code_map = self.config.get("participant_code_map", {})
        participant_code = self.config.get("participant_code", f"P{dataset_id}")
        session_label = self.config.get("session_label", "session1")
        deid_result = deidentify(archive_path, participant_code_map, participant_code, session_label)
        deid_path = deid_result["deid_path"]

        spot_check_prompt(deid_path)

        # Stage 3 — Pass 1 (blind analysis)
        print("\n[Stage 3] Running Pass 1 — blind analysis...")
        pass1_result = run_pass1(deid_path, self.config)
        pass1_output_path = pass1_result["pass1_output_path"]
        anchor_path = pass1_result["anchor_path"]
        anchor_id = Path(anchor_path).stem.split("_")[-1]

        # Stage 4 — Lens dialogue (interactive; pipeline pauses after)
        print("\n[Stage 4] Lens dialogue — researcher reflexivity interview...")
        run_lens_dialogue(self.config, pass1_output_path)

        print("\n" + "=" * 60)
        print("PIPELINE PAUSED — RESEARCHER ACTION REQUIRED")
        print("=" * 60)
        print("\nBefore Pass 2 can run:")
        print("  1. Deposit Pass 1 output to OSF and upgrade the anchor:")
        print(f"     python src/modules/osf_uploader.py --anchor {anchor_path} --doi [DOI]")
        print("  2. Lock your lens record:")
        print("     python src/modules/lens_dialogue.py --lock \\")
        print(f"       --run-id {anchor_id} --researcher-id [orcid]")
        print("\nThen run Pass 2:")
        print("  python src/agent/pass2_runner.py \\")
        print(f"    --deid {deid_path} --lens artifacts/lens_{anchor_id}.json \\")
        print(f"    --pass1-hash {pass1_result['pass1_hash']} --dataset-id {anchor_id}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="HAAARP pipeline orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check-preflight",
        action="store_true",
        help="Verify required documents exist and exit.",
    )
    parser.add_argument(
        "--dataset",
        metavar="PATH",
        help="Path to raw de-identified dataset JSON to process.",
    )
    parser.add_argument(
        "--config",
        default="config/defaults.yaml",
        metavar="PATH",
        help="Path to pipeline config YAML (default: config/defaults.yaml).",
    )
    args = parser.parse_args()

    orc = Orchestrator(config_path=args.config)

    if args.check_preflight:
        orc.check_preflight()
        print("[OK] All preflight documents found.")
        sys.exit(0)

    if args.dataset:
        orc.run_pipeline(args.dataset)
    else:
        parser.print_help()
        sys.exit(1)
