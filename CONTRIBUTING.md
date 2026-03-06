# Contributing to the Agentic Human–AI Research Pipeline

Thank you for your interest in contributing. This document explains how to contribute code, documentation, or empirical findings, and the legal basis on which contributions are accepted.

---

## Developer Certificate of Origin (DCO)

This project uses the **Developer Certificate of Origin (DCO)** to confirm that contributors have the right to submit their contributions under the project's licence.

By making a contribution to this project you certify that:

1. The contribution was created in whole or in part by you, and you have the right to submit it under the open-source licence indicated in the file; or
2. The contribution is based upon previous work that, to the best of your knowledge, is covered under an appropriate open-source licence and you have the right to submit that work with modifications; or
3. The contribution was provided directly to you by some other person who certified (1) or (2) above, and you have not modified it; and
4. You understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information you submit with it, including your sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open-source licence(s) involved.

**To sign off:** add a `Signed-off-by` line to every commit message:

```
git commit -s -m "Your commit message"
```

This produces:

```
Your commit message

Signed-off-by: Your Name <your@email.com>
```

Commits without a sign-off will not be merged.

---

## Why DCO matters for this project

This project is dual-licensed: AGPL-3.0 for open use, and a separate commercial licence available on request. The DCO ensures that all contributions are properly licensed and that the maintainers can offer the codebase under commercial terms without legal ambiguity. You retain copyright on your contributions — the DCO is not a copyright transfer.

---

## What to contribute

**Empirical evaluations** — if you have piloted the pipeline in a real or simulated study, findings (positive or negative) are welcome. Open an Issue labelled `empirical-evaluation` with a brief description; we will discuss how to document and credit the contribution.

**Bug reports and governance issues** — use GitHub Issues. If you have found a way to circumvent a governance constraint (e.g. a path that allows Pass 2 to run before Pass 1 is anchored), label the issue `governance-bug` — these are treated as high priority.

**Method adaptations** — if you have configured the pipeline for a method not currently in the routing layer (e.g. grounded theory, narrative analysis, content analysis), a PR with the new method config and associated test fixtures is welcome.

**Documentation fixes** — typos, broken links, and unclear instructions can be fixed via PR with no prior discussion needed.

---

## Governance constraints apply to contributions

The `GUARDRAILS.md` and `COPILOT_INSTRUCTIONS.md` files define constraints that apply to AI-assisted development of this repository. The same constraints apply to human contributions:

- Do not remove or weaken governance checks (DPIA gate, Pass 1 lock, human verdict requirement)
- Do not add network calls, cloud API dependencies, or external data transmission
- Do not auto-populate fields that require human authorship (lens responses, theory_signoff justification)
- All new modules and governance changes must have corresponding tests in `tests/`

---

## Code style

- Python 3.10+
- PEP 8 with 100-character line limit
- All exit codes must match the definitions in `docs/error_codes.md`
- JSON schema changes must be covered by tests in `tests/` and pass `pytest tests/ -v`

---

## Licence for contributions

By contributing you agree that your contribution is licensed under AGPL-3.0 (for code) and CC BY 4.0 (for documentation in `docs/`, root repository documentation, and `implementation docs/`), consistent with the project's dual-licence structure. The maintainers reserve the right to offer the codebase, including your contribution, under a commercial licence to third parties, as described in `COMMERCIAL_LICENSE.md`. This does not affect your own rights to use your contribution.
