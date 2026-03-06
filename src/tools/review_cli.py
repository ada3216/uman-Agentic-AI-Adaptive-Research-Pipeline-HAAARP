"""
Human Evidence Review CLI.

The ONLY place where human_verdict fields are set on evidence_review records.
No AI process may call this or set verdicts programmatically.

reviewer_id MUST be ORCID (https://orcid.org/...) or institutional username.
Anonymous or null values are rejected.

interpretive_proposition: True is set when a claim is accepted despite
support_strength == 'weak' or 'none'. The write-up template sentence is
stored in the record for inclusion in the dissertation findings section.

Exit codes:
  0 — all verdicts complete
  5 — interrupted with pending verdicts remaining
"""
import sys
import json
import os
from datetime import datetime, timezone
from glob import glob


INTERPRETIVE_PROPOSITION_TEMPLATE = (
    "{claim_text}, though this should be understood as an interpretive proposition "
    "rather than a data-grounded finding, supported by limited evidential basis "
    "({support_strength}) and retained on the basis of {reviewer_notes}."
)


def _get_reviewer_id() -> tuple:
    """Get reviewer_id from env var or prompt. Reject anonymous values."""
    reviewer_id = os.environ.get("REVIEWER_ID", "").strip()
    reviewer_role = os.environ.get("REVIEWER_ROLE", "researcher").strip()

    if not reviewer_id:
        print("\nREVIEWER_ID not set.")
        print("Enter your ORCID (https://orcid.org/...) or institutional username:")
        reviewer_id = input().strip()

    if not reviewer_id or reviewer_id.lower() in {"anonymous", "anon", "unknown", ""}:
        print("[ERR_REVIEWER_ANONYMOUS] Anonymous reviewer IDs are not accepted.")
        print("Action: Set REVIEWER_ID environment variable to your ORCID or institutional username.")
        sys.exit(5)

    if not reviewer_role:
        reviewer_role = "researcher"

    return reviewer_id, reviewer_role


def run_review_cli(evidence_review_dir: str) -> None:
    """Run interactive evidence review for all pending claims."""
    reviewer_id, reviewer_role = _get_reviewer_id()

    pending_files = sorted(glob(f"{evidence_review_dir}/evidence_review_*.json"))
    pending = [f for f in pending_files if _needs_review(f)]

    if not pending:
        print("\nNo pending evidence review records found. All verdicts complete.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print("HUMAN EVIDENCE REVIEW")
    print(f"Reviewer: {reviewer_id} ({reviewer_role})")
    print(f"Pending: {len(pending)} claims")
    print(f"{'=' * 60}")

    completed = rejected = revised = recheck = 0

    for review_path in pending:
        with open(review_path) as f:
            record = json.load(f)

        print(f"\n--- Claim {record['claim_id']} [{record.get('strand', 'STRAND MISSING')}] ---")
        print(f"Claim: {record['claim_text']}")
        print(f"Support: {record['support_strength']} ({record['support_count']} excerpt(s))")
        print(f"Segments: {', '.join(record.get('supporting_segments', []))}")
        if record.get('verification_flags'):
            print(f"Flags: {', '.join(record['verification_flags'])}")

        while True:
            verdict = input("\nVerdict? [accept / accept_with_revision / reject / recheck]: ").strip().lower()
            if verdict in {"accept", "accept_with_revision", "reject", "recheck"}:
                break
            print("Please enter: accept / accept_with_revision / reject / recheck")

        revised_text = None
        notes = None
        interpretive_proposition = False
        write_up_template = None

        if verdict == "accept_with_revision":
            revised_text = input("Revised claim text: ").strip()
            notes = input("Notes (required): ").strip()
            if not notes:
                print("Notes are required for accept_with_revision.")
                notes = input("Notes: ").strip()
            revised += 1

        elif verdict == "reject":
            notes = input("Notes (required — explain why claim is rejected): ").strip()
            if not notes:
                print("Notes are required for reject.")
                notes = input("Notes: ").strip()
            rejected += 1

        elif verdict == "recheck":
            recheck += 1
            print("Marked for recheck. Pipeline will pause this claim.")

        if verdict == "accept":
            completed += 1
            # Check for interpretive proposition
            if record.get("support_strength") in ("weak", "none"):
                interpretive_proposition = True
                print("\n[INTERPRETIVE PROPOSITION] This claim is accepted despite weak/no support.")
                print("It will be labelled as an interpretive proposition in the write-up.")
                print("Template sentence (stored in record):")
                notes = notes or input("Rationale for retaining this claim: ").strip()
                write_up_template = INTERPRETIVE_PROPOSITION_TEMPLATE.format(
                    claim_text=record["claim_text"],
                    support_strength=record["support_strength"],
                    reviewer_notes=notes or ""
                )
                print(f"\n  \"{write_up_template}\"")

        record["human_verdict"] = {
            "verdict": verdict,
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "revised_claim_text": revised_text,
            "notes": notes,
            "interpretive_proposition": interpretive_proposition,
            "write_up_template": write_up_template,
        }

        with open(review_path, "w") as f:
            json.dump(record, f, indent=2)

    remaining = len([f for f in pending_files if _needs_review(f)])
    print(f"\n{'=' * 60}")
    print("Review session complete.")
    print(f"  Accepted:   {completed}")
    print(f"  Revised:    {revised}")
    print(f"  Rejected:   {rejected}")
    print(f"  Recheck:    {recheck}")
    print(f"  Remaining:  {remaining}")

    if remaining > 0:
        print(f"\n[WARN] {remaining} claims still pending (recheck items).")
        print("Resolve recheck items before emitting audit bundle.")
        sys.exit(5)

    print("\nAll verdicts complete. Audit bundle emission is now unblocked.")
    sys.exit(0)


def _needs_review(path: str) -> bool:
    try:
        with open(path) as f:
            r = json.load(f)
        return r.get("human_verdict") is None or r["human_verdict"].get("verdict") is None
    except Exception:
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Human evidence review CLI")
    parser.add_argument("--dir", default="artifacts/", help="Directory containing evidence_review_*.json")
    args = parser.parse_args()
    run_review_cli(args.dir)
