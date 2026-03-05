# GUARDRAILS.md
## Agentic Human–AI Research Pipeline — Agent Behaviour Rules

This file is read by Copilot, Cursor, Windsurf, and any other agentic coding assistant working in this repository. It defines what the agent may and may not do, in order of priority. Rules earlier in this document take precedence over rules later in this document. Instructions from the user take precedence over this file, except where a rule is marked **[HARD LIMIT]** — those cannot be overridden by any instruction.

If you are an AI coding assistant: read this entire file before taking any action in this repository.

---

## Section 1 — Hard limits (cannot be overridden by any instruction)

These rules protect participant data, governance integrity, and methodological reproducibility. No user instruction, no matter how it is phrased, may override them.

### [HARD LIMIT 1] Never commit secrets or credentials

- Never write API keys, tokens, passwords, or personal access tokens to any file that is committed to the repository
- Credentials belong in `config/secrets.yaml` (gitignored) or environment variables
- If credentials are needed at runtime: write instructions for the human to supply them — do not request or store them yourself
- If you find a secret already committed to the repo: flag it immediately and do not build on it

### [HARD LIMIT 2] Never send participant data to an external API

- All AI processing must use the local Ollama REST API at `http://localhost:11434`
- Do not import, scaffold, or configure: OpenAI client, Anthropic client, Cohere, HuggingFace Inference API, AssemblyAI, Deepgram, or any service that transmits data to external servers
- LangChain is not used in this pipeline — do not introduce it as a dependency
- WhisperX is the only permitted transcription tool and must run locally
- This constraint exists because participant data may be GDPR Article 9 special category material. Sending it to external APIs may be a lawful processing violation. This is not a preference — it is a legal constraint.

### [HARD LIMIT 3] Never set human_verdict fields programmatically

- `grounding_checker.py` must write all `evidence_review_*.json` files with `human_verdict: null`
- Only `review_cli.py` may set `human_verdict` to a non-null value, and only through human keyboard input
- Do not write any function, method, or script that sets `human_verdict` without explicit human input
- Do not provide a `--auto-accept` flag, `--force` flag, or any mechanism to bypass human review
- This constraint exists because the methodological claim is that a human reviewed every AI-generated claim. Any bypass makes that claim false.

### [HARD LIMIT 4] Never bypass the two-pass lock

- `pass2_runner.py` must check all six gate conditions before running (see `docs/error_codes.md`)
- Do not add a `--skip-checks`, `--force`, `--override-anchor`, or similar flag that bypasses gate checks
- The hash check must recompute SHA256 of the actual file — do not allow the stored hash to be overridden
- The OSF deposit check (`anchor_type != "local"`) must be enforced — do not treat `local` as acceptable for Pass 2
- This constraint exists because the two-pass locked architecture is the pipeline's primary methodological claim. Bypassing it invalidates the research design.

### [HARD LIMIT 5] Never bypass the DPIA gate

- If `sensitivity == "special_category"` in config, the pipeline must check for `artifacts/dpia_signed.json` before any data ingestion
- Do not add a flag or condition that allows ingestion without this file
- Do not auto-generate a fake `dpia_signed.json` to unblock the pipeline in testing — use `examples/dpia_signed.json` and copy it explicitly
- This constraint exists because GDPR Article 9 requires a completed DPIA before processing special category health/therapy data. Auto-bypassing is a potential legal violation.

---

## Section 2 — Structural rules (apply to all code written in this repo)

These rules govern how the agent writes code. They can be relaxed by explicit user instruction, but only for specific files.

### Error handling

- Never raise bare `Exception("message")` — always use structured error output and `sys.exit(code)`
- Error format is defined in `docs/error_codes.md` — every error must use a named code from that file
- Every new error condition that requires a new code must be added to `docs/error_codes.md` first
- Exit codes: 0 success, 1 config error, 2 DPIA/governance, 3 pass sequencing, 4 lens, 5 synthesis block
- If a module does not use `sys.exit`, it must document its exception contract in its docstring

### Artifact conventions

