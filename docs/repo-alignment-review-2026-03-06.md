# Repo Alignment Review — 2026-03-06

## Scope

This review treats the newly added root documents as the intended target state:

- `README.md`
- `HOW_TO_COMPLY.md`
- `COMMERCIAL_LICENSE.md`
- `CONTRIBUTING.md`

The goal is therefore **not** to rewrite those back toward the older scaffold. The goal is to identify the minimum changes needed in the rest of the repository so the existing docs, agent instructions, dev plan, test plan, and setup story all align with the new public-facing position.

This review also covers:

- whether the existing Adaptabot coding agent is a good base for this repo
- whether the existing Adaptabot phase-gate verifier can be reused as-is
- what setup gaps still block the repo from being an optimal coding starting point

## Overall Assessment

The new root docs fit the repository direction well at a conceptual level. They are stronger, clearer, and more publication-ready than the older minimal scaffold language.

The main problem is not conceptual fit. The main problem is **repo alignment drift**:

- the new root docs describe a more mature and public-ready project surface
- several older control docs still assume a narrower repo shape and earlier scaffold stage
- a few referenced assets do not yet exist
- the install/run story is inconsistent across files

Conclusion: keep the new root docs as the target, and update the surrounding docs and repo scaffolding to match them.

## Priority Order

### P0 — Must fix before coding in earnest

- Add a root `LICENSE` file. Multiple docs now rely on it, but it does not exist.
- Decide and standardise the dependency-install path.
  Current state: `README.md` and `docs/runbook.md` refer to `requirements.txt`, but no `requirements.txt` or `pyproject.toml` exists.
- Update the repo remote to the new GitHub URL before any push.
  Current origin still points to the old AART repo.
- Remove the Windows `:Zone.Identifier` files from version control scope and ignore them going forward.
- Create repo-specific AI agent files before serious implementation starts, because the repo now has sufficiently strong governance constraints to benefit from custom agents.

### P1 — Should fix next

- Align guardrails and instructions with the new root docs.
- Align README/runbook/dev plan/test plan references to actual files and commands.
- Add missing prompt files and schema files that current docs already claim should exist.
- Add or revise missing verification assets mentioned by the test plan.

### P2 — Optional but advisable

- Normalize naming across title, acronym, and repo slug.
- Add explicit contributor workflow automation for DCO if that policy is going to be enforced.
- Add packaging/dev tooling beyond the current minimal Makefile if desired.

## Required Changes By File

### `README.md`

Keep the new README as the public-facing direction, but revise these points:

- Replace the placeholder clone URL with the real repo URL: `https://github.com/ada3216/uman-Agentic-AI-Adaptive-Research-Pipeline-HAAARP`.
- Resolve the install command mismatch.
  Current problem: README says `pip install -r requirements.txt --break-system-packages`, but `requirements.txt` does not exist.
- Resolve the model-name mismatch.
  Current problem: README quick start says `qwen3.5:27b`, while `config/defaults.yaml` uses `qwen2.5-27b-instruct` and the rest of the repo is aligned to that.
- Replace the nonexistent demo command.
  Current problem: `python src/pipeline.py --demo` points to a file that does not exist.
  Likely replacement: point to `docs/runbook.md`, `src/agent/orchestrator.py`, or a later-created demo notebook/script.
- Fix companion-doc paths.
  Current problem: the README references `Agentic_Pipeline_Dev_Plan_v2.1.md` and `TEST_PLAN.md` as if they are at repo root, but they actually live under `implementation docs/`.
- Remove or update structure references to files that do not exist yet.
  Current examples: `docs/scaling_framework.md`, `docs/authorship_disclosure_template.md`, and `scripts/`.
- Replace placeholder citation metadata.
  Current problem: arXiv ID placeholders remain.
- Once `LICENSE` is added, keep the licensing section as written.

### `HOW_TO_COMPLY.md`

Keep the document. Make these fixes:

- Replace `[YOUR EMAIL ADDRESS]` with the real contact address already used in `COMMERCIAL_LICENSE.md`: `adaptagentic@proton.me`.
- Once `LICENSE` exists, keep the AGPL explanation unchanged.
- Optionally add one sentence clarifying whether the repo title is “Agentic Human–AI Research Pipeline” and the repo slug is simply an implementation slug, to avoid naming ambiguity.

### `COMMERCIAL_LICENSE.md`

Keep the document. Make these fixes:

- Add the actual `LICENSE` file it references.
- Optionally add one sentence clarifying the commercial-license contact workflow if you want fewer inbound clarification emails.

### `CONTRIBUTING.md`

Keep the document. Make these fixes:

- Replace implicit file-location assumptions with actual repo paths.
  Example: point contributors to `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md` and `implementation docs/TEST_PLAN.md` rather than implying root-level spec files.
- Decide whether the sentence “All new modules must have corresponding tests in `tests/test_pipeline.py`” is still the intended rule.
  If the repo is going to grow, that should probably become “in `tests/`” rather than only one file.
- If DCO is truly mandatory, add enforcement details to CI or repository settings later.
  Right now the document states a policy, but the repo does not visibly enforce it.

### `GUARDRAILS.md`

This file needs the most important alignment work outside the new root docs.

Required changes:

- Update Section 4 root-file policy.
  Current text says the only permitted root-level files are `README.md`, `Makefile`, `RELEASE_GUIDE.md`, `COPILOT_INSTRUCTIONS.md`, and `GUARDRAILS.md`.
  That now conflicts with the new root docs and with the practical need for a root `LICENSE` file.
- Explicitly allow these root docs:
  `README.md`, `LICENSE`, `COMMERCIAL_LICENSE.md`, `HOW_TO_COMPLY.md`, `CONTRIBUTING.md`, `COPILOT_INSTRUCTIONS.md`, `GUARDRAILS.md`, `Makefile`, `.gitignore`.
- Update the “Human documentation” rule so it does not imply that public-facing docs must live only under `docs/`.
  The repo now clearly uses both root governance/public docs and `docs/` implementation docs.
- Add a short note that the new root docs are canonical public/legal/contributor documents and must stay aligned with the implementation docs.
- If the repo will use custom agents, add a brief mention that agent definitions may live under `.github/agents/`.

Recommended but not mandatory:

- Add a short note about ignoring Windows metadata files such as `*:Zone.Identifier`.

### `COPILOT_INSTRUCTIONS.md`

This file is broadly aligned already, but it should be updated lightly:

- Add one short section noting that root governance/public docs are part of the canonical repo surface.
- Consider adding `LICENSE` to the list of files the agent should preserve when working on licensing-related changes.
- Optionally point agents to the future repo-specific custom agent files once created.

No major rewrite is needed here.

### `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md`

This should receive **minimal, additive** changes, not a broad rewrite.

Recommended changes:

- In Phase 0, expand the root-doc deliverables to acknowledge the new docs:
  `LICENSE`, `COMMERCIAL_LICENSE.md`, `HOW_TO_COMPLY.md`, `CONTRIBUTING.md`.
- Keep the architecture and governance content intact.
- Update any implied install assumptions so they match the chosen dependency strategy.
  Right now the plan assumes a buildable scaffold, but the repo still lacks a formal dependency file.
- Add a short Phase 0 or Phase 0.5 task for repo custom agents under `.github/agents/`.
  This is now justified by the maturity of the repo’s governance constraints.
- Do not substantially change the phase structure unless implementation realities require it.

Important note:

- The dev plan currently remains the right place to define build tasks and missing scaffolds.
  It should not be weakened just to match missing implementation.

### `implementation docs/TEST_PLAN.md`

This file should mostly be kept, but a few references need to be reconciled with reality.

Current mismatches that need resolution:

