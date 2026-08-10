#!/usr/bin/env bash
#
# PROJECT RATCHET — environment setup
# Creates a Python virtualenv (if absent) and installs dependencies.

set -euo pipefail

VENV=".venv"
PYTHON="${PYTHON:-python3}"

if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found — run from the repo root." >&2
    exit 1
fi

if [ ! -d "$VENV" ]; then
    echo "Creating virtualenv '$VENV'…"
    "$PYTHON" -m venv "$VENV"
else
    echo "Virtualenv '$VENV' already exists."
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Installing dependencies from requirements.txt…"
pip install -r requirements.txt

echo "Setup complete. Activate with: source .venv/bin/activate"
