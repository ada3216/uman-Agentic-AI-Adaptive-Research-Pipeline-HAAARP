Generic Research Workflow System · Drop-in Artifacts 
v1.0
# Generic Pipeline Toolkit

Four ready-to-use artifacts that can be dropped into any implementation of the generic agentic research pipeline. Artifact 1 is the lens dialogue module. Artifact 2 is the DPIA sensitivity classification table. Artifact 3 is the Human Evidence Review JSON schema. Artifact 4 is the study config JSON template showing how all four link together.
Artifact 1 — Lens Dialogue
Artifact 2 — DPIA Table
Artifact 3 — Evidence Review JSON
Artifact 4 — Study Config
 ARTIFACT 1 — LENS DIALOGUE 
A1
## Structured Lens Dialogue Module

generative · 8–12 questions · configurable by method
The generative reflexivity elicitation that powers the lens-informed pass. Unlike a preset (which is a static label), this dialogue draws out the researcher's positionality, theoretical orientation, hypotheses, and interpretive boundaries through structured questions. Saved as lens_[run_id].json and hashed before Pass 2 begins. The full dialogue transcript is saved alongside the lens summary. Lens vocabulary named here feeds the amplification detection in the grounding verification pass. Design constraint: 8–12 questions maximum — fewer loses depth, more creates fatigue and drift. Questions are grouped into five thematic sections.
**Configuration by method (onboarding Q5 feeds this)**

      Questions in sections 1 and 3 adapt based on theoretical_orientation from onboarding. A phenomenological orientation receives questions about meaning-making and lived experience; a psychodynamic orientation receives questions about relational dynamics and transference concepts; a positivist/quantitative orientation receives a lighter lens (hypothesis mapping only, sections 1 and 4; positionality section is abbreviated). The question set below is the full qualitative/mixed version.
    
 Section 1 
Section 1 — Researcher Identity & Theoretical Stance
L1.1 
free text
What is your theoretical orientation — how do you naturally make sense of human experience?
Phenomenological / psychodynamic / CBT / critical / constructivist / other — describe in your own words, not just the label. A short memo is more useful than a category name.
L1.2 
free text
If you have clinical or practitioner experience relevant to this study, describe your relationship to this kind of work.
How does your practice experience shape what you notice? What does working in this area feel like from the inside?
 Section 2 
Section 2 — Research Aims & Hypotheses
L2.1 
free text
State your primary research question in plain language — as you would explain it to a participant.
Then note: is this the same wording as in your pre-registration? If it has drifted, flag the difference here.
L2.2 
memo
What do you expect to find — your honest hypotheses going in?
List 3–5 specific expectations. These will be cross-checked against your pre-registration. Any that are new or modified will be flagged in the lens summary as post-hoc and must be acknowledged.
L2.3 
memo
What concepts, constructs, or vocabulary do you want the AI to be sensitive to in the data?
Name specific terms, theoretical constructs, relational dynamics, or linguistic features. These become the lens vocabulary — they are also used by the grounding verification pass to detect potential amplification.
 Section 3 
Section 3 — Participant & Context Assumptions
L3.1 
yes/no + memo
Does your study involve vulnerable groups or power dynamics that might shape how participants present their experience?
If yes: describe the dynamic and how it might affect what participants say or avoid saying. This shapes how the AI interprets hedging, silence, and resistance in the data.
L3.2 
memo
What do you think participants might find difficult to talk about, or might not say directly?
Where do you expect omission, indirection, or displacement? This feeds the relational moment flagging in PDA and the interpretive layer in IPA.
 Section 4 
Section 4 — Analytic Focus, Exclusions & Evidence Standards
L4.1 
list
What will you explicitly NOT be looking for in this analysis?
Name specific themes, constructs, or readings that are outside the scope of this study. This prevents scope creep in AI-generated outputs and keeps the analysis focused.
L4.2 
preference
What counts as adequate evidential support for a claim in this study?
Default: ≥2 distinct excerpts from different participants to support a generalised claim. Adjust here if your study design or method requires a different standard. This threshold is passed to the grounding verification agent.
default → require_excerpt_count: 2 · adjust if needed
L4.3 
memo
Where is the boundary between what you will call an interpretation and what you will call a data-grounded finding?
How confident do you need to be, and with what level of support, before moving from "the data suggests" to "the data shows"? Naming this boundary helps calibrate the grounding verification pass.
 Section 5 