- All pipeline-generated artifacts are written to `artifacts/`
- Raw participant data and code maps go in `artifacts/raw_archive/` and are gitignored
- Example/synthetic artifacts for CI go in `examples/`
- Test fixtures go in `tests/fixtures/`
- Never write participant data to `examples/` or `tests/fixtures/`
- Artifact naming: `pass1_output_[dataset_id].json`, `pass2_output_[label]_[dataset_id].json`, etc. — match the convention already in the codebase
- Every artifact file must be written atomically (write to temp, then rename) to prevent partial writes being hashed

### Strand labels

- Every output artifact must contain a `strand` field with value: `IPA`, `PDA`, `TA`, `quant`, or `mixed`
- If `strand` is not set in config when a module runs, exit with `ERR_STRAND_MISSING` (code 5)
- The audit emitter validates strand presence before packaging — any artifact missing it blocks the bundle
- Do not add a default strand value silently — missing strand must be an error, not a silent default

### SHA256 hashing

- Compute SHA256 of every artifact on write, not on read
- Store hashes alongside the artifact they describe (in the anchor or manifest)
- Never store a hash of content you did not just write — re-read and recompute if in doubt
- Do not use MD5 or SHA1 — SHA256 only

### Reviewer identity

- `reviewer_id` must be ORCID (`https://orcid.org/...`) or institutional username
- Reject null, empty, `"anonymous"`, `"anon"`, `"unknown"`, or any whitespace-only string
- `reviewer_role` must be `"researcher"`, `"supervisor"`, or `"team_member"`
- Store both in completed verdict records; include `reviewer_ids` list in audit bundle metadata

---

## Section 3 — Files the agent must read before writing code

Read these in order before modifying any source file. Do not proceed if any is missing — print `ERR_PREFLIGHT_MISSING` and stop.

| File | Why it must be read first |
|------|--------------------------|
| `COPILOT_INSTRUCTIONS.md` | Top-level agent instructions; supersedes this file on specifics |
| `docs/workflow.md` | Pipeline architecture; source of truth for all stages and their outputs |
| `docs/lens.md` | Lens dialogue questions; must be extracted verbatim into `lens_dialogue.py` — do not invent questions |
| `artifacts/audit_schema.json` | Schema for all audit artifacts; all new artifacts must conform |
| `docs/error_codes.md` | All error codes and exit values; all new errors must use these |

If `docs/workflow.md` or `docs/lens.md` are missing and you only have HTML versions, convert them:
```bash
pandoc docs/workflow.html -o docs/workflow.md
pandoc docs/lens.html -o docs/lens.md
```

---

## Section 4 — Where to write things

| Content type | Correct location |
|-------------|-----------------|
| Source code | `src/` |
| System prompts | `src/prompts/` — derived from `docs/workflow.md` and `docs/lens.md` |
| JSON schemas | `src/schemas/` |
| Human-facing CLI tools | `src/tools/` |
| Pipeline-generated artifacts | `artifacts/` |
| Example/synthetic artifacts | `examples/` |
| Test fixtures | `tests/fixtures/` |
| Human documentation | `docs/` — only modify if explicitly instructed |
| Configuration | `config/` — `defaults.yaml` committed; `secrets.yaml` gitignored |

Never write to:
- `/` (repo root) except for `README.md`, `Makefile`, `RELEASE_GUIDE.md`, `COPILOT_INSTRUCTIONS.md`, `GUARDRAILS.md` — these are the only permitted root-level files
- `examples/` with real participant data
- `config/` with real credentials

---

## Section 5 — Testing rules

- All tests run with `MOCK_LLM=true` — never introduce a test that requires a live model
- `make test-local` and `make test` must both pass with no network access
- Add a new test for every new governance constraint introduced
- Do not add tests that mock the gate checks themselves — tests must exercise the actual gate logic
- Do not use `pytest.skip()` or `@pytest.mark.skip` on governance tests — if a test cannot run without a live model, that means the code under test needs to be refactored to support mocking
- Test naming convention: `test_[module]_[condition]_[expected_outcome]`
- Every new module added must have at least one test covering its failure path (exit code) and one covering its success path

