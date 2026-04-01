"""Top-level orchestration for the CRO audit engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.cro.cro_scoring import CROScoringEngine
from app.cro.evidence import CROEvidenceInput, EvidenceSignal
from app.cro.heuristic_rules import HeuristicAnalysis, HeuristicRuleEngine, ProductPageParser
from app.cro.rewrite_engine import CRORewriteEngine
from app.cro.vision_service import GoogleAICROVisionService


class CROAuditInput(BaseModel):
    """Input payload accepted by the CRO audit engine."""

    store_url: str = Field(default="", description="Store or product URL.")
    product_page_html: str | None = Field(default=None, description="Raw product page HTML.")
    product_price: float = Field(..., gt=0)
    target_audience: str = Field(..., min_length=2)
    traffic_source: str = Field(..., min_length=2)
    device_focus: str = Field(..., min_length=6, description="Typically Mobile or Desktop.")


class ScreenshotAuditRequest(BaseModel):
    product_price: float = Field(..., gt=0)
    target_audience: str = Field(..., min_length=2)
    traffic_source: str = Field(..., min_length=2)
    device_focus: str = Field(..., min_length=6)
    store_url: str = ""
    product_page_html: str | None = None
    save_image: bool = False


class AuditFix(BaseModel):
    issue: str
    recommendation: str
    expected_impact: str


class ABTestIdea(BaseModel):
    hypothesis: str
    variant: str
    primary_metric: str


class PsychologicalImprovement(BaseModel):
    principle: str
    suggestion: str


class RewriteSuggestions(BaseModel):
    headline: str
    bullets: list[str]
    cta_text: str
    bundle_pricing: str


class CategoryConfidence(BaseModel):
    confidence: str
    evidence_visibility: str
    note: str | None = None


class CROAuditResult(BaseModel):
    cro_score: int
    biggest_leak: str
    high_priority_fixes: list[AuditFix]
    medium_priority_fixes: list[AuditFix]
    low_priority_fixes: list[AuditFix]
    ab_test_ideas: list[ABTestIdea]
    psychological_improvements: list[PsychologicalImprovement]
    mobile_specific_improvements: list[str]
    category_scores: dict[str, int]
    rewrite_suggestions: RewriteSuggestions
    analysis_notes: list[str] = Field(default_factory=list)
    overall_confidence: str = "high"
    category_confidence: dict[str, CategoryConfidence] = Field(default_factory=dict)
    missing_evidence_notes: list[str] = Field(default_factory=list)
    recommended_next_uploads: list[str] = Field(default_factory=list)
    saved_image_path: str | None = None


class CROAuditEngine:
    """Composable orchestration layer for generic e-commerce CRO audits."""

    def __init__(
        self,
        parser: ProductPageParser | None = None,
        rule_engine: HeuristicRuleEngine | None = None,
        scoring_engine: CROScoringEngine | None = None,
        rewrite_engine: CRORewriteEngine | None = None,
        vision_service: GoogleAICROVisionService | None = None,
    ) -> None:
        self.parser = parser or ProductPageParser()
        self.rule_engine = rule_engine or HeuristicRuleEngine()
        self.scoring_engine = scoring_engine or CROScoringEngine()
        self.rewrite_engine = rewrite_engine or CRORewriteEngine()
        self.vision_service = vision_service or GoogleAICROVisionService()

    def run_audit(self, audit_input: CROAuditInput) -> CROAuditResult:
        page = self.parser.parse(
            store_url=audit_input.store_url,
            product_page_html=audit_input.product_page_html,
        )
        evidence = self.parser.to_evidence(page)
        return self.run_audit_from_evidence(
            evidence=evidence,
            audit_input=audit_input,
        )

    def run_screenshot_audit(
        self,
        request: ScreenshotAuditRequest,
        image_bytes: bytes,
        mime_type: str,
        saved_image_path: str | None = None,
    ) -> CROAuditResult:
        evidence = self.vision_service.extract_evidence(
            image_bytes=image_bytes,
            mime_type=mime_type,
            device_focus=request.device_focus,
        )

        if request.product_page_html or request.store_url:
            evidence.analysis_notes.append(
                "Advanced fallback inputs were provided but the screenshot analysis remained the primary evidence source."
            )

        result = self.run_audit_from_evidence(
            evidence=evidence,
            audit_input=CROAuditInput(
                store_url=request.store_url,
                product_page_html=request.product_page_html,
                product_price=request.product_price,
                target_audience=request.target_audience,
                traffic_source=request.traffic_source,
                device_focus=request.device_focus,
            ),
        )
        result.saved_image_path = saved_image_path
        return result

    def run_audit_from_evidence(
        self,
        evidence: CROEvidenceInput,
        audit_input: CROAuditInput,
    ) -> CROAuditResult:
        analysis = self.rule_engine.analyze(
            evidence=evidence,
            product_price=audit_input.product_price,
            target_audience=audit_input.target_audience,
            traffic_source=audit_input.traffic_source,
            device_focus=audit_input.device_focus,
        )

        weighted_scores = self._build_weighted_scores(analysis)
        return CROAuditResult(
            cro_score=self.scoring_engine.calculate(weighted_scores),
            biggest_leak=analysis.biggest_leak,
            high_priority_fixes=self._serialize_fixes(analysis, "High"),
            medium_priority_fixes=self._serialize_fixes(analysis, "Medium"),
            low_priority_fixes=self._serialize_fixes(analysis, "Low"),
            ab_test_ideas=self._build_ab_tests(evidence, audit_input, analysis),
            psychological_improvements=self._build_psychological_improvements(analysis),
            mobile_specific_improvements=self._build_mobile_improvements(evidence, analysis),
            category_scores=analysis.category_scores,
            rewrite_suggestions=self._build_rewrites(evidence, audit_input),
            analysis_notes=analysis.analysis_notes,
            overall_confidence=analysis.overall_confidence,
            category_confidence=self._serialize_category_confidence(analysis.category_confidence),
            missing_evidence_notes=analysis.missing_evidence_notes,
            recommended_next_uploads=analysis.recommended_next_uploads,
        )

    def _build_weighted_scores(self, analysis: HeuristicAnalysis) -> dict[str, int]:
        scores = dict(analysis.category_scores)
        scores["copy_persuasion"] = round(
            (scores.get("copy_persuasion", 0) + scores.get("value_proposition_strength", 0)) / 2
        )
        return scores

    def _serialize_fixes(self, analysis: HeuristicAnalysis, priority: str) -> list[AuditFix]:
        return [
            AuditFix(
                issue=issue.issue,
                recommendation=issue.recommendation,
                expected_impact=issue.expected_impact,
            )
            for issue in analysis.issues
            if issue.expected_impact == priority
        ]

    def _serialize_category_confidence(
        self,
        category_confidence: dict[str, EvidenceSignal],
    ) -> dict[str, CategoryConfidence]:
        return {
            category: CategoryConfidence(
                confidence=signal.confidence,
                evidence_visibility=signal.evidence_visibility,
                note=signal.note,
            )
            for category, signal in category_confidence.items()
        }

    def _build_ab_tests(
        self,
        evidence: CROEvidenceInput,
        audit_input: CROAuditInput,
        analysis: HeuristicAnalysis,
    ) -> list[ABTestIdea]:
        ideas: list[ABTestIdea] = []
        if any(issue.category == "cta_visibility_and_strength" for issue in analysis.issues):
            ideas.append(
                ABTestIdea(
                    hypothesis="A more specific CTA will better match buyer intent and improve product-page click-through.",
                    variant=self.rewrite_engine.suggest_cta_text(
                        current_cta=evidence.cta_texts[0] if evidence.cta_texts else None,
                        traffic_source=audit_input.traffic_source,
                    ),
                    primary_metric="CTA click-through rate",
                )
            )
        if any(issue.category == "offer_structure" for issue in analysis.issues):
            ideas.append(
                ABTestIdea(
                    hypothesis="A bundle offer will increase perceived value and lift average order value.",
                    variant=self.rewrite_engine.suggest_bundle_pricing(audit_input.product_price),
                    primary_metric="Average order value",
                )
            )
        if any(issue.category == "above_the_fold_clarity" for issue in analysis.issues):
            ideas.append(
                ABTestIdea(
                    hypothesis="An outcome-driven headline will reduce bounce and improve add-to-cart rate.",
                    variant=self.rewrite_engine.rewrite_headline(evidence.headline, audit_input.target_audience),
                    primary_metric="Add-to-cart rate",
                )
            )
        return ideas

    def _build_psychological_improvements(self, analysis: HeuristicAnalysis) -> list[PsychologicalImprovement]:
        improvements: list[PsychologicalImprovement] = []
        issue_categories = {issue.category for issue in analysis.issues}
        if "social_proof_presence" in issue_categories:
            improvements.append(
                PsychologicalImprovement(
                    principle="Social proof",
                    suggestion="Bring testimonials, rating volume, or customer counts closer to the purchase decision.",
                )
            )
        if "trust_signals" in issue_categories:
            improvements.append(
                PsychologicalImprovement(
                    principle="Risk reversal",
                    suggestion="Reduce purchase anxiety with a guarantee, return promise, and secure checkout cues.",
                )
            )
        if "urgency_and_scarcity" in issue_categories:
            improvements.append(
                PsychologicalImprovement(
                    principle="Urgency",
                    suggestion="Use truthful time or stock constraints so shoppers feel a reason to act now.",
                )
            )
        if "pricing_psychology" in issue_categories or "offer_structure" in issue_categories:
            improvements.append(
                PsychologicalImprovement(
                    principle="Anchoring",
                    suggestion="Show the value hierarchy between single-unit and multi-unit offers to make the middle option attractive.",
                )
            )
        return improvements

    def _build_mobile_improvements(self, evidence: CROEvidenceInput, analysis: HeuristicAnalysis) -> list[str]:
        suggestions: list[str] = []
        if any(issue.category == "mobile_usability" for issue in analysis.issues):
            suggestions.append("Tighten vertical spacing so the headline, product image, proof, and CTA fit within the first few scrolls.")
        if evidence.cta_near_testimonial is False:
            suggestions.append("Pin a concise review badge or testimonial snippet near the sticky mobile CTA.")
        if evidence.mobile_spacing_score >= 6:
            suggestions.append("Remove empty spacer sections and overly tall wrappers that delay the offer on smaller screens.")
        if analysis.overall_confidence != "high":
            suggestions.append("Upload a dedicated mobile screenshot that includes the CTA region for stronger mobile-specific recommendations.")
        return suggestions

    def _build_rewrites(self, evidence: CROEvidenceInput, audit_input: CROAuditInput) -> RewriteSuggestions:
        return RewriteSuggestions(
            headline=self.rewrite_engine.rewrite_headline(evidence.headline, audit_input.target_audience),
            bullets=self.rewrite_engine.rewrite_bullets(evidence.bullets, audit_input.target_audience),
            cta_text=self.rewrite_engine.suggest_cta_text(
                current_cta=evidence.cta_texts[0] if evidence.cta_texts else None,
                traffic_source=audit_input.traffic_source,
            ),
            bundle_pricing=self.rewrite_engine.suggest_bundle_pricing(audit_input.product_price),
        )


def run_cro_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Convenience helper for frameworks that prefer plain dictionaries."""

    engine = CROAuditEngine()
    result = engine.run_audit(CROAuditInput(**payload))
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result.dict()