Section 5 — Pass 1 Surprises & Lock Confirmation
L5.1 
memo
Having reviewed the Pass 1 blind output — what surprised you? What didn't fit your expectations?
What does the data seem to want to say that you weren't expecting? This observation is included in the lens summary and feeds the disconfirmation mandate for Pass 2.
L5.2 
confirmation + lock
Confirm that the lens summary the AI has produced accurately represents your understanding and is ready to be locked.
Once confirmed, the lens summary is hashed and timestamped. It cannot be modified. Any subsequent changes require a new lens version (lens_v2) with its own hash — the delta between versions is noted in the audit trail.
{
"lens_id"
: 
"lens_[run_id]"
,
  
"version"
: 
"v1"
,                          
// increment if lens is updated
"timestamp_utc"
: 
"ISO8601"
,
  
"researcher_id"
: 
"orcid or username"
,
  
"prereg_doi"
: 
"10.17605/OSF.IO/xxxxx"
,
  
"dialogue_transcript_path"
: 
"lens_dialogue_[run_id].txt"
,
  
"theoretical_orientation"
: 
"researcher's own words"
,
  
"clinical_orientation"
: 
"if applicable"
,
  
"primary_hypotheses"
: 
[
{
"hypothesis"
: 
"string"
, 
"in_prereg"
: 
true
}
// false = post-hoc, flagged
]
,
  
"lens_vocabulary"
: 
[
"list of named constructs"
]
,    
// used in amplification detection
"explicit_exclusions"
: 
[
"what researcher will not look for"
]
,
  
"evidence_standard"
: 
{
"require_excerpt_count"
: 
2
,
    
"generalisation_threshold"
: 
"≥2 distinct participants"
}
,
  
"pass1_surprises"
: 
"researcher's memo on unexpected blind-pass findings"
,
  
"posthoc_hypothesis_flags"
: 
[
"any hypothesis not in prereg"
]
,
  
"lens_summary_hash"
: 
"sha256"
,                  
// hash of this file
"researcher_confirmation"
: 
true
,               
// must be true before pass 2
"locked"
: 
true
// set by pipeline after confirmation
}
 ARTIFACT 2 — DPIA TABLE 
A2
## DPIA Sensitivity Classification Table

pipeline enforcement logic
Maps data type and modality to required governance actions. The pipeline reads the sensitivity field from study config and enforces the requirements at this table. Special category data triggers a hard block on ingestion until DPIA is complete. This table applies UK/GDPR jurisdiction — adapt the specific regulatory references for other jurisdictions.
| Sensitivity Level | Example data types | Pipeline action | Required governance steps |
| --- | --- | --- | --- |
| public_text | Published blog posts, public social media, public documents, published academic text | proceed | Standard academic citation practice Minimal de-identification (remove usernames if pseudonymous) Note data source in methodology |
| personal_non_sensitive | Identifiable interview data (non-health), survey responses with demographic identifiers, professional correspondence | proceed with warning | Pseudonymisation required before AI processing Access log — document who can access raw data Retention policy — define and document Participant consent covering data use DPIA recommended but not mandatory Ethics committee notification |
| special_category | Health data, therapy session recordings/transcripts, mental health information, sexual orientation, criminal convictions, biometric data, data on minors | HARD BLOCK — ingestion blocked until DPIA complete | DPIA mandatory — submit to institutional DPO before any data collection GDPR Article 9 lawful basis confirmed (explicit consent for research: Art. 9(2)(a)) Ethics committee approval required — include data-flow diagram Enhanced pseudonymisation — names, locations, dates, all identifying details replaced before AI sees any data AI processing explicitly named in consent form with local-only execution statement Storage encryption on all devices holding original data Access controls documented — named individuals only Retention limit defined per data type (recordings / transcripts / AI outputs / audit files) Breach protocol documented — notification chain and timeframe Participant right to withdraw post-transcription defined BPS Code of Ethics and Conduct (2021) compliance statement |

**Pipeline enforcement**

      The sensitivity field in study config (from onboarding Q4) triggers this logic. If sensitivity == "special_category": require_dpia = true, block_ingestion_until_dpia_complete = true. The pipeline reads a dpia_complete boolean and a dpia_document_path from study config before proceeding past Stage −1. These fields must be set manually by the researcher after DPIA approval — there is no automated bypass.
    
