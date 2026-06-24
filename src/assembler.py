import sys
import struct

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

def get_instruction_size(instruction):
    instruction_size = 0

    SINGLE_BYTE_OPS = {"DUP", "SWAP", "DROP", "ADD", "SUB", "AND", "OR", "XOR", "NOT", "LOAD32", "STORE32", "RET", "HALT"}
    TWO_BYTE_OPS = {"JMP", "JZ", "JNZ", "CALL"}

    instruction_list = instruction.split(" ", 1)

    if instruction_list[0] not in OPCODE_TABLE:
        raise ValueError(f"Unknown opcode '{instruction_list[0]}' in get_instruction_size")
    
    instruction_mnemonic = instruction_list[0] 
    opcode_byte = OPCODE_TABLE[instruction_mnemonic]

    if (len(instruction_list) == 2):
         instruction_operand = instruction_list[1] 
    else:
        instruction_operand = None


    #Calculates and returns the size of single byte operations
    if (instruction_operand is not None and instruction_mnemonic in SINGLE_BYTE_OPS): 
          raise ValueError(f"Instruction '{instruction_mnemonic}' requires an operand but none was provided.")
    
    if (instruction_mnemonic in SINGLE_BYTE_OPS):
        instruction_size = 1
        return instruction_size
    

    #Calculates and returns the size of two byte operations
    elif (instruction_mnemonic in TWO_BYTE_OPS):

        if(instruction_operand is None):
              raise ValueError(f"Instruction '{instruction_mnemonic}' requires an operand but none was provided.")
        
        instruction_size = 3
    
    #Calculates and returns the size of PUSH32 instructions
    elif (instruction_mnemonic == "PUSH32"):

        if(instruction_operand is None):
              raise ValueError(f"Instruction '{instruction_mnemonic}' requires an operand but none was provided.")

        instruction_size = 5

    #Calculates and returns the size of SYSCALL instructions
    elif (instruction_mnemonic == "SYSCALL"):

        if(instruction_operand is None):
              raise ValueError(f"Instruction '{instruction_mnemonic}' requires an operand but none was provided.")
        
        instruction_size = 2


    return instruction_size

def resolve_labels(assembly_lines):

    label_offsets = {}
    byte_offset = 0

    for line in assembly_lines:
        cleaned_line = line.strip()

        if not cleaned_line:
            continue
        
        if cleaned_line.endswith(':'):
            label_name = cleaned_line[:-1].strip()

            if not label_name:
                raise ValueError("Invalid label format: empty name.")

            if label_name in label_offsets:
                raise ValueError(f"Duplicate label definition: '{label_name}'")

            label_offsets[label_name] = byte_offset
            continue
        
        instruction_size = get_instruction_size(cleaned_line)
        byte_offset += instruction_size

    return label_offsets

def parsed_bytecode_line(instruction):
    parsed_bytecode_line = b""

    instruction_list = instruction.split(" ", 1)

    if instruction_list[0] not in OPCODE_TABLE:
        raise ValueError("parsed Opcode mmemoric in parse_btyecode_line is not present in instruction table")
    
    instruction_mnemonic = instruction_list[0] 
    opcode_byte = OPCODE_TABLE[instruction_mnemonic]
    
    if (len(instruction_list) == 2):
         instruction_operand = instruction_list[1] 
    else:
        instruction_operand = None


    SINGLE_BYTE_OPS = {"DUP", "SWAP", "DROP", "ADD", "SUB", "AND", "OR", "XOR", "NOT", "LOAD32", "STORE32", "RET", "HALT"}
    TWO_BYTE_OPS = {"JMP", "JZ", "JNZ", "CALL"}

    if (instruction_operand is not None and instruction_mnemonic in SINGLE_BYTE_OPS): 
        raise ValueError("Parsed invalid instruction operand pairing in parsed_bytecode_line,") 
    
    #Single byte operations
    elif (instruction_mnemonic in SINGLE_BYTE_OPS):
        parsed_bytecode_line = bytes([opcode_byte])

    #Two byte operations
    elif (instruction_mnemonic in TWO_BYTE_OPS):

        if(instruction_operand is None):
            raise ValueError("Parsed invalid instruction operand pairing in parsed_bytecode_line,") 
        
        int_value = int(instruction_operand)
        packed_bytes = struct.pack(">h", int_value)

        parsed_bytecode_line = bytes([opcode_byte]) + packed_bytes

    #Push32
    elif (instruction_mnemonic == "PUSH32"):

        if(instruction_operand is None):
            raise ValueError("Parsed invalid instruction operand pairing in parsed_bytecode_line,") 
        
        int_value = int(instruction_operand)
        packed_bytes = struct.pack(">i", int_value)

        parsed_bytecode_line = bytes([opcode_byte]) + packed_bytes

    #Syscall
    elif (instruction_mnemonic == "SYSCALL"):

        if(instruction_operand is None):
            raise ValueError("Parsed invalid instruction operand pairing in parsed_bytecode_line,") 
        
        int_value = int(instruction_operand)
        packed_bytes = struct.pack(">B", int_value)

        parsed_bytecode_line = bytes([opcode_byte]) + packed_bytes
      
    return parsed_bytecode_line
    

def assemble_payload(bytecode):
    payload = b""
    TWO_BYTE_OPS = {"JMP", "JZ", "JNZ", "CALL"}

    if isinstance(bytecode, str):
        lines = bytecode.splitlines()
    else:
        lines = list(bytecode)

    label_offsets = resolve_labels(lines)
    current_offset = 0

    for line in lines:
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if cleaned_line.endswith(':'):
            continue

        line_list = cleaned_line.split(" ", 1)
        instruction_mnemonic = line_list[0]

        if instruction_mnemonic in TWO_BYTE_OPS:
            if len(line_list) != 2:
                raise ValueError(f"Instruction '{instruction_mnemonic}' requires an operand.")

            operand = line_list[1].strip()

            try:
                int(operand)
            except ValueError:
                if operand not in label_offsets:
                    raise ValueError(f"Unknown label '{operand}'.")

                relative_offset = label_offsets[operand] - current_offset
                cleaned_line = f"{instruction_mnemonic} {relative_offset}"

        instruction_bytes = parsed_bytecode_line(cleaned_line)
        payload += instruction_bytes
        current_offset += len(instruction_bytes)

        if len(payload) > 256:
            raise ValueError("Bytecode exceeds 256-byte limit.")

    return payload


