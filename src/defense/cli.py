"""Defense / scenario CLI entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="defense",
        description="Defensive evaluation scenarios for Project Ratchet fixture (lab only).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scenario = sub.add_parser("scenario", help="Run a single scenario")
    p_scenario.add_argument(
        "name",
        choices=["key-steal", "rng-subversion", "key-corrupt", "all"],
    )
    p_scenario.add_argument("--workdir", type=Path, default=Path("."))
    p_scenario.add_argument("--mock", action="store_true", default=True)
    p_scenario.add_argument("--json", action="store_true", help="Emit JSON report")

    return parser


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