**Jurisdiction note**

      This table is written for UK research (GDPR as retained in UK law, BPS ethics framework, university ethics committees). For EU research: same GDPR provisions apply. For US research: replace BPS with APA ethics guidelines; replace GDPR with IRB approval process (45 CFR 46) and relevant state privacy law. For clinical research: additional regulatory layers (e.g., NHS R&D approval in UK) may apply — check with institutional research governance office.
    
 ARTIFACT 3 — EVIDENCE REVIEW JSON 
A3
## Human Evidence Review JSON Schema

completable record · one file per claim
Produced by the grounding verification agent with human_verdict: null. The researcher completes the human_verdict object for every flagged claim. The completed file becomes part of the audit bundle. Synthesis is blocked until all verdicts are filled. For team workflows, the adjudicator fields are activated when verdicts disagree. For solo researchers, adjudicator fields remain null and are noted as not applicable.
{
"claim_id"
: 
"C12"
,                          
// unique per claim, per run
"run_id"
: 
"pass2_[timestamp]"
,              
// links to audit metadata
"strand"
: 
"IPA | PDA | TA | quant | mixed"
,
  
"generated_by"
: 
"pass2 | grounding_agent"
,
  
"claim_text"
: 
"verbatim claim from Pass 2 output"
,

  
"supporting_segments"
: 
[
"P01_interview_L45_49"
,              
// format: [participant]_[source]_L[start]_[end]
"P03_session2_L12_18"
]
,
  
"support_count"
: 
2
,
  
"support_strength"
: 
"strong | moderate | weak | none"
,
                                              
// strong ≥3 | moderate 2 | weak 1 | none 0
"verification_flags"
: 
[
"low_evidence_count"
,               
// below configured require_excerpt_count
"lens_vocabulary_only"
,              
// excerpts only use researcher's lens terms
"overgeneralisation"
,               
// broad claim, single excerpt source
"excerpt_not_found"
,                
// citation drift — possible hallucination
"excerpt_does_not_support"
,         
// excerpt exists but claim is overstated
"single_participant_only"
// claim generalises beyond one participant
]
,

  
"human_verdict"
: 
{
"verdict"
: 
null
,                    
// researcher fills: accept | accept_with_revision | reject | recheck
"reviewer_id"
: 
null
,               
// orcid or username
"timestamp_utc"
: 
null
,             
// ISO8601 — auto-filled on save
"revised_claim_text"
: 
null
,        
// required if accept_with_revision
"notes"
: 
null
,                     
// required if accept_with_revision or reject
"interpretive_proposition"
: 
false
// set true if accepted despite weak/none support
// claims marked true are labelled in write-up
}
,

  
"adjudication"
: 
{
// team workflows only; null for solo researchers
"required"
: 
false
,                  
// set true if coder verdicts disagree
"adjudicator_id"
: 
null
,
    
"adjudication_timestamp_utc"
: 
null
,
    
"adjudication_notes"
: 
null
// required if adjudication occurred
}
}
**Verdict definitions**
**accept**
 — claim is well-grounded; no modification needed.
**accept_with_revision**
 — claim is defensible but overstated; revised_claim_text required; notes required.
**reject**
 — claim is unsupported or hallucinated; removed from analysis; notes required explaining why.
**recheck**
 — transcript needs re-examination before verdict; pipeline pauses this claim until resolved.

      Claims accepted despite weak or none support must have interpretive_proposition set to true — these are labelled as interpretive propositions rather than data-grounded findings in the write-up. The proportion of claims in each verdict category is reported in the methodology appendix.
    
 ARTIFACT 4 — STUDY CONFIG 
A4
## Study Config JSON Template

