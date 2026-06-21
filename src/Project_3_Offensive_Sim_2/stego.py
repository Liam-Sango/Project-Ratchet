import hashlib
import hmac
import PIL.Image
import numpy
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

def generate_positions(image_shape: tuple, k_extract: bytes, num_positions: int) -> list[tuple]:
    height, width, channels = image_shape
    total_positions = height * width * channels

    if num_positions > total_positions:
        raise ValueError(
            f"Requested {num_positions} positions but image only has {total_positions}."
        )

    seed_bytes = hashlib.sha256(k_extract).digest()

    used = set()
    positions = []
    counter = 0

    while len(positions) < num_positions:
        counter_bytes = counter.to_bytes(8, "big")
        index_bytes = hmac.new(seed_bytes, counter_bytes, hashlib.sha256).digest()
        index = int.from_bytes(index_bytes, "big") % total_positions
        counter += 1

        if index in used:
            continue
        used.add(index)

        n = index
        channel = n % 3
        n = n // 3
        x = n % width
        y = n // width
        positions.append((x, y, channel))

    return positions

def embed(cover_image_path: str, payload: bytes, k_extract: bytes) -> PIL.Image:
    image = PIL.Image.open(cover_image_path).convert("RGB")
    pixels = numpy.array(image, dtype=numpy.uint8)

    bits = bytes_to_bits(payload)
    positions = generate_positions(pixels.shape, k_extract, len(bits))

    for bit, (x, y, channel) in zip(bits, positions):
        pixels[y, x, channel] = (pixels[y, x, channel] & 0xFE) | bit

    return PIL.Image.fromarray(pixels)

def extract(stego_image_path: str, k_extract: bytes, payload_length: int) -> bytes:
    image = PIL.Image.open(stego_image_path).convert("RGB")
    pixels = numpy.array(image, dtype=numpy.uint8)

    num_bits = payload_length * 8
    positions = generate_positions(pixels.shape, k_extract, num_bits)

    bits = []
    for (x, y, channel) in positions:
        bits.append(int(pixels[y, x, channel] & 1))

    return bits_to_bytes(bits)
