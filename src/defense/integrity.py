"""Keyfile and RNG health helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_keyfile_schema(path: Path) -> tuple[bool, str]:
    """Return (ok, reason). No raw key material in reason strings beyond field names."""
    raise NotImplementedError


def keyfile_fingerprint(path: Path) -> str:
    """Non-reversible summary (e.g. SHA-256 of canonical JSON) for integrity compare."""
    raise NotImplementedError


def rng_position_health(
    positions: list[int],
    *,
    capacity: int,
    sample_count: int,
) -> dict[str, Any]:
    """Structural/statistical checks on stego position samples."""
    raise NotImplementedError


def assert_hmac_ctr_generator(module_path: str | None = None) -> tuple[bool, str]:
    """Boundary check: production position generator must be HMAC-CTR style."""
    raise NotImplementedError
