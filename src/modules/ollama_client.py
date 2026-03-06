"""
Ollama REST client — local-only LLM interface.

All data stays on-device. Never calls external endpoints.
api_base defaults to http://localhost:11434 (Ollama default).

If MOCK_LLM=true (env var), returns synthetic responses without network access.
Required for all automated tests — always set MOCK_LLM=true in test runs.
"""
import os
import json
from typing import Optional


# ── Synthetic mock responses ─────────────────────────────────────────────────

_MOCK_PASS1_RESPONSE = json.dumps({
    "strand": "IPA",
    "run_label": "pass1_blind",
    "pass1_themes": [
        {
            "theme_id": "T1",
            "label": "Difficulty articulating distress",
            "candidate_statements": ["felt like too much to explain"],
            "participant_codes": [],
            "excerpt_count": 1,
        },
        {
            "theme_id": "T2",
            "label": "Anticipation of not being understood",
            "candidate_statements": ["no one would quite understand what I meant"],
            "participant_codes": [],
            "excerpt_count": 1,
        },
    ],
})

_MOCK_PASS2_RESPONSE = json.dumps({
    "strand": "IPA",
    "run_label": "seed42",
    "claims": [
        {
            "claim_id": "CL001",
            "claim_text": "Participants demonstrated ambivalence about help-seeking.",
            "supporting_segments": [],
            "confidence": "moderate",
        },
        {
            "claim_id": "CL002",
            "claim_text": "Anticipation of misunderstanding functioned as a relational barrier.",
            "supporting_segments": [],
            "confidence": "moderate",
        },
    ],
})

_MOCK_LENS_SUMMARY = (
    "1. Theoretical framework: Constructivist phenomenological approach informed by "
    "embodied cognition and relational psychoanalytic theory.\n"
    "2. Researcher positionality: Clinical background in integrative therapy with "
    "particular attentiveness to rupture, repair, and shame dynamics.\n"
    "3. Explicit hypotheses going into Pass 2: Participants will express ambivalence "
    "about help-seeking; help-seeking language will be hedged or qualified.\n"
    "4. Concepts to be sensitive to: rupture, repair, embodied experience, hedging, "
    "qualification, shame, proximity, distance.\n"
    "5. Disconfirmation mandate: Surface material that resists the lens equally to "
    "material that confirms it. The gap is analytically generative.\n"
    "6. Pass 1 surprises: Embodied sensory language was more prominent than expected."
)


# ── Client ───────────────────────────────────────────────────────────────────

def call_generate(
    api_base: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    seed: Optional[int] = None,
    expect_json: bool = True,
) -> str:
    """
    POST to Ollama /api/generate. Returns model response text.

    If MOCK_LLM=true, returns synthetic data without any network access.
    Raises ValueError if the server is unreachable or the response is malformed.

    Args:
        api_base:      Ollama base URL, e.g. http://localhost:11434
        model:         Model name, e.g. qwen2.5-27b-instruct
        system_prompt: System instruction passed to the model
        user_prompt:   Data / user turn passed to the model
        temperature:   Sampling temperature (0.0 for deterministic)
        seed:          Optional integer seed for reproducibility
        expect_json:   Informational only; response is always returned as str
    """
    if os.environ.get("MOCK_LLM", "").lower() == "true":
        return _mock_response(system_prompt, seed, temperature)

    try:
        import urllib.request

        payload: dict = {
            "model": model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if seed is not None:
            payload["options"]["seed"] = seed

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{api_base}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("response", "")

    except Exception as exc:
        raise ValueError(
            f"[ERR_PREFLIGHT_MISSING] Ollama not reachable at {api_base}.\n"
            f"Action: Start Ollama with: ollama serve\n"
            f"        Then pull the model: ollama pull {model}\n"
            f"Detail: {exc}"
        ) from exc


def _mock_response(system_prompt: str, seed: Optional[int], temperature: float) -> str:
    """Return the appropriate synthetic mock based on the system prompt content."""
    lc = system_prompt.lower()
    if "blind analysis" in lc or "pass 1" in lc:
        return _MOCK_PASS1_RESPONSE
    if "lens-informed" in lc or "pass 2" in lc:
        resp = json.loads(_MOCK_PASS2_RESPONSE)
        if seed is not None:
            resp["run_label"] = f"seed{seed}"
        elif temperature == 0.0:
            resp["run_label"] = "deterministic"
        return json.dumps(resp)
    return _MOCK_LENS_SUMMARY
