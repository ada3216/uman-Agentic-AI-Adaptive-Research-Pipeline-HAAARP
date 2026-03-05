# Agentic Human–AI Research Pipeline — Phased Development Plan v2.1

**Changes from v2.0:**
- OSF/institutional repo deposit enforced as hard prerequisite before Pass 2 (anchor_type: local no longer accepted)
- Structured error codes and human advice strings defined (docs/error_codes.md + pipeline constants)
- Shell return codes defined for all CLI tools and orchestrator
- COPILOT_INSTRUCTIONS.md added as Phase 0 task (agent must read before touching any code)
- Example artifacts added: examples/dpia_signed.json, examples/lens_example_locked.json
- CI: mocks-only stated explicitly; make test-local target added
- PGP signing flow documented in Phase 6 with actual command
- Schema additions: strand indexed, interpretive_proposition display semantics, reviewer_id provenance (ORCID required)
- Coherence fix: pre-flight docs must exist as Markdown in repo; HTML exports alone are insufficient
- Coherence fix: artifacts/audit_schema.json must be produced as actual JSON in Phase 0

This document is the single source-of-truth for a Copilot-style custom agent executing against this repository. Each phase contains: *Goal*, *Tasks* (explicit developer-style steps), *Required inputs* (files or values that must exist), and *Artifacts/Acceptance criteria* (what must be produced and what conditions mark the task done).

---

## Key policy anchors (referenced throughout)

- **OSF** (Open Science Framework) — immutable deposit for pass1 hash anchor and pre-registration. URL: https://osf.io
- **BPS** (British Psychological Society) — ethics guidelines 2021; governs consent and participant rights
- **GDPR Article 9** — lawful basis for special category health/therapy data; governs DPIA requirement
- **Local-only constraint** — all AI processing must run on the researcher's own machine; no data may be sent to external APIs or cloud services at any stage. This is a hard constraint enforced by DPIA, not a preference.

---

## Pre-flight: what must exist before any phase begins

The following files must be present in `docs/` and `artifacts/` as **Markdown or JSON files** before Phase 0 runs. The Copilot agent must not create these — they are human-authored documents from the research design process.

> **Coherence note:** HTML versions of these documents may exist as exports but are not sufficient for the pipeline. The agent reads Markdown. If only HTML versions are present, convert them to Markdown before proceeding: `pandoc docs/workflow.html -o docs/workflow.md`

```
docs/workflow.md          — main pipeline spec (8-stage agentic workflow)
docs/lens.md              — lens dialogue questions (10 Qs) + guidance
artifacts/audit_schema.json   — JSON schema for audit metadata (see Phase 0 task 5)
artifacts/dpia_checklist.md   — DPIA submission template (Markdown)
artifacts/consent_snippets.md — consent language templates (Markdown)
```

If any of these are missing, the agent must halt and print an error using the format defined in `docs/error_codes.md`:
```
[ERR_PREFLIGHT_MISSING] Required document not found: docs/workflow.md
Action: This file must be provided by the researcher before the pipeline can be built.
        Convert from HTML if available: pandoc docs/workflow.html -o docs/workflow.md
```

---

# Phase 0 — Repo sanity & onboarding

**Goal**: Confirm repo contains base docs, create canonical folder structure, generate manifest, create COPILOT_INSTRUCTIONS.md.

**Required inputs**
- Five documents listed in Pre-flight above

**Tasks**

1. Read `COPILOT_INSTRUCTIONS.md` if it exists. If it does not exist yet, create it now (see Task 8 below) before doing anything else.

2. Validate presence of all five required files. Compute SHA256 for each. Write `artifacts/repo_manifest.json`:
```json
{
  "generated_at": "ISO8601",
  "schema_version": "1.0",
  "files": [
    { "path": "docs/workflow.md", "sha256": "...", "description": "main pipeline spec" },
    { "path": "docs/lens.md", "sha256": "...", "description": "lens dialogue questions and guidance" },
    { "path": "artifacts/audit_schema.json", "sha256": "...", "description": "audit metadata JSON schema" },
    { "path": "artifacts/dpia_checklist.md", "sha256": "...", "description": "DPIA submission template" },
    { "path": "artifacts/consent_snippets.md", "sha256": "...", "description": "consent language templates" }
  ]
}
```

3. Create canonical folder structure if not present:
```
src/agent/          — orchestrator, pass runners
src/modules/        — adapters, gates, emitters
src/prompts/        — lens prompt template, pass1 and pass2 system prompts
src/schemas/        — JSON schemas (audit, lens, evidence_review)
src/tools/          — human-facing CLI tools
notebooks/          — demo notebook
docs/               — human docs (already present)
artifacts/          — generated artifacts (hashes, lens outputs, evidence review records)
examples/           — example filled artifacts for CI and documentation
tests/fixtures/     — synthetic test data
config/             — defaults.yaml (no secrets ever committed here)
osf_deposit_example/ — sample OSF deposit metadata
```

4. Create top-level `README.md` pointing to `docs/` and `artifacts/`. Required sections: purpose, folder map, quick-start, link to `docs/workflow.md`, link to `COPILOT_INSTRUCTIONS.md`.

5. Create `config/defaults.yaml`:
```yaml
# Pipeline configuration — no secrets committed here
# Provider credentials go in environment variables or config/secrets.yaml (gitignored)

model:
  provider: local                    # local | (hosted only if not special_category data)
  backend: ollama                    # ollama | llamacpp
  model_name: qwen2.5-27b-instruct
  api_base: http://localhost:11434   # Ollama default endpoint
  temperature: 0.3
  deterministic_temperature: 0.0    # used for the deterministic stability run
  seeds: [42, 99, 123]

sensitivity: personal_non_sensitive  # public_text | personal_non_sensitive | special_category
                                     # IMPORTANT: special_category triggers DPIA hard block
                                     # NEVER set to "normal" — not a valid value

pre_registration_doi: null           # must be set before Pass 1 runs; soft warning if null

study:
  strand: null                       # IPA | PDA | TA | quant | mixed — required, indexed field
  team_structure: solo               # solo | team
  academic_level: masters            # masters | phd | lab

stability_testing:
  seeded_reruns: 3
  deterministic_run: true
  alternate_model_optional: true     # only for phd/lab; off by default at masters

osf:
  deposit_required: true             # pass1 anchor MUST be deposited before Pass 2 can run
  osf_api_base: https://api.osf.io/v2
  # OSF token goes in config/secrets.yaml — never here
```

