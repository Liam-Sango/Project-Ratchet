"""JSON and human-readable scenario reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.defense.events import Alert

import json


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
    #Initialises our report variable
    text_report = f""

    #Adds our scenario string to our report
    text_report += "Scenario: "
    text_report += report.scenario
    text_report += "\n"

    #Adds our result string to our report
    text_report += "Result:   "

    if report.passed:
        text_report += "PASS"
    else: 
        text_report += "FAIL"
    text_report += "\n"

    #Adds our alert strings to our report

    #Alert header
    if report.alerts is not None:
        alert_len = len(report.alerts)
        text_report += f"Alerts ({alert_len}):"
        text_report += "\n"

    elif report.alerts is None:
        text_report += f"Alerts: none"
        text_report += "\n"

    #Alert bodies
    for alert in report.alerts:
        alert_str = f""

        alert_str += f"  [{alert.class_}] " 

        if alert.event_index is not None:
            alert_str += f"@event {alert.event_index} - "
            alert_str += f"{alert.message}"
            text_report += "\n"
        else: 
            alert_str += f"{alert.message}"
            text_report += "\n"

        text_report += alert_str
        








    

def render_json(report: ScenarioReport) -> str:
    json_report =json.dumps(report_to_dict(report), indent=2)
    return json_report


def render_bundle_text(reports: list[ScenarioReport]) -> str:
    raise NotImplementedError


def render_bundle_json(reports: list[ScenarioReport]) -> str:
    raise NotImplementedError


def report_to_dict(report: ScenarioReport) -> dict[str, Any]:
    return asdict(report)
