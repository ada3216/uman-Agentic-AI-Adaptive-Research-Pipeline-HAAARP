Generic Research Workflow System · Architecture Specification 
v1.0
# Agentic Research Pipeline — Generic Architecture

A modular, configurable pipeline that adapts to any research method (qualitative, quantitative, mixed), modality (text, audio, video, image, survey), and academic level. Bespoke-quality rigour reproduced through structured onboarding, hardcoded pipeline constraints, and configurable but non-optional governance gates.
any method
any modality
masters → lab
human-in-the-loop
audit-first
 Relationship to bespoke 
01
## Relationship to the Bespoke Psychotherapy Design

context
Bespoke design (MScPsychotherapy)
Hand-crafted for IPA + PDA, constructivist epistemology, therapy session + interview data, solo researcher, UK ethics framework. Lens protocol, two-pass architecture, grounding verification, and strand-specific quality criteria are all built in as named, fixed pipeline stages. Reference implementation — maximum depth, maximum specificity.

Generic system
The bespoke design abstracted into a configurable pipeline. The same methodological rigour is reproduced through structured onboarding (which collects the parameters needed to configure each module), hardcoded pipeline constraints (which enforce sequencing regardless of method), and method-routing logic (which selects quality criteria, analysis agents, and governance steps based on study config). The bespoke design is the reference implementation and proof of concept.

**Build order recommendation**

      Build the bespoke pipeline first (you are already doing this). The generic version is built by abstracting the bespoke pipeline — adding a configuration layer and onboarding module on top of working components. Do not build generic first and bespoke second.
    
 Architecture 
02
## Modular Architecture

pipeline design
Eight pipeline stages. Core stages (grey) run for every study. Modality adapters (blue) are selected by study config. Analysis engines (purple/green) are routed by method. Human gates (orange) are enforced regardless of method or level. Lock stages (red) enforce sequencing constraints.
core
 runs always
qualitative
 qual methods
quantitative
 quant methods
human gate
 non-delegable
⚙ config gate
 blocks until condition met
🔒 lock
 immutable after this point
**Stage −1**
Governance
Onboarding wizard
Study config JSON generation
⚙ DPIA gate (blocks if special_category)
⚙ Pre-registration gate (requires DOI)
Ethics consent template auto-generation
↓ governance approved → pipeline unlocked
**Stage 0**
Ingest + Preprocess
De-identification agent
Audit metadata layer (auto, every run)
Audio → Whisper transcription + diarisation
Text normalisation + cleaning
Survey CSV schema check + summary stats
Video → subtitle extraction + frame sampling
Image → captioning + tag extraction
↓ de-identified, preprocessed data enters analysis
**Stage 1**
Pass 1 — Blind
IPA initial noticing agent
PDA discourse feature extraction agent
Thematic Analysis — open coding agent
Descriptive statistics agent
Variable relationship mapping agent
Pass 1 output hash + timestamp → locked
🔒 Pass 1 locked — cannot be modified
↓ Pass 1 hash stored → lens conversation unlocked
**Stage 2**
Lens Dialogue
Onboarding-configured lens dialogue (8–12 Qs)
Pre-registration consistency check
Lens summary generation + hash
🔒 Lens summary locked — cannot be modified
⚙ Pass 2 blocked until lens hash confirmed
↓ lens hash confirmed → Pass 2 unlocked
**Stage 3**
Pass 2 — Positioned
IPA lens-informed PET development agent
PDA positioned discourse reannotation agent
Thematic Analysis — focused coding agent
Hypothesis-directed statistical analysis agent
Disconfirmation + lens-amplification guard
Stability testing (3 seeds + 1 deterministic run)
Pass 1 → Pass 2 delta generation
↓ Pass 2 complete → grounding verification
**Stage 3.5**
Grounding Verify
Claim–evidence grounding agent (all strands)
Hallucination detection (excerpt_not_found)
Overgeneralisation flagging
Lens-vocabulary amplification check
claim_evidence JSON generation (human_verdict: null)
Human Evidence Review (fill human_verdict)
⚙ Synthesis blocked until all verdicts filled
↓ human verdicts complete → synthesis
**Stage 4**
Synthesis
Cross-strand triangulation mapping agent
Member checking (IPA credibility — auto-draft)
Stats table + figure generation agent
Lens delta report generation
Interpretive synthesis (researcher — non-delegable)
↓ synthesis complete → output + archive
**Stage 5**
Output + Archive
Methodology chapter scaffold (AI-drafted)
Full audit bundle assembly
OSF / institutional repo deposit
Persistent identifier assignment
 Onboarding wizard 
03
## Researcher Onboarding Wizard — 9 Questions