6. Create `.gitignore` covering: `config/secrets.yaml`, `*.env`, `artifacts/raw_archive/`, `*_participant_code_map.json`.
   Create `config/secrets.example.yaml` with placeholder keys and instructions.

7. Create `Makefile` at repo root:
```makefile
.PHONY: test test-local lint

# Run tests with mocked LLM calls only — no live model required
test-local:
	MOCK_LLM=true pytest tests/ -v

# CI target — same as test-local; enforces mock flag
test:
	MOCK_LLM=true pytest tests/ -v

lint:
	flake8 src/ tests/
```

8. Create `COPILOT_INSTRUCTIONS.md` at repo root (see separate spec — the agent must treat this as the highest-priority instruction document):
```markdown
# COPILOT_INSTRUCTIONS.md
## Read this before touching any file in this repo.

### Three absolute rules
1. NEVER commit secrets. Write config/secrets.example.yaml and exit with instructions.
2. Two-pass lock is enforced in code, not by trust. Pass 2 CANNOT run unless:
   - pass1_anchor.json exists AND hash matches AND anchor_type is NOT "local"
   - lens_[run_id].json exists AND locked == true AND researcher_signature is non-null
3. DPIA gate is a hard code block, not a warning. If sensitivity == special_category,
   check for artifacts/dpia_signed.json before ingesting any data. If absent, exit with
   ERR_DPIA_MISSING (see docs/error_codes.md).

### Files to read before writing any code
- docs/workflow.md — pipeline architecture and stage specifications
- docs/lens.md — lens dialogue questions (10 Qs); extract verbatim into lens_dialogue.py
- artifacts/audit_schema.json — all audit artifacts must conform to this schema
- docs/error_codes.md — all errors must use these codes and advice strings

### Where to write things
- All AI-generated artifacts → artifacts/
- All source code → src/
- All test fixtures → tests/fixtures/
- Example filled artifacts (for CI) → examples/
- Never write to docs/ unless explicitly asked

### Error handling
Use structured error codes (docs/error_codes.md). Never raise bare Exception().
Every error must include: code, message, and action (what the human should do next).

### Strand labels
Every output artifact must carry a strand field: IPA | PDA | TA | quant | mixed.
Audit emitter validates this before packaging. Missing strand = packaging blocked.
```

9. Create `docs/error_codes.md` (full spec — see Phase 1 Task 2 for the content).

10. Verify `artifacts/audit_schema.json` exists. If not, create it from the schema described in the generic-toolkit docs. This file is a pre-flight dependency for Phase 2b.

**Artifacts / Acceptance criteria**
- `COPILOT_INSTRUCTIONS.md` present at repo root
- `artifacts/repo_manifest.json` exists with SHA256 for all five required docs
- Folder structure complete including `examples/` and `osf_deposit_example/`
- `README.md` present
- `config/defaults.yaml` present with `sensitivity: personal_non_sensitive`
- `Makefile` present with `test-local` and `test` targets
- `.gitignore` covers secrets, raw archive, code maps
- `docs/error_codes.md` present

---

# Phase 1 — Integration map

**Goal**: Document which component plugs into each pipeline stage. Produce machine-readable map, adapter scaffolds, and error codes registry.

**Tasks**

1. Create `docs/integration_map.md` with the following stage-to-component assignments:

| Stage | Module | Component | Notes |
|---|---|---|---|
| Ingest + de-ID | `src/modules/ingest_and_deid.py` | Local filesystem | No cloud storage for special category data |
| Transcription | `src/modules/transcribe_adapter.py` | **WhisperX (local only)** | Do NOT suggest AssemblyAI or any cloud transcription — DPIA violation for special category data |
| Orchestration | `src/agent/orchestrator.py` | Local Python sequential runner | Not LangChain — sequenced runner with blocking gates |
| Pass 1 (blind) | `src/agent/pass1_runner.py` | Local model via Ollama REST API | `POST http://localhost:11434/api/generate` |
| Lens dialogue | `src/modules/lens_dialogue.py` | Local model via Ollama REST API | Structured 10-question interview |
| Pass 2 (positioned) | `src/agent/pass2_runner.py` | Local model via Ollama REST API | Requires pass1 anchor (osf_doi or repo_accession) + lens hash |
| Grounding verification | `src/modules/grounding_checker.py` | Local model via Ollama REST API | Does not modify claims |
| Human evidence review | `src/tools/review_cli.py` | Terminal CLI | Human-completed; AI must not set verdicts |
| Audit bundle | `src/modules/audit_emitter.py` | Local filesystem + OSF upload | OSF for immutable anchor |
| DPIA gate | `src/modules/dpia_gate.py` | Local filesystem check | Reads `artifacts/dpia_signed.json`; blocks with ERR_DPIA_MISSING if absent |
| OSF deposit | `src/modules/osf_uploader.py` | OSF API | Required post-Pass 1; upgrades anchor_type from local to osf_doi |

2. Create `docs/error_codes.md` with the complete error code registry:

```markdown
# Pipeline Error Codes

All pipeline errors use structured output:
  [ERROR_CODE] Description
  Action: What the researcher should do next.

## DPIA and governance errors
ERR_DPIA_MISSING        — artifacts/dpia_signed.json not found
  Action: Complete the DPIA checklist (artifacts/dpia_checklist.md), obtain DPO sign-off,
          and save the signed record to artifacts/dpia_signed.json

ERR_DPIA_INVALID        — dpia_signed.json exists but is missing required fields
  Action: Check that dpia_signed.json contains: dpo_name, signature_date, decision=approved

## Pass sequencing errors
ERR_PASS1_ANCHOR_MISSING  — pass1_anchor_[dataset_id].json not found in artifacts/
  Action: Run pass1_runner.py first, then deposit to OSF, then retry Pass 2.

ERR_PASS1_HASH_MISMATCH   — stored pass1_hash does not match SHA256 of pass1_output file
  Action: The Pass 1 output file may have been modified after hashing. Do not proceed.
          Restore pass1_output from the OSF deposit or re-run Pass 1 on the original data.

ERR_PASS1_ANCHOR_LOCAL    — anchor_type is "local"; external deposit required before Pass 2
  Action: Deposit pass1_output to OSF or institutional repo. Run osf_uploader.py, then
          update artifacts/pass1_anchor_[dataset_id].json with anchor_type and anchor_value.

ERR_LENS_NOT_LOCKED       — lens_[run_id].json exists but locked != true
  Action: Complete the lens dialogue and call lock_lens() with your researcher ID.

ERR_LENS_SIGNATURE_MISSING — lens locked but researcher_signature is null
  Action: Re-run lock_lens() and provide your ORCID or institutional username.

## Data and schema errors
ERR_STRAND_MISSING        — artifact is missing the required strand field
  Action: Add strand: IPA|PDA|TA|quant|mixed to the artifact and re-run.

ERR_VERDICT_INCOMPLETE    — one or more evidence_review records have human_verdict: null
  Action: Run review_cli.py and complete all pending verdicts before emitting audit bundle.

ERR_SENSITIVITY_UNKNOWN   — sensitivity value not recognised
  Action: Set sensitivity in config/defaults.yaml to one of:
          public_text | personal_non_sensitive | special_category

ERR_PREREG_MISSING        — pre_registration_doi is null (soft warning, not a hard block)
  Action: Consider depositing a pre-registration at OSF before Pass 1 runs.
          This will be flagged in the audit bundle if absent.

## Preflight errors
ERR_PREFLIGHT_MISSING     — required pre-flight document not found
  Action: See docs listed in Pre-flight section of the dev plan.
          Convert HTML to Markdown if needed: pandoc file.html -o file.md

## Return codes (shell)
  0   — success
  1   — ERR_PREFLIGHT_MISSING or ERR_SENSITIVITY_UNKNOWN (configuration error)
  2   — ERR_DPIA_MISSING or ERR_DPIA_INVALID (governance block)
  3   — ERR_PASS1_ANCHOR_MISSING, ERR_PASS1_HASH_MISMATCH, or ERR_PASS1_ANCHOR_LOCAL
  4   — ERR_LENS_NOT_LOCKED or ERR_LENS_SIGNATURE_MISSING
  5   — ERR_VERDICT_INCOMPLETE or ERR_STRAND_MISSING (synthesis block)
```

3. Create adapter scaffolds in `src/modules/` for each module with:
   - Module docstring explaining purpose, inputs, outputs
   - Function signatures with type hints
   - `# TODO` markers at implementation points
   - Return codes documented in comments

4. Create `docs/integration_snippets.md` with example config blocks showing how to switch model, how to configure OSF credentials via environment variable, and how to run WhisperX locally.

**Artifacts / Acceptance criteria**
- `docs/integration_map.md` present with all eleven stages mapped
- `docs/error_codes.md` present with all codes, messages, actions, and return codes
- Adapter scaffolds in `src/modules/` with documented I/O signatures
- `config/defaults.yaml` references only local providers

---

# Phase 2a — Core pipeline: ingest, pass1, lens dialogue

**Goal**: Implement ingest + de-ID, Pass 1 runner with immutable anchor, and lens dialogue module.

**Required inputs**
- `config/defaults.yaml` (Phase 0)
- `docs/lens.md` — agent must READ this file to extract the 10 lens questions before implementing `lens_dialogue.py`
- `artifacts/audit_schema.json` — agent must READ this to implement audit_emitter correctly
- `docs/error_codes.md` — all error conditions must use these codes

**Tasks**

1. Implement `src/modules/ingest_and_deid.py`:
```python
import sys

ERROR_CODES = {
    "ERR_SENSITIVITY_UNKNOWN": 1,
    "ERR_DPIA_MISSING": 2,
}

def ingest(raw_path: str) -> dict:
    """
    Copies raw file to artifacts/raw_archive/ with timestamp.
    Returns: { "archive_path": str, "dataset_id": str (uuid4), "sha256": str, "timestamp_utc": str }
    On failure: prints structured error and sys.exit(1)
    """

def deidentify(archive_path: str, participant_code_map: dict) -> dict:
    """
    Replaces names, locations, dates, organisations with participant codes.
    participant_code_map: { "real_name": "P01", ... } — stored separately, never in AI inputs.
    Returns: { "deid_path": str, "sha256": str, "replacements_count": int }
    Output files MUST be named: deidentified_[participant_code]_[session].json
    Analysis agents must ONLY accept files matching this naming pattern.
    On failure: prints structured error and sys.exit(1)
    """

def spot_check_prompt(deid_path: str) -> str:
    """
    Prints a formatted notice to stdout and requires researcher acknowledgement (input()).
    Not automated — blocks until researcher types 'confirmed'.
    """
```