- It references `notebooks/demo_pipeline.ipynb`, which does not exist.
- It references `tests/test_adversarial.py`, which does not exist.
- It requires additional schemas in `src/schemas/`:
  `anchor_schema.json`, `lens_schema.json`, `stability_schema.json`, `dpia_schema.json`.
  Only `evidence_review_schema.json` exists today.

Recommended approach:

- Keep the test plan expectations.
- Treat the missing notebook/test/schema files as implementation backlog to create, not as reasons to weaken the plan.

### `docs/runbook.md`

This file needs targeted alignment with the new README and actual repo state.

Required changes:

- Replace `pip install -r requirements.txt` unless a `requirements.txt` file is added.
- Ensure the Ollama model name matches `config/defaults.yaml` and the README.
- Confirm whether `src/modules/lens_dialogue.py` invocation examples match the actual CLI contract you want to keep.
- Keep the sequencing and governance explanation. It fits the repo well.

### `src/prompts/README.md`

This document is internally coherent, but it currently documents prompt files that do not exist.

Required follow-on work:

- Create:
  - `src/prompts/pass1_system_prompt.txt`
  - `src/prompts/pass2_system_prompt.txt`
  - `src/prompts/lens_summary_prompt.txt`

No major text change is needed unless the prompt strategy changes.

### `.gitignore`

Add ignore rules for Windows metadata files:

- `*:Zone.Identifier`

Then remove the currently present `:Zone.Identifier` files from the repo working tree.

### `.github/workflows/ci.yml`

This file is generally fine, but it needs to align with the final dependency-install story.

Required change:

- If you add `requirements.txt` or `requirements-dev.txt`, install from that.
- If you adopt `pyproject.toml`, install via that.
- Avoid leaving CI with a one-off dependency install path while the README and runbook use another.

## Repo Setup Gaps That Still Block “Optimal To Start Coding”

These are not just documentation issues. They are practical readiness gaps.

### Missing `LICENSE`

This is the clearest blocker because multiple new docs now depend on it.

### Missing dependency manifest

There is currently no `requirements.txt` or `pyproject.toml`.

Decision needed:

- either add a minimal `requirements.txt` now
- or switch all user-facing docs and CI instructions to a different canonical install method

Given the current repo, adding a minimal `requirements.txt` is likely the least disruptive option.

### Missing custom agents

There are currently no repo-specific custom agent files in `.github/agents/`.

For this repo, that is now worth fixing because the governance constraints are specific enough to merit dedicated agents.

### Missing prompt files

The code and docs expect disk-based prompt files, but `src/prompts/*.txt` does not exist yet.

### Missing schemas promised by the test plan

Missing today:

- `src/schemas/anchor_schema.json`
- `src/schemas/lens_schema.json`
- `src/schemas/stability_schema.json`
- `src/schemas/dpia_schema.json`

### Missing verification assets promised by the test plan

Missing today:

- `notebooks/demo_pipeline.ipynb`
- `tests/test_adversarial.py`

### Scaffold code is still scaffold code

The repo is a real scaffold, not yet a near-complete implementation.

Examples of current implementation gap indicators:

- many `TODO` markers remain in `src/`
- `src/agent/orchestrator.py` still contains placeholder orchestration logic
- prompt loading paths are documented but not implemented end-to-end
- several local-model and OSF integration steps are still placeholders

That is acceptable, but it means “optimal to start coding” still requires a small setup pass first.

## Adaptabot Coder Agent Assessment

## Verdict

The existing Adaptabot coder agent is a **useful structural base**, but it should **not** be copied as-is.

## What is worth reusing

- The pattern of a dedicated implementation agent
- The “read the authoritative spec before coding” workflow
- The “write tests with the source change, not later” rule
- The remediation loop after phase-gate failures

## What does not fit this repo as-is

- It references `GUARDRAILS_v8.md`, `DEVPLAN_v8.md`, and Adaptabot-specific phase documents.
- It assumes Adaptabot architectural concerns such as provider SDK boundaries and `structlog`.
- It uses outdated tool names in frontmatter.
- It is tuned for a different codebase shape and different phase transitions.

