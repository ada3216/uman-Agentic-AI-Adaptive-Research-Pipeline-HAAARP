# Agentic Human–AI Research Pipeline — Comprehensive Test Plan

**Version:** 1.1  
**Applies to:** Scaffold v2.1 and Copilot-built implementation  
**Purpose:** Defines what must be tested, how, and what acceptable outcomes look like across all pipeline stages. This document is the authority for test coverage decisions — if a behaviour is not described here, it is not considered tested.

**Changes in v1.1:** Added full schema validation coverage (T-SCH-06–10), reproducibility metadata tests (T-REP-01–04), local-only enforcement via import scanning (T-SEC-01–02), filesystem safety tests (T-FS-01–04), stronger OSF anchor validation (T-OSF-07), lens semantic integrity tests (T-LENS-08–09), additional grounding adversarial cases (T-GC-11–14), stability edge cases (T-SM-05–07), audit bundle completeness (T-AE-10–12), orchestrator failure states (T-ORCH-01–03), and encoding/format hygiene tests (T-FMT-01–04).

---

## Test philosophy

The pipeline's value is its governance architecture, not its LLM output quality. Tests therefore focus on whether the pipeline enforces its constraints correctly, not on whether the AI produces good qualitative analysis. LLM output quality is a future empirical question. Constraint enforcement is verifiable now.

Five testing layers:

1. **Unit tests** — each module's gate logic in isolation, all LLM calls mocked
2. **Integration tests** — stage-to-stage handoff, artifact naming, schema conformance
3. **End-to-end tests** — full pipeline run on synthetic data, producing a valid audit bundle
4. **Adversarial tests** — deliberate attempts to bypass governance constraints
5. **Security and hygiene tests** — import scanning, filesystem safety, encoding, format validation

All layers run with `MOCK_LLM=true`. No live model. No network. `make test-local` runs layers 1, 2, and 5. End-to-end execution follows the CLI flow documented in `docs/runbook.md`. Layer 4 runs via `pytest tests/test_adversarial.py`.

---

## Layer 1 — Unit tests

### 1.1 DPIA gate (`src/modules/dpia_gate.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-DPIA-01 | `sensitivity=special_category`, `dpia_signed.json` absent | `sys.exit(2)`, prints `ERR_DPIA_MISSING` with action string |
| T-DPIA-02 | `sensitivity=special_category`, file present but `dpia_complete: false` | `sys.exit(2)`, prints `ERR_DPIA_INVALID` |
| T-DPIA-03 | `sensitivity=special_category`, file present but `decision != "approved"` | `sys.exit(2)`, prints `ERR_DPIA_INVALID` |
| T-DPIA-04 | `sensitivity=special_category`, file present but `dpo_name` null | `sys.exit(2)`, prints `ERR_DPIA_INVALID` |
| T-DPIA-05 | `sensitivity=personal_non_sensitive` | Returns `None`, no exit |
| T-DPIA-06 | `sensitivity=public_text` | Returns `None`, no exit |
| T-DPIA-07 | `sensitivity="normal"` (invalid value) | Caught by orchestrator as `ERR_SENSITIVITY_UNKNOWN`, `sys.exit(1)` |
| T-DPIA-08 | `sensitivity=special_category`, valid signed DPIA | Returns `None`, no exit, no message |

**Acceptance:** All 8 pass. T-DPIA-07 must be caught in orchestrator, not dpia_gate.

---

### 1.2 Pass 1 runner (`src/agent/pass1_runner.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-P1-01 | `strand` not set in config | `sys.exit(5)`, prints `ERR_STRAND_MISSING` |
| T-P1-02 | `pre_registration_doi: null` | Runs successfully, prints `WARN_PREREG_MISSING`, does NOT exit |
| T-P1-03 | Successful run | Writes `pass1_output_[dataset_id].json` with `strand` field present |
| T-P1-04 | Successful run | Writes `pass1_anchor_[dataset_id].json` with `anchor_type: local` |
| T-P1-05 | Successful run | `pass1_anchor.pass1_hash` == SHA256 of `pass1_output` file |
| T-P1-06 | Successful run | `prompt_osf_deposit()` is called after output written |
| T-P1-07 | Mock LLM returns malformed JSON | Error caught gracefully; does not write partial artifact |

