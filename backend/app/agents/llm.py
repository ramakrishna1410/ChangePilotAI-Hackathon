"""Thin LLM client wrapper shared by all agents.

Swapping to Azure OpenAI in production means changing only this file (use
`AzureOpenAI` client with endpoint/deployment instead of `OpenAI` with an
API key) — no agent logic changes.
"""
from __future__ import annotations

import json

from openai import OpenAI

from app.config import CHAT_MODEL, OPENAI_API_KEY

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def call_structured(system_prompt: str, user_prompt: str) -> dict:
    """Calls the chat model in JSON mode and returns the parsed JSON object.

    Retrieved evidence is always passed inside the user message as clearly
    delimited, quoted reference data (see rag/retriever.format_evidence_block)
    — it is never treated as instructions, per §6.3 of the design doc.
    """
    response = _get_client().chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        seed=42,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    return json.loads(content)
