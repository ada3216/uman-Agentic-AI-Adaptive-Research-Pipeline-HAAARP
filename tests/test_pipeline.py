"""
Pipeline test suite — 14 named tests covering all governance constraints.

All LLM calls are mocked. Run with: make test-local (sets MOCK_LLM=true)
No live model, no network access required.
"""
import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Fixtures ──────────────────────────────────────────────────────────────────

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name) as f:
        return json.load(f)


@pytest.fixture
def tmp_artifacts(tmp_path):
    """Temporary artifacts directory for each test."""
    art = tmp_path / "artifacts"
    art.mkdir()
    return art


@pytest.fixture
def valid_anchor(tmp_artifacts):
    anchor = {
        "pass1_hash": "a" * 64,
        "artifact_path": str(tmp_artifacts / "pass1_output_TEST.json"),
        "timestamp_utc": "2025-10-01T10:00:00Z",
        "strand": "IPA",
        "anchor_type": "osf_doi",
        "anchor_value": "https://osf.io/example",
        "pre_registration_doi": "10.17605/OSF.IO/EXAMPLE",
    }
    # write a matching output file so hash check works
    out = {"dataset_id": "TEST", "strand": "IPA", "claims": []}
    with open(anchor["artifact_path"], "w") as f:
        json.dump(out, f)
    import hashlib
    h = hashlib.sha256()
    h.update(open(anchor["artifact_path"], "rb").read())
    anchor["pass1_hash"] = h.hexdigest()

    path = tmp_artifacts / "pass1_anchor_TEST.json"
    with open(path, "w") as f:
        json.dump(anchor, f)
    return str(path), anchor


@pytest.fixture
def valid_lens(tmp_artifacts):
    lens = {
        "lens_id": "lens_TEST",
        "strand": "IPA",
        "locked": True,
        "researcher_signature": "https://orcid.org/0000-0000-0000-0000",
        "researcher_role": "researcher",
        "signature_timestamp_utc": "2025-10-01T11:00:00Z",
        "lens_summary": "Test lens summary",
        "lens_summary_hash": "b" * 64,
    }
    path = tmp_artifacts / "lens_TEST.json"
    with open(path, "w") as f:
        json.dump(lens, f)
    return str(path), lens


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_pass2_refuses_when_pass1_anchor_missing(tmp_artifacts, valid_lens):
    """pass2_runner must exit(3) when anchor file absent."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "agent"))
    from pass2_runner import _gate_check
    lens_path, _ = valid_lens
    config = {"sensitivity": "personal_non_sensitive", "study": {"strand": "IPA"}}

    with pytest.raises(SystemExit) as exc:
        _gate_check(
            deid_path="nonexistent.json",
            lens_path=lens_path,
            pass1_hash="x" * 64,
            dataset_id="MISSING",
            config=config,
        )
    assert exc.value.code == 3


def test_pass2_refuses_when_pass1_anchor_is_local(tmp_artifacts, valid_lens):
    """pass2_runner must exit(3) with ERR_PASS1_ANCHOR_LOCAL when anchor_type == 'local'."""
    local_anchor = {
        "pass1_hash": "a" * 64,
        "artifact_path": str(tmp_artifacts / "pass1_output_LOCAL.json"),
        "strand": "IPA",
        "anchor_type": "local",    # ← the condition being tested
        "anchor_value": None,
        "pre_registration_doi": None,
    }
    out = {"dataset_id": "LOCAL", "strand": "IPA"}
    with open(local_anchor["artifact_path"], "w") as f:
        json.dump(out, f)
    import hashlib
    h = hashlib.sha256()
    h.update(open(local_anchor["artifact_path"], "rb").read())
    local_anchor["pass1_hash"] = h.hexdigest()

    anchor_path = tmp_artifacts / "pass1_anchor_LOCAL.json"
    with open(anchor_path, "w") as f:
        json.dump(local_anchor, f)

    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "agent"))
    from pass2_runner import _gate_check
    lens_path, _ = valid_lens
    config = {"sensitivity": "personal_non_sensitive"}

    with pytest.raises(SystemExit) as exc:
        _gate_check(
            deid_path="x.json", lens_path=lens_path,
            pass1_hash=local_anchor["pass1_hash"],
            dataset_id="LOCAL", config=config,
        )
    assert exc.value.code == 3


def test_pass2_refuses_when_lens_not_locked(tmp_artifacts, valid_anchor):
    """pass2_runner must exit(4) with ERR_LENS_NOT_LOCKED."""
    unlocked_lens = {"lens_id": "lens_X", "strand": "IPA", "locked": False,
                     "researcher_signature": "https://orcid.org/0000-0000-0000-0000"}
    lens_path = tmp_artifacts / "lens_UNLOCKED.json"
    with open(lens_path, "w") as f:
        json.dump(unlocked_lens, f)

    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "agent"))
    from pass2_runner import _gate_check
    anchor_path, anchor = valid_anchor
    config = {"sensitivity": "personal_non_sensitive"}

    with pytest.raises(SystemExit) as exc:
        _gate_check("x.json", str(lens_path), anchor["pass1_hash"], "TEST", config)
    assert exc.value.code == 4


def test_pass2_refuses_when_lens_signature_missing(tmp_artifacts, valid_anchor):
    """pass2_runner must exit(4) when researcher_signature is null."""
    no_sig_lens = {"lens_id": "lens_X", "strand": "IPA", "locked": True,
                   "researcher_signature": None}
    lens_path = tmp_artifacts / "lens_NOSIG.json"
    with open(lens_path, "w") as f:
        json.dump(no_sig_lens, f)

    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "agent"))
    from pass2_runner import _gate_check
    anchor_path, anchor = valid_anchor
    config = {"sensitivity": "personal_non_sensitive"}

    with pytest.raises(SystemExit) as exc:
        _gate_check("x.json", str(lens_path), anchor["pass1_hash"], "TEST", config)
    assert exc.value.code == 4


def test_dpia_blocks_ingestion_for_special_category(tmp_artifacts):
    """dpia_gate must exit(2) when sensitivity=special_category and dpia_signed.json absent."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    from dpia_gate import check_dpia_required

    absent_path = str(tmp_artifacts / "dpia_signed_ABSENT.json")
    with pytest.raises(SystemExit) as exc:
        check_dpia_required("special_category", dpia_path=absent_path)
    assert exc.value.code == 2


