# Agentic Analysis Workflow Design

*Six-phase human–AI collaborative pipeline for IPA + Psychodynamic Discourse Analysis with lens-informed two-pass architecture*

> Research Methodology · Agentic AI Workflow · MScPsychotherapy Dissertation

## Time Estimates

| Metric | Value | Note |
|--------|-------|------|
| Total Est. Human Hours | 190–265 | with lens protocol applied |
| Framework Build | 50–80 | included in total above |
| Analysis (IPA + PDA) | 95–130 | human oversight only |
| Writing & Synthesis | 60–80 | inc. triangulation |
| AI Reduction vs. Unaided | ~55% | lens adds further ~10% |

---

## Phase 0 — Preprocessing Pipeline
*~10–15 hrs setup · then fully automated*

Build once, run automatically for all transcripts. Takes raw Whisper output and produces clean, structured, analysis-ready JSON. No human involvement in the run — only in setup and quality-checking output.

### Whisper transcription + diarisation
`automated`

Run locally via whisper.cpp or faster-whisper on your 3090s. Diarisation agent separates therapist and client turns using speaker labels. All processing offline — no data leaves machine.
- Model: large-v3 or distil-large-v3 for speed/accuracy balance
- Output: raw transcript with speaker tags and timestamps
- Flag low-confidence segments for human review

**Output:** timestamped JSON with speaker labels + confidence scores per segment

### Transcript cleaning and normalisation agent
`automated`

Removes disfluencies (where analytically irrelevant), standardises formatting, handles overlapping speech, produces clean readable version alongside preserved raw version.
- Preserves paralinguistic features (pauses, laughter, emphasis) in annotation layer
- Produces two versions: clean read and analytic notation version

**Output:** clean_transcript.json + annotated_transcript.json per session

### Spot-check and sign-off on transcription quality
`human check`

Review flagged low-confidence segments. Correct diarisation errors where therapist/client turns were misassigned. Estimated 20–30 mins per transcript.
**Output:** verified, locked transcript set ready for analysis phases

---

## Phase 1 — Pass 1 — Blind Analysis (No Researcher Lens)
*~15–20 hrs human · AI runs overnight*

The AI reads all data with no framing — no theoretical context, no researcher positionality, no hypotheses. This produces a genuine baseline and prevents the lens from dominating the data. Both strands run simultaneously.

### IPA Strand — Interviews

**[AI agent]** Initial noticing pass — descriptive, linguistic, and conceptual annotations on each interview transcript. No clustering yet.

**[AI agent]** Candidate experiential statement extraction — what does this participant seem to be saying about their experience? Surface-level only.

**[AI agent]** Initial emergent themes per participant — grouped candidate statements. No cross-case work yet.

**[human review]** Read Pass 1 IPA output. Note what surprises you. Do not analyse yet — this feeds the lens conversation.

### PDA Strand — Session Transcripts

**[AI agent]** Discourse feature extraction — subject positions, pronoun use, modality, hedging, metaphor clusters, turn length patterns per session.

**[AI agent]** Relational moment flagging — turn sequences with elevated intensity, topic avoidance, repair attempts, significant silences or interruptions.

**[AI agent]** Session-level summary — dominant relational register, notable shifts in discourse tone, any unusual or striking features.

**[human review]** Skim PDA Pass 1 output. Note anything clinically striking. Feed observations into lens conversation.

---

## Phase 2 — Lens Conversation — Researcher Positionality Dialogue
*~4–6 hrs · human-led*

The pivot point of the entire workflow. Researcher conducts a structured dialogue with the AI using the Lens Protocol document. The output — the Researcher Lens Summary — frames all subsequent analysis. See the Lens Protocol document for full question set.

### Structured reflexivity conversation with AI
`human-led dialogue`

Work through all seven sections of the Lens Protocol. AI asks follow-up questions where useful. Researcher shares theoretical commitments, positionality, hypotheses, and reactions to Pass 1 output.
- Cover: theoretical positioning, positionality, hypothesis mapping, disconfirmation mandate
- Share what surprised you in Pass 1
- Be specific about psychodynamic vocabulary you want the AI to be sensitive to

**Output:** conversational transcript of lens dialogue — save in full for methodology appendix

### AI produces Researcher Lens Summary document
`AI output`

AI synthesises the conversation into a structured positionality document: theoretical frame, hypotheses, concepts to be sensitive to, disconfirmation mandate. Researcher reviews and confirms accuracy before Pass 2 begins.
**Output:** researcher_lens_summary.md — confirmed by researcher, locked as analysis frame for Pass 2

---

## Phase 3 — Pass 2 — Lens-Informed Interpretive Analysis
*~35–50 hrs human · AI runs overnight per strand*

The AI re-analyses all data through the researcher lens. This is the primary analytic pass. The AI now has enough context to attempt genuine interpretive work, not just pattern recognition. Human role here shifts from generating to evaluating and refining.

### IPA Strand — Pass 2

**[AI agent]** Lens-positioned reannotation — revisit all initial annotations through the researcher's theoretical frame. Flag which annotations shift meaning when the lens is applied.

**[AI agent]** Personal Experiential Theme (PET) development per participant — second-order interpretation, moving from description to meaning. Draft 3–6 PETs per participant with supporting extracts.

**[AI agent — disconfirmation pass]** Explicit review: what in this participant's data does NOT fit the researcher lens? What resists the frame? These are marked separately with confidence rating.

**[human interpretive layer]** Review AI-proposed PETs. Accept, revise, reject, or combine. Write interpretive commentary. Add the double-hermeneutic layer — what does the researcher make of what the participant is making of their experience?

