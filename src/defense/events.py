"""Event types and in-process collector for fixture instrumentation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    FILE_READ = "file_read"
    HTTP_GET = "http_get"
    ARWEAVE_UPLOAD = "arweave_upload"
    STEGO_EMBED = "stego_embed"
    STEGO_EXTRACT = "stego_extract"
    DECRYPT_SUCCESS = "decrypt_success"
    DECRYPT_FAIL = "decrypt_fail"
    KEYFILE_LOAD = "keyfile_load"
    KEYFILE_SAVE = "keyfile_save"
    RATCHET_ADVANCE = "ratchet_advance"
    RNG_SAMPLE = "rng_sample"
    VM_START = "vm_start"
    VM_END = "vm_end"


@dataclass(frozen=True)
class Event:
    type: EventType
    timestamp: float
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    class_: str
    message: str
    event_index: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)


class EventCollector:
    """Append-only event sink. No-op safe when unused by fixture."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def emit(self, event_type: EventType, detail: dict[str, Any] | None = None) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def as_list(self) -> list[Event]:
        raise NotImplementedError


_active: EventCollector | None = None


def get_collector() -> EventCollector | None:
    return _active


def set_collector(collector: EventCollector | None) -> None:
    global _active
    _active = collector


def emit(event_type: EventType, detail: dict[str, Any] | None = None) -> None:
    """Emit to active collector if attached; no-op otherwise."""
    raise NotImplementedError