2. Implement `src/agent/pass1_runner.py`:
```python
import sys

def run_pass1(deid_path: str, config: dict) -> dict:
    """
    Runs blind analysis — NO researcher lens, NO theoretical framing in prompt.
    Calls local model at config['model']['api_base'] via POST /api/generate.
    Reads pass1 system prompt from src/prompts/pass1_system_prompt.txt.
    
    Writes:
      artifacts/pass1_output_[dataset_id].json
      artifacts/pass1_anchor_[dataset_id].json
    
    pass1_anchor format:
    {
      "pass1_hash": sha256 of pass1_output file,
      "artifact_path": "artifacts/pass1_output_[dataset_id].json",
      "timestamp_utc": ISO8601,
      "operator_id": from config,
      "pre_registration_doi": from config (logs ERR_PREREG_MISSING warning if null),
      "strand": from config.study.strand (indexed, required),
      "anchor_type": "local",      ← MUST be upgraded to osf_doi before Pass 2 can run
      "anchor_value": null         ← filled by osf_uploader after deposit
    }
    
    Returns: { "pass1_output_path": str, "pass1_hash": str, "anchor_path": str }
    On failure: prints structured error and sys.exit(3)
    """
    
def prompt_osf_deposit(anchor_path: str) -> None:
    """
    After Pass 1 completes, prints instructions for OSF deposit:
      1. Go to https://osf.io and create a new project or use your pre-registration project
      2. Upload artifacts/pass1_output_[dataset_id].json
      3. Copy the DOI or accession number from OSF
      4. Run: python src/modules/osf_uploader.py --anchor [anchor_path] --doi [DOI]
    Blocks until researcher confirms deposit is complete.
    """
```

3. Create `src/prompts/pass1_system_prompt.txt`. **Agent must not invent this prompt.** Read Stage 1 from `docs/workflow.md` and write a system prompt that:
   - Contains no researcher lens, no theoretical framing
   - For IPA strand: initial noticing, candidate experiential statements, draft emergent themes per participant — no cross-case work at this stage
   - For PDA strand: discourse feature extraction, subject positions, relational moment flagging, session-level summary
   - Explicitly states: "You have not been given any theoretical frame or researcher hypotheses. Your task is to read carefully and surface what is present in the data without interpretive direction."
   - Ends with instruction to output structured JSON with `strand` field present

4. Implement `src/modules/lens_dialogue.py`. **Agent must READ `docs/lens.md` before implementing.**
```python
import sys

LENS_QUESTIONS = [
    # Extract all 10 questions verbatim from docs/lens.md
    # Must cover: theoretical orientation, clinical orientation,
    # primary hypotheses (cross-checked against prereg), lens vocabulary,
    # explicit exclusions, evidence standards, vulnerable groups/power dynamics,
    # expected participant indirection, pass1 surprises, researcher signature + lock
]

def run_lens_dialogue(config: dict, pass1_output_path: str, model_client) -> dict:
    """
    Runs structured 10-question reflexivity interview.
    Presents each question to researcher via stdout input prompt.
    Researcher types responses — AI is not generating answers.
    AI summarises responses into lens_summary after all questions answered.
    
    Requires researcher_signature (ORCID preferred; institutional username accepted)
    + ISO timestamp for lock.
    
    Writes: artifacts/lens_[run_id].json
    Returns: { "lens_path": str, "lens_hash": str, "locked": bool }
    On failure: prints structured error and sys.exit(4)
    """

def lock_lens(lens_path: str, researcher_id: str, researcher_role: str = "researcher") -> dict:
    """
    Adds to lens JSON:
      researcher_signature: researcher_id (ORCID preferred)
      researcher_role: "researcher" | "supervisor" | "team_member"
      signature_timestamp_utc: ISO8601 (auto-set)
    Computes final lens_hash (SHA256 of complete file including signature).
    Sets locked: true.
    
    Returns: { "lens_hash": str, "locked": True }
    Raises ERR_LENS_SIGNATURE_MISSING (sys.exit(4)) if researcher_id is null or empty.
    Pipeline refuses Pass 2 until this returns successfully.
    """
```

**Artifacts / Acceptance criteria**
- `ingest_and_deid.py` produces `deidentified_[code]_[session].json` output files only
- `pass1_runner.py` produces `pass1_anchor_[dataset_id].json` with `anchor_type: local` and all required fields including `strand`
- `pass1_runner.py` prints OSF deposit instructions after completing and requires acknowledgement
- `pass1_anchor.json` includes `pre_registration_doi` (null logs warning, does not block)
- `src/prompts/pass1_system_prompt.txt` exists and contains `strand` field instruction
- `lens_dialogue.py` contains all 10 questions extracted from `docs/lens.md`
- `lock_lens()` requires `researcher_id` non-null; exits with code 4 if missing
- `lock_lens()` records `researcher_role` in lens JSON

---

# Phase 2b — Core pipeline: OSF deposit, pass2, stability, grounding, review, audit

**Goal**: Implement OSF deposit enforcer, Pass 2 enforcement, stability loop, grounding verification, human review CLI, and audit emitter.

**Required inputs**
- `artifacts/pass1_anchor_[dataset_id].json` with `anchor_type: local` (Phase 2a)
- `artifacts/lens_[run_id].json` with `locked: true` (Phase 2a)
- `artifacts/dpia_signed.json` if `sensitivity == special_category`
- `examples/dpia_signed.json` and `examples/lens_example_locked.json` (Phase 0 example artifacts)

**Tasks**

1. Implement `src/modules/osf_uploader.py`:
```python
import sys

def deposit_pass1_anchor(anchor_path: str, osf_token: str) -> dict:
    """
    Uploads pass1_output file to OSF and updates anchor JSON with:
      anchor_type: "osf_doi" | "repo_accession"
      anchor_value: "https://osf.io/xxxxx" or accession number
    
    If osf_token not available: prints manual deposit instructions and
    provides a CLI prompt to enter the DOI/accession manually.
    
    Returns: { "anchor_type": str, "anchor_value": str, "updated_anchor_path": str }
    On failure: prints ERR_PASS1_ANCHOR_LOCAL and sys.exit(3)
    """
    
def deposit_audit_bundle(bundle_path: str, osf_token: str) -> dict:
    """
    Uploads audit bundle to OSF after study completion.
    Returns: { "deposit_doi": str }
    """
```

