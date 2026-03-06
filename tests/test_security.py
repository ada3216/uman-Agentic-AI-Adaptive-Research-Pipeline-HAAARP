"""Static security and hygiene checks for the repository scaffold."""

from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_zone_identifier_files_absent() -> None:
    lingering = list(ROOT.rglob("*:Zone.Identifier"))
    assert lingering == []


def test_prompt_files_exist() -> None:
    prompt_dir = ROOT / "src" / "prompts"
    expected = {
        "pass1_system_prompt.txt",
        "pass2_system_prompt.txt",
        "lens_summary_prompt.txt",
    }
    assert expected.issubset({path.name for path in prompt_dir.glob("*.txt")})


def test_required_schema_files_exist() -> None:
    schema_dir = ROOT / "src" / "schemas"
    expected = {
        "anchor_schema.json",
        "dpia_schema.json",
        "evidence_review_schema.json",
        "lens_schema.json",
        "stability_schema.json",
    }
    assert expected.issubset({path.name for path in schema_dir.glob("*.json")})
