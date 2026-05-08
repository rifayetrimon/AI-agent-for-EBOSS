import base64
import io
import logging
import re
from typing import Optional

import httpx
from colorthief import ColorThief
from PIL import Image

logger = logging.getLogger(__name__)


_DATA_URI_RE = re.compile(r"^data:image/[^;]+;base64,(.+)$", re.IGNORECASE)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _bytes_to_palette(data: bytes, palette_size: int) -> dict:
    img_buf = io.BytesIO(data)
    Image.open(img_buf).verify()
    img_buf.seek(0)

    ct = ColorThief(img_buf)
    dominant = ct.get_color(quality=1)
    palette = ct.get_palette(color_count=max(palette_size, 2), quality=1)
    return {
        "dominant": _rgb_to_hex(dominant),
        "palette": [_rgb_to_hex(c) for c in palette],
    }


def extract_colors(source: str, palette_size: int = 6, timeout: float = 15.0) -> dict:
    """Extract dominant + N-color palette from an image.

    Accepts:
      - http(s):// URL
      - data:image/...;base64,... data URI
    Returns: {"dominant": "#RRGGBB", "palette": ["#RRGGBB", ...]}
    Raises ValueError on invalid input or unreachable URL.
    """
    if not source:
        raise ValueError("empty image source")

    m = _DATA_URI_RE.match(source.strip())
    if m:
        try:
            data = base64.b64decode(m.group(1))
        except Exception as e:
            raise ValueError(f"invalid base64 in data URI: {e}")
        return _bytes_to_palette(data, palette_size)

    if source.startswith("http://") or source.startswith("https://"):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                r = client.get(source, headers={"User-Agent": "ai-agent-gateway/1.0"})
                r.raise_for_status()
                content_type = r.headers.get("content-type", "")
                if "image" not in content_type and not source.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
                ):
                    logger.warning(
                        "[logo_analyzer] non-image content-type %r for %s — attempting anyway",
                        content_type,
                        source,
                    )
                data = r.content
        except httpx.HTTPError as e:
            raise ValueError(f"failed to fetch logo: {e}")
        return _bytes_to_palette(data, palette_size)

    raise ValueError("source must be an http(s) URL or a data:image/...;base64,... URI")


def safe_extract_colors(source: Optional[str], palette_size: int = 6) -> Optional[dict]:
    """Same as extract_colors but returns None on any failure (logs the reason)."""
    if not source:
        return None
    try:
        return extract_colors(source, palette_size=palette_size)
    except Exception as e:
        logger.warning("[logo_analyzer] could not extract logo colours: %s", e)
        return None
