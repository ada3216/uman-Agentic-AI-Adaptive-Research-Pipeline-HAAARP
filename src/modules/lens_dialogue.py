"""
Lens Dialogue Module — structured researcher reflexivity elicitation.

Presents 10 questions to the researcher (via stdout), collects responses,
uses local LLM to summarise into lens_summary, then locks the record.

The 10 questions MUST be extracted from docs/lens.md — do not invent them.
This stub contains placeholder questions; Copilot agent must replace with
verbatim questions from docs/lens.md before implementation is complete.

researcher_signature must be ORCID or institutional username — not null.
Lock requires non-null signature or exits with code 4.

Exit codes: 0 success, 4 on lens/signature errors
"""
import sys
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ─── COPILOT AGENT: Replace these with verbatim questions from docs/lens.md ───
# Section references below indicate which section of lens.md each Q comes from.
LENS_QUESTIONS = [
    # L1.1 — theoretical orientation
    "What is your theoretical orientation for this study? Please describe the frameworks, "
    "traditions, or theoretical commitments that inform how you approach this data.",

    # L1.2 — clinical/professional orientation
    "What is your relevant professional or clinical experience with this topic or population? "
    "How might that experience shape what you notice or attend to?",

    # L2.1 — primary hypotheses
    "What are your primary hypotheses or expectations going into this analysis? "
    "Please list them explicitly so they can be cross-checked against your pre-registration.",

    # L2.2 — lens vocabulary
    "What specific concepts, constructs, or vocabulary from your theoretical frame are you "
    "likely to use or look for in the data? List these as your lens vocabulary.",

    # L3.1 — vulnerable groups / power dynamics
    "Are there specific vulnerabilities, power dynamics, or relational complexities in your "
    "participant group that you expect to shape how they speak or present their experience?",

    # L3.2 — expected participant indirection
    "Do you expect participants to express certain experiences indirectly, through hedging, "
    "displacement, or omission? If so, how do you expect that to manifest?",

    # L4.1 — explicit exclusions
    "What are you explicitly NOT looking for in this analysis? "
    "What would you set aside or treat as out of scope?",

    # L4.2 — evidence standard
    "What is your evidence standard for a finding? How many participants and excerpts "
    "would you require before treating something as a theme rather than a notable instance?",

    # L5.1 — Pass 1 surprises
    "Having seen the Pass 1 blind analysis output, what surprised you? "
    "What did the blind reading surface that you had not anticipated?",

    # L5.2 — confirmation + lock
    "Please review your responses above. Is this an accurate and complete account of your "
    "theoretical lens and positionality as you begin the positioned analysis? "
    "Type your ORCID or institutional username below to confirm and lock this record.",
]
# ──────────────────────────────────────────────────────────────────────────────


