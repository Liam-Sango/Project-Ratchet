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

from src.stego import (
    embed,
    extract,
)

from src.arweave_interface import (
    MockArweave,
)

from src.assembler import (
    assemble_payload
)

from src.vm import (
    execute_bytecode,
    VirtualMachine,
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
    with tempfile.TemporaryDirectory() as td:
        # Temp paths for cover and stego images
        cover_path = os.path.join(td, "cover.png")
        stego_path = os.path.join(td, "stego.png")

        # Large enough RGB cover for payload + 4-byte length prefix
        Image.new("RGB", (512, 512), (128, 128, 128)).save(cover_path)

        k = os.urandom(32)

        payload = b"STEGO_TEST"

        # Embed payload at keyed LSB positions
        stego_img = embed(cover_path, payload, k)

        assert stego_img is not None, (
            "embed must succeed for a payload within cover capacity"
        )

        stego_img.save(stego_path)

        # key recovers payload
        stego_out = extract(stego_path, k)

        assert stego_out == payload, (
            "extract with correct K_extract must recover the embedded payload"
        )

def test_arweave_mock_wallet_history() -> None:
    with tempfile.TemporaryDirectory() as td:
        mock = MockArweave()
        image_path = os.path.join(td, "cover.png")
        wallet_1 = "ABCDEF"
        wallet_2 = "GHIJKL"

        # Fresh mock: no history for either wallet
        assert mock.get_wallet_transactions(wallet_1) == [], (
            "wallet_1 history must start empty"
        )
        assert mock.get_wallet_transactions(wallet_2) == [], (
            "wallet_2 history must start empty"
        )
        assert mock.get_latest_transaction(wallet_1) is None, (
            "latest tx for empty wallet_1 must be None"
        )

        Image.new("RGB", (512, 512), (128, 128, 128)).save(image_path)

        # Two uploads from wallet_1; wallet_2 must stay empty
        w1_t1_txid = mock.upload_image(wallet_1, image_path)
        assert mock.get_wallet_transactions(wallet_2) == [], (
            "wallet_2 must stay empty when only wallet_1 uploads"
        )

        w1_t2_txid = mock.upload_image(wallet_1, image_path)
        assert w1_t1_txid != w1_t2_txid, (
            "successive uploads must produce distinct txids"
        )

        w1_history = mock.get_wallet_transactions(wallet_1)
        assert len(w1_history) == 2, (
            "wallet_1 history length must match upload count"
        )
        assert w1_history[0] == w1_t1_txid, (
            "first history entry must be the first upload txid"
        )
        assert w1_history[1] == w1_t2_txid, (
            "second history entry must be the second upload txid"
        )
        assert mock.get_latest_transaction(wallet_1) == w1_t2_txid, (
            "latest transaction must be the most recent upload"
        )

        with open(image_path, "rb") as f:
            on_disk = f.read()

        assert mock.download_image(w1_t1_txid) == on_disk, (
            "download_image must return the uploaded file bytes"
        )

        try:
            mock.download_image("not_a_real_txid")
            assert False, "download of unknown txid must raise KeyError"
        except KeyError:
            pass
    

def test_vm_execute_and_wipe() -> None:
    # Track A: execute_bytecode snapshot after PUSH32 7 HALT
    ta_payload = assemble_payload(["PUSH32 7", "HALT"])
    ta_result = execute_bytecode(ta_payload)

    assert ta_result["is_halted"] is True, (
        "execute_bytecode must halt on HALT"
    )
    assert ta_result["data_stack"] == [7], (
        "data stack snapshot must contain the pushed value 7"
    )

    # Track B: direct VirtualMachine run + wipe clears ephemeral state
    tb_payload = assemble_payload(["PUSH32 7", "HALT"])
    vm = VirtualMachine(bytearray(tb_payload))
    vm.run()

    assert vm.is_halted is True, (
        "VM.run must set is_halted after HALT"
    )
    assert list(vm.data_stack) == [7], (
        "data stack must hold 7 before wipe"
    )

    vm.wipe()

    assert len(vm.data_stack) == 0, (
        "wipe must clear the data stack"
    )
    assert len(vm.return_stack) == 0, (
        "wipe must clear the return stack"
    )
    assert len(vm.memory) == 0, (
        "wipe must clear VM memory"
    )
    assert len(vm.bytecode) == 0, (
        "wipe must clear the bytecode buffer"
    )
    assert len(vm.buffers) == 0, (
        "wipe must clear handle buffers"
    )

def test_failure_wrong_k_extract() -> None:
    with tempfile.TemporaryDirectory() as td:
        # Temp paths for cover and stego images
        cover_path = os.path.join(td, "cover.png")
        stego_path = os.path.join(td, "stego.png")

        # Large enough RGB cover for payload + 4-byte length prefix
        Image.new("RGB", (512, 512), (128, 128, 128)).save(cover_path)

        k_wrong = os.urandom(32)
        k_right = os.urandom(32)

        payload = b"STEGO_TEST"

        # Embed payload at keyed LSB positions
        stego_img = embed(cover_path, payload, k_right)

        assert stego_img is not None, (
            "embed must succeed for a payload within cover capacity"
        )

        stego_img.save(stego_path)

        # Correct key recovers payload; wrong key must not
        stego_out = extract(stego_path, k_right)
        bad_stego_out = extract(stego_path, k_wrong)

        assert stego_out == payload, (
            "extract with correct K_extract must recover the embedded payload"
        )

        assert bad_stego_out != payload, (
            "extract with wrong K_extract must not recover the payload"
        )
    

def test_failure_tampered_stego() -> None:
    with tempfile.TemporaryDirectory() as td:
        # Temp paths for cover and stego images
        cover_path = os.path.join(td, "cover.png")
        stego_path = os.path.join(td, "stego.png")

        # Large enough RGB cover for payload + 4-byte length prefix
        Image.new("RGB", (512, 512), (128, 128, 128)).save(cover_path)

        k = os.urandom(32)

        payload = b"STEGO_TEST"

        # Embed payload at keyed LSB positions
        stego_img = embed(cover_path, payload, k)

        assert stego_img is not None, (
            "embed must succeed for a payload within cover capacity"
        )

        stego_img.save(stego_path)

        # Extract message out of stego image
        stego_out = extract(stego_path, k)

        assert stego_out == payload, (
            "extract with correct K_extract must recover the embedded payload"
        )

        # Corrupt the saved stego image by pixel punching
        img = Image.open(stego_path)
        pixels = img.load()

        for y in range(512):
            for x in range(512):
                pixels[x, y] = (0, 0, 0)

        img.save(stego_path)

        #Extract and compare the corrupted image to the initial payload
        bad_out = extract(stego_path, k)

        assert bad_out != payload, (
            "extract with corrupted stego image must not recover the embedded payload"
        )

def test_failure_oversized_bytecode() -> None:
    #52x PUSH32 (5 bytes each) = 260 bytes > 256-byte limit
    oversized_bytecode = ["PUSH32 1"] * 52 + ["HALT"]
    
    try: 
        assemble_payload(oversized_bytecode)
        assert False, "assemble_payload must reject oversized bytecode"
    except ValueError:
        pass


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
