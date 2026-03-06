# How to Comply with AGPL-3.0

This is a plain-English guide for organisations and developers who want to use the Agentic Human–AI Research Pipeline in a product or service and need to understand what the AGPL-3.0 licence requires of them.

*This is not legal advice. For formal legal review, consult a lawyer.*

---

## The key difference between AGPL and other open licences

Most permissive open-source licences (MIT, Apache-2.0) allow you to use code in a commercial product or hosted service without releasing your own source code. **AGPL-3.0 does not.**

AGPL-3.0 adds a "network use" clause: if you run a modified or unmodified copy of this software as a service that users interact with over a network (a web app, an API, a hosted research platform, a SaaS product), you must make the **complete corresponding source code** of that service available to those users under AGPL-3.0.

---

## Scenarios and what they require

### Scenario 1: Academic or research use, running locally

You run the pipeline on your own machine or university server to analyse your own research data. You do not offer it as a service to others.

**What AGPL requires:** Nothing beyond the standard conditions (preserve copyright notices, include the licence text). You can modify the code freely. You do not need to release your modifications.

### Scenario 2: You modify the code and share it with colleagues

You fork the repo, make changes, and give the modified code to collaborators.

**What AGPL requires:** You must provide the modified source code under AGPL-3.0 to whoever you distribute it to. In practice: share your fork on GitHub or include the source alongside the executable.

### Scenario 3: You build a hosted service or product using this pipeline

You integrate this pipeline into a platform that other people use — a research tool, a therapy session analysis service, a QDA platform, an internal enterprise tool accessible over a network.

**What AGPL requires:** You must make the complete corresponding source code of your service (including your modifications to this pipeline and any tightly integrated components) available to users of your service, under AGPL-3.0. "Users" means anyone who interacts with the service over the network.

**How to comply in practice:**
1. Host your full source code in a publicly accessible repository (GitHub, GitLab, etc.)
2. Include a prominent link to that repository in your service's interface (e.g. in a footer, an "About" page, or your API documentation)
3. The source must correspond to the version of the software actually running — keep it up to date

### Scenario 4: You want to use this pipeline in a commercial product without releasing your source code

You want to embed the pipeline in a closed commercial product or service and cannot or do not want to release your source code under AGPL-3.0.

**What you need:** A separate commercial licence. Contact the authors at `adaptagentic@proton.me` with a description of your intended use and deployment model. Commercial licences are available by arrangement and waive the source-disclosure obligations of AGPL-3.0.

---

## What you do NOT need to release

- Your research data or participant transcripts (data is not code)
- Your analysis outputs, findings, or reports
- Unrelated parts of your codebase that are not derived from or tightly integrated with this pipeline
- Your system prompts, if they are configuration inputs rather than modifications to the pipeline code itself (though this boundary can be ambiguous — seek legal advice if uncertain)

---

## Practical checklist for AGPL compliance (hosted service)

- [ ] Source code of the service (including pipeline modifications) is publicly available
- [ ] Source repository is linked from the service interface
- [ ] The linked source corresponds to the version currently deployed
- [ ] Copyright notices from the original repository are preserved
- [ ] The `LICENSE` file (AGPL-3.0 full text) is included in the source repository
- [ ] Any modifications are clearly marked as modifications

---

## Questions

If you are unsure whether your use case requires AGPL compliance or a commercial licence, contact `adaptagentic@proton.me` with a description of your use case. We are happy to clarify before you build.