def run_lens_dialogue(config: dict, pass1_output_path: str, model_client=None,
                      run_id: str = None) -> dict:
    """
    Runs structured 10-question reflexivity interview.
    Researcher types responses — AI is NOT generating the answers.
    AI summarises all responses into lens_summary after Q10.

    Requires researcher_signature (ORCID preferred) + ISO timestamp for lock.

    Writes: artifacts/lens_[run_id].json
    Returns: { "lens_path": str, "lens_hash": str, "locked": bool }
    """
    if not run_id:
        run_id = str(uuid.uuid4())[:8]

    prereg_doi = config.get("pre_registration_doi")
    strand = config.get("study", {}).get("strand")

    print(f"\n{'='*60}")
    print("LENS DIALOGUE — Researcher Reflexivity Interview")
    print(f"Run ID: {run_id}  |  Strand: {strand}")
    print(f"{'='*60}")
    print("\nYour responses will be hashed and locked as part of the audit trail.")
    print("The AI will summarise your responses — it does not generate the answers.\n")

    responses = []
    posthoc_flags = []

    for i, question in enumerate(LENS_QUESTIONS, 1):
        print(f"\nQ{i}: {question}")
        response = input("> ").strip()
        responses.append({"question_number": i, "question": question, "response": response})

        # Q3 — cross-check hypotheses against pre-registration
        if i == 3 and prereg_doi:
            print(f"\n  [Note] These hypotheses will be cross-checked against {prereg_doi}.")
            print("  Any hypothesis not present in your pre-registration will be flagged as post-hoc.")
            # TODO: implement actual cross-check via pre-reg DOI lookup

    # AI summarises responses (local model call)
    # TODO: implement summary call via Ollama REST API
    lens_summary = "[TODO: AI-generated summary of researcher lens from Q1-Q9 responses]"

    record = {
        "lens_id": f"lens_{run_id}",
        "version": "v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "prereg_doi": prereg_doi,
        "strand": strand,
        "pass1_output_path": pass1_output_path,
        "dialogue_responses": responses,
        "lens_summary": lens_summary,
        "lens_vocabulary": [],      # TODO: extract from Q2 response
        "primary_hypotheses": [],   # TODO: extract from Q3 response + posthoc flags
        "posthoc_hypothesis_flags": posthoc_flags,
        "explicit_exclusions": [],  # TODO: extract from Q7 response
        "evidence_standard": {},    # TODO: extract from Q8 response
        "pass1_surprises": "",      # TODO: extract from Q9 response
        "researcher_signature": None,
        "researcher_role": "researcher",
        "signature_timestamp_utc": None,
        "researcher_confirmation": False,
        "locked": False,
    }

    Path("artifacts").mkdir(exist_ok=True)
    lens_path = f"artifacts/lens_{run_id}.json"
    with open(lens_path, "w") as f:
        json.dump(record, f, indent=2)

    print(f"\nLens dialogue saved to {lens_path}")
    print("Review your responses, then lock with:")
    print(f"  python src/modules/lens_dialogue.py --lock --run-id {run_id} --researcher-id [orcid]")

    return {"lens_path": lens_path, "lens_hash": None, "locked": False}


def lock_lens(lens_path: str, researcher_id: str,
              researcher_role: str = "researcher") -> dict:
    """
    Locks the lens record with researcher signature and SHA256 hash.
    researcher_id must be ORCID or institutional username — not null, not anonymous.
    Returns: { "lens_hash": str, "locked": True }
    Exits with code 4 if signature invalid.
    """
    if not researcher_id or researcher_id.strip().lower() in {"", "anonymous", "anon", "unknown"}:
        print("\n[ERR_LENS_SIGNATURE_MISSING] researcher_id is null or anonymous.")
        print("Action: Provide your ORCID (https://orcid.org/...) or institutional username.")
        sys.exit(4)

    if not Path(lens_path).exists():
        print(f"\n[ERR_LENS_NOT_LOCKED] Lens file not found: {lens_path}")
        print("Action: Run lens_dialogue first.")
        sys.exit(4)

    with open(lens_path) as f:
        record = json.load(f)

    record["researcher_signature"] = researcher_id.strip()
    record["researcher_role"] = researcher_role
    record["signature_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    record["researcher_confirmation"] = True
    record["locked"] = True

    with open(lens_path, "w") as f:
        json.dump(record, f, indent=2)

    lens_hash = _sha256_file(lens_path)
    record["lens_summary_hash"] = lens_hash

    with open(lens_path, "w") as f:
        json.dump(record, f, indent=2)

    # Recompute hash of complete file including the hash field itself
    final_hash = _sha256_file(lens_path)

    print(f"\n[OK] Lens locked.")
    print(f"     Researcher: {researcher_id}")
    print(f"     Timestamp:  {record['signature_timestamp_utc']}")
    print(f"     Hash:       {final_hash}")
    print(f"\nPass 2 is now unlocked (pending OSF anchor confirmation).")
    return {"lens_hash": final_hash, "locked": True}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    import argparse, yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", help="Run ID")
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--researcher-id", help="ORCID or institutional username")
    parser.add_argument("--pass1-output", default="", help="Path to pass1_output.json")
    parser.add_argument("--config", default="config/defaults.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    if args.lock:
        if not args.run_id:
            print("--run-id required for --lock"); sys.exit(1)
        lens_path = f"artifacts/lens_{args.run_id}.json"
        lock_lens(lens_path, args.researcher_id or "")
    else:
        run_lens_dialogue(config, args.pass1_output, run_id=args.run_id)
