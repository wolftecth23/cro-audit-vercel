from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.cro import CROAuditEngine, CROAuditInput, CROAuditResult, ScreenshotAuditRequest
from app.cro.vision_service import LocalScreenshotStorage

router = APIRouter(prefix="/cro", tags=["CRO Audit"])

audit_engine = CROAuditEngine()
storage = LocalScreenshotStorage()


@router.post("/audit", response_model=CROAuditResult, status_code=status.HTTP_200_OK)
def run_cro_audit(payload: CROAuditInput) -> CROAuditResult:
    return audit_engine.run_audit(payload)


@router.post("/audit-image", response_model=CROAuditResult, status_code=status.HTTP_200_OK)
async def run_cro_audit_image(
    screenshot: Annotated[UploadFile, File(...)],
    product_price: Annotated[float, Form(...)],
    target_audience: Annotated[str, Form(...)],
    traffic_source: Annotated[str, Form(...)],
    device_focus: Annotated[str, Form(...)],
    store_url: Annotated[str, Form()] = "",
    product_page_html: Annotated[str | None, Form()] = None,
    save_image: Annotated[bool, Form()] = False,
) -> CROAuditResult:
    image_bytes = await screenshot.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded screenshot is empty.")

    saved_image_path: str | None = None
    if save_image:
        saved_image_path = storage.save(image_bytes, screenshot.filename)

    request = ScreenshotAuditRequest(
        product_price=product_price,
        target_audience=target_audience,
        traffic_source=traffic_source,
        device_focus=device_focus,
        store_url=store_url,
        product_page_html=product_page_html,
        save_image=save_image,
    )
    try:
        return audit_engine.run_screenshot_audit(
            request=request,
            image_bytes=image_bytes,
            mime_type=screenshot.content_type or "image/png",
            saved_image_path=saved_image_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
