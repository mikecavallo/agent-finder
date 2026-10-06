"""Deterministic, regex-based resume extraction.

Used by the offline mock provider and as a fallback for fields an LLM leaves empty.
It is intentionally simple: it works well on conventionally formatted resumes and is
meant for demos and tests, not as a replacement for the LLM providers.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel, Field

LICENSE_PATTERNS: dict[str, re.Pattern] = {
    "P&C": re.compile(r"property\s*(?:and|&)\s*casualty|\bP\s*&\s*C\b|\bP/C\b", re.I),
    "Life & Health": re.compile(
        r"life\s*(?:and|&)\s*health|\bL\s*&\s*H\b|life,\s*accident\s*(?:and|&)\s*health", re.I
    ),
    "Personal Lines": re.compile(r"personal\s+lines\s+(?:license|licensed|producer)", re.I),
    "Series 6": re.compile(r"series\s*6\b", re.I),
    "Series 7": re.compile(r"series\s*7\b", re.I),
    "Series 63": re.compile(r"series\s*63\b", re.I),
}

KNOWN_LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "Portuguese",
    "Mandarin",
    "Cantonese",
    "Vietnamese",
    "Korean",
    "Tagalog",
    "Arabic",
    "Russian",
    "German",
    "Italian",
    "Haitian Creole",
    "Hindi",
]

IN_PROGRESS = re.compile(r"pursuing|studying|in progress|scheduled|preparing for|working toward", re.I)
SALES_WORDS = re.compile(r"\bsales\b|account executive|business development|producer|\bagent\b|quota", re.I)
SERVICE_WORDS = re.compile(
    r"customer service|client service|customer support|service representative|call center|customer success|\bCSR\b|teller|concierge",
    re.I,
)

YEAR_RANGE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
CITY_STATE = re.compile(r"\b([A-Z][a-zA-Z.\s]+),\s*([A-Z]{2})\b")
EXPLICIT_YEARS = re.compile(
    r"(\d{1,2}(?:\.\d)?)\+?\s*years?\s+(?:of\s+)?(?:\w+\s+){0,3}?(sales|customer service|client service)",
    re.I,
)


class ExtractedProfile(BaseModel):
    name: str = "Unknown candidate"
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    current_title: str | None = None
    licenses: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    years_sales: float | None = None
    years_customer_service: float | None = None
    summary: str = ""


@dataclass
class _Role:
    line: str
    text: str
    years: float


@dataclass
class HeuristicResult:
    profile: ExtractedProfile
    sales_roles: list[str] = field(default_factory=list)
    service_roles: list[str] = field(default_factory=list)
    relocation_ok: bool = False


def _roles(lines: list[str], today: date) -> list[_Role]:
    roles = []
    for i, line in enumerate(lines):
        match = YEAR_RANGE.search(line)
        if not match:
            continue
        start = int(match.group(1))
        end_raw = match.group(2).lower()
        end = today.year if end_raw in ("present", "current") else int(end_raw)
        # Classify the role from its own line; fall back to the previous line when the
        # dates sit alone (e.g. "2018 - 2021" under a "Title, Company" line).
        own_words = YEAR_RANGE.sub("", line).strip(" |,-()")
        context = line if len(own_words) > 3 else " ".join(lines[max(0, i - 1) : i + 1])
        roles.append(_Role(line=line, text=context, years=max(0.0, float(end - start))))
    return roles


def extract_profile(text: str, today: date | None = None) -> HeuristicResult:
    today = today or date.today()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    profile = ExtractedProfile()
    if lines:
        profile.name = lines[0][:120]

    if m := EMAIL.search(text):
        profile.email = m.group(0)
    if m := PHONE.search(text):
        profile.phone = m.group(0).strip()
    for line in lines[:6]:
        if m := CITY_STATE.search(line):
            profile.location = f"{m.group(1).strip()}, {m.group(2)}"
            break

    # Lines like "studying for my P&C license" must not count as holding the license.
    held_lines = [ln for ln in lines if not IN_PROGRESS.search(ln)]
    profile.licenses = [
        name for name, pattern in LICENSE_PATTERNS.items() if any(pattern.search(ln) for ln in held_lines)
    ]
    profile.languages = [lang for lang in KNOWN_LANGUAGES if re.search(rf"\b{lang}\b", text)]
    if "English" not in profile.languages:
        profile.languages.insert(0, "English")

    roles = _roles(lines, today)
    sales_roles = [r for r in roles if SALES_WORDS.search(r.text)]
    service_roles = [r for r in roles if SERVICE_WORDS.search(r.text)]
    years_sales = sum(r.years for r in sales_roles)
    years_service = sum(r.years for r in service_roles)
    for m in EXPLICIT_YEARS.finditer(text):
        value = float(m.group(1))
        if m.group(2).lower() == "sales":
            years_sales = max(years_sales, value)
        else:
            years_service = max(years_service, value)
    profile.years_sales = years_sales if (sales_roles or years_sales) else 0.0
    profile.years_customer_service = years_service if (service_roles or years_service) else 0.0

    if roles:
        profile.current_title = YEAR_RANGE.sub("", roles[0].line).split("|")[0].strip(" ,-|")[:120] or None

    summary_lines = [ln for ln in lines[1:8] if len(ln) > 60 and not EMAIL.search(ln)]
    profile.summary = summary_lines[0][:400] if summary_lines else ""

    return HeuristicResult(
        profile=profile,
        sales_roles=[r.text for r in sales_roles],
        service_roles=[r.text for r in service_roles],
        relocation_ok=bool(re.search(r"relocat", text, re.I)),
    )
