"""Heuristic CRO rules and HTML signal extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag

from app.cro.evidence import ALL_CRO_CATEGORIES, CROEvidenceInput, EvidenceSignal, default_category_signals


GENERIC_CTA_TEXTS = {
    "add to cart",
    "buy now",
    "shop now",
    "learn more",
    "submit",
    "continue",
}
TRUST_PATTERNS = (
    "secure checkout",
    "ssl",
    "money-back",
    "money back",
    "guarantee",
    "free returns",
    "easy returns",
    "trusted by",
    "warranty",
)
URGENCY_PATTERNS = (
    "limited time",
    "ends tonight",
    "selling fast",
    "low stock",
    "only",
    "last chance",
    "countdown",
    "before it's gone",
)
SOCIAL_PROOF_PATTERNS = (
    "review",
    "reviews",
    "testimonial",
    "testimonials",
    "rated",
    "stars",
    "customers",
)
BENEFIT_PATTERNS = (
    "helps",
    "designed to",
    "so you can",
    "without",
    "faster",
    "easier",
    "better",
    "improve",
    "save",
)
CHECKOUT_FRICTION_PATTERNS = (
    "shipping calculated at checkout",
    "taxes calculated at checkout",
    "create account",
    "sign in to continue",
    "coupon code",
)
NEXT_UPLOAD_PROMPTS = {
    "above_the_fold_clarity": "above-the-fold hero screenshot",
    "value_proposition_strength": "headline and supporting copy screenshot",
    "cta_visibility_and_strength": "CTA area screenshot",
    "social_proof_presence": "mid-page social proof section screenshot",
    "trust_signals": "trust badge or guarantee section screenshot",
    "pricing_psychology": "pricing block screenshot",
    "offer_structure": "bundle or variant offer screenshot",
    "mobile_usability": "mobile screenshot showing spacing and CTA placement",
    "checkout_friction_risks": "shipping and purchase detail screenshot",
    "urgency_and_scarcity": "offer timing or stock indicator screenshot",
    "copy_persuasion": "benefit and body-copy screenshot",
}


@dataclass
class ParsedPageContext:
    """Normalized signals extracted from the product page."""

    source_url: str
    html: str
    text: str
    headline: str | None
    subheadline: str | None
    cta_texts: list[str]
    cta_near_testimonial: bool
    bullets: list[str]
    paragraphs: list[str]
    reviews_texts: list[str]
    trust_texts: list[str]
    urgency_texts: list[str]
    price_texts: list[str]
    image_count: int
    form_count: int
    mobile_spacing_score: int
    detected_issues: list[str] = field(default_factory=list)


@dataclass
class HeuristicIssue:
    """A single CRO issue found during analysis."""

    issue: str
    recommendation: str
    expected_impact: str
    category: str
    priority_score: int


@dataclass
class HeuristicAnalysis:
    """Full results of rule evaluation before output shaping."""

    category_scores: dict[str, int]
    issues: list[HeuristicIssue]
    biggest_leak: str
    analysis_notes: list[str]
    category_confidence: dict[str, EvidenceSignal]
    overall_confidence: str
    missing_evidence_notes: list[str]
    recommended_next_uploads: list[str]


class ProductPageParser:
    """Builds a normalized page context from raw or fetched HTML."""

    def load_html(self, store_url: str, product_page_html: str | None) -> str:
        if product_page_html and product_page_html.strip():
            return product_page_html
        if not store_url:
            raise ValueError("Either `store_url` or `product_page_html` must be provided.")

        request = Request(store_url, headers={"User-Agent": "Mozilla/5.0 CROAuditEngine/1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8", errors="ignore")
        except URLError as exc:
            raise ValueError(f"Unable to fetch product page HTML from {store_url}.") from exc

    def parse(self, store_url: str, product_page_html: str | None) -> ParsedPageContext:
        html = self.load_html(store_url=store_url, product_page_html=product_page_html)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        headlines = [self._clean_text(node.get_text(" ", strip=True)) for node in soup.find_all(["h1", "h2"], limit=3)]
        cta_nodes = soup.find_all(["button", "a", "input"])
        cta_texts = [
            self._clean_cta_text(node)
            for node in cta_nodes
            if self._clean_cta_text(node)
        ]
        bullets = [self._clean_text(item.get_text(" ", strip=True)) for item in soup.find_all("li")]
        paragraphs = [self._clean_text(item.get_text(" ", strip=True)) for item in soup.find_all("p")]

        reviews_texts = self._collect_pattern_matches(text, SOCIAL_PROOF_PATTERNS)
        trust_texts = self._collect_pattern_matches(text, TRUST_PATTERNS)
        urgency_texts = self._collect_pattern_matches(text, URGENCY_PATTERNS)
        price_texts = re.findall(r"(?:\$|USD\s?)\s?\d+(?:[.,]\d{2})?", text)

        return ParsedPageContext(
            source_url=store_url,
            html=html,
            text=text,
            headline=headlines[0] if headlines else None,
            subheadline=headlines[1] if len(headlines) > 1 else None,
            cta_texts=cta_texts[:10],
            cta_near_testimonial=self._cta_has_social_proof_nearby(cta_nodes),
            bullets=bullets[:12],
            paragraphs=paragraphs[:12],
            reviews_texts=reviews_texts,
            trust_texts=trust_texts,
            urgency_texts=urgency_texts,
            price_texts=price_texts,
            image_count=len(soup.find_all("img")),
            form_count=len(soup.find_all("form")),
            mobile_spacing_score=self._estimate_mobile_spacing_risk(soup, html),
        )

    def to_evidence(self, page: ParsedPageContext) -> CROEvidenceInput:
        return CROEvidenceInput(
            source_type="html",
            headline=page.headline,
            subheadline=page.subheadline,
            body_text=page.text,
            cta_texts=page.cta_texts,
            cta_near_testimonial=page.cta_near_testimonial,
            bullets=page.bullets,
            paragraphs=page.paragraphs,
            reviews_texts=page.reviews_texts,
            trust_texts=page.trust_texts,
            urgency_texts=page.urgency_texts,
            price_texts=page.price_texts,
            image_count=page.image_count,
            form_count=page.form_count,
            mobile_spacing_score=page.mobile_spacing_score,
            category_signals=default_category_signals(visibility="visible", confidence="high"),
        )

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _clean_cta_text(self, node: Tag) -> str:
        if node.name == "input":
            return self._clean_text(str(node.get("value", "")))
        return self._clean_text(node.get_text(" ", strip=True))

    def _collect_pattern_matches(self, text: str, patterns: Iterable[str]) -> list[str]:
        lowered = text.lower()
        return [pattern for pattern in patterns if pattern in lowered]

    def _cta_has_social_proof_nearby(self, cta_nodes: Iterable[Tag]) -> bool:
        for node in cta_nodes:
            container = node.parent
            hops = 0
            while container is not None and hops < 3:
                window_text = self._clean_text(container.get_text(" ", strip=True)).lower()
                if any(pattern in window_text for pattern in SOCIAL_PROOF_PATTERNS):
                    return True
                container = container.parent if isinstance(container.parent, Tag) else None
                hops += 1
        return False

    def _estimate_mobile_spacing_risk(self, soup: BeautifulSoup, html: str) -> int:
        blank_div_count = 0
        spacer_class_hits = 0
        for node in soup.find_all(["div", "section"]):
            node_text = self._clean_text(node.get_text(" ", strip=True))
            class_names = " ".join(node.get("class", [])).lower()
            style = str(node.get("style", "")).lower()
            if not node_text and len(node.find_all(recursive=False)) == 0:
                blank_div_count += 1
            if any(token in class_names for token in ("spacer", "space", "gap", "margin", "padding")):
                spacer_class_hits += 1
            if any(token in style for token in ("padding-top: 80", "padding-top:80", "margin-top: 80", "height: 100")):
                spacer_class_hits += 1

        br_clusters = len(re.findall(r"(<br\s*/?>\s*){3,}", html, flags=re.IGNORECASE))
        return blank_div_count + spacer_class_hits + (br_clusters * 2)


class HeuristicRuleEngine:
    """Applies generic e-commerce CRO heuristics to normalized evidence."""

    def analyze(
        self,
        evidence: CROEvidenceInput,
        product_price: float,
        target_audience: str,
        traffic_source: str,
        device_focus: str,
    ) -> HeuristicAnalysis:
        scores = {category: 10 for category in ALL_CRO_CATEGORIES}
        issues: list[HeuristicIssue] = []
        notes = list(evidence.analysis_notes)
        missing_evidence_notes: list[str] = []
        recommended_next_uploads = list(evidence.recommended_next_uploads)
        category_confidence = self._normalized_signals(evidence)

        self._apply_visibility_defaults(scores, category_confidence, missing_evidence_notes, recommended_next_uploads)

        body_text = evidence.body_text.lower()

        if self._can_assert_absence(category_confidence, "above_the_fold_clarity"):
            if not evidence.headline or len(evidence.headline.split()) < 4:
                self._add_issue(
                    issues,
                    scores,
                    "above_the_fold_clarity",
                    "Weak value proposition above the fold",
                    "Lead with a clearer headline that explains the main outcome, audience, or pain solved within the first screen.",
                    "High",
                    95,
                )

        if self._can_assert_absence(category_confidence, "value_proposition_strength") and not evidence.subheadline:
            self._add_issue(
                issues,
                scores,
                "value_proposition_strength",
                "Missing supporting subheadline",
                "Add a subheadline that explains why this product is different and what objection it removes.",
                "Medium",
                72,
            )

        if self._can_assert_absence(category_confidence, "copy_persuasion"):
            if not any(pattern in body_text for pattern in BENEFIT_PATTERNS):
                self._add_issue(
                    issues,
                    scores,
                    "copy_persuasion",
                    "Copy leans feature-first instead of benefit-first",
                    f"Reframe core messaging around the transformation {target_audience} wants, not just product attributes.",
                    "High",
                    84,
                )

            long_paragraphs = [paragraph for paragraph in evidence.paragraphs if len(paragraph.split()) >= 35]
            if long_paragraphs:
                self._add_issue(
                    issues,
                    scores,
                    "copy_persuasion",
                    "Long unstructured text blocks create scanning friction",
                    "Break dense paragraphs into benefit-led bullets, short sections, and bold proof points.",
                    "Medium",
                    67,
                )

        if self._can_assert_absence(category_confidence, "cta_visibility_and_strength"):
            if not evidence.cta_texts:
                self._add_issue(
                    issues,
                    scores,
                    "cta_visibility_and_strength",
                    "Primary CTA is hard to detect",
                    "Ensure there is a clear purchase CTA in the first screen and repeat it after key persuasion blocks.",
                    "High",
                    92,
                )
            elif any(text.lower() in GENERIC_CTA_TEXTS for text in evidence.cta_texts):
                self._add_issue(
                    issues,
                    scores,
                    "cta_visibility_and_strength",
                    "Generic CTA text reduces click motivation",
                    f"Use a CTA that reflects the offer and intent from {traffic_source} traffic instead of generic action language.",
                    "High",
                    88,
                )

        if self._can_assert_absence(category_confidence, "social_proof_presence"):
            if not evidence.reviews_texts:
                self._add_issue(
                    issues,
                    scores,
                    "social_proof_presence",
                    "Social proof is missing from the product page",
                    "Add star ratings, testimonial snippets, or quantified customer outcomes near decision points.",
                    "High",
                    90,
                )
            elif evidence.cta_near_testimonial is False:
                self._add_issue(
                    issues,
                    scores,
                    "social_proof_presence",
                    "Testimonials are not reinforcing the CTA",
                    "Place a testimonial or rating cluster immediately above or beside the primary CTA.",
                    "High",
                    86,
                )

        if self._can_assert_absence(category_confidence, "trust_signals"):
            if not evidence.trust_texts:
                self._add_issue(
                    issues,
                    scores,
                    "trust_signals",
                    "Trust signals are thin",
                    "Add secure checkout, returns, shipping clarity, and guarantee messaging close to the purchase action.",
                    "Medium",
                    70,
                )

            if not any("guarantee" in text.lower() or "money back" in text.lower() for text in evidence.trust_texts):
                self._add_issue(
                    issues,
                    scores,
                    "trust_signals",
                    "Guarantee text is missing",
                    "Add a specific guarantee such as a 30-day money-back promise near the CTA and purchase details.",
                    "High",
                    91,
                )

        if self._can_assert_absence(category_confidence, "pricing_psychology"):
            if product_price >= 25 and len(set(evidence.price_texts)) <= 1:
                self._add_issue(
                    issues,
                    scores,
                    "pricing_psychology",
                    "Pricing lacks anchoring or comparison context",
                    "Show compare-at pricing, savings, or value framing to make the current price feel easier to justify.",
                    "Medium",
                    68,
                )

        if self._can_assert_absence(category_confidence, "offer_structure"):
            if "bundle" not in body_text and "save" not in body_text:
                self._add_issue(
                    issues,
                    scores,
                    "offer_structure",
                    "Bundle pricing structure is missing",
                    "Introduce multi-pack or subscribe-and-save offers to increase average order value and perceived value.",
                    "High",
                    82,
                )

        if device_focus.lower() == "mobile" and self._can_assert_absence(category_confidence, "mobile_usability"):
            if evidence.mobile_spacing_score >= 6:
                self._add_issue(
                    issues,
                    scores,
                    "mobile_usability",
                    "Mobile layout likely wastes vertical space",
                    "Reduce spacer sections, oversized padding, and stacked dead zones so the CTA and proof appear sooner on mobile.",
                    "High",
                    87,
                )
            if evidence.image_count == 0:
                self._add_issue(
                    issues,
                    scores,
                    "mobile_usability",
                    "Product imagery is weak for mobile shoppers",
                    "Add compressed above-the-fold imagery that communicates the product fast without pushing the CTA too far down.",
                    "Medium",
                    61,
                )

        if self._can_assert_absence(category_confidence, "checkout_friction_risks"):
            if any(pattern in body_text for pattern in CHECKOUT_FRICTION_PATTERNS):
                self._add_issue(
                    issues,
                    scores,
                    "checkout_friction_risks",
                    "Checkout friction cues are visible too early",
                    "Delay non-essential checkout friction such as account creation prompts and clarify final charges sooner.",
                    "Medium",
                    64,
                )
            if "free shipping" not in body_text and "shipping" not in body_text:
                self._add_issue(
                    issues,
                    scores,
                    "checkout_friction_risks",
                    "Shipping clarity is missing",
                    "Clarify shipping timing and cost before the shopper reaches checkout to reduce abandonment risk.",
                    "Medium",
                    69,
                )

        if self._can_assert_absence(category_confidence, "urgency_and_scarcity") and not evidence.urgency_texts:
            self._add_issue(
                issues,
                scores,
                "urgency_and_scarcity",
                "Urgency and scarcity signals are absent",
                "Add believable urgency such as low-stock status, shipping cutoff times, or promotional end dates.",
                "Medium",
                71,
            )

        if evidence.form_count > 2:
            notes.append("Multiple forms detected; confirm that only one primary conversion path is emphasized.")

        sorted_issues = sorted(issues, key=lambda issue: issue.priority_score, reverse=True)
        biggest_leak = sorted_issues[0].issue if sorted_issues else "No major CRO leak detected"
        return HeuristicAnalysis(
            category_scores={key: max(0, min(10, value)) for key, value in scores.items()},
            issues=sorted_issues,
            biggest_leak=biggest_leak,
            analysis_notes=notes,
            category_confidence=category_confidence,
            overall_confidence=self._overall_confidence(category_confidence),
            missing_evidence_notes=missing_evidence_notes,
            recommended_next_uploads=self._dedupe(recommended_next_uploads),
        )

    def _normalized_signals(self, evidence: CROEvidenceInput) -> dict[str, EvidenceSignal]:
        signals = default_category_signals(visibility="visible", confidence="high")
        for category, signal in evidence.category_signals.items():
            signals[category] = signal
        return signals

    def _apply_visibility_defaults(
        self,
        scores: dict[str, int],
        category_confidence: dict[str, EvidenceSignal],
        missing_evidence_notes: list[str],
        recommended_next_uploads: list[str],
    ) -> None:
        for category, signal in category_confidence.items():
            if signal.evidence_visibility == "not_shown":
                scores[category] = min(scores[category], 7)
                missing_evidence_notes.append(
                    signal.note or f"Could not fully verify {category.replace('_', ' ')} from the provided screenshot."
                )
                recommended_next_uploads.append(NEXT_UPLOAD_PROMPTS[category])
            elif signal.evidence_visibility == "unclear":
                scores[category] = min(scores[category], 8)
                missing_evidence_notes.append(
                    signal.note or f"Evidence for {category.replace('_', ' ')} was visible but unclear."
                )
                recommended_next_uploads.append(NEXT_UPLOAD_PROMPTS[category])

    def _can_assert_absence(self, category_confidence: dict[str, EvidenceSignal], category: str) -> bool:
        return category_confidence[category].evidence_visibility == "visible"

    def _overall_confidence(self, category_confidence: dict[str, EvidenceSignal]) -> str:
        visible = sum(1 for signal in category_confidence.values() if signal.evidence_visibility == "visible")
        unclear = sum(1 for signal in category_confidence.values() if signal.evidence_visibility == "unclear")
        not_shown = sum(1 for signal in category_confidence.values() if signal.evidence_visibility == "not_shown")
        low_confidence = sum(1 for signal in category_confidence.values() if signal.confidence == "low")

        if visible >= 8 and unclear <= 2 and not_shown <= 1 and low_confidence <= 2:
            return "high"
        if visible >= 4:
            return "medium"
        return "low"

    def _dedupe(self, values: list[str]) -> list[str]:
        deduped: list[str] = []
        for value in values:
            if value and value not in deduped:
                deduped.append(value)
        return deduped

    def _add_issue(
        self,
        issues: list[HeuristicIssue],
        scores: dict[str, int],
        category: str,
        issue: str,
        recommendation: str,
        expected_impact: str,
        priority_score: int,
    ) -> None:
        scores[category] = max(0, scores[category] - self._deduction(expected_impact))
        issues.append(
            HeuristicIssue(
                issue=issue,
                recommendation=recommendation,
                expected_impact=expected_impact,
                category=category,
                priority_score=priority_score,
            )
        )

    def _deduction(self, expected_impact: str) -> int:
        return {"High": 4, "Medium": 2, "Low": 1}.get(expected_impact, 1)
