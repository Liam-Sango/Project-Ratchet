from __future__ import annotations

import tempfile, os, argparse, json
from PIL import Image
from src.main import run_server, run_agent, shared_state
from src.keys import server_generate_k_root, server_derive_allkeys, server_save_server_keys, agent_save_agent_keys, server_load_server_keys, agent_load_agent_keys

def test_full_loop_integration() -> None:
    with tempfile.TemporaryDirectory() as td:
        # 1) Paths you invent (just strings under td)
        server_keyfile = os.path.join(td, "server.json")
        agent_keyfile = os.path.join(td, "agent.json")
        cover_path = os.path.join(td, "cover.png")
        wallet_path = os.path.join(td, "wallet.json")
        secret_bin = os.path.join(td, "secret.bin")

        #Place a comment here later
        byte_val = b"LOL"
        with open(secret_bin, "wb") as f:
            f.write(byte_val)

        open(wallet_path, "w").write("{}")
        Image.new("RGB", (512, 512), (128, 128, 128)).save(cover_path)

        # Keys via keys.py — not hand-rolled hex
        k_root = server_generate_k_root()
        d = server_derive_allkeys(k_root)

        initial_task_ratchet = d["K_ratchet"]
        initial_exfil_ratchet = d["K_exfil_ratchet"]

        server_save_server_keys(
            server_keyfile,
            k_root,
            d["K_ratchet"],
            d["K_exfil_ratchet"],
            agent_wallet="agent_wallet",   # must match mock upload string in main.py
            last_seen_txid="",
        )
        agent_save_agent_keys(
            agent_keyfile,
            d["K_ratchet"],
            d["K_exfil_ratchet"],
            d["K_extract"],
            server_wallet="server_wallet",  # must match mock server wallet string
            last_seen_txid="",
            cover_path="",
        )

        exfil_task = (
            "PUSH32 0 PUSH32 1936024434 STORE32 "
            "PUSH32 4 PUSH32 1702112866 STORE32 "
            "PUSH32 8 PUSH32 1768816640 STORE32 "
            "PUSH32 0 SYSCALL 0 SYSCALL 6 HALT"
        )

        old_dir = os.getcwd()
        try:
            os.chdir(td)

            # Clear residual process state, then call main
            shared_state.clear()

            server_args = argparse.Namespace(
                keyfile=server_keyfile,
                cover=cover_path,
                wallet=wallet_path,
                mock=True,
                task=exfil_task,
                retrieve=None,
            )
            assert run_server (server_args) == 1, "server send should return 1"

            server_keys = server_load_server_keys(server_keyfile)

            assert server_keys["K_ratchet"] != initial_task_ratchet, (
                "after server send: task ratchet should advance"
            )
            assert server_keys["K_exfil_ratchet"] == initial_exfil_ratchet, (
                "after server send: exfil ratchet should not advance"
            )

            assert "mock" in shared_state, "after server send: mock Arweave missing from shared_state"
            assert "txid" in shared_state, "after server send: task txid missing from shared_state"

            agent_args = argparse.Namespace(
                keyfile=agent_keyfile,
                wallet=wallet_path,
                mock=True,
                bootstrap_url="mock://x",  # ignored in mock; uses shared_state["txid"]
                watch=False,
            )

            assert run_agent(agent_args) == 1, "agent bootstrap should return 1"

            agent_keys = agent_load_agent_keys(agent_keyfile)
            server_keys = server_load_server_keys(server_keyfile)

            assert agent_keys["K_ratchet"] != initial_task_ratchet, (
                "after agent bootstrap: task ratchet should advance"
            )
            assert agent_keys["K_ratchet"] == server_keys["K_ratchet"], (
                "after agent bootstrap: server and agent task ratchets should match"
            )
            assert agent_keys["K_exfil_ratchet"] != initial_exfil_ratchet, (
                "after agent bootstrap: agent exfil ratchet should advance"
            )
            assert server_keys["K_exfil_ratchet"] == initial_exfil_ratchet, (
                "after agent bootstrap: server exfil ratchet advances only on retrieve"
            )
            assert "K_root" not in agent_keys, (
                "agent key material must not include K_root"
            )

            # TODO: server retrieve + post-retrieve exfil ratchet asserts

        finally:
            os.chdir(old_dir)


def test_keys_isolation() -> None:
    raise NotImplementedError


def test_crypto_roundtrip_and_tamper() -> None:
    raise NotImplementedError


def test_stego_roundtrip() -> None:
    raise NotImplementedError


def test_arweave_mock_wallet_history() -> None:
    raise NotImplementedError


def test_vm_execute_and_wipe() -> None:
    raise NotImplementedError


def test_failure_wrong_k_extract() -> None:
    raise NotImplementedError


def test_failure_tampered_stego() -> None:
    raise NotImplementedError


def test_failure_oversized_bytecode() -> None:
    raise NotImplementedError


def test_failure_ratchet_desync() -> None:
    raise NotImplementedError


def test_failure_wrong_wallet() -> None:
    raise NotImplementedError


def test_failure_missing_cover() -> None:
    raise NotImplementedError


def test_security_backward_secrecy() -> None:
    raise NotImplementedError


def test_security_k_root_absent_from_agent_paths() -> None:
    raise NotImplementedError


def test_security_vm_wipe() -> None:
    raise NotImplementedError


def test_scenario_key_steal_detects() -> None:
    raise NotImplementedError


def test_scenario_key_corrupt_fail_closed() -> None:
    raise NotImplementedError


def test_scenario_rng_subversion_flags() -> None:
    raise NotImplementedError


def run_all() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    test_full_loop_integration()