2. Implement stability testing loop inside `src/agent/pass2_runner.py`:
```python
import sys

ERROR_CODES = {
    "ERR_PASS1_ANCHOR_MISSING": 3,
    "ERR_PASS1_HASH_MISMATCH": 3,
    "ERR_PASS1_ANCHOR_LOCAL": 3,
    "ERR_LENS_NOT_LOCKED": 4,
    "ERR_LENS_SIGNATURE_MISSING": 4,
    "ERR_DPIA_MISSING": 2,
}

def run_pass2(deid_path: str, lens_path: str, pass1_hash: str, config: dict) -> dict:
    """
    Refuses to run unless ALL of the following are true:
      (a) artifacts/pass1_anchor_[dataset_id].json exists → else ERR_PASS1_ANCHOR_MISSING
      (b) stored pass1_hash matches SHA256 of pass1_output file → else ERR_PASS1_HASH_MISMATCH
      (c) anchor_type is NOT "local" (osf_doi or repo_accession required) → else ERR_PASS1_ANCHOR_LOCAL
      (d) lens_[run_id].json exists AND locked == true → else ERR_LENS_NOT_LOCKED
      (e) lens researcher_signature is non-null → else ERR_LENS_SIGNATURE_MISSING
      (f) if sensitivity == special_category: artifacts/dpia_signed.json exists → else ERR_DPIA_MISSING
    
    Each failure prints the structured error with action string from docs/error_codes.md
    and calls sys.exit(error_code).
    
    Reads pass2 system prompt from src/prompts/pass2_system_prompt.txt.
    Injects lens_summary from lens JSON into system prompt.
    
    Stability testing — runs four times:
      Run A: seed=42
      Run B: seed=99
      Run C: seed=123
      Run D: temperature=0.0, deterministic (greedy)
    
    Writes:
      artifacts/pass2_output_seed42_[dataset_id].json
      artifacts/pass2_output_seed99_[dataset_id].json
      artifacts/pass2_output_seed123_[dataset_id].json
      artifacts/pass2_output_deterministic_[dataset_id].json
      artifacts/stability_report_[dataset_id].json
    
    Returns: { "primary_output_path": str, "stability_report_path": str }
    sys.exit(0) on success
    """

def compute_stability_metrics(outputs: list[dict]) -> dict:
    """
    Returns: {
      "theme_stability_score": float,  proportion consistent across ≥2/3 seeded + deterministic
      "jaccard_mean": float,           mean Jaccard of theme label sets across all run pairs
      "jaccard_pairs": [...],
      "lens_amplification_index": float,
      "unstable_themes": [...]         themes present in <2/3 runs; labelled provisional
    }
    """
```

3. Create `src/prompts/pass2_system_prompt.txt`. **Agent must READ `docs/lens.md` and `docs/workflow.md` before writing.** The prompt must:
   - Begin with: "You are now reading this data through the researcher's theoretical lens. The lens summary is as follows: {lens_summary}"
   - Include disconfirmation mandate: explicitly direct the AI to surface material that resists or complicates the lens
   - Include lens-amplification guard warning
   - Specify JSON output with `strand` field (indexed, required)
   - Specify supporting segment anchor format per modality (from `docs/workflow.md` Stage 7)

4. Create `src/prompts/pass1_vs_pass2_delta_prompt.txt` that compares Pass 1 and Pass 2, outputting `artifacts/lens_delta_report_[strand]_[dataset_id].md`.

5. Implement `src/modules/grounding_checker.py`:
```python
import sys

def verify_grounding(pass2_output_path: str, transcript_path: str,
                     lens_vocabulary: list, config: dict) -> dict:
    """
    For each claim in pass2_output:
      1. Verify supporting_segments exist at stated locations in transcript
      2. Assess whether each segment supports the claim
      3. Count excerpts and participants; rate support_strength:
            strong:   ≥3 excerpts AND ≥3 distinct participants
            moderate: 2 excerpts, 2 participants
            weak:     1 excerpt, 1 participant
            none:     0 excerpts
      4. Flag: overgeneralisation, lens_vocabulary_only, excerpt_not_found,
               excerpt_does_not_support, single_participant_only,
               prosody_anchor_unverified, timecode_anchor_unverified
    
    Does NOT modify claims. Only flags and generates review records.
    All evidence_review_*.json files have human_verdict: null on creation.
    
    Returns: {
      "claim_evidence_table_path": str,
      "evidence_review_paths": list[str],
      "hallucination_count": int
    }
    sys.exit(0) on success; sys.exit(5) if strand field missing from any claim
    """
```
   Evidence review JSON must match `src/schemas/evidence_review_schema.json`.

6. Implement `src/tools/review_cli.py`:
```python
import sys
import os

def run_review_cli(evidence_review_dir: str) -> None:
    """
    Exit codes:
      0  — all verdicts completed
      5  — interrupted with verdicts remaining (recheck items still present)
    
    reviewer_id: read from env var REVIEWER_ID; if absent, prompt.
                 Must be ORCID (https://orcid.org/...) or institutional username.
                 Reject null or anonymous values.
    reviewer_role: "researcher" | "supervisor" | "team_member"
    
    For each claim with human_verdict == null:
      - Display: claim_id, strand, claim_text, supporting_segments,
                 support_strength, verification_flags
      - Prompt: "Verdict? [accept / accept_with_revision / reject / recheck]"
      - accept_with_revision: require revised_claim_text AND notes
      - reject: require notes
      - accept with support_strength weak or none:
            set interpretive_proposition: true
            print: "This claim will be labelled as an interpretive proposition
                    in the write-up. Template sentence required — see
                    docs/workflow.md section on interpretive propositions."
      
    interpretive_proposition display semantics (for write-up):
      When interpretive_proposition: true, the claim MUST appear in the findings
      section with this template sentence:
        "[claim text], though this should be understood as an interpretive
        proposition rather than a data-grounded finding, supported by limited
        evidential basis ([support_strength]) and retained on the basis of
        [reviewer notes]."
      The audit bundle includes the template sentence in the evidence_review record.
    
    Saves: reviewer_id, reviewer_role, timestamp_utc (auto-set), interpretive_proposition flag.
    On completion: prints accept/revised/rejected/recheck summary.
    Pipeline synthesis blocked until all verdicts non-null.
    """
```

