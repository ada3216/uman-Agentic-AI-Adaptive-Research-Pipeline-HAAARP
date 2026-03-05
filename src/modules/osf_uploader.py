"""
OSF Uploader — deposits artifacts to Open Science Framework.

OSF personal access token must be in environment variable OSF_TOKEN
or in config/secrets.yaml (gitignored). Never committed.

This module upgrades pass1_anchor from anchor_type: local to anchor_type: osf_doi.
Pass 2 and audit bundle packaging BOTH require this step to complete first.

See docs/error_codes.md for ERR_PASS1_ANCHOR_LOCAL.
"""
import sys
import json
import os
from pathlib import Path


def deposit_pass1_anchor(anchor_path: str, doi: str = None) -> dict:
    """
    Upgrades pass1_anchor from anchor_type: local to osf_doi.

    If OSF_TOKEN env var is set: attempts automatic API deposit.
    If no token: prints manual deposit instructions and prompts for DOI/accession.

    Returns: { "anchor_type": str, "anchor_value": str, "updated_anchor_path": str }
    """
    if not Path(anchor_path).exists():
        print(f"[ERR_PASS1_ANCHOR_MISSING] Anchor file not found: {anchor_path}")
        print("Action: Run pass1_runner.py first.")
        sys.exit(3)

    with open(anchor_path) as f:
        anchor = json.load(f)

    osf_token = os.environ.get("OSF_TOKEN")

    if doi:
        # DOI provided directly on CLI
        anchor_value = doi
        anchor_type = "osf_doi" if "osf.io" in doi.lower() else "repo_accession"
    elif osf_token:
        # TODO: implement OSF API deposit
        # POST https://api.osf.io/v2/nodes/[project_id]/files/
        # Set Authorization: Bearer [osf_token]
        print("OSF auto-upload not yet implemented. Use --doi flag to supply accession manually.")
        sys.exit(1)
    else:
        print("\nNo OSF token found and no --doi provided.")
        print("Manual deposit instructions:")
        print("  1. Go to https://osf.io and create/open your project")
        print(f"  2. Upload: {anchor['artifact_path']}")
        print("  3. Copy the DOI or file URL from OSF")
        print("  4. Re-run: python src/modules/osf_uploader.py --anchor", anchor_path, "--doi [DOI]")
        print("\nOr set OSF_TOKEN environment variable for automatic upload.")
        sys.exit(0)

    anchor["anchor_type"] = anchor_type
    anchor["anchor_value"] = anchor_value

    with open(anchor_path, "w") as f:
        json.dump(anchor, f, indent=2)

    print(f"\n[OK] Anchor upgraded: anchor_type={anchor_type}, anchor_value={anchor_value}")
    print(f"Pass 2 is now unlocked for dataset {anchor.get('artifact_path', '')}")
    return {"anchor_type": anchor_type, "anchor_value": anchor_value, "updated_anchor_path": anchor_path}


def deposit_audit_bundle(bundle_path: str) -> dict:
    """
    Deposits final audit bundle to OSF after study completion.
    Requires OSF_TOKEN environment variable.
    Returns: { "deposit_doi": str }
    """
    # TODO: implement OSF API upload for audit bundle
    print("Audit bundle deposit not yet implemented.")
    print("Manual: upload", bundle_path, "to your OSF project and record the DOI.")
    return {"deposit_doi": None}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deposit artifacts to OSF")
    parser.add_argument("--anchor", help="Path to pass1_anchor JSON file")
    parser.add_argument("--bundle", help="Path to audit bundle zip")
    parser.add_argument("--doi", help="OSF DOI or accession number (if depositing manually)")
    args = parser.parse_args()

    if args.anchor:
        deposit_pass1_anchor(args.anchor, doi=args.doi)
    elif args.bundle:
        deposit_audit_bundle(args.bundle)
    else:
        print("Specify --anchor or --bundle")
        sys.exit(1)