configures pipeline
Runs once at study setup. Outputs a study config JSON that drives all subsequent pipeline decisions — method routing, DPIA triggering, lens module configuration, quality criteria selection, and robustness level. Required fields block pipeline start if missing. Required fields shown in blue; optional in green.
Q1 
required
Study title and primary aim
Short title + one sentence aim. Feeds study_config.study_title and is included in all audit metadata.
Q2 
required
What modalities does your data include?
Select all: text transcripts / audio / video / images / survey CSV / other. Determines which ingest and preprocessing agents are activated.
Q3 
required
What is your primary analytic method?
IPA / PDA / Reflexive Thematic Analysis / Grounded Theory / Discourse Analysis / Quantitative / Mixed. Routes analysis agents and quality criteria.
Q4 
required
What is the data sensitivity level?
Public text / Personal non-sensitive / Special category (health, therapy, sexual orientation, criminal). Triggers DPIA gate if special_category. Pipeline blocks ingestion until DPIA complete.
Q5 
required
What is your theoretical and clinical orientation?
Phenomenological / Psychodynamic / CBT / Critical / Constructivist / Positivist / Other + short memo. Feeds the lens dialogue module — configures the theoretical vocabulary questions.
Q6 
required
Solo researcher or team?
Solo / 2-person team / larger team. Activates adjudication policy in Human Evidence Review if team. Configures inter-coder workflow for PDA or coding-based methods.
Q7 
required
What outputs do you need?
Themes / codebook / stats table / figures / write-up scaffolding / claim_evidence_table / evidence_review_records. Configures output agents and archive bundle.
Q8 
optional
Academic level
Masters / PhD / Research lab. Affects robustness check defaults — alternate model runs are optional at masters level, recommended at PhD/lab. Does not affect core rigour requirements.
Q9 
optional
Pre-registration DOI and ethics committee ID
If not yet available, pipeline will prompt for these before Stage 1 begins. Pre-registration DOI propagates into every audit metadata file. Ethics ID included in DPIA documentation.
**UI principle**

      Onboarding must show required vs optional clearly, and explain why each required field is needed. Researchers are more likely to provide accurate answers when they understand the downstream effect. Fields Q4 (sensitivity) and Q9 (pre-reg DOI) have the highest impact on governance — these should include brief inline explanations.
    
 Pipeline constraints 
04
## Hardcoded Pipeline Constraints

enforced regardless of method
These constraints are not configurable. They enforce the sequencing and governance principles that differentiate a rigorous pipeline from a flexible wrapper. Hard constraints block pipeline execution. Soft constraints generate warnings and require researcher acknowledgement.
HARD BLOCK
Pass 2 blocked until Pass 1 is hashed and locked
The SHA256 hash of the complete Pass 1 output JSON must be stored and timestamped before the lens dialogue begins. The pipeline reads this hash as a prerequisite and will not proceed. This is the single biggest contributor to methodological rigour — it makes blind-pass-first a technical guarantee, not a researcher commitment.
HARD BLOCK
Synthesis blocked until all human_verdict fields are filled
The triangulation/synthesis stage cannot begin until every flagged claim in the grounding verification output has a human_verdict recorded. Claims with verdict "recheck" pause the pipeline until re-examined. This enforces the Human Evidence Review as a non-delegable gate.
HARD BLOCK
Ingestion blocked for special_category data until DPIA is complete
If onboarding Q4 returns "special_category", the pipeline will not ingest any data until a completed DPIA document path is provided and the ethics committee approval ID is recorded. No override is available.
HARD BLOCK
De-identification must complete before any analysis agent sees data
The de-identification agent runs as the first preprocessing step. Analysis agents receive de-identified files only. The pipeline enforces this by passing only deidentified_[participant_code]_[session].json to analysis agents — never the original transcript.
SOFT WARN
Pre-registration DOI should be present before Pass 1
If no pre-registration DOI is provided, the pipeline generates a warning and requires researcher acknowledgement before proceeding. The DOI is not hard-blocked (some studies begin before pre-registration is complete) but absence is logged in every audit metadata file and must be explained in the methodology chapter.
SOFT WARN
Lens conversation hypotheses are cross-checked against pre-registration
Any hypothesis stated in the lens conversation that does not appear in the pre-registered plan is flagged in the lens summary document. The researcher must acknowledge each flagged addition before the lens is locked. These additions are labelled as post-hoc in the methodology.
 Method routing 
05
## Method Routing — Analysis Engines & Quality Criteria