**Acceptance:** All 7 pass.

---

### 1.3 Pass 2 gate checks (`src/agent/pass2_runner.py` — `_gate_check`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-P2-01 | `pass1_anchor` file absent | `sys.exit(3)`, prints `ERR_PASS1_ANCHOR_MISSING` |
| T-P2-02 | `anchor_type: local` | `sys.exit(3)`, prints `ERR_PASS1_ANCHOR_LOCAL` with OSF instructions |
| T-P2-03 | `pass1_hash` does not match file SHA256 | `sys.exit(3)`, prints `ERR_PASS1_HASH_MISMATCH` |
| T-P2-04 | Lens file absent | `sys.exit(4)`, prints `ERR_LENS_NOT_LOCKED` |
| T-P2-05 | Lens present but `locked: false` | `sys.exit(4)`, prints `ERR_LENS_NOT_LOCKED` |
| T-P2-06 | Lens locked but `researcher_signature: null` | `sys.exit(4)`, prints `ERR_LENS_SIGNATURE_MISSING` |
| T-P2-07 | `sensitivity=special_category`, `dpia_signed.json` absent | `sys.exit(2)`, prints `ERR_DPIA_MISSING` |
| T-P2-08 | All gates pass (`anchor_type: osf_doi`, lens locked with signature, DPIA valid) | Proceeds to stability loop; returns `dict` with output paths |
| T-P2-09 | `anchor_type: repo_accession` | Treated identically to `osf_doi`; proceeds |

**Acceptance:** All 9 pass. Ordering matters: gate checks must run in sequence a→f and stop at first failure.

---

### 1.4 Lens dialogue (`src/modules/lens_dialogue.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-LENS-01 | `lock_lens()` called with `researcher_id: null` | `sys.exit(4)`, prints `ERR_LENS_SIGNATURE_MISSING` |
| T-LENS-02 | `lock_lens()` called with `researcher_id: "anonymous"` | `sys.exit(4)` |
| T-LENS-03 | `lock_lens()` called with valid ORCID | Sets `locked: true`, writes `researcher_signature`, writes `signature_timestamp_utc` |
| T-LENS-04 | `lock_lens()` called with valid ORCID | Computes `lens_summary_hash` as SHA256 of complete file |
| T-LENS-05 | `LENS_QUESTIONS` list | Contains exactly 10 questions |
| T-LENS-06 | `LENS_QUESTIONS` list | Questions NOT returned as responses — list contains strings, not dicts with empty answer fields |
| T-LENS-07 | `lock_lens()` called on already-locked lens | Either idempotent (re-locks with new timestamp) or prints warning — must NOT corrupt the record |

**Acceptance:** All 7 pass. T-LENS-05 is a structural check that Copilot correctly extracted 10 questions from `docs/lens.md`.

---

### 1.5 Grounding checker (`src/modules/grounding_checker.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-GC-01 | Claim with 0 verifiable segments | `support_strength: "none"`, `hallucination_count += 1` |
| T-GC-02 | Claim with 1 segment, 1 participant | `support_strength: "weak"`, flag `low_evidence_count` |
| T-GC-03 | Claim with ≥3 segments, ≥3 participants | `support_strength: "strong"` |
| T-GC-04 | Claim with only lens vocabulary extracts | Flag `lens_vocabulary_only` |
| T-GC-05 | Broad claim with 1 excerpt | Flag `overgeneralisation` |
| T-GC-06 | `claim_text` in evidence_review output | Exactly matches `claim_text` in pass2_output — not modified |
| T-GC-07 | All evidence_review records | `human_verdict: null` on creation |
| T-GC-08 | `strand` field absent from pass2_output | `sys.exit(5)`, prints `ERR_STRAND_MISSING` |
| T-GC-09 | Audio segment with timestamp anchor | Verification flag `prosody_anchor_unverified` set if anchor not found in transcript |
| T-GC-10 | Video segment with timecode anchor | Verification flag `timecode_anchor_unverified` set if anchor not found |

**Acceptance:** All 10 pass. T-GC-06 is critical — immutability of claims.

---