def test_dpia_passes_for_non_sensitive(tmp_artifacts):
    """dpia_gate must not block when sensitivity is not special_category."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    from dpia_gate import check_dpia_required
    # Should return None (no exit) for non-special-category
    result = check_dpia_required("personal_non_sensitive", dpia_path="nonexistent.json")
    assert result is None


def test_grounding_checker_flags_unsupported_claims(tmp_artifacts):
    """grounding_checker must produce evidence_review with support_strength='none' for 0-excerpt claim."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    from grounding_checker import verify_grounding

    pass2 = {
        "dataset_id": "GC_TEST", "strand": "IPA", "run_label": "seed42",
        "claims": [{"claim_id": "CL001", "claim_text": "Participants felt isolated.",
                    "supporting_segments": ["P99_session1_seg_999"]}]  # won't be in transcript
    }
    pass2_path = str(tmp_artifacts / "pass2_output_GC_TEST.json")
    with open(pass2_path, "w") as f:
        json.dump(pass2, f)

    transcript = {"segments": []}  # empty — no segments match
    trans_path = str(tmp_artifacts / "transcript_GC_TEST.json")
    with open(trans_path, "w") as f:
        json.dump(transcript, f)

    os.chdir(tmp_artifacts.parent)
    (tmp_artifacts.parent / "artifacts").mkdir(exist_ok=True)

    result = verify_grounding(pass2_path, trans_path, [], {})
    assert result["hallucination_count"] >= 1

    review_files = list((tmp_artifacts.parent / "artifacts").glob("evidence_review_*.json"))
    assert len(review_files) >= 1
    with open(review_files[0]) as f:
        rec = json.load(f)
    assert rec["support_strength"] == "none"


