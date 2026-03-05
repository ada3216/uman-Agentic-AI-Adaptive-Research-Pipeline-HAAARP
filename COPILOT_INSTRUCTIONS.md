# COPILOT_INSTRUCTIONS.md
## Read this before touching any file in this repo.

This repository implements a governance-first AI-assisted research pipeline.
The governance architecture is not optional — it is the point.

---

## Three absolute rules

### 1. NEVER commit secrets
- Write `config/secrets.example.yaml` with placeholder keys
- All credentials go in environment variables or gitignored `config/secrets.yaml`
- If a provider key is required at runtime: print instructions, do not request or store it
- `.gitignore` must cover: `config/secrets.yaml`, `*.env`, `artifacts/raw_archive/`

### 2. Two-pass lock is enforced in code, not by trust
Pass 2 CANNOT run unless ALL of these are true:
- `artifacts/pass1_anchor_[dataset_id].json` exists
- Stored `pass1_hash` matches SHA256 of the actual `pass1_output` file
- `anchor_type` is `osf_doi` or `repo_accession` — NOT `local`
- `artifacts/lens_[run_id].json` exists AND `locked == true`
- `lens.researcher_signature` is non-null (ORCID or institutional username)

Each condition failure prints a structured error from `docs/error_codes.md`
and calls `sys.exit(correct_code)`. Never raise a bare `Exception`.

### 3. DPIA gate is a hard code block, not a warning
If `sensitivity == "special_category"` in `config/defaults.yaml`:
- Check for `artifacts/dpia_signed.json` before ingesting any data
- If absent: print `ERR_DPIA_MISSING` with action string and `sys.exit(2)`
- No override. No bypass. No bare Exception.

---

## Files to read before writing any code

Read these in order. Do not skip any.

| File | Why |
|------|-----|
| `docs/workflow.md` | Pipeline architecture and stage specs; source of truth for all stages |
| `docs/lens.md` | Lens dialogue questions (10 Qs); extract verbatim into `lens_dialogue.py` |
| `artifacts/audit_schema.json` | All audit artifacts must conform to this schema |
| `docs/error_codes.md` | All errors must use these codes, messages, and exit values |

If any of these files are missing: halt with `ERR_PREFLIGHT_MISSING` and print the action string.

---

## Where to write things

| Content | Location |
|---------|----------|
| All AI-generated artifacts | `artifacts/` |
| All source code | `src/` |
| All test fixtures | `tests/fixtures/` |
| Example filled artifacts (for CI) | `examples/` |
| Human docs | `docs/` — only modify if explicitly asked |
| Prompts | `src/prompts/` |
| JSON schemas | `src/schemas/` |

Never write participant data, code maps, or raw recordings anywhere in the repo.

---

## Error handling — non-negotiable format

Every error output must follow this format:
```
[ERROR_CODE] Brief description
Action: Exactly what the researcher should do next, in plain language.
```

All codes and exit values are in `docs/error_codes.md`. Use them.

Exit code summary:
- `0` — success
- `1` — configuration error (preflight missing, unknown sensitivity)
- `2` — governance block (DPIA missing or invalid)
- `3` — pass sequencing error (anchor missing, hash mismatch, anchor local)
- `4` — lens error (not locked, signature missing)
- `5` — synthesis block (verdicts incomplete, strand missing)

---

## Strand labels — required on every artifact

Every output artifact (`pass1_output`, `pass2_output`, `evidence_review`, audit bundle entry)
must have a `strand` field. Valid values: `IPA`, `PDA`, `TA`, `quant`, `mixed`.

The audit emitter validates this before packaging. Missing strand = `ERR_STRAND_MISSING` + `sys.exit(5)`.

---

## Human verdicts — non-delegable

`grounding_checker.py` only writes `evidence_review_*.json` with `human_verdict: null`.
`review_cli.py` is the ONLY place verdicts are set.
No AI process may set `human_verdict` to a non-null value. Ever.

---

## OSF deposit — mandatory before Pass 2

After Pass 1 completes, `anchor_type` is `local`. This is temporary.
Before Pass 2 can run, the anchor must be upgraded:
- Deposit `pass1_output` to OSF or institutional repo
- Run `osf_uploader.py` to update `anchor_type` to `osf_doi` and fill `anchor_value`
- Only then will Pass 2 run

The audit emitter also refuses to package if `anchor_type` is still `local`.

---

## Testing — MOCK_LLM=true always

All tests run with `MOCK_LLM=true` environment variable.
No live model. No network access.
`make test-local` runs the full suite locally.
`make test` is the CI target — same behaviour.

There are 14 named tests in `tests/test_pipeline.py`. All must pass.
