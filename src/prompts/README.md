# src/prompts/

System prompts for the AI analysis pipeline.

All prompt files are plain text (`.txt`). They are read from disk at runtime — never hardcoded into Python source.

## Required prompt files

| File | Stage | Source |
|------|-------|--------|
| `pass1_system_prompt.txt` | Pass 1 — blind analysis | Derived from `docs/workflow.md` Stage 1 spec |
| `pass2_system_prompt.txt` | Pass 2 — lens-informed analysis | Derived from `docs/workflow.md` Stage 3 and researcher lens summary |
| `lens_summary_prompt.txt` | Lens dialogue synthesis | Derived from `docs/lens.md` Section 6 output template |

## Creation instructions

**Do not invent prompt content.** Each prompt must be derived from the corresponding section of `docs/workflow.md` or `docs/lens.md`.

- `pass1_system_prompt.txt`: Read Phase 1 (Pass 1 — Blind Analysis) of `docs/workflow.md`. Write a system prompt that contains no researcher lens or theoretical framing, and instructs the model to output structured JSON with a `strand` field.
- `pass2_system_prompt.txt`: Read Phase 3 (Pass 2 — Lens-Informed Interpretive Analysis) of `docs/workflow.md`. Prompt receives the lens summary as a dynamic input at runtime.
- `lens_summary_prompt.txt`: Read Section 6 of `docs/lens.md`. Prompt instructs the model to synthesise the lens conversation into the six-section lens summary document.

## Rules (from GUARDRAILS.md)

- SHA256 of each prompt file is recorded in the artifact anchor at time of the run (`prompt_hash` field)
- Prompt changes between runs affect analysis output — changing a prompt requires a new run and updated anchor hash
- Store each prompt version separately — do not overwrite and re-run without updating the hash
