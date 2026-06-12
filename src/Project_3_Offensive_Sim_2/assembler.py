import sys


OPCODE_TABLE = {
    # Stack
    "PUSH32": 0x01,
    "DUP": 0x02,
    "SWAP": 0x03,
    "DROP": 0x04,

    # Arithmetic
    "ADD": 0x10,
    "SUB": 0x11,
    "AND": 0x12,
    "OR": 0x13,
    "XOR": 0x14,
    "NOT": 0x15,

    # Memory
    "LOAD32": 0x20,
    "STORE32": 0x21,

    # Control
    "JMP": 0x30,
    "JZ": 0x31,
    "JNZ": 0x32,
    "CALL": 0x33,
    "RET": 0x34,

    # System
    "SYSCALL": 0x40,

    # Halt
    "HALT": 0xFF,
}


def parse_bytecode_line(instruction):
    parsed_bytecode_line = ""

    #

    instruction_list = instruction.split(" ", 1)
    instruction_mmemoric = instruction_list[1]



    #Pre pass error checking
    if instruction_mmemoric not in OPCODE_TABLE.values():
        raise(ValueError)("Opcode in parse_btyecode_line is not present in instruction_mmemoric table")


    #first pass (opcodes)
    if (instruction_mmemoric == "PUSH32"):
        print("ABC")

    elif (instruction_mmemoric == "SYSCALL"):
        print("ABC")

    elif (instruction_mmemoric == "JMP"):
        print("DEF")
    elif (instruction_mmemoric == "JZ"):
        print("DEF")
    elif (instruction_mmemoric == "JNZ"):
        print("DEF")
    elif (instruction_mmemoric == "CALL"):
        print("DEF")

    else:
        {parsed_bytecode_line == OPCODE_TABLE.get(instruction_mmemoric)}


    #Second pass (Labels)
    return parsed_bytecode_line
    

def assemble_payload(bytecode):
    payload = ""

    if sys.getsizeof(payload > 256):
        return 0
    

    print("")

