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
