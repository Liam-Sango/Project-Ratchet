# Project Ratchet

A defensive security research platform implementing a covert tasking and exfiltration channel using Arweave's permaweb as a permanent dead drop. The system simulates how a sophisticated threat actor might remotely task a compromised agent to exfiltrate cryptographic key material, enabling systematic study of detectability, forensic footprint, and resilience against defensive tooling.

All components run in a sandboxed lab environment. The system never interacts with real targets or production networks.

## Architecture

Four components form a closed-loop channel:

1. **Command Server** (`main.py`) — composes tasking, encrypts with a ratchet key, hides it in a cover image via keyed steganography, uploads to Arweave (or mock). Retrieves and decrypts exfiltrated key material.
2. **Arweave Permaweb** — immutable dead-drop storage. Mock (`MockArweave`) for testing; real gateway for timing analysis.
3. **Centralized Platform** (bootstrap only) — one-time delivery channel for the first tasking image.
4. **Simulated Agent** (`main.py`) — fetches tasking images, extracts payloads, decrypts, executes bytecode in an ephemeral VM, exfiltrates key material to Arweave, wipes all artifacts.

### Key Hierarchy

| Key | Purpose | Persistence |
|-----|---------|-------------|
| `K_root` | Master key; derives all others | Server-only, never on agent |
| `K_ratchet` | Tasking ratchet (server → agent) | Advances after each task decrypt |
| `K_exfil_ratchet` | Exfiltration ratchet (agent → server) | Advances after each exfil |
| `K_cmd` | Per-message AES-256-GCM key | Ephemeral; zeroed after use |
| `K_extract` | Steganographic position PRNG seed | Long-term, embedded at deployment |

`K_root` is never referenced in agent code paths — a verifiable security property.

## File Structure

```
src/
    main.py              — CLI orchestrator (server + agent subcommands)
    keys.py              — Key management, ratchet advancement, keyfile I/O
    assembler.py         — Two-pass bytecode assembler (256-byte limit)
    vm.py                — Stack-based VM with syscalls, ephemeral wipe, timeout
    crypto_wrapper.py    — AES-256-GCM encrypt/decrypt (direction-agnostic)
    stego.py             — Keyed LSB steganography with length-prefix
    arweave_interface.py — MockArweave + real gateway upload/download/wallet-watch
    test_harness.py      — (pending) integration + isolation + failure-mode tests
    
```
## Usage

### Server (send a task)

```bash
python -m src.main server --keyfile server.json --task "PUSH32 42 HALT" --cover cover.png --wallet wallet.json --mock
```

### Agent (bootstrap fetch)

```bash
python -m src.main agent --keyfile agent.json --wallet wallet.json --bootstrap-url http://example.com/task.png --mock
```

### Agent (watch for replies)

```bash
python -m src.main agent --keyfile agent.json --wallet wallet.json --watch --mock
```

`--bootstrap-url` and `--watch` are mutually exclusive. `--mock` uses `MockArweave` instead of the real Arweave network.

## Dependencies

- Python 3.10+
- `cryptography` (AES-256-GCM)
- `Pillow` (image processing)
- `numpy` (pixel array operations)
- `arweave` (real Arweave wallet/network; lazy-imported, only needed for real mode)

## Design Principles

- **Indistinguishability** — all payloads are cryptographically indistinguishable from random noise
- **Backward secrecy** — one-way HMAC ratchets prevent retrospective decryption
- **No persistent infrastructure** — after bootstrap, all communication flows through Arweave
- **Ephemeral execution** — VM state is zeroed and garbage-collected post-execution
- **Small payload optimisation** — 256-byte bytecode envelope for key material (32–64 bytes)

## Known Limitations

- No post-compromise forward security (DH ratcheting deferred)
- Non-atomic keyfile writes (crash mid-write corrupts state)
- Preemptive VM timeout not enforced during blocking syscalls
- `zero_key` is best-effort (Python's `cryptography` library may retain internal key copies)
- Server-side exfil retrieval not yet implemented
- Test harness (`test_harness.py`) not yet implemented