import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _request(method: str, url: str, payload: dict, header_name: str, header_value: str) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if header_value:
        headers[header_name] = header_value
    method = (method or "PUT").upper()
    if method not in ("POST", "PUT", "PATCH"):
        method = "PUT"
    with httpx.Client(timeout=30.0) as client:
        r = client.request(method, url, json=payload, headers=headers)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}


def update_color_config(payload: dict) -> dict[str, Any]:
    """Save a chosen color palette to the CMS via the configured save API.

    Configure via env vars (leave URL blank for dry-run mode):
      CMS_COLOR_API_URL
      CMS_COLOR_API_METHOD       (POST | PUT | PATCH; default PUT)
      CMS_COLOR_API_AUTH_HEADER  (default: Authorization)
      CMS_COLOR_API_AUTH_VALUE   (e.g. "Bearer abc123")
    """
    url = os.getenv("CMS_COLOR_API_URL", "").strip()
    if not url:
        logger.warning("[cms_client] DRY-RUN colour update — no CMS_COLOR_API_URL configured. Payload: %s", payload)
        return {"dry_run": True, "payload": payload}
    return _request(
        method=os.getenv("CMS_COLOR_API_METHOD", "PUT"),
        url=url,
        payload=payload,
        header_name=os.getenv("CMS_COLOR_API_AUTH_HEADER", "Authorization"),
        header_value=os.getenv("CMS_COLOR_API_AUTH_VALUE", "").strip(),
    )


def update_template(payload: dict) -> dict[str, Any]:
    """Save a chosen template to the CMS via the configured save API.

    Configure via env vars (leave URL blank for dry-run mode):
      CMS_TEMPLATE_API_URL
      CMS_TEMPLATE_API_METHOD       (POST | PUT | PATCH; default PUT)
      CMS_TEMPLATE_API_AUTH_HEADER  (default: Authorization)
      CMS_TEMPLATE_API_AUTH_VALUE
    """
    url = os.getenv("CMS_TEMPLATE_API_URL", "").strip()
    if not url:
        logger.warning("[cms_client] DRY-RUN template update — no CMS_TEMPLATE_API_URL configured. Payload: %s", payload)
        return {"dry_run": True, "payload": payload}
    return _request(
        method=os.getenv("CMS_TEMPLATE_API_METHOD", "PUT"),
        url=url,
        payload=payload,
        header_name=os.getenv("CMS_TEMPLATE_API_AUTH_HEADER", "Authorization"),
        header_value=os.getenv("CMS_TEMPLATE_API_AUTH_VALUE", "").strip(),
    )
