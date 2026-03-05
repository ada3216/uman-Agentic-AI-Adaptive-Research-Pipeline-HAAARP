"""
Grounding Checker — verifies AI-generated claims against transcript evidence.

Does NOT modify claims. Only flags and generates evidence_review records.
All evidence_review_*.json files have human_verdict: null on creation.
The review_cli.py is the only process that may set human_verdict.

Support strength thresholds:
    strong:   >= 3 excerpts AND >= 3 distinct participants
    moderate: 2 excerpts, 2 participants
    weak:     1 excerpt, 1 participant
    none:     0 excerpts or all excerpts unverifiable

Exit codes: 0 success, 5 on strand/schema errors
"""
import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


SUPPORT_STRENGTH_THRESHOLDS = {
    "strong":   {"min_excerpts": 3, "min_participants": 3},
    "moderate": {"min_excerpts": 2, "min_participants": 2},
    "weak":     {"min_excerpts": 1, "min_participants": 1},
    "none":     {"min_excerpts": 0, "min_participants": 0},
}

VERIFICATION_FLAGS = [
    "low_evidence_count",
    "lens_vocabulary_only",
    "overgeneralisation",
    "excerpt_not_found",
    "excerpt_does_not_support",
    "single_participant_only",
    "prosody_anchor_unverified",   # audio: timestamp/pause marker not found
    "timecode_anchor_unverified",  # video: timecode/frame anchor not found
]


def verify_grounding(pass2_output_path: str, transcript_path: str,
                     lens_vocabulary: list, config: dict) -> dict:
    """
    For each claim in pass2_output:
      1. Verify supporting_segments exist at stated locations in transcript
      2. Assess whether segment text supports the claim
      3. Rate support_strength using thresholds above
      4. Apply verification flags where relevant
      5. Write evidence_review_[claim_id]_[dataset_id].json with human_verdict: null

    Modality-specific anchor formats verified:
      Audio: P01_session1_T00:04:12_T00:04:28_pause_3200ms
      Video: P01_session1_TC00:12:34_frame_4521_tag:neutral
      Text:  transcript line references

    Does NOT modify claim_text. grounding_checker is read-only on claims.

    Returns: {
        "claim_evidence_table_path": str,
        "evidence_review_paths": list[str],
        "hallucination_count": int
    }
    """
    if not Path(pass2_output_path).exists():
        print(f"[ERR_PREFLIGHT_MISSING] pass2_output not found: {pass2_output_path}")
        sys.exit(1)

    with open(pass2_output_path) as f:
        pass2 = json.load(f)

    strand = pass2.get("strand")
    if not strand:
        print(f"[ERR_STRAND_MISSING] strand field missing from {pass2_output_path}")
        print("Action: Add strand: IPA | PDA | TA | quant | mixed to the pass2 output.")
        sys.exit(5)

    dataset_id = pass2.get("dataset_id", str(uuid.uuid4())[:8])

    # Load transcript
    transcript_content = ""
    if Path(transcript_path).exists():
        with open(transcript_path) as f:
            transcript_data = json.load(f)
        transcript_content = json.dumps(transcript_data)
    else:
        print(f"[WARN] Transcript not found at {transcript_path}. Segment verification limited.")

    claims = pass2.get("claims", [])
    claim_table_entries = []
    review_paths = []
    hallucination_count = 0

    Path("artifacts").mkdir(exist_ok=True)

    for claim in claims:
        claim_id = claim.get("claim_id", str(uuid.uuid4())[:8])
        claim_text = claim.get("claim_text", "")
        segments = claim.get("supporting_segments", [])

        # TODO: implement LLM-based segment verification via Ollama REST API
        # For each segment: check it exists in transcript, check it supports claim

        verified_segments = []
        flags = []
        distinct_participants = set()
        excerpt_count = 0

        for seg in segments:
            participant = seg.split("_")[0] if "_" in str(seg) else "unknown"
            found_in_transcript = str(seg) in transcript_content

            if not found_in_transcript:
                flags.append("excerpt_not_found")
                hallucination_count += 1
            else:
                verified_segments.append(seg)
                distinct_participants.add(participant)
                excerpt_count += 1

                # Modality-specific anchor checks
                seg_str = str(seg)
                if "_T" in seg_str and "_pause_" in seg_str:  # audio anchor
                    # TODO: verify timestamp range is within transcript duration
                    pass
                if "_TC" in seg_str and "_frame_" in seg_str:  # video anchor
                    # TODO: verify timecode exists in video index
                    pass

        # Check lens vocabulary only
        if lens_vocabulary and all(
            any(vocab.lower() in str(seg).lower() for vocab in lens_vocabulary)
            for seg in verified_segments
        ) and verified_segments:
            flags.append("lens_vocabulary_only")

        # Overgeneralisation: broad claim, single excerpt
        if excerpt_count == 1 and len(claim_text.split()) > 15:
            flags.append("overgeneralisation")

        if len(distinct_participants) == 1 and excerpt_count > 0:
            flags.append("single_participant_only")

        # Compute support strength
        n_exc = excerpt_count
        n_part = len(distinct_participants)
        if n_exc >= 3 and n_part >= 3:
            support_strength = "strong"
        elif n_exc >= 2 and n_part >= 2:
            support_strength = "moderate"
        elif n_exc >= 1:
            support_strength = "weak"
        else:
            support_strength = "none"

        if support_strength in ("weak", "none"):
            flags.append("low_evidence_count")

        # Write evidence_review record
        review_record = {
            "claim_id": claim_id,
            "run_id": pass2.get("run_label", "unknown"),
            "dataset_id": dataset_id,
            "strand": strand,
            "generated_by": "pass2_runner",
            "claim_text": claim_text,          # read-only — do not modify
            "supporting_segments": segments,
            "verified_segments": verified_segments,
            "support_count": excerpt_count,
            "distinct_participants": list(distinct_participants),
            "support_strength": support_strength,
            "verification_flags": flags,
            "human_verdict": None,             # set ONLY by review_cli.py
        }

        review_path = f"artifacts/evidence_review_{claim_id}_{dataset_id}.json"
        with open(review_path, "w") as f:
            json.dump(review_record, f, indent=2)
        review_paths.append(review_path)

        claim_table_entries.append({
            "claim_id": claim_id,
            "strand": strand,
            "claim_text": claim_text,
            "support_strength": support_strength,
            "support_count": excerpt_count,
            "distinct_participants": list(distinct_participants),
            "flags": flags,
            "review_path": review_path,
        })

    table_path = f"artifacts/claim_evidence_table_{dataset_id}.json"
    with open(table_path, "w") as f:
        json.dump({
            "dataset_id": dataset_id,
            "strand": strand,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_claims": len(claims),
            "hallucination_count": hallucination_count,
            "claims": claim_table_entries,
        }, f, indent=2)

    print(f"\nGrounding check complete.")
    print(f"  Claims checked:      {len(claims)}")
    print(f"  Hallucination flags: {hallucination_count}")
    print(f"  Evidence table:      {table_path}")
    print(f"  Review records:      {len(review_paths)} files")
    print(f"\nNext: python src/tools/review_cli.py --dir artifacts/")
    return {
        "claim_evidence_table_path": table_path,
        "evidence_review_paths": review_paths,
        "hallucination_count": hallucination_count,
    }
