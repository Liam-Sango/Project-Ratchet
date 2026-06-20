import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidToken
from src.Project_3_Offensive_Sim_2.keys import derive_cmd_key, advance_ratchet

#Replaces a key with zero.
def zero_key (key: bytearray):
    for x in range(len(key)):
        key[x] = 0

def encrypt_task(bytecode: bytes, K_ratchet: bytes) -> tuple[bytes, bytes]:
    #Generate random values
    salt = os.urandom(16)
    iv = os.urandom(12)

    #Derive K_cmd
    k_cmd = bytearray(derive_cmd_key(K_ratchet, salt))

    aesgcm = AESGCM(bytes(k_cmd))

    ciphertext_and_tag = aesgcm.encrypt(iv, bytecode, None)
    payload = salt + iv + ciphertext_and_tag

    zero_key(k_cmd)
    new_k_ratchet = advance_ratchet(K_ratchet)

    return(payload, new_k_ratchet)

def decrypt_task(payload: bytes, k_ratchet: bytes) -> tuple[bytes, bytes] | None:
    print("ABC")
