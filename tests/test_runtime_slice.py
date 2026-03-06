"""
Runtime slice tests — validates prompt loading, Ollama mock, stability metrics,
lens field extraction, and orchestrator config load.

All run with MOCK_LLM=true (no Ollama required).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add src/ and src/agent/ to path so all modules resolve cleanly
_REPO = Path(__file__).parent.parent
_SRC = _REPO / "src"
for _p in [str(_SRC), str(_SRC / "agent"), str(_SRC / "modules")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


FIXTURES = _REPO / "tests" / "fixtures"


# ── ollama_client ─────────────────────────────────────────────────────────────

def test_ollama_mock_pass1_returns_valid_json(monkeypatch):
    """call_generate with MOCK_LLM=true returns parseable JSON for a Pass 1 prompt."""
    monkeypatch.setenv("MOCK_LLM", "true")
    from modules.ollama_client import call_generate
    result = call_generate(
        api_base="http://localhost:11434",
        model="qwen2.5-27b-instruct",
        system_prompt="You are conducting Pass 1 — blind analysis.",
        user_prompt="Dataset strand: IPA\n\nData: {}",
    )
    parsed = json.loads(result)
    assert "pass1_themes" in parsed
    assert "strand" in parsed


def test_ollama_mock_pass2_returns_valid_json(monkeypatch):
    """call_generate with MOCK_LLM=true returns parseable JSON for a Pass 2 prompt."""
    monkeypatch.setenv("MOCK_LLM", "true")
    from modules.ollama_client import call_generate
    result = call_generate(
        api_base="http://localhost:11434",
        model="qwen2.5-27b-instruct",
        system_prompt="You are conducting Pass 2 — lens-informed interpretive analysis.",
        user_prompt="Researcher Lens Summary: ...\n\nData: {}",
        seed=42,
    )
    parsed = json.loads(result)
    assert "claims" in parsed
    assert parsed["run_label"] == "seed42"


def test_ollama_mock_deterministic_labels_run(monkeypatch):
    """Deterministic run (seed=None, temperature=0.0) gets correct run_label."""
    monkeypatch.setenv("MOCK_LLM", "true")
    from modules.ollama_client import call_generate
    result = call_generate(
        api_base="http://localhost:11434",
        model="qwen2.5-27b-instruct",
        system_prompt="You are conducting Pass 2 — lens-informed interpretive analysis.",
        user_prompt="Data: {}",
        seed=None,
        temperature=0.0,
    )
    parsed = json.loads(result)
    assert parsed["run_label"] == "deterministic"


def test_ollama_mock_lens_summary_returns_string(monkeypatch):
    """Lens summary call returns a non-empty string."""
    monkeypatch.setenv("MOCK_LLM", "true")
    from modules.ollama_client import call_generate
    result = call_generate(
        api_base="http://localhost:11434",
        model="qwen2.5-27b-instruct",
        system_prompt="Summarise the following researcher lens dialogue into 6 sections.",
        user_prompt="Q1: ...\nA: ...",
        expect_json=False,
    )
    assert isinstance(result, str)
    assert len(result) > 20


# ── pass1_runner ──────────────────────────────────────────────────────────────

def test_pass1_runner_writes_anchor_integration(tmp_path, monkeypatch):
    """run_pass1 with a real deid fixture produces strand-labelled anchor (MOCK_LLM=true)."""
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()

    deid = tmp_path / "deidentified_P01_session1.json"
    deid.write_text((FIXTURES / "synthetic_transcript_P01.json").read_text())

    config = {
        "study": {"strand": "IPA"},
        "model": {
            "api_base": "http://localhost:11434",
            "model_name": "qwen2.5-27b-instruct",
            "temperature": 0.3,
        },
    }

    from agent import pass1_runner
    # Mock input() so prompt_osf_deposit does not block in CI
    with patch("builtins.input", return_value=""):
        result = pass1_runner.run_pass1(str(deid), config)

    assert "pass1_output_path" in result
    assert "pass1_hash" in result
    assert "anchor_path" in result
    anchor = json.loads(Path(result["anchor_path"]).read_text())
    assert anchor["strand"] == "IPA"
    assert anchor["anchor_type"] == "local"
    assert len(anchor["pass1_hash"]) == 64


# ── compute_stability_metrics ─────────────────────────────────────────────────

def test_stability_metrics_identical_runs(tmp_path):
    """Four identical runs → stability 1.0, Jaccard mean 1.0."""
    from agent.pass2_runner import compute_stability_metrics
    paths = []
    for i, label in enumerate(["seed42", "seed99", "seed123", "deterministic"]):
        p = tmp_path / f"pass2_{label}.json"
        p.write_text(json.dumps({
            "run_label": label,
            "claims": [
                {"claim_text": "Theme A — ambivalence about help-seeking."},
                {"claim_text": "Theme B — anticipation of misunderstanding."},
            ],
        }))
        paths.append(str(p))
    result = compute_stability_metrics(paths)
    assert result["theme_stability_score"] == 1.0
    assert result["jaccard_mean"] == 1.0
    assert result["jaccard_pairs"] != []
    assert result["unstable_themes"] == []


def test_stability_metrics_divergent_runs(tmp_path):
    """Runs with no overlapping claims → stability 0.0, Jaccard mean 0.0."""
    from agent.pass2_runner import compute_stability_metrics
    paths = []
    for i, label in enumerate(["seed42", "seed99", "seed123", "deterministic"]):
        p = tmp_path / f"pass2_{label}.json"
        p.write_text(json.dumps({
            "run_label": label,
            "claims": [{"claim_text": f"Unique theme only in run {i}."}],
        }))
        paths.append(str(p))
    result = compute_stability_metrics(paths)
    assert result["jaccard_mean"] == 0.0
    assert result["theme_stability_score"] == 0.0
    assert len(result["unstable_themes"]) > 0


def test_stability_metrics_partial_overlap(tmp_path):
    """Partial overlap → stability and Jaccard between 0 and 1."""
    from agent.pass2_runner import compute_stability_metrics
    shared = {"claim_text": "Shared theme across all runs."}
    paths = []
    for i, label in enumerate(["seed42", "seed99", "seed123", "deterministic"]):
        p = tmp_path / f"pass2_{label}.json"
        p.write_text(json.dumps({
            "run_label": label,
            "claims": [shared, {"claim_text": f"Run-specific theme {i}."}],
        }))
        paths.append(str(p))
    result = compute_stability_metrics(paths)
    assert result["jaccard_mean"] is not None
    assert 0.0 < result["jaccard_mean"] < 1.0
    assert result["theme_stability_score"] is not None
    shared_key = shared["claim_text"][:80].lower()
    assert shared_key not in result["unstable_themes"]


# ── lens_dialogue field extraction ────────────────────────────────────────────

def test_lens_split_lines():
    """_split_lines handles numbered lists, hyphens, and blanks."""
    from modules.lens_dialogue import _split_lines
    text = "1. First item\n- Second item\n\n3) Third item; Fourth via semicolon"
    result = _split_lines(text)
    assert "First item" in result
    assert "Second item" in result
    assert "Third item" in result
    assert "Fourth via semicolon" in result
    assert "" not in result


def test_lens_split_vocabulary():
    """_split_vocabulary splits comma-separated terms."""
    from modules.lens_dialogue import _split_vocabulary
    result = _split_vocabulary("rupture, repair, embodied experience; shame")
    assert "rupture" in result
    assert "repair" in result
    assert "embodied experience" in result
    assert "shame" in result


def test_lens_parse_evidence_standard():
    """_parse_evidence_standard extracts numeric thresholds."""
    from modules.lens_dialogue import _parse_evidence_standard
    result = _parse_evidence_standard(
        "I would need at least 2 excerpts and evidence from 3 participants."
    )
    assert result["require_excerpt_count"] == 2
    assert "3" in result["generalisation_threshold"]


# ── orchestrator config loading ───────────────────────────────────────────────

def test_orchestrator_loads_yaml_config(tmp_path, monkeypatch):
    """Orchestrator reads config/defaults.yaml and populates self.config."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "defaults.yaml").write_text(
        "sensitivity: personal_non_sensitive\nstudy:\n  strand: IPA\n"
    )
    from agent.orchestrator import Orchestrator
    orc = Orchestrator(config_path=str(config_dir / "defaults.yaml"))
    assert orc.config.get("sensitivity") == "personal_non_sensitive"
    assert orc.config.get("study", {}).get("strand") == "IPA"


def test_orchestrator_missing_config_uses_empty_dict(tmp_path, monkeypatch):
    """Orchestrator falls back to {} if config file is absent."""
    monkeypatch.chdir(tmp_path)
    from agent.orchestrator import Orchestrator
    orc = Orchestrator(config_path="nonexistent_config.yaml")
    assert orc.config == {}
