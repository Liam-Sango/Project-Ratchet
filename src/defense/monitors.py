"""Detection rules for scenarios S1–S3."""

from __future__ import annotations

from pathlib import Path

from src.defense.events import Alert, Event


def monitor_key_steal(
    events: list[Event],
    *,
    sensitive_paths: list[str] | None = None,
) -> list[Alert]:
    """S1: sensitive file_read and read→exfil composite rules."""
    raise NotImplementedError


def monitor_key_corruption(events: list[Event]) -> list[Alert]:
    """S3: keyfile integrity and decrypt fail-closed signals."""
    raise NotImplementedError


def monitor_rng_subversion(events: list[Event]) -> list[Alert]:
    """S2: PRNG/CSPRNG health and boundary checks."""
    raise NotImplementedError


def run_all_monitors(
    events: list[Event],
    *,
    sensitive_paths: list[str] | None = None,
    policy_path: Path | None = None,
) -> list[Alert]:
    raise NotImplementedError
