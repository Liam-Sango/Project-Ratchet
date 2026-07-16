"""Scenario injectors and runners (S1 key-steal, S2 RNG subversion, S3 key corruption)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.defense.events import Alert, Event
from src.defense.report import ScenarioReport


class ScenarioId(str, Enum):
    KEY_STEAL = "key-steal"
    RNG_SUBVERSION = "rng-subversion"
    KEY_CORRUPT = "key-corrupt"


@dataclass
class ScenarioConfig:
    scenario: ScenarioId
    workdir: Path
    sensitive_paths: list[str] | None = None
    mock: bool = True


def inject_key_steal(config: ScenarioConfig) -> list[Event]:
    raise NotImplementedError


def inject_rng_subversion(config: ScenarioConfig) -> list[Event]:
    raise NotImplementedError


def inject_key_corrupt(config: ScenarioConfig) -> list[Event]:
    raise NotImplementedError


def run_scenario(config: ScenarioConfig) -> ScenarioReport:
    raise NotImplementedError


def run_all(workdir: Path, *, mock: bool = True) -> list[ScenarioReport]:
    raise NotImplementedError
