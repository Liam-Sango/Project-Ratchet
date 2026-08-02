"""JSON and human-readable scenario reports."""

from __future__ import annotations

import json
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
    text_report = ""

    text_report += "Scenario: "
    text_report += report.scenario
    text_report += "\n"

    text_report += "Result:   "
    if report.passed:
        text_report += "PASS"
    else:
        text_report += "FAIL"
    text_report += "\n"

    if report.alerts:
        text_report += f"Alerts ({len(report.alerts)}):\n"
        for alert in report.alerts:
            line = f"  [{alert.class_}] "
            if alert.event_index is not None:
                line += f"@event {alert.event_index} — {alert.message}"
            else:
                line += alert.message
            text_report += line + "\n"
    else:
        text_report += "Alerts: none\n"

    if report.metrics:
        text_report += "Metrics:\n"
        for key, value in report.metrics.items():
            text_report += f"  {key}: {value}\n"
    else:
        text_report += "Metrics: none\n"

    if report.false_positive_notes:
        text_report += "False positives:\n"
        for fp in report.false_positive_notes:
            text_report += f"  - {fp}\n"
    else:
        text_report += "False positives: none\n"

    if report.residual_risks:
        text_report += "Residual risks:\n"
        for rr in report.residual_risks:
            text_report += f"  - {rr}\n"
    else:
        text_report += "Residual risks: none\n"

    if report.detail:
        text_report += "Detail:\n"
        for key, value in report.detail.items():
            text_report += f"  {key}: {value}\n"

    return text_report


def render_json(report: ScenarioReport) -> str:
    json_report =json.dumps(report_to_dict(report), indent=2)
    return json_report


def render_bundle_text(reports: list[ScenarioReport]) -> str:
    text_bundle = ""

    #Finds the total number of reports in the report list
    report_total = len(reports)

    #Finds the result of each report in the report list
    passed_count = sum(1 for r in reports if r.passed)
    failed_count = sum(1 for r in reports if not r.passed)

    #Finds the overall result
    overall_passed = all(r.passed for r in reports)

    if overall_passed:
        overall_result = "PASS"
    else:
        overall_result = "FAIL"

    #Takes the values gathered and puts them into a header
    text_bundle += f"Scenarios: {report_total} (PASS: {passed_count} FAIL: {failed_count})\n"
    text_bundle += f"Overall:   {overall_result}\n"

    #Creates the report with the report list
    parts = [render_text(r) for r in reports]
    if parts:
        text_bundle += "──────────\n".join(parts)

    return text_bundle


def render_bundle_json(reports: list[ScenarioReport]) -> str:
    raise NotImplementedError


def report_to_dict(report: ScenarioReport) -> dict[str, Any]:
    return asdict(report)