produced by onboarding · drives entire pipeline
Generated by the onboarding wizard from researcher answers. Drives all pipeline decisions — module activation, quality criteria routing, DPIA enforcement, pass constraints, and output configuration. This file should be stored alongside the pre-registration and included in the audit bundle. The bespoke MScPsychotherapy study is shown as a worked example in the comments.
{
// ── STUDY IDENTITY ──────────────────────────────────────────────────────
"study_title"
: 
"string"
,               
// e.g. "Client experiences of working with a therapist perceived as different"
"study_aim"
: 
"one sentence"
,
  
"pre_registration_doi"
: 
"string or null"
,  
// propagates into every audit metadata file
"ethics_committee_id"
: 
"string or null"
,

  
// ── DATA & SENSITIVITY ──────────────────────────────────────────────────
"modalities"
: 
[
"audio"
, 
"text"
, 
"survey_csv"
]
,   
// activates modality adapters
"sensitivity"
: 
"public_text | personal_non_sensitive | special_category"
,
  
"dpia_required"
: 
true
,                  
// auto-set if sensitivity == special_category
"dpia_complete"
: 
false
,                 
// researcher sets true after DPO approval
"dpia_document_path"
: 
"string or null"
,   
// required if dpia_required == true
// ── METHOD & QUALITY CRITERIA ──────────────────────────────────────────
"method"
: 
"IPA | PDA | mixed | TA | GT | discourse | quant"
,
  
"method_strands"
: 
[
"IPA"
, 
"PDA"
]
,          
// for mixed designs — routes strand-specific QC
"quality_criteria"
: 
{
"IPA"
: 
"lincoln_guba_trustworthiness"
,  
// never inter-rater reliability
"PDA"
: 
"krippendorff_alpha_with_CI"
,    
// applied to coding phase only
"quant"
: 
"pvalues_CI_effect_sizes_corrections"
}
,

  
// ── PIPELINE CONSTRAINTS ───────────────────────────────────────────────
"pass1_hash_required"
: 
true
,             
// hardcoded true — cannot be set false
"lens_hash_required"
: 
true
,              
// hardcoded true — cannot be set false
"human_verdict_gate"
: 
true
,             
// hardcoded true — synthesis blocked until complete
"deidentify_before_analysis"
: 
true
,      
// hardcoded true — cannot be set false
// ── LENS MODULE ────────────────────────────────────────────────────────
"lens_module"
: 
"lens_protocol_v1"
,
  
"lens_question_count"
: 
10
,              
// 8–12 range; configured by method and orientation
"lens_hash"
: 
"null until lens is locked"
,

  
// ── RESEARCHER & TEAM ──────────────────────────────────────────────────
"onboarding"
: 
{
"theoretical_orientation"
: 
"string"
,  
// from Q5 — configures lens dialogue
"team_structure"
: 
"solo | 2-person | team"
,  
// activates adjudication policy if not solo
"academic_level"
: 
"masters | phd | lab"
}
,

  
// ── OUTPUTS ────────────────────────────────────────────────────────────
"outputs"
: 
[
"IPA_themes"
, 
"PDA_codebook"
, 
"claim_evidence_table"
,
    
"evidence_review_records"
, 
"methodology_scaffold"
, 
"audit_bundle"
]
,

  
// ── MODEL & STABILITY ──────────────────────────────────────────────────
"model_defaults"
: 
{
"provider"
: 
"local"
,
    
"model_name"
: 
"qwen2.5-27b-instruct"
,
    
"deterministic_run"
: 
true
,
    
"seeds"
: 
[
42
, 
99
, 
123
]
}
,
  
"stability_tests"
: 
{
"seeded_reruns"
: 
3
,
    
"deterministic_run"
: 
true
,
    
"alternate_model_optional"
: 
true
// recommended at phd/lab; optional at masters
}
,

  
// ── ARCHIVE ────────────────────────────────────────────────────────────
"audit_settings"
: 
{
"save_to"
: 
"osf | institutional_repo | local"
,
    
"persistent_id"
: 
true
,
    
"bundle_contents"
: 
[
"study_config.json"
, 
"lens_[run_id].json"
, 
"audit_metadata_*.json"
,
      
"pass1_output_hash.txt"
, 
"lens_delta_report.md"
,
      
"evidence_review_*.json"
, 
"stability_test_report.md"
]
}
}
**Hardcoded fields**

      pass1_hash_required, lens_hash_required, human_verdict_gate, and deidentify_before_analysis are always set to true by the pipeline — they cannot be overridden by the study config. If a researcher manually sets them to false, the pipeline ignores the override and logs a warning. These are the four non-negotiable sequencing constraints from the architecture specification.
    
Generic Pipeline Toolkit v1.0 · Four Drop-in Artifacts
Lens Dialogue · DPIA Table · Evidence Review JSON · Study Config
