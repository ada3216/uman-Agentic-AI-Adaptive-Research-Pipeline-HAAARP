# DPIA Checklist — Data Protection Impact Assessment

**Complete this document before running the pipeline with `sensitivity: special_category` data.**

This checklist must be completed, signed off by a Data Protection Officer (or ethical supervisor acting in that capacity), and saved as `artifacts/dpia_signed.json` before any data ingestion can proceed.

---

## About this requirement

Under GDPR Article 9, processing special category data (health data, therapy transcripts, data revealing mental health information) requires a completed DPIA. This pipeline enforces this requirement in code — the pipeline will not ingest data until `artifacts/dpia_signed.json` exists with `dpia_complete: true` and `decision: approved`.

For a master's dissertation: your university ethics committee sign-off typically satisfies this requirement. Check with your supervisor and/or institutional DPO.

---

## Checklist

### 1. Description of processing

- **Purpose of data collection:** [Describe your research question and why data collection is necessary]
- **Type of data:** [e.g., audio recordings of psychotherapy sessions, interview transcripts]
- **Sensitivity classification:** `special_category` — health/therapy data (GDPR Art. 9)
- **Number of participants:** [n]
- **Data subjects:** [e.g., psychotherapy clients, research participants]

### 2. Necessity and proportionality

- [ ] The research question cannot be adequately answered without this data
- [ ] The minimum necessary amount of data is collected
- [ ] Data will be pseudonymised before AI processing (via `ingest_and_deid.py`)

### 3. Local processing confirmation

- [ ] All AI processing uses a local model only (no data sent to external APIs)
- [ ] No participant data will be stored in cloud services
- [ ] Transcription uses WhisperX locally — no cloud transcription services

### 4. Participant safeguards

- [ ] Written informed consent obtained from all participants
- [ ] Participants informed of AI use in data analysis
- [ ] Right to withdraw explained and documented
- [ ] Consent documentation stored separately from analysis data
- [ ] See `artifacts/consent_snippets.md` for approved consent language

### 5. Security measures

- [ ] Data stored on encrypted device/volume
- [ ] Access limited to named researchers only
- [ ] Data destruction plan documented

### 6. Researcher sign-off

- **Researcher name and role:** [Name, role/student number]
- **Date checklist completed:** [YYYY-MM-DD]
- **ORCID (if available):** [https://orcid.org/...]

### 7. DPO / Supervisor sign-off

To be completed by Data Protection Officer or ethics supervisor:

- **Name:** [Name]
- **Role:** [DPO / Ethics committee / Supervisor acting as ethics lead]
- **Institution:** [Institution name]
- **Decision:** [ ] Approved  [ ] Requires revision  [ ] Rejected
- **Conditions (if any):** [Any conditions attached to approval]
- **Date:** [YYYY-MM-DD]
- **Signature:** *(wet or digital signature; reference number may substitute)*

---

## After completion

Once this checklist is signed off:

1. Create `artifacts/dpia_signed.json` using `examples/dpia_signed.json` as your template
2. Fill in all required fields: `dpo_sign_off.dpo_name`, `signature_date`, `decision: "approved"`, `dpia_complete: true`
3. Keep this checklist stored alongside your ethics documentation
4. The pipeline will automatically detect `dpia_signed.json` and allow processing to proceed

**Do not create a fake `dpia_signed.json` to bypass this gate. Doing so may constitute a GDPR lawful processing violation for special category health data.**