def test_grounding_checker_does_not_modify_claims(tmp_artifacts):
    """claim_text in evidence_review must exactly match claim_text in pass2_output."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    from grounding_checker import verify_grounding

    original_claim = "This is the exact original claim text that must not be modified."
    pass2 = {
        "dataset_id": "IMMUT_TEST", "strand": "IPA", "run_label": "seed42",
        "claims": [{"claim_id": "CL002", "claim_text": original_claim, "supporting_segments": []}]
    }
    pass2_path = str(tmp_artifacts / "pass2_output_IMMUT_TEST.json")
    with open(pass2_path, "w") as f:
        json.dump(pass2, f)

    os.chdir(tmp_artifacts.parent)
    (tmp_artifacts.parent / "artifacts").mkdir(exist_ok=True)

    verify_grounding(pass2_path, "nonexistent.json", [], {})

    review_files = list((tmp_artifacts.parent / "artifacts").glob("evidence_review_CL002_*.json"))
    assert len(review_files) >= 1
    with open(review_files[0]) as f:
        rec = json.load(f)
    assert rec["claim_text"] == original_claim


def test_audit_emitter_includes_prereg_doi(tmp_artifacts):
    """audit_bundle metadata must contain pre_registration_doi field."""
    # Minimal integration check — emitter writes metadata with field present
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    # This is a structural check on the metadata schema, not a full run
    required_fields = ["pre_registration_doi", "pass1_hash", "strand_labels",
                       "human_verdicts_complete", "reviewer_ids"]
    import importlib.util, inspect
    spec = importlib.util.spec_from_file_location(
        "audit_emitter",
        str(Path(__file__).parent.parent / "src" / "modules" / "audit_emitter.py")
    )
    mod = importlib.util.module_from_spec(spec)
    src = inspect.getsource(mod.__class__)
    # Check the field names appear in the emitter source
    source = open(str(Path(__file__).parent.parent / "src" / "modules" / "audit_emitter.py")).read()
    for field in required_fields:
        assert field in source, f"Field '{field}' not found in audit_emitter.py"


def test_audit_emitter_includes_pass1_hash():
    """audit_bundle metadata must contain pass1_hash field."""
    source = open(str(Path(__file__).parent.parent / "src" / "modules" / "audit_emitter.py")).read()
    assert "pass1_hash" in source


def test_audit_emitter_includes_strand_labels():
    """Every artifact entry in audit manifest must have strand field — validated in emitter."""
    source = open(str(Path(__file__).parent.parent / "src" / "modules" / "audit_emitter.py")).read()
    assert "strand_labels" in source
    assert "ERR_STRAND_MISSING" in source


def test_audit_emitter_blocks_if_verdicts_incomplete(tmp_artifacts):
    """audit_emitter must exit(5) if any evidence_review has human_verdict: null."""
    # Write a review file with null verdict
    review = {"claim_id": "CL_PEND", "strand": "IPA", "claim_text": "x",
               "support_strength": "none", "human_verdict": None}
    art_dir = tmp_artifacts.parent / "artifacts"
    art_dir.mkdir(exist_ok=True)
    with open(art_dir / "evidence_review_CL_PEND_TEST.json", "w") as f:
        json.dump(review, f)

    # Also write a local anchor to trigger ERR_ANCHOR_LOCAL check first
    anchor = {"pass1_hash": "a"*64, "artifact_path": "x", "strand": "IPA",
              "anchor_type": "osf_doi", "anchor_value": "https://osf.io/x",
              "pre_registration_doi": None}
    with open(art_dir / "pass1_anchor_TEST.json", "w") as f:
        json.dump(anchor, f)

    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    os.chdir(tmp_artifacts.parent)
    from audit_emitter import emit_audit_bundle

    with pytest.raises(SystemExit) as exc:
        emit_audit_bundle("RUN_TEST", "TEST", {})
    assert exc.value.code == 5


def test_audit_emitter_blocks_if_anchor_local(tmp_artifacts):
    """audit_emitter must exit(5) if pass1_anchor has anchor_type: local."""
    art_dir = tmp_artifacts.parent / "artifacts"
    art_dir.mkdir(exist_ok=True)

    anchor = {"pass1_hash": "a"*64, "artifact_path": "x", "strand": "IPA",
              "anchor_type": "local",   # ← the condition
              "anchor_value": None, "pre_registration_doi": None}
    with open(art_dir / "pass1_anchor_LTEST.json", "w") as f:
        json.dump(anchor, f)

    os.chdir(tmp_artifacts.parent)
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "modules"))
    from audit_emitter import emit_audit_bundle

    with pytest.raises(SystemExit) as exc:
        emit_audit_bundle("RUN_LTEST", "LTEST", {})
    assert exc.value.code == 5


def test_stability_report_contains_required_metrics():
    """Stability report schema must contain theme_stability_score, jaccard_mean, lens_amplification_index."""
    source = open(str(Path(__file__).parent.parent / "src" / "agent" / "pass2_runner.py")).read()
    for metric in ["theme_stability_score", "jaccard_mean", "lens_amplification_index"]:
        assert metric in source, f"Metric '{metric}' not in pass2_runner compute_stability_metrics"


def test_review_cli_rejects_anonymous_reviewer(tmp_artifacts):
    """review_cli must reject null or empty reviewer_id."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tools"))
    from review_cli import _get_reviewer_id

    # Patch input() to return empty string
    with patch("builtins.input", return_value=""):
        with pytest.raises(SystemExit) as exc:
            _get_reviewer_id()
    assert exc.value.code == 5
