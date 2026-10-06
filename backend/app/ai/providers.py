"""LLM provider abstraction: Anthropic Claude (default), OpenAI (optional), and an offline mock.

All providers return the same ScreeningResult; the overall score is computed by
app.ai.rubric.aggregate so it is comparable across providers.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel

from ..config import Settings
from .extraction import IN_PROGRESS, ExtractedProfile, extract_profile
from .prompts import OUTREACH_SYSTEM, SCREENING_SYSTEM, outreach_prompt, screening_prompt
from .rubric import CRITERIA, JobCriteria

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Raised when an LLM provider cannot produce a usable result."""


@dataclass
class JobContext:
    title: str
    location: str
    description: str
    criteria: JobCriteria


@dataclass
class ScreeningResult:
    profile: ExtractedProfile
    assessments: dict[str, tuple[float, str]]
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    scored_by: str = "mock"


# ---------------------------------------------------------------------------
# Structured output schema shared by the LLM providers
# ---------------------------------------------------------------------------


class LLMProfile(BaseModel):
    name: str
    email: str | None
    phone: str | None
    location: str | None
    current_title: str | None
    licenses: list[str]
    languages: list[str]
    years_sales: float | None
    years_customer_service: float | None
    summary: str


class LLMCriterion(BaseModel):
    score: float
    evidence: str


class LLMAssessments(BaseModel):
    licenses: LLMCriterion
    sales: LLMCriterion
    customer_service: LLMCriterion
    bilingual: LLMCriterion
    location: LLMCriterion


class LLMScreening(BaseModel):
    profile: LLMProfile
    assessments: LLMAssessments
    strengths: list[str]
    concerns: list[str]


def _from_llm(parsed: LLMScreening, resume_text: str, scored_by: str) -> ScreeningResult:
    """Convert LLM output to a ScreeningResult, filling gaps from the regex extractor."""
    fallback = extract_profile(resume_text).profile
    data = parsed.profile.model_dump()
    for key in ("email", "phone", "location"):
        if not data.get(key):
            data[key] = getattr(fallback, key)
    if not data.get("name"):
        data["name"] = fallback.name
    profile = ExtractedProfile(**data)
    assessments = {
        key: (getattr(parsed.assessments, key).score, getattr(parsed.assessments, key).evidence)
        for key in CRITERIA
    }
    return ScreeningResult(
        profile=profile,
        assessments=assessments,
        strengths=parsed.strengths[:3],
        concerns=parsed.concerns[:3],
        scored_by=scored_by,
    )


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


class ScoringProvider:
    name = "base"

    @property
    def label(self) -> str:
        return self.name

    async def screen(self, resume_text: str, job: JobContext) -> ScreeningResult:
        raise NotImplementedError

    async def draft_outreach(
        self, candidate: ExtractedProfile, highlights: list[str], job: JobContext, recruiter_name: str
    ) -> str:
        raise NotImplementedError


def _norm(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "")


