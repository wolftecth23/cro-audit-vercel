"""Screenshot analysis backed by the Google AI Studio Gemini API."""

from __future__ import annotations

import base64
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from app.cro.evidence import CROEvidenceInput, EvidenceSignal, default_category_signals


class VisionCategorySignal(BaseModel):
    confidence: str = Field(default="medium")
    evidence_visibility: str = Field(default="unclear")
    note: str | None = None


class VisionExtractionPayload(BaseModel):
    headline: str | None = None
    subheadline: str | None = None
    body_text: str = ""
    cta_texts: list[str] = Field(default_factory=list)
    cta_near_testimonial: bool | None = None
    bullets: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    reviews_texts: list[str] = Field(default_factory=list)
    trust_texts: list[str] = Field(default_factory=list)
    urgency_texts: list[str] = Field(default_factory=list)
    price_texts: list[str] = Field(default_factory=list)
    image_count: int = 1
    form_count: int = 0
    mobile_spacing_score: int = 0
    analysis_notes: list[str] = Field(default_factory=list)
    recommended_next_uploads: list[str] = Field(default_factory=list)
    category_confidence: dict[str, VisionCategorySignal] = Field(default_factory=dict)


class GoogleAICROVisionService:
    """Calls Gemini vision models and maps results into CRO evidence."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
        self.endpoint = endpoint or os.getenv(
            "GEMINI_GENERATE_CONTENT_ENDPOINT",
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
        )

    def extract_evidence(
        self,
        image_bytes: bytes,
        mime_type: str,
        device_focus: str,
    ) -> CROEvidenceInput:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured for screenshot audits.")

        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        prompt = self._build_prompt(device_focus)
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded_image,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }

        raw_text = self._call_gemini(payload)
        parsed_payload = VisionExtractionPayload(**self._extract_json(raw_text))

        signals = default_category_signals(visibility="not_shown", confidence="low")
        for category, signal in parsed_payload.category_confidence.items():
            signals[category] = EvidenceSignal(
                confidence=signal.confidence,
                evidence_visibility=signal.evidence_visibility,
                note=signal.note,
            )

        return CROEvidenceInput(
            source_type="screenshot",
            headline=parsed_payload.headline,
            subheadline=parsed_payload.subheadline,
            body_text=parsed_payload.body_text,
            cta_texts=parsed_payload.cta_texts,
            cta_near_testimonial=parsed_payload.cta_near_testimonial,
            bullets=parsed_payload.bullets,
            paragraphs=parsed_payload.paragraphs,
            reviews_texts=parsed_payload.reviews_texts,
            trust_texts=parsed_payload.trust_texts,
            urgency_texts=parsed_payload.urgency_texts,
            price_texts=parsed_payload.price_texts,
            image_count=parsed_payload.image_count,
            form_count=parsed_payload.form_count,
            mobile_spacing_score=parsed_payload.mobile_spacing_score,
            analysis_notes=parsed_payload.analysis_notes,
            category_signals=signals,
            recommended_next_uploads=parsed_payload.recommended_next_uploads,
        )

    def _call_gemini(self, payload: dict[str, Any]) -> str:
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                data = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini vision request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError("Could not reach the Gemini API.") from exc

        text_parts: list[str] = []
        for candidate in data.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                if part.get("text"):
                    text_parts.append(part["text"])

        combined = "\n".join(text_parts).strip()
        if not combined:
            raise RuntimeError("Gemini vision returned an empty response.")
        return combined

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            raise RuntimeError("Gemini vision did not return a parseable JSON object.")
        return json.loads(match.group(0))

    def _build_prompt(self, device_focus: str) -> str:
        return f"""
You are a CRO auditor extracting structured evidence from a single e-commerce product-page screenshot.
Focus only on what is actually visible. Do not invent hidden sections.

Return only one valid JSON object with these keys:
- headline: string or null
- subheadline: string or null
- body_text: string
- cta_texts: string[]
- cta_near_testimonial: boolean or null
- bullets: string[]
- paragraphs: string[]
- reviews_texts: string[]
- trust_texts: string[]
- urgency_texts: string[]
- price_texts: string[]
- image_count: integer
- form_count: integer
- mobile_spacing_score: integer from 0 to 10
- analysis_notes: string[]
- recommended_next_uploads: string[]
- category_confidence: object whose keys are:
  above_the_fold_clarity
  value_proposition_strength
  cta_visibility_and_strength
  social_proof_presence
  trust_signals
  pricing_psychology
  offer_structure
  mobile_usability
  checkout_friction_risks
  urgency_and_scarcity
  copy_persuasion

Each category_confidence value must be an object:
- confidence: "high", "medium", or "low"
- evidence_visibility: "visible", "unclear", or "not_shown"
- note: string or null

Guidance:
- Device focus is {device_focus}.
- If a category cannot be verified from one screenshot, mark it "not_shown" or "unclear".
- Capture visible CTA copy, review snippets, guarantee text, trust badges, pricing, urgency labels, and dense copy.
- Estimate mobile_spacing_score based on visible whitespace and stacked empty gaps only.
- recommended_next_uploads should suggest concrete missing screenshots like "mid-page social proof section" or "mobile sticky CTA area".
""".strip()


class LocalScreenshotStorage:
    """Simple local filesystem storage for optional screenshot persistence."""

    def __init__(self, upload_dir: str | None = None) -> None:
        default_dir = "/tmp/cro_audits" if os.getenv("VERCEL") else "runtime_uploads/cro_audits"
        configured = upload_dir or os.getenv("CRO_AUDIT_UPLOAD_DIR", default_dir)
        self.upload_dir = Path(configured)

    def save(self, image_bytes: bytes, original_filename: str | None) -> str:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(original_filename or "audit.png").suffix or ".png"
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{suffix}"
        path = self.upload_dir / filename
        path.write_bytes(image_bytes)
        return str(path.resolve())
