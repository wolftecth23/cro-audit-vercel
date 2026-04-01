"""Normalized CRO evidence models shared across input sources."""

from __future__ import annotations

from dataclasses import dataclass, field


ALL_CRO_CATEGORIES: tuple[str, ...] = (
    "above_the_fold_clarity",
    "value_proposition_strength",
    "cta_visibility_and_strength",
    "social_proof_presence",
    "trust_signals",
    "pricing_psychology",
    "offer_structure",
    "mobile_usability",
    "checkout_friction_risks",
    "urgency_and_scarcity",
    "copy_persuasion",
)

WEIGHTED_CRO_CATEGORIES: tuple[str, ...] = (
    "above_the_fold_clarity",
    "cta_visibility_and_strength",
    "social_proof_presence",
    "pricing_psychology",
    "mobile_usability",
    "offer_structure",
    "trust_signals",
    "urgency_and_scarcity",
    "copy_persuasion",
)


@dataclass
class EvidenceSignal:
    """Visibility and confidence for one CRO category."""

    confidence: str = "high"
    evidence_visibility: str = "visible"
    note: str | None = None


@dataclass
class CROEvidenceInput:
    """Source-agnostic CRO signals used by the scoring engine."""

    source_type: str
    headline: str | None = None
    subheadline: str | None = None
    body_text: str = ""
    cta_texts: list[str] = field(default_factory=list)
    cta_near_testimonial: bool | None = None
    bullets: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    reviews_texts: list[str] = field(default_factory=list)
    trust_texts: list[str] = field(default_factory=list)
    urgency_texts: list[str] = field(default_factory=list)
    price_texts: list[str] = field(default_factory=list)
    image_count: int = 0
    form_count: int = 0
    mobile_spacing_score: int = 0
    analysis_notes: list[str] = field(default_factory=list)
    category_signals: dict[str, EvidenceSignal] = field(default_factory=dict)
    recommended_next_uploads: list[str] = field(default_factory=list)


def default_category_signals(
    visibility: str = "visible",
    confidence: str = "high",
) -> dict[str, EvidenceSignal]:
    """Return a full CRO category visibility map."""

    return {
        category: EvidenceSignal(
            confidence=confidence,
            evidence_visibility=visibility,
        )
        for category in ALL_CRO_CATEGORIES
    }