### 1.6 Review CLI (`src/tools/review_cli.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-RC-01 | `REVIEWER_ID` env var not set, input empty | `sys.exit(5)`, prints rejection message |
| T-RC-02 | `REVIEWER_ID = "anonymous"` | `sys.exit(5)` |
| T-RC-03 | No pending records | `sys.exit(0)`, prints completion message |
| T-RC-04 | Verdict `accept_with_revision`, no notes provided | Re-prompts until notes supplied; does not proceed without |
| T-RC-05 | Verdict `reject`, no notes provided | Re-prompts until notes supplied |
| T-RC-06 | `accept` verdict, `support_strength: "weak"` | Sets `interpretive_proposition: true`, writes `write_up_template` string |
| T-RC-07 | `accept` verdict, `support_strength: "none"` | Same as T-RC-06 |
| T-RC-08 | All verdicts complete, no rechecks | `sys.exit(0)` |
| T-RC-09 | One or more `recheck` verdicts remain | `sys.exit(5)` |
| T-RC-10 | Completed verdict record | Contains `reviewer_id`, `reviewer_role`, `timestamp_utc` (all non-null) |

**Acceptance:** All 10 pass.

---

### 1.7 Audit emitter (`src/modules/audit_emitter.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-AE-01 | `anchor_type: local` | `sys.exit(5)`, prints `ERR_ANCHOR_LOCAL_AT_BUNDLE` |
| T-AE-02 | Any `evidence_review` has `human_verdict: null` | `sys.exit(5)`, prints `ERR_VERDICT_INCOMPLETE`, lists pending files |
| T-AE-03 | Any artifact missing `strand` field | `sys.exit(5)`, prints `ERR_STRAND_MISSING` |
| T-AE-04 | `pre_registration_doi: null` | Logs `WARN_PREREG_MISSING`, does NOT block packaging |
| T-AE-05 | All validations pass | Produces `audit_bundle_[run_id].zip` |
| T-AE-06 | Completed bundle | Metadata JSON contains: `pre_registration_doi`, `pass1_hash`, `pass1_anchor_type`, `lens_hash`, `strand_labels`, `human_verdicts_complete`, `hallucination_rate`, `theme_stability_score`, `jaccard_mean`, `reviewer_ids`, `interpretive_propositions` |
| T-AE-07 | Completed bundle | `pass1_anchor_type` is `osf_doi` or `repo_accession` — NOT `local` |
| T-AE-08 | Completed bundle | `bundle_sha256` == SHA256 of the zip file |
| T-AE-09 | Completed bundle | `sys.exit(0)` |

**Acceptance:** All 9 pass.

---

### 1.8 OSF uploader (`src/modules/osf_uploader.py`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-OSF-01 | `--anchor` path absent | `sys.exit(3)`, prints `ERR_PASS1_ANCHOR_MISSING` |
| T-OSF-02 | `--anchor` valid, `--doi` provided | Updates `anchor_type` to `osf_doi`, writes `anchor_value` = doi, `sys.exit(0)` |
| T-OSF-03 | `--anchor` valid, `--doi` contains `osf.io` | `anchor_type: osf_doi` |
| T-OSF-04 | `--anchor` valid, `--doi` is accession (no `osf.io`) | `anchor_type: repo_accession` |
| T-OSF-05 | No token, no `--doi` | Prints manual deposit instructions, `sys.exit(0)` (not an error) |
| T-OSF-06 | After successful upgrade | `pass1_anchor.json` on disk has updated `anchor_type` and `anchor_value` |

**Acceptance:** All 6 pass.

---

### 1.9 Stability metrics (`pass2_runner.compute_stability_metrics`)

| Test ID | Condition | Expected outcome |
|---------|-----------|-----------------|
| T-SM-01 | 4 identical outputs | `theme_stability_score: 1.0`, `jaccard_mean: 1.0` |
| T-SM-02 | 4 completely different outputs | `theme_stability_score: 0.0`, `jaccard_mean: 0.0` |
| T-SM-03 | Any run output | `stability_report` contains all required keys: `theme_stability_score`, `jaccard_mean`, `jaccard_pairs`, `lens_amplification_index`, `unstable_themes` |
| T-SM-04 | Themes in <2/3 runs | Listed in `unstable_themes` |

**Acceptance:** All 4 pass. T-SM-01 and T-SM-02 are boundary checks.

---

## Layer 2 — Integration tests

