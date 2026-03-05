# Agentic Human–AI Research Pipeline

A governance-first, open-source infrastructure for AI-assisted qualitative and mixed-methods research.

## What this is

A modular pipeline that enforces methodological safeguards at the infrastructure level:
- Two-pass analysis (blind → positioned) with cryptographic locking
- Structured researcher reflexivity elicitation (lens dialogue)
- DPIA gating for sensitive data — a hard code block, not a recommendation
- Per-claim human evidence review before any claim enters the findings
- Full audit bundle with immutable OSF anchor

All AI processing runs locally via Ollama. No participant data is sent to external APIs or cloud services.

## Quick start

```bash
# 1. Configure
cp config/secrets.example.yaml config/secrets.yaml
# Edit config/defaults.yaml: set sensitivity, strand, pre_registration_doi

# 2. Run tests (no model required)
make test-local

# 3. Full pipeline — see docs/runbook.md for step-by-step commands
```

## Folder map

```
src/agent/          orchestrator, pass1 and pass2 runners
src/modules/        ingest, de-ID, lens dialogue, grounding, audit, OSF upload
src/tools/          human evidence review CLI
src/prompts/        system prompts (derived from docs/workflow.md and docs/lens.md)
src/schemas/        JSON schemas for all artifact types
docs/               workflow spec, lens guide, runbook, error codes, architecture
artifacts/          generated artifacts (never commit participant data)
examples/           filled example artifacts for CI (synthetic data only)
tests/              pytest suite (14 named tests, all mocked)
config/             defaults.yaml (committed); secrets.yaml (gitignored)
implementation docs/ dev plan, test plan
```

## Key documents

- [Pipeline workflow](docs/workflow.md) — six-phase human–AI workflow design
- [Lens protocol](docs/lens.md) — structured researcher reflexivity dialogue
- [Step-by-step runbook](docs/runbook.md) — how to run the pipeline
- [Error codes](docs/error_codes.md) — all error codes and recovery actions
- [Agent governance rules](GUARDRAILS.md) — hard limits and structural rules for AI coding assistants
- [Agent instructions](COPILOT_INSTRUCTIONS.md) — concise rules for Copilot/Cursor/Windsurf
- [Dev plan](implementation%20docs/Agentic_Pipeline_Dev_Plan_v2.1.md) — implementation roadmap and design rationale
- [Generic architecture](docs/generic-architecture.md) — adapting this pipeline to other research methods
- [Generic toolkit](docs/generic-toolkit.md) — drop-in artifacts for other implementations

## For examiners and supervisors

The pipeline produces an **audit bundle** (`artifacts/audit_bundle_[run_id].zip`) containing:
- All analysis artifacts with SHA256 hashes
- Cryptographic link to OSF deposit of Pass 1 output
- Locked researcher lens summary with ORCID signature
- Human evidence review records for every AI-generated claim
- Stability metrics across seeded analysis runs

This bundle is designed to be included in your dissertation methodology appendix and/or deposited alongside your findings on OSF.

## License

MIT