configured by study config
The study config JSON (produced by onboarding) routes each study to the appropriate analysis agents and quality criteria. Multiple methods can be active simultaneously for mixed designs.
| Method | Analysis agents activated | Quality criteria | Lens module |
| --- | --- | --- | --- |
| IPA | Initial noticing → PET development → cross-case GET mapping → member check draft | Lincoln & Guba trustworthinessmember checkingaudit trail | Full 8–12 Q generative dialogue, positionality-focused |
| PDA | Discourse feature extraction → subject position mapping → relational moment flagging → cross-session pattern agent | Krippendorff's α + CI≥20% double-codeadjudication protocol | Theoretical vocabulary + psychodynamic construct questions |
| Reflexive TA | Open coding → focused coding → theme development → thematic map agent | Lincoln & Gubareflexive memo logaudit trail | Researcher orientation + semantic vs latent focus questions |
| Grounded Theory | Open coding → axial coding → selective coding → theoretical saturation check | Theoretical saturationconstant comparisonmemo trail | Theoretical sensitivity questions; emergent focus (lighter lens) |
| Quantitative | Schema check → summary stats → hypothesis-directed analysis → bootstrap stability → figure generation | p-values + CIseffect sizesappropriate correctionsbootstrap / cross-validation | Hypothesis mapping only — no positionality dialogue; pre-registration is primary rigor mechanism |
| Mixed | All relevant agents active simultaneously; strand label in every audit file; triangulation mapping agent active | Strand-appropriate criteria applied per output; cross-strand triangulation requires researcher interpretive synthesis | Full dialogue — covers both theoretical orientation and hypothesis mapping |

 Modality adapters 
06
## Modality Adapters

selected by study config
| Modality | Preprocessing steps | Features passed to analysis agents | Special considerations |
| --- | --- | --- | --- |
| text | De-identification → normalisation → analytic notation version | Clean text + line-numbered version + paralinguistic annotation layer | Primary modality — always fully supported |
| audio | Whisper transcription → diarisation → confidence flagging → de-identification → cleaning | Timestamped transcript + speaker labels + prosody markers (pauses, emphasis) + confidence scores | Prosody features passed as annotation layer; AI cannot interpret intonation — flag for human review |
| video | Subtitle extraction → frame sampling → image feature extraction per frame | Timestamped subtitles + frame-level object/emotion tags + scene descriptions | Image features are hypothesis-generators only; facial expression analysis requires ethical justification in DPIA |
| image | Captioning → tag extraction → de-identification of any visible personal data | Caption text + semantic tags → fed into thematic coding layer | No facial recognition without explicit ethics approval and consent |
| survey CSV | Schema check → type validation → summary statistics → missing data report | Clean dataframe + variable schema + descriptive stats → quant analysis agents | Variable selection agent assists but researcher confirms final variable set |

 Adjudication policy 
07
## Adjudication Policy (Team Workflows)

activated if team ≥ 2
Activated when onboarding Q6 returns "team". Dormant for solo researchers — adjudicator fields in the Evidence Review JSON remain null and are noted as not applicable in the methodology. For solo researchers, the researcher themselves is the sole arbiter; the human_verdict field serves as a self-audit record.
TEAM ONLY
When human_verdicts disagree across coders
If two reviewers produce different verdicts for the same claim_id, the pipeline flags a disagreement and blocks that claim from the synthesis stage. A third adjudicator (or the PI) reviews the disagreement and completes the adjudicator_id and adjudication_notes fields in the Evidence Review JSON. The rationale is recorded and becomes part of the audit trail. This applies to PDA coding disagreements (Krippendorff's α < 0.667) as well as Human Evidence Review verdict disagreements.
**Solo researcher note**

      For solo researchers (including the MScPsychotherapy project this system was designed from), the adjudication fields are dormant. The researcher's own human_verdict record serves as the decision audit. The grounding verification pass and the disconfirmation mandate in the lens instructions serve as the primary safeguards against unexamined interpretive bias.
    
 Implementation options 
08
## Implementation Options by Level

practical
| Level | Implementation approach | Optional | Not required |
| --- | --- | --- | --- |
| Masters (solo) | Python scripts + Jupyter notebooks + prompt template library + structured JSON/CSV artifact storage. Documented runbook. Local LLM (27B dense). OSF for archiving. | Alternate model robustness run | Docker / containerisation; external adjudication; UI |
| PhD | As above plus: modular script library, automated stability testing pipeline, basic UI for onboarding, structured logging. Alternate model run recommended. | Microservices architecture | Full containerisation for solo researcher |
| Research lab | Full modular microservices, containerised pipeline, team workflow with adjudication, UI for onboarding and review, scheduler for stability tests, institutional repo integration. | Nothing optional at lab scale | — |

Generic Agentic Research Pipeline — Architecture v1.0
Reference implementation: MScPsychotherapy IPA + PDA bespoke design