These test handoffs between modules — artifact naming conventions, schema conformance, and stage sequencing.

### 2.1 Artifact naming

| Test ID | What is checked |
|---------|----------------|
| T-INT-01 | De-identified output files are named `deidentified_[participant_code]_[session].json` — no other pattern accepted by analysis modules |
| T-INT-02 | `pass1_output_[dataset_id].json` — dataset_id present and consistent with anchor |
| T-INT-03 | `pass2_output_[label]_[dataset_id].json` — all four runs present after Pass 2 completes |
| T-INT-04 | `evidence_review_[claim_id]_[dataset_id].json` — one file per claim |
| T-INT-05 | `audit_bundle_[run_id].zip` and matching `audit_bundle_[run_id].json` — both present |

### 2.2 Schema conformance

| Test ID | What is checked |
|---------|----------------|
| T-SCH-01 | All `pass1_output` files validate against `artifacts/audit_schema.json` |
| T-SCH-02 | All `evidence_review` files validate against `src/schemas/evidence_review_schema.json` |
| T-SCH-03 | `strand` field present and value in `{"IPA", "PDA", "TA", "quant", "mixed"}` on every artifact |
| T-SCH-04 | `human_verdict` in evidence_review is either `null` (pre-review) or a complete object with `verdict`, `reviewer_id`, `reviewer_role`, `timestamp_utc` |
| T-SCH-05 | `reviewer_id` is non-null, non-anonymous in any completed verdict record |
| T-SCH-06 | `pass1_anchor.json` validates against `src/schemas/anchor_schema.json` — `anchor_type` enum, `strand` present, `pass1_hash` is 64-char hex |
| T-SCH-07 | `lens_*.json` validates against `src/schemas/lens_schema.json` — `locked` boolean, `researcher_signature` non-null when locked, `lens_summary_hash` present |
| T-SCH-08 | `stability_report_*.json` validates against `src/schemas/stability_schema.json` — all five required metric keys present (values may be null for mocked runs) |
| T-SCH-09 | `audit_bundle_*.json` metadata validates against bundle section of `artifacts/audit_schema.json` — `pass1_anchor_type` must be `osf_doi` or `repo_accession`, not `local` |
| T-SCH-10 | `dpia_signed.json` validates against `src/schemas/dpia_schema.json` — `dpo_sign_off` complete, `dpia_complete: true`, `sensitivity_class` present |

**Schema creation requirement (T-SCH-06–10):** Copilot must create `anchor_schema.json`, `lens_schema.json`, `stability_schema.json`, and `dpia_schema.json` in `src/schemas/` during Phases 2a/2b, alongside the modules that produce those artifacts. Each schema should `$ref` shared definitions in `artifacts/audit_schema.json`. Without these schemas, field name drift between phases will go undetected.

### 2.3 Hash integrity

| Test ID | What is checked |
|---------|----------------|
| T-HASH-01 | SHA256 in `pass1_anchor` matches recomputed hash of `pass1_output` file |
| T-HASH-02 | `bundle_sha256` in metadata matches recomputed hash of zip file |
| T-HASH-03 | `lens_summary_hash` changes if lens record is modified after locking (tamper detection) |

### 2.4 Reproducibility metadata

| Test ID | What is checked |
|---------|----------------|
| T-REP-01 | `pass1_output` contains `model_config` block: `model_name`, `temperature`, `seed`, `ollama_version` |
| T-REP-02 | `pass2_output` (all four runs) contains `model_config` block with `seed` matching run label |
| T-REP-03 | `audit_bundle` metadata includes `model_name`, `temperature`, `ollama_version` |
| T-REP-04 | Two runs with identical seed and mocked LLM produce byte-identical `pass1_output` content (determinism check for mocked path) |

**Note on `model_sha`:** Hashing Ollama model files is not reliably achievable across platforms. Record `model_name` and `ollama_version` instead. Flag `model_sha` as a Phase 6 optional enhancement.

### 2.5 Stage sequencing

| Test ID | What is checked |
|---------|----------------|
| T-SEQ-01 | Orchestrator refuses to call `run_pass2` if `pass1_anchor` absent |
| T-SEQ-02 | Orchestrator refuses to call `emit_audit_bundle` if any `evidence_review` has `human_verdict: null` |
| T-SEQ-03 | `run_lens_dialogue` can be called before or after `run_pass1`, but `lock_lens` cannot be called before `run_pass1` completes (anchor path check) |
| T-SEQ-04 | `grounding_checker` can only be called after `pass2` has produced output for the same `dataset_id` |