7. Implement `src/modules/audit_emitter.py`:
```python
import sys

def emit_audit_bundle(run_id: str, dataset_id: str, config: dict) -> dict:
    """
    Validates before packaging (failures print structured error + sys.exit(5)):
      - All evidence_review files have non-null human_verdict
      - pass1_anchor anchor_type is NOT "local" (OSF deposit must have occurred)
      - Every artifact entry has a strand field (indexed, non-null)
      - pre_registration_doi present (warning if null, not a block)
    
    Packages into artifacts/audit_bundle_[run_id].zip
    
    Writes artifacts/audit_bundle_[run_id].json:
    {
      "bundle_id": run_id,
      "bundle_sha256": str,
      "timestamp_utc": ISO8601,
      "pre_registration_doi": str or null,
      "pass1_hash": str,
      "pass1_anchor_type": str,       ← must be osf_doi or repo_accession
      "pass1_anchor_value": str,      ← verifiable URL or accession
      "lens_hash": str,
      "strand_labels": [...],         ← indexed; must be present for every artifact
      "human_verdicts_complete": bool,
      "interpretive_propositions": [...],  ← list of claim_ids with flag true
      "hallucination_rate": float,
      "theme_stability_score": float,
      "jaccard_mean": float,
      "lens_amplification_index": float,
      "reviewer_ids": [...],          ← ORCID/usernames of all reviewers
      "artifact_manifest": [...]
    }
    
    Returns: { "bundle_path": str, "bundle_sha256": str, "metadata_path": str }
    sys.exit(0) on success
    """
```

8. Write `docs/runbook.md` with the exact CLI command sequence:
```
Step 1:  Configure — edit config/defaults.yaml; set sensitivity, strand, pre_registration_doi
Step 2:  Ingest and de-identify — python src/modules/ingest_and_deid.py --raw [path]
Step 3:  Run Pass 1 (blind) — python src/agent/pass1_runner.py --config config/defaults.yaml
Step 4:  Deposit Pass 1 anchor to OSF — python src/modules/osf_uploader.py --anchor [path]
          (manual if no token: go to osf.io, upload, copy DOI, run with --doi flag)
Step 5:  Run lens dialogue — python src/modules/lens_dialogue.py --run-id [id]
Step 6:  Review and lock lens — python src/modules/lens_dialogue.py --lock --researcher-id [orcid]
Step 7:  Run Pass 2 (stability loop) — python src/agent/pass2_runner.py --config config/defaults.yaml
          Note: runs 4 passes; expect 2–4x Pass 1 runtime
Step 8:  Run grounding verification — python src/modules/grounding_checker.py --dataset-id [id]
Step 9:  Human evidence review — python src/tools/review_cli.py --dir artifacts/
Step 10: Emit audit bundle — python src/modules/audit_emitter.py --run-id [id]
Step 11: Deposit audit bundle to OSF — python src/modules/osf_uploader.py --bundle [path]
```
Include expected output file at each step. Include common failure messages with their error code and resolution. Cross-reference `docs/error_codes.md`.

**Artifacts / Acceptance criteria**
- `pass2_runner.py` checks anchor_type is NOT "local"; exits with ERR_PASS1_ANCHOR_LOCAL (code 3) if so
- `pass2_runner.py` prints structured error with action string for every failure condition
- `review_cli.py` requires reviewer_id to be non-null ORCID or institutional username; rejects anonymous
- `review_cli.py` exits with code 0 (all done) or code 5 (rechecks remaining)
- `review_cli.py` includes interpretive_proposition template sentence in saved JSON
- `audit_emitter.py` validates anchor_type is not local before packaging
- `audit_emitter.py` includes `reviewer_ids` and `interpretive_propositions` lists in metadata
- `docs/runbook.md` present with all 11 steps and cross-reference to error codes

---

# Phase 3 — Tests, validation & QA

**Goal**: Automated checks enforcing methodological rules. All LLM calls mocked. Tests run with `make test-local` (no live model, no network).

**Required inputs**
- All Phase 2a and 2b modules implemented
- `examples/dpia_signed.json` (Phase 0 example artifacts)
- `examples/lens_example_locked.json` (Phase 0 example artifacts)

**Tasks**

1. Create test fixtures in `tests/fixtures/`:
   - `synthetic_transcript_P01.json` — short de-identified text transcript, 10–15 segments
   - `synthetic_pass1_output.json` — valid Pass 1 output with `strand` field present
   - `synthetic_pass2_output.json` — 5 claims: mix of supported and unsupported
   - `synthetic_lens.json` — copy of `examples/lens_example_locked.json` for test use
   - `synthetic_pass1_anchor.json` — valid anchor with `anchor_type: osf_doi` (not local)
   - `synthetic_dpia_signed.json` — copy of `examples/dpia_signed.json` for test use

