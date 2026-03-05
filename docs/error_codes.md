# Pipeline Error Codes

All pipeline errors use this structured format:
```
[ERROR_CODE] Brief description
Action: What the researcher should do next (plain language, specific).
```

---

## Exit code summary

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Configuration error (preflight missing, unknown sensitivity) |
| `2` | Governance block (DPIA missing or invalid) |
| `3` | Pass sequencing error (anchor missing, hash mismatch, anchor local) |
| `4` | Lens error (not locked, signature missing) |
| `5` | Synthesis block (verdicts incomplete, strand missing) |

---

## DPIA and governance errors (exit 2)

**ERR_DPIA_MISSING**
```
[ERR_DPIA_MISSING] artifacts/dpia_signed.json not found.
Action: Complete the DPIA checklist (artifacts/dpia_checklist.md), obtain DPO sign-off,
        and save the signed record to artifacts/dpia_signed.json.
        See examples/dpia_signed.json for the required format.
```

**ERR_DPIA_INVALID**
```
[ERR_DPIA_INVALID] dpia_signed.json is missing required fields.
Action: Ensure dpia_signed.json contains: dpo_sign_off.dpo_name, signature_date,
        decision == "approved", and dpia_complete == true.
```

---

## Pass sequencing errors (exit 3)

**ERR_PASS1_ANCHOR_MISSING**
```
[ERR_PASS1_ANCHOR_MISSING] pass1_anchor_[dataset_id].json not found in artifacts/
Action: Run pass1_runner.py first. Deposit to OSF. Then retry Pass 2.
```

**ERR_PASS1_HASH_MISMATCH**
```
[ERR_PASS1_HASH_MISMATCH] SHA256 of pass1_output does not match stored pass1_hash.
Action: The file may have been modified after hashing. Do not proceed.
        Restore from your OSF deposit or re-run Pass 1. Do not re-hash.
```

**ERR_PASS1_ANCHOR_LOCAL**
```
[ERR_PASS1_ANCHOR_LOCAL] pass1_anchor has anchor_type: local. External deposit required.
Action: Deposit pass1_output to OSF or institutional repo. Then run:
          python src/modules/osf_uploader.py --anchor [path] --doi [DOI]
        Pass 2 and audit bundle packaging both require this step.
```

---

## Lens errors (exit 4)

**ERR_LENS_NOT_LOCKED**
```
[ERR_LENS_NOT_LOCKED] lens_[run_id].json exists but locked != true.
Action: python src/modules/lens_dialogue.py --lock --run-id [id] --researcher-id [orcid]
```

**ERR_LENS_SIGNATURE_MISSING**
```
[ERR_LENS_SIGNATURE_MISSING] Lens locked but researcher_signature is null or empty.
Action: Re-run lock_lens() with your ORCID or institutional username.
        Anonymous signatures are not accepted.
```

---

## Synthesis block errors (exit 5)

**ERR_VERDICT_INCOMPLETE**
```
[ERR_VERDICT_INCOMPLETE] One or more evidence_review records have human_verdict: null.
Action: python src/tools/review_cli.py --dir artifacts/
        Complete all pending verdicts before emitting the audit bundle.
```

**ERR_STRAND_MISSING**
```
[ERR_STRAND_MISSING] Artifact [filename] is missing the required strand field.
Action: Add strand: IPA | PDA | TA | quant | mixed to the artifact.
```

**ERR_ANCHOR_LOCAL_AT_BUNDLE**
```
[ERR_ANCHOR_LOCAL_AT_BUNDLE] Audit bundle cannot be packaged: anchor_type is local.
Action: Complete OSF deposit (Step 4, docs/runbook.md) before emitting audit bundle.
```

---

## Configuration errors (exit 1)

**ERR_PREFLIGHT_MISSING**
```
[ERR_PREFLIGHT_MISSING] Required document not found: [filename]
Action: If HTML version exists: pandoc [file].html -o [file].md
```

**ERR_SENSITIVITY_UNKNOWN**
```
[ERR_SENSITIVITY_UNKNOWN] Sensitivity value "[value]" not recognised.
Action: Set sensitivity to: public_text | personal_non_sensitive | special_category
        "normal" is not valid and silently bypasses DPIA gating.
```

---

## Soft warnings (exit 0 — logged, not blocking)

**WARN_PREREG_MISSING** — pre_registration_doi is null; flagged in audit bundle.
**WARN_POSTHOC_HYPOTHESIS** — hypothesis not in pre-registration; flagged as post-hoc.
