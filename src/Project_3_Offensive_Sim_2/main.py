import logging

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


#Fill out later
from src.Project_3_Offensive_Sim_2.assembler import assemble_payload
from src.Project_3_Offensive_Sim_2.crypto_wrapper import encrypt_task, decrypt_task
from src.Project_3_Offensive_Sim_2.stego import embed, extract
from src.Project_3_Offensive_Sim_2.vm import execute_bytecode
from src.Project_3_Offensive_Sim_2.arweave_interface import MockArweave

def run_server(args):
    print("TEMP")

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


