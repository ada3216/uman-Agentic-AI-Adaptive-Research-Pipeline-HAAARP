"""
Orchestrator — main pipeline sequencer.

Enforces stage ordering. Does NOT run analysis directly.
Calls each runner/module in sequence and checks preconditions before each step.

Exit codes: see docs/error_codes.md
"""
import sys
import json
import hashlib
from pathlib import Path


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
        # TODO: load config from yaml
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
                    f"If HTML version exists: pandoc {path.replace('.md','.html')} -o {path}"
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
        if not (dpia.get("dpia_complete") and
                dpia.get("dpo_sign_off", {}).get("decision") == "approved"):
            pipeline_error(
                "ERR_DPIA_INVALID",
                "dpia_signed.json is missing required fields.",
                "Ensure dpia_signed.json contains dpo_sign_off.decision == 'approved'\n"
                "and dpia_complete == true."
            )

    def run_pipeline(self, dataset_path: str) -> None:
        """Run the full pipeline in sequence. Each step is a hard gate."""
        # TODO: implement full pipeline orchestration
        # Stage order: preflight → sensitivity check → ingest → deid →
        #   pass1 → prompt_osf_deposit → lens_dialogue → lens_lock →
        #   pass2 (after anchor confirmed) → grounding → human_review → audit_bundle
        print("TODO: implement pipeline orchestration")
