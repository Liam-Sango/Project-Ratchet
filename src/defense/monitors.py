"""Detection rules for scenarios S1–S3."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from src.defense.events import Alert, Event, EventType



def monitor_key_steal(
    events: list[Event],
    *,
    sensitive_paths: list[str] | None = None,
) -> list[Alert]:
    """S1: sensitive file_read and read→exfil composite rules."""

    #RULE 1 (Sensitive read path matching)
    if sensitive_paths is None:
        sensitive_paths = ["*key*", "*wallet*", "*secret*", "*credential*", "*.pem", "*.json"]
    alerts = []

    for i, event in enumerate(events):
        if event.type == EventType.FILE_READ:
            path = event.detail.get("path", "")

            for pattern in sensitive_paths:
                if fnmatch.fnmatch(path, pattern):
                    alerts.append(Alert(
                        class_="SENSITIVE_READ",
                        message=f"Sensitive file read: {path} (matched {pattern})",
                        event_index=i,
                        detail={"path": path, "pattern": pattern},
                    ))
                    break   # one alert per event, don't double-fire

    #RULE 2 (Exfil upload pattern matching)
    pending_reads = []
    window = 10

    for i, event in enumerate(events):
        if event.type == EventType.FILE_READ:
            pending_reads.append(i)
        elif event.type == EventType.ARWEAVE_UPLOAD:
            for read_idx in pending_reads:
                if read_idx < i and i - read_idx <= window:
                    alerts.append(Alert(
                        class_="READ_EXFIL_CHAIN",
                        message=f"Read at event {read_idx} followed by exfil upload at event {i} (gap {i - read_idx})",
                        event_index=i,
                        detail={"read_index": read_idx, "gap": i - read_idx},
                    ))

    return alerts 

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