**[AI agent]** Cross-case analysis — map PETs across all participants. Propose Group Experiential Themes (GETs) with convergence/divergence mapping. Flag idiographic outliers.

**[human sign-off]** Accept/revise GETs. Write final IPA interpretive narrative per theme.

### PDA Strand — Pass 2

**[AI agent]** Lens-positioned discourse reannotation — revisit flagged relational moments through Avdi & Georgaca framework. Apply researcher's named psychodynamic concepts as interpretive lens.

**[AI agent]** Subject position analysis — how does each participant construct and negotiate their subject position in relation to the therapist across sessions 1→3? Track shifts in positioning.

**[AI agent]** Transference/countertransference marker analysis — flag linguistic and interactional features consistent with transferential dynamics. Rate confidence. Note where evidence is ambiguous.

**[AI agent — disconfirmation pass]** What discursive material resists psychodynamic interpretation? What appears relationally neutral or unremarkable against expectations? Flagged separately.

**[human interpretive layer]** Apply clinical and psychodynamic interpretive judgment to AI-flagged moments. This is the step that requires practitioner knowledge — what do these discourse patterns mean relationally and psychodynamically?

**[AI agent]** Cross-session and cross-participant pattern synthesis — how do discourse patterns evolve across three sessions? What is consistent across participants?

---

## Phase 4 — Triangulation — Cross-Strand Synthesis
*~15–20 hrs human · AI produces mapping framework*

Where the two strands are brought into dialogue. The AI produces the convergence/divergence map; the researcher does the interpretive synthesis. The gap between what participants said in interview and what happened discursively in sessions is often where the most analytically interesting findings live.

### Cross-strand mapping — IPA themes × PDA patterns
`AI agent`

For each participant: map IPA Group Experiential Themes against PDA discourse patterns. Produce a convergence/divergence matrix. Flag:
- Where reported experience (IPA) and enacted discourse (PDA) align
- Where they diverge — participant says X but discourse shows Y
- Where the PDA reveals something not accessed by interview at all
- Where the IPA provides meaning that the PDA alone could not produce

**Output:** triangulation_matrix.md — per participant and across participants

### Pass 1 vs Pass 2 delta analysis
`AI agent`

Compare blind pass and lens-informed pass outputs systematically. What did the lens illuminate that blind reading missed? What did blind reading surface that the lens tended to overlook? This delta is part of your methodological transparency and reflexivity argument.
**Output:** lens_delta_report.md — included in methodology appendix

### Interpretive triangulation — researcher writes cross-strand findings
`human synthesis`

This is the irreducibly human step. Using the AI-produced mapping as scaffolding, the researcher writes the interpretive narrative that makes sense of convergences and divergences across both strands. This is where your clinical knowledge, theoretical depth, and understanding of the therapeutic relationship is most necessary.
**Output:** triangulated findings narrative — feeds directly into dissertation findings chapter

---

## Phase 5 — Write-Up Scaffolding & Framework Build
*~60–80 hrs total (inc. framework build)*

Includes both the technical build of the agentic framework itself (done before any data arrives) and the write-up phase. AI assists significantly with both.

### Agentic framework construction
`AI-assisted build`

Build the agent pipeline before data collection begins. Use your existing experience with opencode / copilot agents. AI writes the majority of the code and prompt engineering.
- Whisper preprocessing pipeline — ~10 hrs
- IPA annotation and clustering agents — ~15 hrs
- PDA discourse feature and relational moment agents — ~15 hrs
- Triangulation mapping agent — ~8 hrs
- Testing and iteration on synthetic/pilot data — ~10 hrs

**Output:** working local agent pipeline, tested and documented

### Methodology chapter drafting
`AI-assisted`

AI drafts methodology chapter sections using your decisions and the audit trail documents produced throughout the process. Researcher edits and deepens. The audit trail created by the two-pass design gives you unusually rich methodological material.
- Epistemological positioning — constructivist–interpretivist
- Rationale for IPA + PDA mixed design
- Description of human–AI collaborative process with lens protocol
- Reflexivity section — uses lens conversation transcript and lens summary directly

### Findings chapter scaffolding
`AI-assisted`

AI organises the triangulated findings into chapter structure. Researcher writes the interpretive narrative within that structure. AI assists with academic register, coherence, and structural logic.
---

## Full Human Hours Estimate
*revised with lens protocol*

| Task | Without AI | AI only (no lens) | AI + Lens Protocol | Notes |
|---|---|---|---|---|
| Preprocessing & transcription QC | 20–25 | 10–15 | 10–15 | lens has no effect here |
| Pass 1 — blind analysis | — | 8–12 | 8–12 | new step, human review only |
| Lens conversation | — | — | 4–6 | replaces some later reflexivity work |
| IPA analysis — human oversight | 120–150 | 55–70 | 40–55 | lens raises AI quality, reduces reviews needed |
| PDA analysis — human oversight | 220–300 | 70–90 | 55–75 | biggest AI gain regardless of lens |
| Triangulation | 40–60 | 18–25 | 15–20 | AI mapping + human synthesis |
| Framework build | — | 50–80 | 50–80 | previously uncosted — now included |
| Writing up | 80–100 | 55–70 | 55–70 | lens produces richer methodology material |
| Total | 460–635 | 225–305 | 190–265 | ~58% reduction on unaided |

> Context A 12-month part-time masters dissertation typically demands 600–900 total hours across all components. The 190–265 hrs above covers analysis and write-up only. Add literature review (60–80 hrs), ethics and governance (20–30 hrs), participant recruitment and management (20–30 hrs), and supervision preparation (10–15 hrs). Revised total: approximately 300–420 hrs — comfortably within the expected range for a part-time masters at the upper end of ambition.
