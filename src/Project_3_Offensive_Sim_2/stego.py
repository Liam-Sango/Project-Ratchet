import PIL.Image

def bytes_to_bits(data: bytes) -> list[int]:
    bit_list = []

    for x in range(len(data)):
        byte_value = data[x]

        for position in range(7, -1, -1):
            bit = (byte_value >> position) & 1
            bit_list.append(bit)

    return bit_list

def bits_to_bytes(bits: list[int]) -> bytes:
    byte_values = []

    for x in range(len(bits) // 8):
         byte_chunk = 0

         for i in range(8):
            byte_chunk = (byte_chunk << 1) | bits[(x * 8) + i]

         byte_values.append(byte_chunk)

    finished_bytes = bytes(byte_values)
    return finished_bytes

def generate_positions(image_shape, k_extract: bytes, num_positions: int) -> list[tuple]:
    print ("TEMP")

def embed(cover_image_path: str, payload: bytes, k_extract: bytes) -> PIL.Image:
    print ("TEMP")

def extract(stego_image_path: str, k_extract: bytes, payload_length: int) -> bytes:
    print("TEMP")