"""Rewrite suggestions for CRO improvements."""

from __future__ import annotations

from typing import Iterable


class CRORewriteEngine:
    """Generates copy rewrites without relying on store-specific assumptions."""

    def rewrite_headline(self, current_headline: str | None, target_audience: str) -> str:
        headline = (current_headline or "This product").strip(" -")
        return f"Get the result {target_audience} want faster with {headline.lower()}."

    def rewrite_bullets(self, bullets: Iterable[str], target_audience: str) -> list[str]:
        normalized = [bullet.strip(" -*") for bullet in bullets if bullet and bullet.strip()]
        if not normalized:
            return [
                f"Helps {target_audience} reach the desired outcome with less friction.",
                f"Turns key product features into practical day-to-day wins for {target_audience}.",
                f"Reduces hesitation by making the next step feel simple and low risk.",
            ]

        rewritten: list[str] = []
        for bullet in normalized[:4]:
            rewritten.append(self._benefitize_bullet(bullet, target_audience))
        return rewritten

    def suggest_cta_text(self, current_cta: str | None, traffic_source: str) -> str:
        current = (current_cta or "").strip().lower()
        if "add to cart" in current:
            if traffic_source.lower() == "facebook":
                return "Get Mine Now"
            if traffic_source.lower() == "google":
                return "See Price & Order Now"
            return "Claim Yours Today"
        if not current:
            return "Get Yours Risk-Free Today"
        return f"{current_cta.strip()} Today"

    def suggest_bundle_pricing(self, product_price: float) -> str:
        two_pack = round(product_price * 1.8, 2)
        three_pack = round(product_price * 2.4, 2)
        return (
            f"Offer 1 for ${product_price:.2f}, 2 for ${two_pack:.2f} (save 10%), "
            f"and 3 for ${three_pack:.2f} (save 20%) to anchor value and lift AOV."
        )

    def _benefitize_bullet(self, bullet: str, target_audience: str) -> str:
        lowered = bullet.lower()
        if lowered.startswith("made with"):
            return f"Gives {target_audience} a more reliable result because it is {lowered}."
        if lowered.startswith(("includes", "features", "contains")):
            return f"Gives {target_audience} a more reliable result because it {lowered}."
        return f"Helps {target_audience} because it {lowered[0].lower() + lowered[1:]}."