class MockProvider(ScoringProvider):
    """Deterministic, offline scorer built on the regex extractor. No network, no API key."""

    name = "mock"

    def __init__(self, today: date | None = None):
        self.today = today

    async def screen(self, resume_text: str, job: JobContext) -> ScreeningResult:
        heuristic = extract_profile(resume_text, today=self.today)
        p = heuristic.profile
        c = job.criteria
        a: dict[str, tuple[float, str]] = {}

        required = c.required_licenses
        held = [lic for lic in required if _norm(lic) in {_norm(x) for x in p.licenses}]
        if required:
            score = len(held) / len(required)
            missing = [lic for lic in required if lic not in held]
            if held and not missing:
                a["licenses"] = (score, f"Holds all required licenses ({', '.join(held)}).")
            elif held:
                a["licenses"] = (score, f"Holds {', '.join(held)}; missing {', '.join(missing)}.")
            elif any(IN_PROGRESS.search(ln) and "licens" in ln.lower() for ln in resume_text.splitlines()):
                a["licenses"] = (0.25, "Licensing is in progress; required licenses not yet held.")
            else:
                a["licenses"] = (0.0, f"No mention of required licenses ({', '.join(required)}).")
        else:
            a["licenses"] = (
                1.0 if p.licenses else 0.5,
                f"Licenses found: {', '.join(p.licenses) or 'none'}.",
            )

        yrs = p.years_sales or 0.0
        if c.min_sales_years > 0:
            a["sales"] = (
                min(1.0, yrs / c.min_sales_years),
                f"About {yrs:g} years in sales roles (minimum {c.min_sales_years:g}).",
            )
        else:
            a["sales"] = (1.0 if yrs > 0 else 0.3, f"About {yrs:g} years in sales roles.")

        cs = p.years_customer_service or 0.0
        if cs >= 1:
            a["customer_service"] = (1.0, f"About {cs:g} years in customer-facing service roles.")
        elif cs > 0 or heuristic.sales_roles:
            a["customer_service"] = (
                0.5,
                "Customer contact through sales roles; little dedicated service experience.",
            )
        else:
            a["customer_service"] = (0.0, "No customer service experience mentioned.")

        wanted = [lang for lang in c.languages if lang in p.languages]
        if wanted:
            a["bilingual"] = (1.0, f"Speaks {', '.join(wanted)}.")
        else:
            a["bilingual"] = (0.0, f"No mention of {', '.join(c.languages) or 'additional languages'}.")

        a["location"] = self._location(p.location, job.location, heuristic.relocation_ok)

        # Strengths and concerns, most heavily weighted criteria first; unweighted ones skipped.
        weights = c.effective_weights(job.location)
        strengths, concerns = [], []
        for key in sorted(a, key=lambda k: -weights[k]):
            score, evidence = a[key]
            if weights[key] == 0:
                continue
            if score >= 0.75:
                strengths.append(evidence)
            elif score < 0.4:
                concerns.append(evidence)

        return ScreeningResult(
            profile=p, assessments=a, strengths=strengths[:3], concerns=concerns[:3], scored_by=self.label
        )

    @staticmethod
    def _location(candidate_loc: str | None, job_loc: str, relocation_ok: bool) -> tuple[float, str]:
        if not job_loc.strip():
            return 1.0, "No location requirement."
        if not candidate_loc:
            return (
                (0.3, "Location not stated; mentions willingness to relocate.")
                if relocation_ok
                else (0.0, "Location not stated.")
            )
        cand_city, _, cand_state = (part.strip().lower() for part in candidate_loc.partition(","))
        job_city, _, job_state = (part.strip().lower() for part in job_loc.partition(","))
        if cand_city == job_city and cand_state == job_state:
            return 1.0, f"Based in {candidate_loc}."
        if cand_state and cand_state == job_state:
            return 0.6, f"Based in {candidate_loc}, same state as the role."
        if relocation_ok:
            return 0.3, f"Based in {candidate_loc}; open to relocating."
        return 0.0, f"Based in {candidate_loc}, outside the role's area."

    async def draft_outreach(self, candidate, highlights, job, recruiter_name):
        first = candidate.name.split()[0] if candidate.name else "there"
        where = f" in {job.location}" if job.location else ""
        points = [re.sub(r"\s*\(minimum[^)]*\)", "", h).rstrip(".") for h in highlights[:2]]
        points = [p[0].lower() + p[1:] for p in points if p]
        stood_out = (
            f"A couple of things stood out on your resume: {'; '.join(points)}."
            if points
            else "Your background caught my attention."
        )
        return (
            f"Subject: {job.title} opportunity{where}\n\n"
            f"Hi {first},\n\n"
            f"I'm {recruiter_name}, and I'm hiring for a {job.title} role{where}. {stood_out}\n\n"
            "Would you be open to a 15-minute call this week to talk about the role and what you're "
            "looking for next?\n\n"
            f"Best regards,\n{recruiter_name}"
        )


