import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def send_message(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch a drafted message via the configured external send API.

    If SEND_API_URL is not configured, this runs in dry-run mode and just logs the payload.
    Configure via env vars:
      SEND_API_URL          Required to actually send.
      SEND_API_AUTH_HEADER  e.g. "Authorization" or "X-API-Key". Default: "Authorization".
      SEND_API_AUTH_VALUE   e.g. "Bearer abc123" or the raw key. Optional.
    """
    url = os.getenv("SEND_API_URL", "").strip()
    if not url:
        logger.warning("[send_client] DRY-RUN — no SEND_API_URL configured. Payload: %s", payload)
        return {"dry_run": True, "payload": payload}

    header_name = os.getenv("SEND_API_AUTH_HEADER", "Authorization").strip()
    header_value = os.getenv("SEND_API_AUTH_VALUE", "").strip()
    headers = {"Content-Type": "application/json"}
    if header_value:
        headers[header_name] = header_value

    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}
