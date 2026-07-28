"""Scenario injectors and runners (S1 key-steal, S2 RNG subversion, S3 key corruption)."""

from __future__ import annotations

import os
import argparse
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image

from src.defense.events import Alert, Event, EventCollector, set_collector
from src.defense.report import ScenarioReport
from src.keys import (
    server_generate_k_root,
    server_derive_allkeys,
    server_save_server_keys,
    agent_save_agent_keys,
)
from src.main import run_server, run_agent, shared_state

from src.keys import (
    server_generate_k_root,
    server_derive_k_extract,
    server_derive_allkeys,
    server_save_server_keys,
    agent_save_agent_keys,
    server_load_server_keys,
    agent_load_agent_keys,
    advance_ratchet,
)


import tempfile
import os


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

def _path_to_store_asm(path: str) -> str:
    """Encode a null-terminated path as PUSH32/STORE32 memory-write instructions."""
    data = path.encode("utf-8") + b"\0"
    while len(data) % 4:           # pad to 4-byte boundary
        data += b"\0"
    parts = []
    for i in range(0, len(data), 4):
        word = int.from_bytes(data[i:i+4], "big", signed=True)
        parts.append(f"PUSH32 {i} PUSH32 {word} STORE32")
    return " ".join(parts)

def inject_key_steal(config: ScenarioConfig) -> list[Event]:
    """Run a key-steal scenario through the real fixture and return captured events."""
    collector = EventCollector()
    set_collector(collector)
    try:
        with tempfile.TemporaryDirectory() as td:
            server_keyfile = os.path.join(td, "server.json")
            agent_keyfile = os.path.join(td, "agent.json")
            cover_path = os.path.join(td, "cover.png")
            wallet_path = os.path.join(td, "wallet.json")
            sensitive_path = os.path.join(td, "key.json")

            # Sensitive target file with fake key material
            with open(sensitive_path, "w") as f:
                f.write('{"K_root": "deadbeef", "K_ratchet": "cafebabe"}')

            # Dummy wallet file (mock mode does not read it)
            open(wallet_path, "w").write("{}")

            # Cover image
            Image.new("RGB", (512, 512), (128, 128, 128)).save(cover_path)

            # Provision keys
            k_root = server_generate_k_root()
            d = server_derive_allkeys(k_root)

            server_save_server_keys(
                server_keyfile,
                k_root,
                d["K_ratchet"],
                d["K_exfil_ratchet"],
                agent_wallet="agent_wallet",
                last_seen_txid="",
            )
            
            agent_save_agent_keys(
                agent_keyfile,
                d["K_ratchet"],
                d["K_exfil_ratchet"],
                d["K_extract"],
                server_wallet="server_wallet",
                last_seen_txid="",
                cover_path="",
            )

            # Steal bytecode: write "key.json" to memory, read it, upload via exfil
            steal_task = _path_to_store_asm("key.json") + " PUSH32 0 SYSCALL 0 SYSCALL 6 HALT"

            old_dir = os.getcwd()
            try:
                os.chdir(td)
                shared_state.clear()

                server_args = argparse.Namespace(
                    keyfile=server_keyfile,
                    cover=cover_path,
                    wallet=wallet_path,
                    mock=True,
                    task=steal_task,
                    retrieve=None,
                )
                assert run_server(server_args) == 1, "server send should return 1"

                agent_args = argparse.Namespace(
                    keyfile=agent_keyfile,
                    wallet=wallet_path,
                    mock=True,
                    bootstrap_url="mock://x",
                    watch=False,
                )
                assert run_agent(agent_args) == 1, "agent bootstrap should return 1"

            finally:
                os.chdir(old_dir)
    finally:
        set_collector(None)

    return collector.as_list()


def inject_rng_subversion(config: ScenarioConfig) -> list[Event]:
    raise NotImplementedError


def inject_key_corrupt(config: ScenarioConfig) -> list[Event]:
    raise NotImplementedError


def run_scenario(config: ScenarioConfig) -> ScenarioReport:
    raise NotImplementedError


def run_all(workdir: Path, *, mock: bool = True) -> list[ScenarioReport]:
    raise NotImplementedError