## Recommended new agent

Create a repo-specific agent under:

- `.github/agents/haaarp-coder.agent.md`

Recommended behaviour:

- Read order before coding:
  1. `COPILOT_INSTRUCTIONS.md`
  2. `GUARDRAILS.md`
  3. `docs/workflow.md`
  4. `docs/lens.md`
  5. `docs/error_codes.md`
  6. `artifacts/audit_schema.json`
  7. `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md`
  8. `implementation docs/TEST_PLAN.md`
- Default to local-only/Ollama-safe implementation choices.
- Never weaken DPIA gate, Pass 1 anchor gate, lens lock, or human-verdict requirements.
- Write tests with each source change.
- Prefer additive schema-backed implementation over ad hoc JSON shape drift.
- Do not change dependency files without explicit approval.
- Do not change legal/public docs unless explicitly asked.

## Phase-Gate Agent Assessment

## Verdict

The current Adaptabot phase-gate verifier is **not optimal as-is** for this repo.

Its core idea is good, but it is too tied to:

- Adaptabot namespaces
- typed interface handoffs between explicit numbered phases
- validation scripts that do not exist in this repo
- provider/security contracts specific to Adaptabot

## Recommended decision

Create a new repo-specific verifier instead of directly reusing the Adaptabot one.

Suggested file:

- `.github/agents/haaarp-phase-gate.agent.md`

## What the HAAARP verifier should check

- Preflight document completeness
- Root-doc consistency with implementation docs
- Config/schema/code alignment
- Gate sequencing correctness:
  DPIA, Pass 1 anchor, lens lock, human verdict completeness
- Prompt-file existence and prompt-hash recording expectations
- Local-only dependency/import enforcement
- Test-plan coverage against actual tests
- Missing promised assets such as schemas, notebook, adversarial test file
- CI/install-story consistency

## Why a new verifier is better here

This repo’s verification problem is less about rich typed contracts between modules and more about:

- governance invariants
- doc-to-implementation consistency
- scaffold-completeness verification
- artifact/schema presence

That warrants a different verifier design.

## Naming And Repo Identity Issues To Resolve

There is still a naming consistency issue across title, acronym, and repo slug.

Current state:

- docs title: `Agentic Human–AI Research Pipeline`
- requested GitHub repo slug: `uman-Agentic-AI-Adaptive-Research-Pipeline-HAAARP`

Recommended action:

- decide the canonical public name and acronym
- update README clone instructions and git remote accordingly
- if the GitHub slug intentionally differs from the public-facing title, document that once in README and do not repeat the explanation elsewhere

Also verify whether the leading `uman-` in the repo slug is intentional or a typo before updating `origin`.

## Suggested Execution Sequence After Review Approval

1. Add `LICENSE`.
2. Decide dependency manifest strategy and align README, runbook, and CI.
3. Remove and ignore `:Zone.Identifier` files.
4. Update `GUARDRAILS.md` and lightly update `COPILOT_INSTRUCTIONS.md`.
5. Make the minimal additive changes to `implementation docs/Agentic_Pipeline_Dev_Plan_v2.1.md`.
6. Align `implementation docs/TEST_PLAN.md` references or create the missing assets it expects.
7. Create `.github/agents/haaarp-coder.agent.md`.
8. Create `.github/agents/haaarp-phase-gate.agent.md`.
9. Update git remote to the new GitHub URL.
10. Commit and push once the approved alignment pass is complete.

## Decision Summary

- The new root docs should stay.
- Most changes should be made to the surrounding control docs and repo scaffolding, not to the new docs’ core direction.
- The dev plan should get only minimal additive edits.
- The Adaptabot coder agent is a good base pattern.
- The Adaptabot phase-gate agent should be replaced with a repo-specific verifier.
- The repo is close to being a good coding starting point, but not fully optimal until `LICENSE`, dependency manifest, custom agents, missing schemas/prompts, and verification assets are addressed.