**Running layer 2:** `make test-local` should cover most of these if test fixtures are correctly structured. Schema validation tests require a small JSON schema validator (e.g., `jsonschema` Python package) added to test dependencies.

---

## Layer 2b — Security and local-only enforcement tests

These run as part of `make test-local`. They verify the local-only constraint is enforced in code, not just in policy.

### Import scanning

| Test ID | What is checked |
|---------|----------------|
| T-SEC-01 | `requirements.txt` contains none of the banned packages: `openai`, `anthropic`, `langchain`, `llamaindex`, `cohere`, `replicate`, `huggingface_hub`, `assemblyai`, `deepgram`, `boto3`, `google-cloud-storage` |
| T-SEC-02 | Source tree scan (`src/`) contains no `import` or `from` statements for banned packages — checked via `ast.parse` or `grep` in test |

**Implementation:** T-SEC-01 and T-SEC-02 should be implemented as a single test file `tests/test_security.py` that parses `requirements.txt` and walks `src/` Python files. This runs in CI without needing a live environment.

**Not included:** Socket-level blocking during tests. This is technically achievable via `pytest-socket` but introduces false positives when test fixtures use file I/O. The import scan covers the real risk without the fragility.

### Filesystem safety

| Test ID | What is checked |
|---------|----------------|
| T-FS-01 | `dataset_id` containing `../` is rejected with `ERR_DATASET_INVALID` before any file is written |
| T-FS-02 | `dataset_id` containing `/`, `\`, or null bytes is rejected |
| T-FS-03 | Pipeline refuses to overwrite an existing `pass1_output_[dataset_id].json` without `--force` flag — prevents accidental collision |
| T-FS-04 | Duplicate `dataset_id` in same run triggers `ERR_DATASET_COLLISION` |
| T-FS-05 | All artifact writes go to `artifacts/` — no file written outside repo root (checked by asserting path starts with resolved repo root) |

**Note on T-FS-03:** Atomic writes (write to temp file, then `os.rename`) are already required by the guardrails. T-FS-03 adds the overwrite protection on top — a separate check that the target path does not already exist before the temp write begins.

### OSF anchor integrity

| Test ID | What is checked |
|---------|----------------|
| T-OSF-07 | `anchor_value` must match one of: DOI regex `^10\.\d{4,9}\/.+$` or OSF URL regex `^https://osf\.io/[a-z0-9]{5,}` or institutional repo URL `^https://` — plain strings and null rejected |
| T-OSF-08 | `anchor_type: osf_doi` requires `anchor_value` to match OSF URL pattern |
| T-OSF-09 | `anchor_type: repo_accession` requires `anchor_value` to be non-null and non-empty string |

### Format and encoding hygiene

