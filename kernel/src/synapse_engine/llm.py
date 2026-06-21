"""The LLM seam — one degrade-safe entry point for text generation.

Everything routes through `complete()`, which returns the model's text or
``None``. ``None`` is the signal to fall back to a deterministic floor (the
extractive answer, the heuristic flashcard, …), so the offline-first guarantee
holds: a missing `litellm`, an unreachable Ollama, or any provider error never
raises — it just degrades. Model + endpoint come from `Settings` (litellm picks
the provider from the `ollama/…` or `anthropic/…` prefix on `llm_model`).
"""

from __future__ import annotations

from synapse_engine.config import get_settings


def complete(system: str, user: str, *, temperature: float = 0.2) -> str | None:
    """Return the model's completion, or ``None`` to signal 'use the floor'."""
    try:
        import litellm
    except ImportError:
        return None  # `ai` extra not installed — caller degrades.

    # Degradation is a normal control path here, so keep litellm's error/help
    # banners out of the kernel logs.
    litellm.suppress_debug_info = True

    settings = get_settings()
    kwargs: dict = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if settings.llm_model.startswith("ollama/"):
        kwargs["api_base"] = settings.ollama_base
    if settings.anthropic_api_key and settings.llm_model.startswith("anthropic/"):
        kwargs["api_key"] = settings.anthropic_api_key

    try:
        resp = litellm.completion(**kwargs)
        return (resp.choices[0].message.content or "").strip() or None
    except Exception:
        # Unreachable model, bad model name, timeout — degrade, don't raise.
        return None