class AnthropicProvider(ScoringProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, effort: str = "medium", client=None):
        if client is None:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=api_key)
        self.client = client
        self.model = model
        self.effort = effort

    @property
    def label(self) -> str:
        return f"anthropic:{self.model}"

    async def screen(self, resume_text, job):
        import anthropic

        try:
            response = await self.client.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=SCREENING_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": screening_prompt(
                            resume_text, job.title, job.location, job.description, job.criteria
                        ),
                    }
                ],
                output_format=LLMScreening,
                output_config={"effort": self.effort},
            )
        except anthropic.APIError as exc:
            raise ProviderError(f"Claude request failed: {exc}") from exc
        if response.stop_reason == "refusal":
            raise ProviderError("Claude declined to screen this resume.")
        if response.parsed_output is None:
            raise ProviderError(f"Claude returned no structured output (stop_reason={response.stop_reason}).")
        return _from_llm(response.parsed_output, resume_text, self.label)

    async def draft_outreach(self, candidate, highlights, job, recruiter_name):
        import anthropic

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=OUTREACH_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": outreach_prompt(
                            candidate.name,
                            candidate.summary,
                            highlights,
                            job.title,
                            job.location,
                            recruiter_name,
                        ),
                    }
                ],
                output_config={"effort": "low"},
            )
        except anthropic.APIError as exc:
            raise ProviderError(f"Claude request failed: {exc}") from exc
        if response.stop_reason == "refusal":
            raise ProviderError("Claude declined to draft this email.")
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            raise ProviderError("Claude returned an empty draft.")
        return text


class OpenAIProvider(ScoringProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, client=None):
        if client is None:
            import openai

            client = openai.AsyncOpenAI(api_key=api_key)
        self.client = client
        self.model = model

    @property
    def label(self) -> str:
        return f"openai:{self.model}"

    async def screen(self, resume_text, job):
        import openai

        schema = json.dumps(LLMScreening.model_json_schema())
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": f"{SCREENING_SYSTEM}\n\nRespond with JSON matching this schema:\n{schema}",
                    },
                    {
                        "role": "user",
                        "content": screening_prompt(
                            resume_text, job.title, job.location, job.description, job.criteria
                        ),
                    },
                ],
            )
        except openai.OpenAIError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        try:
            parsed = LLMScreening.model_validate_json(response.choices[0].message.content or "")
        except ValueError as exc:
            raise ProviderError(f"OpenAI returned invalid JSON: {exc}") from exc
        return _from_llm(parsed, resume_text, self.label)

    async def draft_outreach(self, candidate, highlights, job, recruiter_name):
        import openai

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": OUTREACH_SYSTEM},
                    {
                        "role": "user",
                        "content": outreach_prompt(
                            candidate.name,
                            candidate.summary,
                            highlights,
                            job.title,
                            job.location,
                            recruiter_name,
                        ),
                    },
                ],
            )
        except openai.OpenAIError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError("OpenAI returned an empty draft.")
        return text


_provider_override: ScoringProvider | None = None


def set_provider_override(provider: ScoringProvider | None) -> None:
    """Used by tests to inject a provider."""
    global _provider_override
    _provider_override = provider


_provider_cache: dict[tuple, ScoringProvider] = {}


def get_provider(settings: Settings) -> ScoringProvider:
    """Return the configured provider, falling back to the mock when no API key is set."""
    if _provider_override is not None:
        return _provider_override
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        key = ("anthropic", settings.anthropic_api_key, settings.anthropic_model, settings.anthropic_effort)
        if key not in _provider_cache:
            _provider_cache[key] = AnthropicProvider(
                settings.anthropic_api_key, settings.anthropic_model, settings.anthropic_effort
            )
        return _provider_cache[key]
    if settings.llm_provider == "openai" and settings.openai_api_key:
        key = ("openai", settings.openai_api_key, settings.openai_model)
        if key not in _provider_cache:
            _provider_cache[key] = OpenAIProvider(settings.openai_api_key, settings.openai_model)
        return _provider_cache[key]
    if settings.llm_provider != "mock" and ("fallback-warned",) not in _provider_cache:
        logger.warning(
            "LLM_PROVIDER=%s but no API key is set; using the offline mock scorer.", settings.llm_provider
        )
        _provider_cache[("fallback-warned",)] = MockProvider()
    return MockProvider()