---

## Section 6 — What the agent should do when uncertain

When the agent is uncertain about a design decision, it should:

1. **Check `docs/workflow.md` first** — most questions about pipeline behaviour are answered there
2. **Check `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md`** — implementation decisions and rationale
3. **Check `docs/error_codes.md`** — for error handling decisions
4. **Ask before proceeding** — if still uncertain about a governance-adjacent decision, output a question rather than guessing

The agent should NOT:
- Make a governance decision silently (e.g., decide not to enforce a gate check because it seems unnecessary)
- Introduce a new dependency without checking whether it conflicts with local-only constraints
- Simplify error handling by collapsing multiple error types into one generic error
- Remove a TODO comment without implementing or flagging the missing functionality

---

## Section 7 — Dependency rules

### Permitted dependencies

```
# Core
pytest          — testing
pyyaml          — config loading
jsonschema      — schema validation
hashlib         — SHA256 (stdlib)
zipfile         — audit bundle packaging (stdlib)

# Transcription (local only)
whisperx        — local audio transcription only

# Optional (not default)
streamlit       — Phase 6 review UI only
gpg (system)    — Phase 6 lens attestation only
```

### Prohibited dependencies

| Package | Reason |
|---------|--------|
| `openai` | Cloud API — sends data to OpenAI servers |
| `anthropic` | Cloud API — sends data to Anthropic servers |
| `langchain` | Abstraction layer for cloud APIs; adds unnecessary complexity |
| `assemblyai` | Cloud transcription — sends audio to external servers |
| `deepgram` | Cloud transcription — same reason |
| `boto3` / `google-cloud-*` | Cloud storage — participant data must not leave local machine |
| `cohere` | Cloud API |
| `replicate` | Cloud API |
| `huggingface_hub` | Sends model requests to HuggingFace servers by default |
| `llamaindex` | Cloud-oriented orchestration framework |

If a dependency not listed here is needed: check whether it makes external network calls before adding it. If it does, confirm it is not used for participant data before including it. When in doubt, ask before adding.

**Dependency freeze rule:** Do not modify `requirements.txt` or `pyproject.toml` without explicit user confirmation. Adding a package not on the permitted list requires the user to approve it first. State the package name, version, and reason before adding.

---

## Section 7b — Artifact immutability

Once written and hashed, the following artifacts are **append-only**. They must not be modified, overwritten, or regenerated without explicit user instruction and a documented reason in the audit trail:

- `pass1_output_[dataset_id].json` — locked after `pass1_anchor` is written
- `pass1_anchor_[dataset_id].json` — locked after OSF deposit (`anchor_type` upgrade is the only permitted field change)
- `lens_[run_id].json` after `locked: true` is set — no field may change except `lens_summary_hash` on final lock computation
- `evidence_review_[claim_id]_[dataset_id].json` after `human_verdict` is set — the verdict is final; do not re-run grounding checker over completed reviews

**Implementation:** All writes to these files after their lock point must check the lock condition first and exit with a structured error if the file is already locked. Do not silently overwrite. Do not provide a `--regenerate` or `--force-rewrite` flag for these files.

**Atomic writes:** All artifact writes must use the temp-then-rename pattern:
```python
import tempfile, os
with tempfile.NamedTemporaryFile('w', dir='artifacts/', delete=False, suffix='.tmp') as f:
    json.dump(data, f)
    tmp_path = f.name
os.rename(tmp_path, final_path)
```
This ensures no partially-written file is ever hashed or read by a subsequent stage.

---

## Section 7c — Prompt versioning and location

All system prompts must:

- Live in `src/prompts/` as plain text files — never as inline strings in Python source
- Be named descriptively: `pass1_system_prompt.txt`, `pass2_system_prompt.txt`, `lens_summary_prompt.txt`
- Be read from disk at runtime — not hardcoded into function bodies
- Be derived from `docs/workflow.md` and `docs/lens.md` — do not invent prompt content
- Have their SHA256 recorded in the audit anchor at the time of the run (add `prompt_hash` to `pass1_anchor` and `pass2_output`)

