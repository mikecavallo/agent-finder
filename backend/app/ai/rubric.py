"""The explainable screening rubric.

Every provider (Claude, OpenAI or the offline mock) produces a 0.0-1.0 score and an
evidence sentence for each criterion. The overall 0-100 score is always computed here,
from the job's weights, so the ranking is consistent and auditable regardless of provider.
"""

from pydantic import BaseModel, Field

CRITERIA: dict[str, str] = {
    "licenses": "Insurance licenses",
    "sales": "Sales experience",
    "customer_service": "Customer service",
    "bilingual": "Language skills",
    "location": "Location fit",
}

DEFAULT_WEIGHTS: dict[str, int] = {
    "licenses": 30,
    "sales": 25,
    "customer_service": 20,
    "bilingual": 10,
    "location": 15,
}


class JobCriteria(BaseModel):
    """What the recruiter is screening for. Stored as JSON on the Job."""

    required_licenses: list[str] = Field(default_factory=lambda: ["P&C"])
    min_sales_years: float = 2
    customer_service_required: bool = True
    bilingual_preferred: bool = False
    languages: list[str] = Field(default_factory=lambda: ["Spanish"])
    weights: dict[str, int] = Field(default_factory=lambda: dict(DEFAULT_WEIGHTS))

    def effective_weights(self, location: str) -> dict[str, int]:
        """Weights actually applied: unused criteria get weight 0."""
        weights = {key: max(0, int(self.weights.get(key, DEFAULT_WEIGHTS[key]))) for key in CRITERIA}
        if not self.bilingual_preferred:
            weights["bilingual"] = 0
        if not self.customer_service_required:
            weights["customer_service"] = 0
        if not location.strip():
            weights["location"] = 0
        return weights


class CriterionResult(BaseModel):
    key: str
    label: str
    weight: int
    score: float  # 0.0 - 1.0
    evidence: str


def aggregate(
    assessments: dict[str, tuple[float, str]], weights: dict[str, int]
) -> tuple[float, list[CriterionResult]]:
    """Combine per-criterion scores into a weighted 0-100 total plus a breakdown."""
    breakdown: list[CriterionResult] = []
    total_weight = sum(weights.values())
    weighted = 0.0
    for key, label in CRITERIA.items():
        weight = weights.get(key, 0)
        raw, evidence = assessments.get(key, (0.0, "Not assessed."))
        score = min(1.0, max(0.0, float(raw)))
        if weight == 0:
            evidence = "Not weighted for this opening."
        weighted += weight * score
        breakdown.append(
            CriterionResult(key=key, label=label, weight=weight, score=round(score, 2), evidence=evidence)
        )
    total = round(100 * weighted / total_weight, 1) if total_weight else 0.0
    return total, breakdown
