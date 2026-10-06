"""LLM providers tested with fake clients. No network calls, no API keys."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from app.ai.providers import (
    AnthropicProvider,
    JobContext,
    LLMScreening,
    OpenAIProvider,
    ProviderError,
    set_provider_override,
)
from app.ai.rubric import JobCriteria

from .conftest import RESUME_STRONG

LLM_PAYLOAD = {
    "profile": {
        "name": "Riley Strong",
        "email": None,
        "phone": None,
        "location": "Wilmington, NC",
        "current_title": "Insurance Sales Agent",
        "licenses": ["P&C", "Life & Health"],
        "languages": ["English", "Spanish"],
        "years_sales": 5,
        "years_customer_service": 3,
        "summary": "Licensed bilingual agent.",
    },
    "assessments": {
        "licenses": {"score": 1.0, "evidence": "Holds NC P&C and L&H."},
        "sales": {"score": 1.0, "evidence": "Five years selling insurance."},
        "customer_service": {"score": 0.9, "evidence": "Three years as a bank CSR."},
        "bilingual": {"score": 1.0, "evidence": "Fluent Spanish."},
        "location": {"score": 1.0, "evidence": "Lives in Wilmington."},
    },
    "strengths": ["Licensed", "Bilingual"],
    "concerns": [],
}

CTX = JobContext(title="Agent", location="Wilmington, NC", description="", criteria=JobCriteria())


class FakeAnthropicMessages:
    def __init__(self, stop_reason="end_turn"):
        self.stop_reason = stop_reason
        self.calls = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        parsed = LLMScreening.model_validate(LLM_PAYLOAD) if self.stop_reason == "end_turn" else None
        return SimpleNamespace(stop_reason=self.stop_reason, parsed_output=parsed)

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text="Subject: Hello\n\nHi Riley,")],
        )


def test_anthropic_provider_maps_structured_output():
    messages = FakeAnthropicMessages()
    provider = AnthropicProvider("k", "claude-sonnet-5-5", client=SimpleNamespace(messages=messages))
    result = asyncio.run(provider.screen(RESUME_STRONG, CTX))

    call = messages.calls[0]
    assert call["model"] == "claude-sonnet-5-5"
    assert call["output_format"] is LLMScreening
    assert "<resume>" in call["messages"][0]["content"]
    assert result.scored_by == "anthropic:claude-sonnet-5-5"
    assert result.assessments["customer_service"] == (0.9, "Three years as a bank CSR.")
    # Fields the LLM left empty are filled from the regex extractor.
    assert result.profile.email == "riley.strong@example.com"


def test_anthropic_refusal_raises():
    provider = AnthropicProvider("k", "m", client=SimpleNamespace(messages=FakeAnthropicMessages("refusal")))
    with pytest.raises(ProviderError):
        asyncio.run(provider.screen(RESUME_STRONG, CTX))


def test_openai_provider_parses_json():
    class FakeCompletions:
        async def create(self, **kwargs):
            assert kwargs["response_format"] == {"type": "json_object"}
            msg = SimpleNamespace(content=json.dumps(LLM_PAYLOAD))
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    result = asyncio.run(OpenAIProvider("k", "gpt-test", client=client).screen(RESUME_STRONG, CTX))
    assert result.scored_by == "openai:gpt-test"
    assert result.assessments["licenses"][0] == 1.0


def test_openai_invalid_json_raises():
    class FakeCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    with pytest.raises(ProviderError):
        asyncio.run(OpenAIProvider("k", "m", client=client).screen(RESUME_STRONG, CTX))


def test_api_uses_llm_provider_and_reports_failures(client, auth, job):
    set_provider_override(
        AnthropicProvider("k", "claude-sonnet-5-5", client=SimpleNamespace(messages=FakeAnthropicMessages()))
    )
    r = client.post(f"/api/jobs/{job['id']}/candidates/text", headers=auth, json={"text": RESUME_STRONG})
    assert r.status_code == 201
    assert r.json()["scored_by"] == "anthropic:claude-sonnet-5-5"
    assert r.json()["score"] == 98.0  # 0.9 on customer service (weight 20) -> 100 - 2

    set_provider_override(
        AnthropicProvider("k", "m", client=SimpleNamespace(messages=FakeAnthropicMessages("refusal")))
    )
    r = client.post(f"/api/jobs/{job['id']}/candidates/text", headers=auth, json={"text": RESUME_STRONG})
    assert r.status_code == 502