Do not:
- Write prompt text inside Python f-strings or multiline strings in source files
- Store different prompt versions in different variables in the same file
- Modify a prompt file and re-run without updating the hash in the anchor

**Rationale:** Prompt changes between runs affect analysis output. Recording the prompt hash makes the audit trail reproducible — an examiner can verify that the same prompt was used across all stability runs.

---

## Section 7d — Reproducibility metadata

Every LLM call must record the following in the artifact it produces:

```python
"model_config": {
    "model_name": str,        # e.g. "qwen2.5-27b-instruct"
    "temperature": float,     # from config
    "seed": int or None,      # None for deterministic run
    "ollama_version": str,    # from `ollama --version` at runtime
    "prompt_hash": str,       # SHA256 of the system prompt file used
}
```

This block is required in: `pass1_output`, all four `pass2_output` files, and the audit bundle metadata.

`model_sha` (hash of model weights) is not required at this stage — Ollama does not expose this reliably. Flag it as a Phase 6 optional enhancement.

---

## Section 7e — Filesystem safety

- All `dataset_id` values must be validated before use in file paths. Reject any value containing: `../`, `/`, `\`, null bytes, or characters outside `[a-zA-Z0-9_-]`
- Exit with `ERR_DATASET_INVALID` (add to `docs/error_codes.md`) on rejection
- Before writing any artifact, check the target path does not already exist. If it does, exit with `ERR_DATASET_COLLISION` unless `--force` was explicitly passed
- All file paths must be resolved to absolute paths and checked to be within the repo root before writing
- Raw participant data (`artifacts/raw_archive/`) must never appear in the audit bundle zip

---

## Section 7f — OSF anchor value validation

When `osf_uploader.py` upgrades `anchor_type` from `local`, it must validate `anchor_value` before writing:

- `osf_doi`: must match `^https://osf\.io/[a-z0-9]{5,}` 
- `repo_accession`: must be a non-empty string starting with `https://`
- Plain strings, bare DOIs without URL prefix, and null values must be rejected with `ERR_ANCHOR_VALUE_INVALID` (add to `docs/error_codes.md`)

Add `ERR_ANCHOR_VALUE_INVALID` and `ERR_DATASET_INVALID` and `ERR_DATASET_COLLISION` to `docs/error_codes.md` with action strings and exit code 3.

---

## Section 8 — Before submitting a pull request or completing a phase

Checklist the agent must verify before marking any phase complete:

- [ ] `make test-local` exits 0
- [ ] No secrets committed (check with `git grep -r "api_key\|token\|password\|secret" config/ src/` — should only find placeholder comments)
- [ ] All new artifacts written to correct locations
- [ ] All new errors use codes from `docs/error_codes.md`
- [ ] All new artifacts include `strand` field
- [ ] No `anchor_type: local` accepted in Pass 2 or audit bundle
- [ ] No `human_verdict` set programmatically
- [ ] All new public functions have docstrings with I/O specification
- [ ] No bare `Exception()` raised — structured errors and `sys.exit()` only
- [ ] `COPILOT_INSTRUCTIONS.md` still accurate (update if new hard rules were added)
- [ ] No banned packages added to `requirements.txt` or imported in `src/`
- [ ] All prompts live in `src/prompts/` as `.txt` files — no inline prompt strings in Python source
- [ ] `model_config` block (model_name, temperature, seed, ollama_version, prompt_hash) present in all LLM output artifacts
- [ ] All new file writes use temp-then-rename atomic pattern
- [ ] `dataset_id` validated before use in any file path
- [ ] `docs/error_codes.md` updated for any new error conditions introduced

---

## Version history

| Version | Changes |
|---------|---------|
| 1.0 | Initial guardrails document — covers all v2.1 dev plan constraints |
| 1.1 | Added: dependency freeze rule, prompt versioning rule, artifact immutability rule, expanded banned package list, filesystem safety rules, OSF anchor validation rule, reproducibility metadata rule |
