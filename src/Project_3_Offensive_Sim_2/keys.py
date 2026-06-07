import os
import hashlib
import hmac

#Derive our task persistent keys
K_root = os.urandom(32)
K_ratchet = hmac.new(K_root, b"RATCHET_INIT", hashlib.sha256)
K_extract = hmac.new(K_root, b"EXTRACT", hashlib.sha256)

#Advanced ratchet mechanism
def advance_ratchet(k_ratchet):
    return hmac.new(k_ratchet, b"RATCHET", hashlib.sha256)

#Derives our per task keys
def derive_cmd_key(k_ratchet, salt):
    return hmac.new(k_ratchet, salt + b"CMDKEY", hashlib.sha256)