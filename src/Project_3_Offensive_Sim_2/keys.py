import os

import hashlib
import hmac

#Derive our keys
K_root = os.urandom(32)

K_ratchet = hmac.new(K_root, b"RATCHET_INIT", hashlib.sha256)
K_extract = hmac.new(K_root, b"EXTRACT", hashlib.sha256)

def advance_ratchet():
    print('Hello World')

