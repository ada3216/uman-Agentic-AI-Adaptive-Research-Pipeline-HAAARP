# Pipeline Runbook — Step-by-Step Guide

This document walks you through running the full agentic research pipeline, from setup to audit bundle. Follow each step in order. Do not skip steps — the pipeline's gate checks enforce sequencing.

See `docs/workflow.md` for the conceptual overview of what each phase does and why.

---

## Prerequisites

Before running anything:

1. **Install dependencies**
   ```bash
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
   ```

2. **Install Ollama** (local model runner)
   - Download from [https://ollama.com](https://ollama.com)
   - Start Ollama: `ollama serve`
  - Pull the analysis model: `ollama pull qwen2.5-27b-instruct`
  - Test it's working: `ollama run qwen2.5-27b-instruct "Hello"`

3. **Configure the pipeline**
   ```bash
   cp config/secrets.example.yaml config/secrets.yaml
   ```
   Edit `config/defaults.yaml`:
   - Set `study.strand` to your method: `IPA`, `PDA`, `TA`, `quant`, or `mixed`
   - Set `sensitivity` to match your data type:
     - `public_text` — publicly available text
     - `personal_non_sensitive` — identifiable but not health/therapy data
     - `special_category` — health data, therapy sessions, psychological data (GDPR Art. 9)
   - Set `pre_registration_doi` if you have pre-registered

4. **Complete pre-flight documents** (if not already present)
   - `docs/workflow.md` ← this should already be present
   - `docs/lens.md` ← this should already be present
   - `artifacts/audit_schema.json` ← this should already be present
   - `artifacts/dpia_checklist.md` ← fill this in before processing special category data
   - `artifacts/consent_snippets.md` ← adapt for your consent forms

5. **If using `special_category` data: complete and sign DPIA**
   ```bash
   # After completing artifacts/dpia_checklist.md and obtaining DPO sign-off:
   cp examples/dpia_signed.json artifacts/dpia_signed.json
   # Then edit artifacts/dpia_signed.json with your actual DPO details
   ```

---

## Step 1 — Pre-flight check

```bash
python src/agent/orchestrator.py --check-preflight
```

This verifies all required documents exist. Expected output: `[OK] All pre-flight documents present.`

If you get `ERR_PREFLIGHT_MISSING`, the missing file path and a recovery action will be printed.

---

## Step 2 — Ingest and de-identify data

```bash
python src/modules/ingest_and_deid.py \
  --input path/to/your/data.json \
  --code-map path/to/participant_code_map.json
```

**Important:** Your participant code map (`*_code_map.json`) is gitignored — it must never be committed to the repository.

Output: `artifacts/deidentified_[participant_code]_[session].json`

---

## Step 3 — Run Pass 1 (blind analysis)

```bash
python src/agent/pass1_runner.py \
  --deid-path artifacts/deidentified_P01_session1.json \
  --dataset-id YOUR_DATASET_ID
```

Pass 1 runs with no researcher lens. The AI reads your data and surfaces initial themes and patterns without any theoretical framing.

Output:
- `artifacts/pass1_output_[dataset_id].json`
- `artifacts/pass1_anchor_[dataset_id].json` — anchor type is `local` at this stage

After Pass 1 completes, you'll see a prompt to deposit to OSF **(Step 4 must happen before Pass 2 can run)**.

---

## Step 4 — Deposit Pass 1 output to OSF (required before Pass 2)

1. Log in to [https://osf.io](https://osf.io)
2. Navigate to your project (or create one)
3. Upload `artifacts/pass1_output_[dataset_id].json`
4. Copy the DOI or file URL from OSF
5. Run the uploader:
   ```bash
   python src/modules/osf_uploader.py \
     --anchor artifacts/pass1_anchor_[dataset_id].json \
     --doi https://osf.io/YOUR_FILE_ID
   ```

This upgrades the anchor from `anchor_type: local` to `anchor_type: osf_doi`. **Pass 2 will not run until this step is complete.**

---

## Step 5 — Lens dialogue (researcher reflexivity)

```bash
python src/modules/lens_dialogue.py \
  --dataset-id YOUR_DATASET_ID \
  --researcher-id https://orcid.org/YOUR_ORCID
```

This opens a structured conversation where you answer the 10 reflexivity questions from `docs/lens.md`. Your answers form the researcher lens that frames Pass 2.

After completing the dialogue, lock the lens with your ORCID:
```bash
python src/modules/lens_dialogue.py \
  --lock \
  --run-id LENS_RUN_ID \
  --researcher-id https://orcid.org/YOUR_ORCID
```

Output: `artifacts/lens_[run_id].json` (locked)

---

## Step 6 — Run Pass 2 (lens-informed analysis)

```bash
python src/agent/pass2_runner.py \
  --anchor artifacts/pass1_anchor_[dataset_id].json \
  --lens artifacts/lens_[run_id].json
```

Pass 2 gate checks (all must pass):
1. `pass1_anchor.json` exists ✓
2. `pass1_hash` matches SHA256 of `pass1_output` file ✓
3. `anchor_type` is `osf_doi` or `repo_accession` (not `local`) ✓
4. `lens_[run_id].json` exists ✓
5. `lens.locked == true` ✓
6. `lens.researcher_signature` is non-null ✓

Output: Four `pass2_output_[label]_[dataset_id].json` files (seeded runs for stability)

---

## Step 7 — Grounding verification

```bash
python src/modules/grounding_checker.py \
  --pass2-output artifacts/pass2_output_seeded0_[dataset_id].json
```

The grounding checker creates an evidence review record for each AI-generated claim. All records are created with `human_verdict: null` — they require human completion in Step 8.

Output: `artifacts/evidence_review_[claim_id]_[dataset_id].json` (one per claim)

---

## Step 8 — Human evidence review (required)

```bash
REVIEWER_ID=https://orcid.org/YOUR_ORCID \
python src/tools/review_cli.py --dir artifacts/
```

This opens the CLI for reviewing each AI-generated claim. For each claim you will:
- View the claim and its supporting evidence
- Accept, accept with revision, reject, or flag for recheck
- Provide notes for revised or rejected claims

**This step cannot be automated.** No AI-generated claim can enter the findings without a human verdict.

---

## Step 9 — Emit audit bundle

```bash
python src/modules/audit_emitter.py \
  --dataset-id YOUR_DATASET_ID \
  --run-id LENS_RUN_ID
```

Pre-conditions (all must be met):
- All `evidence_review` records have `human_verdict` set (not null)
- `anchor_type` is `osf_doi` or `repo_accession` (not `local`)
- All artifacts have a `strand` field

Output:
- `artifacts/audit_bundle_[run_id].zip` — full audit bundle
- `artifacts/audit_bundle_[run_id].json` — bundle metadata with `bundle_sha256`

The audit bundle is your chain-of-custody record. Include it in your dissertation methodology appendix and/or deposit it alongside your findings.

---

## Running tests (no live model required)

```bash
make test-local
```

All tests run with mocked LLM calls. No Ollama required. All 14 governance tests must pass.

---

## Troubleshooting

If you encounter an error, the pipeline will print a structured error code and action:

```
[ERR_CODE] Brief description
Action: Exactly what to do next.
```

See `docs/error_codes.md` for the full list of error codes, exit values, and recovery actions.

---

## For supervisors and examiners

See `docs/generic-architecture.md` for the generic architecture specification and the open-source road map.

The audit bundle (`audit_bundle_[run_id].zip`) contains:
- All analysis artifacts with SHA256 hashes
- Pass 1 anchor with OSF deposit link
- Locked researcher lens summary
- Human evidence review records with reviewer identity
- Stability metrics across seeded runs
- Bundle hash for integrity verification