2. Implement `tests/test_pipeline.py` with these named tests:
```python
def test_pass2_refuses_when_pass1_anchor_missing():
    """pass2_runner must exit(3) when anchor absent"""

def test_pass2_refuses_when_pass1_anchor_is_local():
    """pass2_runner must exit(3) with ERR_PASS1_ANCHOR_LOCAL when anchor_type == 'local'"""

def test_pass2_refuses_when_lens_not_locked():
    """pass2_runner must exit(4) with ERR_LENS_NOT_LOCKED if locked != True"""

def test_pass2_refuses_when_lens_signature_missing():
    """pass2_runner must exit(4) with ERR_LENS_SIGNATURE_MISSING if researcher_signature null"""

def test_dpia_blocks_ingestion_for_special_category():
    """dpia_gate must exit(2) with ERR_DPIA_MISSING when dpia_signed.json absent"""

def test_grounding_checker_flags_unsupported_claims():
    """grounding_checker must produce evidence_review with support_strength='none' for unsupported claim"""

def test_grounding_checker_does_not_modify_claims():
    """claim_text in evidence_review must match claim_text in pass2_output exactly"""

def test_audit_emitter_includes_prereg_doi():
    """audit_bundle metadata must contain pre_registration_doi field"""

def test_audit_emitter_includes_pass1_hash():
    """audit_bundle metadata must contain pass1_hash field"""

def test_audit_emitter_includes_strand_labels():
    """every artifact entry in audit manifest must have strand field"""

def test_audit_emitter_blocks_if_verdicts_incomplete():
    """audit_emitter must exit(5) if any evidence_review has human_verdict: null"""

def test_audit_emitter_blocks_if_anchor_local():
    """audit_emitter must exit(5) if pass1_anchor has anchor_type: local"""

def test_stability_report_contains_required_metrics():
    """stability_report must contain theme_stability_score, jaccard_mean, lens_amplification_index"""

def test_review_cli_rejects_anonymous_reviewer():
    """review_cli must reject null or empty reviewer_id"""
```
That is 14 named tests. Mock all LLM calls using `unittest.mock.patch` with `MOCK_LLM=true` env flag.

3. CI workflow `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      MOCK_LLM: "true"      # CRITICAL: all LLM calls are mocked; no live model runs in CI
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install pytest flake8
      - name: Lint
        run: flake8 src/ tests/ --max-line-length=100
      - name: Run tests (mocked LLM only)
        run: make test
```
No secrets stored in workflow. No API keys. No live model calls. This is enforced by `MOCK_LLM=true`.

4. Create `notebooks/demo_pipeline.ipynb` running full pipeline on synthetic fixtures with mock LLM responses. Produces `artifacts/audit_bundle_demo.zip`. Each cell has a markdown explanation of the methodological rationale.

5. Create `docs/validation_report_template.md`:
   - Theme stability score: `___` (proportion stable across all four runs)
   - Jaccard mean: `___` (mean set overlap across seeded run pairs)
   - Lens amplification index: `___`
   - Unstable themes (provisional): `[list]`
   - Hallucination rate: `___`
   - Human verdict distribution: accept `___` / accept_with_revision `___` / reject `___` / recheck `___`
   - Interpretive propositions: `___` (number; list claim IDs)
   - Reviewer IDs: `[list of ORCIDs]`

**Artifacts / Acceptance criteria**
- `make test-local` runs all 14 tests with no network access and no live model
- CI workflow uses `MOCK_LLM=true` explicitly; no secrets committed
- Demo notebook produces `artifacts/audit_bundle_demo.zip`
- `validation_report_template.md` includes interpretive propositions count and reviewer IDs

---

# Phase 4 — Release package & publication

**Goal**: Prepare minimal release bundle for GitHub + OSF deposit.

**Tasks**

1. Create `RELEASE_GUIDE.md` covering:
   - GitHub release creation (tag, release notes, asset upload)
   - OSF deposit procedure: title, authors, abstract, keywords, license, embargo options
   - Required artifact references in OSF deposit: `pre_registration_doi`, `pass1_hash`, `audit_bundle_sha256`
   - How to upgrade `pass1_anchor.json` from `anchor_type: local` to `anchor_type: osf_doi`

2. Create `osf_deposit_example/osf_metadata_example.json` showing `pass1_hash`, `pre_registration_doi`, `strand_labels`, and `reviewer_ids` in an OSF deposit record.

3. Create `docs/methods_note.md` — companion text for dissertation/paper submissions:
   - Two-pass locked design and methodological rationale
   - How to interpret each artifact for examiners
   - Strand-specific quality criteria
   - Grounding verification and human evidence review
   - Interpretive propositions — what they are and how they are labelled

**Artifacts / Acceptance criteria**
- `RELEASE_GUIDE.md` and `osf_deposit_example/` present
- `docs/methods_note.md` present

---

# Phase 5 — Documentation, ethics & handover

**Goal**: Finalize user-facing docs and ethics-ready artefacts.

**Tasks**

1. Update `docs/lens.md` to include:
   - All 10 questions as a fillable template
   - Pointer to `examples/lens_example_locked.json` as a filled example

2. Ensure `artifacts/dpia_checklist.md` contains lawful basis, risk matrix, mitigations, DPO sign-off field, and notes linking `dpia_complete` and `dpia_document_path` to study config.

3. Ensure `artifacts/consent_snippets.md` contains:
   - Variant A: standard qualitative research (personal_non_sensitive)
   - Variant B: special category health/therapy data (GDPR Article 9 / BPS compliant)

4. Create `docs/supervisor_handover_checklist.md` — items to verify in the audit bundle:
   - Pre-registration DOI present and deposited before data collection
   - Pass 1 hash matches the anchor and anchor_type is osf_doi or repo_accession (not local)
   - Lens JSON locked with researcher_signature (ORCID) present
   - Stability report: theme stability score and Jaccard mean documented
   - All human_verdict fields complete (no nulls)
   - Hallucination rate documented
   - All interpretive propositions explicitly labelled with template sentence
   - Krippendorff's α reported with CI for PDA coding (if PDA strand active)
   - Member checking response records present (if IPA strand active)
   - DPIA signed record in artifact bundle
   - Reviewer IDs are ORCID or institutional username (no anonymous verdicts)