| Test ID | What is checked |
|---------|----------------|
| T-FMT-01 | All JSON artifacts written by the pipeline are valid UTF-8 (no byte-order marks, no latin-1 escapes) |
| T-FMT-02 | All `timestamp_utc` fields match ISO-8601 with UTC offset: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$` or `+00:00` suffix |
| T-FMT-03 | All `timestamp_utc` fields are UTC — timezone offset must be `Z` or `+00:00`, never a local offset |
| T-FMT-04 | `participant_code` fields match pattern `^P\d{2,3}$` (or configurable regex) — free-form strings rejected |

---

## Layer 3 — End-to-end test (demo notebook)

`notebooks/demo_pipeline.ipynb` must run to completion on synthetic fixtures without a live model. All LLM calls are replaced with fixture responses.

### 3.1 Setup

- Copy `tests/fixtures/` into working directory
- Set `MOCK_LLM=true`
- Use `examples/dpia_signed.json` as the signed DPIA
- Use `examples/lens_example_locked.json` as the locked lens
- Use `synthetic_pass1_anchor.json` with `anchor_type: osf_doi`

### 3.2 Steps and expected outcomes

| Step | Expected artifact produced | Checks |
|------|---------------------------|--------|
| Ingest | `artifacts/raw_archive/[ts]_SYNTH_[file]` | File exists, SHA256 recorded |
| De-identify | `artifacts/deidentified_P01_session1.json` | Naming pattern correct; no real names in output |
| Pass 1 | `artifacts/pass1_output_SYNTH001.json` | Contains `strand: IPA`, `pass1_themes` non-empty |
| Pass 1 anchor | `artifacts/pass1_anchor_SYNTH001.json` | `anchor_type: local` initially |
| OSF deposit (mocked) | Anchor updated | `anchor_type: osf_doi`, `anchor_value` non-null |
| Lens dialogue (fixture) | `artifacts/lens_DEMO.json` | `locked: true`, `researcher_signature` non-null |
| Pass 2 | 4 output files + `stability_report_SYNTH001.json` | All 4 present; stability report has all required keys |
| Grounding | `claim_evidence_table_SYNTH001.json` + `evidence_review_CL*.json` | All `human_verdict: null`; at least 1 flag present |
| Human review (automated in notebook) | Updated `evidence_review_*.json` | All verdicts non-null; `reviewer_id` = test ORCID |
| Audit bundle | `artifacts/audit_bundle_DEMO.zip` + `audit_bundle_DEMO.json` | ZIP valid; metadata contains all required fields; `sys.exit(0)` |

### 3.3 Acceptance criteria for end-to-end

- Notebook runs from top to bottom with no uncaught exceptions
- `audit_bundle_DEMO.zip` is produced and SHA256 verified
- Metadata JSON passes schema check
- `human_verdicts_complete: true`
- `pass1_anchor_type: osf_doi` (not local)
- At least one claim has `interpretive_proposition: true` (from synthetic weak-evidence claim CL002)

---

## Layer 4 — Negative / adversarial tests

Tests that deliberately try to break governance constraints. These are the most important for methodological defensibility.

| Test ID | Attack | Expected defence |
|---------|--------|-----------------|
| T-ADV-01 | Manually edit `pass1_output` after hashing, then run Pass 2 | `ERR_PASS1_HASH_MISMATCH`, `sys.exit(3)` |
| T-ADV-02 | Set `anchor_type: osf_doi` without depositing (manually edit anchor) | Audit emitter still validates anchor_value non-null — flag if null |
| T-ADV-03 | Set `human_verdict` field directly in JSON (bypassing review_cli) | Audit emitter checks `reviewer_id` non-null and non-anonymous — catches null reviewer |
| T-ADV-04 | Run Pass 2 before lens is locked | `ERR_LENS_NOT_LOCKED`, `sys.exit(4)` |
| T-ADV-05 | Ingest special_category data before DPIA signed | `ERR_DPIA_MISSING`, `sys.exit(2)` |
| T-ADV-06 | Set `sensitivity: normal` in config | `ERR_SENSITIVITY_UNKNOWN`, `sys.exit(1)` |
| T-ADV-07 | Emit audit bundle without completing all verdicts | `ERR_VERDICT_INCOMPLETE`, `sys.exit(5)` |
| T-ADV-08 | Emit audit bundle with local anchor | `ERR_ANCHOR_LOCAL_AT_BUNDLE`, `sys.exit(5)` |

### Extended adversarial — grounding checker

| Test ID | Attack | Expected defence |
|---------|--------|-----------------|
| T-GC-11 | Claim cites participant code that does not appear in transcript (e.g. `P99`) | Segment flagged `excerpt_not_found`; `hallucination_count` incremented |
| T-GC-12 | Claim cites segment ID whose timestamp is outside transcript duration | Flag `prosody_anchor_unverified` or `timecode_anchor_unverified` |
| T-GC-13 | Same segment ID cited multiple times for same claim | Deduplicated — counted as one excerpt, not inflating `support_count` |
| T-GC-14 | Segment ID with malformed timestamp format (e.g. `P01_session1_Tabcde_Tfghij`) | Flag `prosody_anchor_unverified`; does not crash |

### Extended adversarial — lens semantic integrity

| Test ID | Attack | Expected defence |
|---------|--------|-----------------|
| T-LENS-08 | Locked lens file has fewer than 10 questions in `dialogue_responses` | Validation check on lock: `sys.exit(4)` with message indicating incomplete dialogue |
| T-LENS-09 | Any `dialogue_responses` entry has empty string response | Flag `incomplete_response` in lens record; proceed with warning but note in audit bundle |

**Note on T-LENS-09:** Exact text matching against `docs/lens.md` is not enforced — question wording may legitimately change if `lens.md` is updated. Check *count* (10) and *non-empty responses*, not exact phrasing.

### Extended adversarial — stability metrics

| Test ID | Edge case | Expected behaviour |
|---------|-----------|-------------------|
| T-SM-05 | All four Pass 2 runs return zero themes | `theme_stability_score: 0.0`, `jaccard_mean: 0.0`, `unstable_themes: []` — does not crash or divide by zero |
| T-SM-06 | One of the four run output files is missing | `ERR_PASS2_RUN_MISSING` with message identifying which run; stability report not written |
| T-SM-07 | Stability report output | Theme ordering is deterministic across identical inputs (sorted by theme_id) — not random |

### Extended adversarial — audit bundle completeness

| Test ID | What is checked |
|---------|----------------|
| T-AE-10 | Bundle zip contains every file listed in `artifact_manifest` — no manifest entry without corresponding file in zip |
| T-AE-11 | Bundle zip contains no files matching `artifacts/raw_archive/` path — raw participant data must never enter the bundle |
| T-AE-12 | File list inside zip matches `artifact_manifest` exactly — no extra files, no missing files |

### Extended adversarial — orchestrator failure states

| Test ID | Failure scenario | Expected behaviour |
|---------|-----------------|-------------------|
| T-ORCH-01 | Pipeline run is interrupted mid-Pass-2 (simulated by truncating output file) | On resume, detects incomplete output (invalid JSON or missing required fields) and re-runs Pass 2 rather than proceeding with corrupt output |
| T-ORCH-02 | Process crash mid-Pass-2 | `pass1_output` and `pass1_anchor` are unchanged — atomic writes ensure no partial overwrite |
| T-ORCH-03 | Re-run with same `dataset_id` after successful Pass 1 | Existing `pass1_output` and `pass1_anchor` detected; prompts researcher before overwriting; `--force` required to proceed |

**All adversarial tests must result in the expected error and exit code.** If any adversarial test reaches a success state, the governance constraint it tests is broken.

---

## What is NOT tested here (deliberately out of scope)

The following are deliberately out of scope for this test plan and should be addressed in future empirical studies:

- **LLM output quality** — whether Pass 1 and Pass 2 produce good IPA or PDA analysis is an empirical research question, not a CI question
- **Whisper transcription accuracy** — out of scope for unit/integration testing
- **OSF API connectivity** — integration tests use mocked deposit; real API behaviour is an infrastructure concern
- **Human reviewer quality** — the pipeline enforces that a human reviewed every claim; it cannot assess the quality of those reviews
- **Stability metric thresholds** — what constitutes an acceptable Jaccard mean is a methodological judgement for the researcher, not a pipeline constraint

---

## Test execution summary

| Layer | Command | When to run |
|-------|---------|------------|
| 1 + 2 (unit + integration) | `make test-local` | Every commit |
| 2b (security + hygiene) | `make test-local` (included automatically) | Every commit |
| 1–2 CI | `make test` (auto via CI workflow) | Every push/PR |
| 3 (end-to-end) | `jupyter nbconvert --to notebook --execute notebooks/demo_pipeline.ipynb` | Before release tagging |
| 4 (adversarial) | `pytest tests/test_adversarial.py -v` | Before release tagging |

---

## Minimum passing bar for masters-level release

All Layer 1 unit tests pass across 9 modules.
All Layer 2 integration tests pass including all 10 schema validation tests (T-SCH-01–10).
Layer 2b security tests pass: no banned imports in source tree, no banned packages in requirements.txt.
Layer 2b filesystem and format tests pass.
Layer 3 end-to-end produces a valid `audit_bundle_DEMO.zip` with `pass1_anchor_type: osf_doi`.
All Layer 4 adversarial tests result in correct error and exit code — including extended grounding, lens, stability, bundle, and orchestrator tests.
`make test-local` exits 0 with no live model and no network.

**Note on test count:** The test conditions in this document map to more than 100 individual assertions when fully implemented. The count per section header is a grouping convenience — do not use section counts to assess coverage completeness. Use this document's full table as the authority.
