import os
import hashlib
import hmac
import json
import arweave

#Shared functions

#Advanced ratchet mechanism
def advance_ratchet(k_ratchet):
    return hmac.new(k_ratchet, b"RATCHET", hashlib.sha256).digest()

#Derives our per task keys
def derive_cmd_key(k_ratchet, salt):
    return hmac.new(k_ratchet, salt + b"CMDKEY", hashlib.sha256).digest()


#Server side functions

def server_generate_k_root():
    k_root = os.urandom(32)
    return k_root

def server_derive_allkeys(k_root):
    print("ABC")

def server_save_server_keys(keyfile_path, k_root):
    print("ABC")

def server_load_server_keys(keyfile_path):
    print("ABC")


#Agent side functions

def agent_save_agent_keys(keyfile_path, k_ratchet, K_exfil_ratchet, k_extract):
    print("ABC")

def load_agent_keys(keyfile_path):
    print("ABC")


#Wallet functions

def load_wallet(keyfile_path):
    print("ABC")




