import logging
import PIL
import tempfile
import os

# Configure logging before importing project modules
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("forensic.log"),
        logging.StreamHandler(),
    ]
)
#Creates logger object
logger = logging.getLogger(__name__)


#Creates CLI using argparse

#Main parser
import argparse
parser = argparse.ArgumentParser(prog='MAIN', usage="WILL BE FILLED OUT", description="WILL BE FILLED OUT")
subparser = parser.add_subparsers(dest="Command")

#Server subcommands
server_parser = subparser.add_parser(name="server", description="server commands", prog="MAIN")

#--TASK
server_parser.add_argument("--task", required=True, help="Space seperated assembly")
#--COVER
server_parser.add_argument("--cover", required=True, help="Path to the cover image")
#--MOCK
server_parser.add_argument("--mock", action="store_true", help="Use mock Arweave instead of real network")

#Agent subcommands
agent_parser  = subparser.add_parser(name="agent", description="agent commands", prog="MAIN")

#--TXID
agent_parser.add_argument("--txid", required=True, help="The TXID")
#--MOCK
agent_parser.add_argument("--mock", action="store_true", help="Use mock Arweave instead of real network")

#Imports
from src.Project_3_Offensive_Sim_2.keys import K_ratchet
from src.Project_3_Offensive_Sim_2.keys import K_extract

from src.Project_3_Offensive_Sim_2.assembler import OPCODE_TABLE
from src.Project_3_Offensive_Sim_2.assembler import assemble_payload
from src.Project_3_Offensive_Sim_2.crypto_wrapper import encrypt_task, decrypt_task
from src.Project_3_Offensive_Sim_2.stego import embed, extract
from src.Project_3_Offensive_Sim_2.vm import execute_bytecode
from src.Project_3_Offensive_Sim_2.arweave_interface import MockArweave

shared_state = {}

def run_server(args):
    #Splits args.tasks into valid bytecode instructions
    task_string = args.task
    task_tokens = task_string.split()

    lines = []
    current_instruction = []
    for token in task_tokens:

        if token in OPCODE_TABLE:
            if current_instruction:
                lines.append(" ".join(current_instruction))
            current_instruction = [token]
        else:
            current_instruction.append(token)

    if current_instruction:
        lines.append(" ".join(current_instruction))
    
    #Assembles the payload.
    logger.info("Step A, Payload assembly start")
    bytecode = assemble_payload(lines)
    bytecode_length = len(bytecode)
    logger.info(f"Step A, bytecode length is {bytecode_length}")

    #Encrypts the task
    payload, new_ratchet = encrypt_task(bytecode, K_ratchet)
    payload_length = len(payload)
    logger.info(f"Step A, Payload length is {payload_length}")
    logger.info(f"Step A, Payload assembly finished")

    #Embeds the payload
    logger.info(f"Step B, Payload embedding start")
    stego_image = embed(args.cover, payload, K_extract)

    stego_dir = "src/Project_3_Offensive_Sim_2/temp"
    os.makedirs(stego_dir, exist_ok=True)
    stego_path = os.path.join(stego_dir, "stego.png")
    stego_image.save(stego_path)   

    logger.info(f"Step B, Embedded image saved to {stego_path}")
    logger.info(f"Step B, Payload embedding finished")

    logger.info(f"Step C, Image upload start")
    if args.mock:
        mock = MockArweave()
        txid = mock.upload_image(stego_path)
        logger.info(f"Step C, Image uploaded in transaction_id {txid}")
        logger.info(f"Step C, Image upload finished")
    else:
    #Finish later
        raise NotImplementedError("Real Arweave upload not configured")
    
    shared_state["txid"] = txid
    shared_state["payload_length"] = payload_length
    shared_state["new_ratchet"] = new_ratchet
    shared_state["mock"] = mock
    
def run_agent(args):
    print("TEMP")

# Parses args and dispatch
if __name__ == "__main__":
    args = parser.parse_args()

    if args.Command == "server":
        run_server(args)
    elif args.Command == "agent":
        run_agent(args)
    else:
        parser.print_help()


