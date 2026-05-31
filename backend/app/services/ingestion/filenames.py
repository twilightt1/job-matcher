from __future__ import annotations

import re
from pathlib import Path

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(filename: str | None, *, fallback: str = "upload") -> str:
    """Return a filesystem-safe basename while preserving the original extension."""

    raw_name = Path(filename or fallback).name.strip() or fallback
    safe_name = _SAFE_FILENAME_RE.sub("-", raw_name).strip(".-_")
    return safe_name or fallback


def title_from_filename(filename: str | None, *, fallback: str) -> str:
    """Create a readable title from an uploaded filename."""

    safe_name = safe_filename(filename, fallback=fallback)
    stem = Path(safe_name).stem.replace("-", "_").replace("_", " ").strip()
    return stem.title() if stem else fallback
