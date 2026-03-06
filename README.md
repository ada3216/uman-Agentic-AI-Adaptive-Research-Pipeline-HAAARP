# Agentic Human–AI Research Pipeline

A governance-first architecture for AI-assisted qualitative research.  
Companion repository to the paper **"A Governance-First Architecture for AI-Assisted Qualitative Research"** — [arXiv preprint](https://arxiv.org/abs/[ARXIV-ID-TO-ADD]).

---

## What this is

A modular, locally-executed research pipeline in which ethical and methodological safeguards are enforced at the infrastructure level, not left to researcher self-discipline. The pipeline implements:

- **Two-pass analysis** — blind Pass 1 (no researcher context) cryptographically anchored before Pass 2 (theoretically positioned, lens-configured)
- **Structured reflexivity elicitation** — 10-question lens dialogue, locked and hashed before Pass 2
- **Grounding verification** — per-claim evidence checking with support strength ratings and theory-sensitive flagging
- **Human evidence review** — synthesis blocked until every AI-generated claim has an explicit human verdict
- **DPIA gating** — special-category data cannot be ingested without a signed DPIA on record
- **Audit bundle generation** — complete artifact manifest with hashes, pre-registration DOI, and authorship disclosure template

All model execution is local (via Ollama). No participant data leaves the researcher's machine.

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/ada3216/uman-Agentic-AI-Adaptive-Research-Pipeline-HAAARP.git
cd 'uman-Agentic-AI-Adaptive-Research-Pipeline-HAAARP'

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# 3. Install Ollama and pull the default local model
ollama pull qwen2.5-27b-instruct

# 4. Run all governance tests against mock LLM outputs
make test-local

# 5. Follow the end-to-end CLI flow in the runbook
python src/agent/orchestrator.py --check-preflight
```

For the full stage-by-stage execution flow, use `docs/runbook.md`. The repository currently ships as a governance-first scaffold with synthetic fixtures, locked examples, and mocked tests rather than a one-command demo runner.

---

## Reproducing the design

The repository includes everything needed to inspect and evaluate the governance architecture independently:

| Artifact | Location | Purpose |
|---|---|---|
| Master audit schema | `artifacts/audit_schema.json` | Full JSON schema for audit bundle validation |
| Evidence review schema | `src/schemas/evidence_review_schema.json` | Per-claim review record schema |
| Synthetic transcript | `tests/fixtures/synthetic_transcript_P01.json` | Demo participant data (fictional) |
| Demo lens record | `examples/lens_example_locked.json` | Filled reflexivity record |
| Demo DPIA | `examples/dpia_signed.json` | Filled data protection impact assessment |
| CI workflow | `.github/workflows/ci.yml` | Runs all tests with MOCK_LLM=true (no model needed) |

To run CI locally without a GPU:
```bash
MOCK_LLM=true pytest tests/ -v
```

Model configuration (name, version, temperature, seed) is recorded in every audit bundle. Seeds used in stability testing runs are logged at `artifacts/[run_id]/stability_report.json`.

---

## Repository structure

```
src/
  agent/          # Orchestrator and pipeline runner
  modules/        # Core governance modules (lens, grounding, audit emitter, etc.)
  prompts/        # All system prompts (versioned, SHA256-recorded in anchor)
  schemas/        # JSON schemas for all artifact types
  tools/          # Human-facing CLI tools (review_cli)
artifacts/        # Schemas, templates, and generated artifacts
examples/         # Filled demo artifacts
tests/
  fixtures/       # Synthetic data for testing
docs/
  workflow.md          # Eight-phase pipeline workflow
  lens.md              # Lens protocol specification
  runbook.md           # Step-by-step execution guide
config/
  defaults.yaml        # Default configuration (sensitivity, OSF settings)
.github/
  agents/              # Repo-specific implementation and verification agents
```

---

## Pre-flight requirements (researcher provides before first run)

Before handing the repository to an AI coding assistant or running a live study, the following documents must be present:

- `docs/workflow.md` — full pipeline workflow (convert from `agentic-workflow-v3.html`)
- `docs/lens.md` — lens protocol (convert from `lens-protocol-v3.html`)
- `artifacts/dpia_checklist.md` — DPIA checklist
- `artifacts/consent_snippets.md` — consent language templates

Convert with: `pandoc [file].html -o [file].md`

---

## Companion documents

| Document | Purpose |
|---|---|
| `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md` | Full development specification for AI coding assistants |
| `implementation docs/TEST_PLAN.md` | Comprehensive governance and verification test plan |
| `GUARDRAILS.md` | Absolute rules for AI coding assistants working on this repo |
| `COPILOT_INSTRUCTIONS.md` | Read-first instructions for any AI coding assistant |
| `docs/runbook.md` | Practical step-by-step execution flow |

---

## Licence

**Pipeline code (`src/`, `tests/`, supporting configuration):** GNU Affero General Public Licence v3.0 (AGPL-3.0). See `LICENSE` for full terms. In brief: free for academic and research use; if you run this as a hosted service you must release your source code under AGPL-3.0, or obtain a commercial licence.

**Paper, documentation and design documents (`docs/`, root `.md` docs, `implementation docs/`):** Creative Commons Attribution 4.0 International (CC BY 4.0). You may share and adapt with attribution.

**Synthetic demo data (`tests/fixtures/`, `examples/`):** CC0 1.0 Universal (public domain dedication). These are entirely fictional and contain no real participant data.

**Commercial use:** For use of the pipeline software in commercial products or services without the AGPL-3.0 source-disclosure obligations, contact the authors. See `COMMERCIAL_LICENSE.md`.

For a plain-English explanation of what AGPL-3.0 requires for hosted services, see `HOW_TO_COMPLY.md`.


---

## Citing this work

```bibtex
@misc{[AUTHOR]_[YEAR]_governance_pipeline,
  title  = {A Governance-First Architecture for AI-Assisted Qualitative Research},
  author = {[YOUR NAME]},
  year   = {2026},
  note   = {arXiv preprint arXiv:[ARXIV-ID-TO-ADD]},
  url    = {https://arxiv.org/abs/[ARXIV-ID-TO-ADD]}
}
```

---

## Contributing

Empirical evaluations, method adaptations, and bug reports are welcome via GitHub Issues. Before contributing code, read `COPILOT_INSTRUCTIONS.md` and `GUARDRAILS.md` — the governance constraints that apply to AI-assisted development of this repository apply equally to human contributions.

---

*Open Science Statement: No participant data is present in this repository. All synthetic fixtures are fictional.*
