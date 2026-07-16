"""JSON and human-readable scenario reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.defense.events import Alert


@dataclass
class ScenarioReport:
    scenario: str
    passed: bool
    alerts: list[Alert] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    false_positive_notes: list[str] = field(default_factory=list)
    residual_risks: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


def render_text(report: ScenarioReport) -> str:
    raise NotImplementedError


def render_json(report: ScenarioReport) -> str:
    raise NotImplementedError


def render_bundle_text(reports: list[ScenarioReport]) -> str:
    raise NotImplementedError


def render_bundle_json(reports: list[ScenarioReport]) -> str:
    raise NotImplementedError


def report_to_dict(report: ScenarioReport) -> dict[str, Any]:
    return asdict(report)
