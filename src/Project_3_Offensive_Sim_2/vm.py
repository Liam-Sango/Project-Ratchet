class VirtualMachine:
       
       def __init__(self, bytecode, memory_size=4096):
           
           if not isinstance(memory_size, int):
               raise ValueError("Memory size must be an integer")
           
           if not isinstance(bytecode, (bytes, bytearray)):
               raise ValueError("Bytecode must be bytes or bytearray")

           if len(bytecode) > 256:
             raise ValueError("Bytecode must be smaller than 256 bytes")
    
           if memory_size <= 0:
             raise ValueError("Memory size must be above 0")
          
           self.bytecode = bytearray(bytecode)
           self.data_stack = []
           self.return_stack = []
           self.memory = bytearray(memory_size)
           self.instruction_pointer = 0
           self.is_halted = False




def execute_bytecode(bytecode: bytearray | bytes, memory_size : int = 4096):

    vm = VirtualMachine(bytecode, memory_size)

    return vm
    
