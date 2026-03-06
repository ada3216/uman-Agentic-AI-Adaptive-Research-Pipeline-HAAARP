"""Schema validation checks for example and synthetic records."""

import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).parent.parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_example_dpia_matches_dpia_schema() -> None:
    schema = _load_json(ROOT / "src" / "schemas" / "dpia_schema.json")
    instance = _load_json(ROOT / "examples" / "dpia_signed.json")
    validate(instance=instance, schema=schema)


def test_example_lens_matches_lens_schema() -> None:
    schema = _load_json(ROOT / "src" / "schemas" / "lens_schema.json")
    instance = _load_json(ROOT / "examples" / "lens_example_locked.json")
    validate(instance=instance, schema=schema)


def test_synthetic_anchor_matches_anchor_schema() -> None:
    schema = _load_json(ROOT / "src" / "schemas" / "anchor_schema.json")
    instance = _load_json(ROOT / "tests" / "fixtures" / "synthetic_pass1_anchor.json")
    validate(instance=instance, schema=schema)


def test_stability_schema_accepts_expected_shape() -> None:
    schema = _load_json(ROOT / "src" / "schemas" / "stability_schema.json")
    instance = {
        "theme_stability_score": None,
        "jaccard_mean": None,
        "jaccard_pairs": [],
        "lens_amplification_index": None,
        "unstable_themes": [],
    }
    validate(instance=instance, schema=schema)
