"""Adversarial and governance-bypass checks for the research pipeline scaffold."""

from pathlib import Path


ROOT = Path(__file__).parent.parent


def _read(path: str) -> str:
    return (ROOT / path).read_text()


def test_pass2_runner_exposes_no_bypass_flags() -> None:
    source = _read("src/agent/pass2_runner.py")
    forbidden = ["--skip-checks", "--force", "--override-anchor", "skip_checks"]
    for token in forbidden:
        assert token not in source


def test_review_cli_exposes_no_auto_accept_path() -> None:
    source = _read("src/tools/review_cli.py")
    forbidden = ["--auto-accept", "auto_accept", "--force-review"]
    for token in forbidden:
        assert token not in source


def test_local_only_banned_imports_absent_from_source() -> None:
    banned = [
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "import langchain",
        "from langchain",
        "import llamaindex",
        "from llamaindex",
        "import assemblyai",
        "from assemblyai",
        "import deepgram",
        "from deepgram",
        "import boto3",
        "from boto3",
    ]
    for path in (ROOT / "src").rglob("*.py"):
        source = path.read_text()
        for token in banned:
            assert token not in source, f"Found banned import pattern {token} in {path}"


def test_requirements_exclude_banned_packages() -> None:
    requirements = _read("requirements.txt")
    banned = [
        "openai",
        "anthropic",
        "langchain",
        "llamaindex",
        "assemblyai",
        "deepgram",
        "boto3",
        "google-cloud",
    ]
    lower_requirements = requirements.lower()
    for package in banned:
        assert package not in lower_requirements
