"""
DPIA Gate — hard block for special_category data.

Never raises bare Exception. Always prints structured error and exits with code 2.
See docs/error_codes.md
"""
import sys
import json
from pathlib import Path


def check_dpia_required(sensitivity: str, dpia_path: str = "artifacts/dpia_signed.json") -> None:
    """
    Hard block if sensitivity == special_category and dpia_signed.json absent or invalid.
    Exits with code 2 on failure. Returns None on success.
    """
    if sensitivity != "special_category":
        return  # No DPIA required for other sensitivity levels

    if not Path(dpia_path).exists():
        print(f"\n[ERR_DPIA_MISSING] {dpia_path} not found.")
        print("Action: Complete the DPIA checklist (artifacts/dpia_checklist.md),")
        print("        obtain DPO sign-off, and save the signed record to", dpia_path)
        print("        See examples/dpia_signed.json for the required format.\n")
        sys.exit(2)

    with open(dpia_path) as f:
        try:
            dpia = json.load(f)
        except json.JSONDecodeError:
            print(f"\n[ERR_DPIA_INVALID] {dpia_path} is not valid JSON.")
            print("Action: Check the file format against examples/dpia_signed.json.\n")
            sys.exit(2)

    dpo = dpia.get("dpo_sign_off", {})
    if not dpia.get("dpia_complete"):
        print("\n[ERR_DPIA_INVALID] dpia_complete is not true.")
        print("Action: Obtain DPO approval and set dpia_complete: true.\n")
        sys.exit(2)

    if dpo.get("decision") != "approved":
        print("\n[ERR_DPIA_INVALID] dpo_sign_off.decision is not 'approved'.")
        print("Action: Ensure DPO has signed off with decision: approved.\n")
        sys.exit(2)

    if not dpo.get("dpo_name") or not dpo.get("signature_date"):
        print("\n[ERR_DPIA_INVALID] dpo_sign_off is missing dpo_name or signature_date.")
        print("Action: Check dpia_signed.json against examples/dpia_signed.json.\n")
        sys.exit(2)

    # All checks passed
    return