---

# Phase 6 — Optional enhancements (post-release)

**Goal**: Robustness and usability features for PhD/lab scale.

**Suggestions (toggleable via config)**

- **Alternate model robustness run**: add second model run using different local model; compute Jaccard overlap against primary.

- **PGP lens attestation** (document now, implement later):
  The simplest auditor-friendly enhancement. After `lock_lens()` completes:
  ```bash
  gpg --detach-sign --armor artifacts/lens_[run_id].json
  # Produces artifacts/lens_[run_id].json.asc
  # Store .asc file in artifacts/
  # Examiner verifies with: gpg --verify lens_[run_id].json.asc lens_[run_id].json
  ```
  Store public key at `artifacts/researcher_pubkey.asc`.
  Document this flow in `docs/methods_note.md` as an optional enhancement.
  In Phase 6 implementation: add `sign_lens_pgp(lens_path, gpg_keyid)` to `lens_dialogue.py`.

- **Streamlit evidence review UI**: replace `review_cli.py` with lightweight Streamlit app.

- **OSF auto-upload**: implement full `osf_uploader.py` with token-based API calls.

---

# Developer notes for the Copilot agent — absolute rules

1. **Read COPILOT_INSTRUCTIONS.md first.** Before touching any file, read this document. It contains the three absolute rules.

2. **Do not commit secrets.** Write `config/secrets.example.yaml`. All credentials via env vars or gitignored secrets file.

3. **Local-only.** WhisperX local only. Ollama REST API for LLM. No LangChain. No AssemblyAI.

4. **Follow artifact naming conventions.** Always write to `artifacts/`. Always compute SHA256 on write.

5. **Enforce the two-pass lock.** Pass 2 requires: pass1_anchor exists + hash matches + anchor_type NOT "local" + lens locked + researcher_signature non-null. Any failure prints structured error from `docs/error_codes.md` and exits with the correct code.

6. **OSF deposit is mandatory before Pass 2.** `anchor_type: local` is only valid immediately after Pass 1 completes. It must be upgraded to `osf_doi` or `repo_accession` before Pass 2 is allowed to run. The audit emitter also refuses to package if anchor_type is local.

7. **DPIA gate is a hard block.** If sensitivity == special_category: check for `artifacts/dpia_signed.json`. If absent: print ERR_DPIA_MISSING with action string and sys.exit(2). Never raise a bare Exception.

8. **Human verdicts are non-delegable.** `grounding_checker.py` only writes `evidence_review_*.json` with `human_verdict: null`. The `review_cli.py` is the only place verdicts are set. No AI process may set human_verdict to a non-null value.

9. **Strand labels are required, indexed fields on every artifact.** Valid values: `IPA`, `PDA`, `TA`, `quant`, `mixed`. Audit emitter validates this before packaging and exits with ERR_STRAND_MISSING (code 5) if any artifact is missing it.

10. **All errors use structured codes.** Format: `[ERROR_CODE] message\nAction: what to do`. Never raise bare Exception or print plain text errors. All codes and exit values defined in `docs/error_codes.md`.

11. **All CLI tools exit with shell return codes.** 0 = success. 1–5 = specific failure types (see error_codes.md). This enables CI and shell scripting to detect failures cleanly.

12. **Reviewer identity is required.** reviewer_id must be ORCID (https://orcid.org/...) or institutional username. Anonymous or null reviewer_id must be rejected by review_cli.py. Audit bundle includes reviewer_ids list.

13. **Extract prompts from docs.** Lens questions from `docs/lens.md`. Pass 1 and Pass 2 prompts from `docs/workflow.md`. If documents are missing, halt with ERR_PREFLIGHT_MISSING.

14. **Testing.** All 14 named tests must be implemented. MOCK_LLM=true. Tests pass with no network access and no live model.

---

# Acceptance checklist — masters-level release

- [ ] `COPILOT_INSTRUCTIONS.md` present and references the three absolute rules
- [ ] Two-pass sequence enforced programmatically with structured error codes and exit codes
- [ ] Pass 1 anchor deposited externally (anchor_type: osf_doi or repo_accession) before Pass 2 runs
- [ ] Audit emitter refuses to package if anchor_type is local
- [ ] DPIA gate blocks ingestion for special_category; exits with code 2
- [ ] Grounding verification produces per-claim evidence review records with human_verdict: null
- [ ] review_cli.py requires ORCID/institutional reviewer_id; auto-sets interpretive_proposition; exits 0 or 5
- [ ] interpretive_proposition template sentence stored in evidence_review JSON
- [ ] Stability testing: four passes; stability_report with Jaccard metrics generated
- [ ] Strand label indexed on every artifact; audit emitter validates
- [ ] Audit bundle includes: pre_registration_doi, pass1_hash, pass1_anchor_type, lens_hash, strand_labels, human_verdicts_complete, hallucination_rate, theme_stability_score, jaccard_mean, reviewer_ids, interpretive_propositions
- [ ] All 14 pytest tests pass with MOCK_LLM=true
- [ ] `make test-local` runs without network or live model
- [ ] CI workflow uses MOCK_LLM=true; no secrets committed
- [ ] Demo notebook produces `artifacts/audit_bundle_demo.zip`
- [ ] `docs/runbook.md` — 11 steps with error codes and resolution
- [ ] `docs/error_codes.md` — all codes, messages, actions, exit codes
- [ ] `RELEASE_GUIDE.md` and `osf_deposit_example/` present
- [ ] `docs/supervisor_handover_checklist.md` present
- [ ] `examples/dpia_signed.json` and `examples/lens_example_locked.json` present for CI
- [ ] No secrets committed anywhere
