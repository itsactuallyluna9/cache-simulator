import random

def rng_instructions(amount: int, memory_size: int):
    memory_width = memory_size.bit_length() - 1
    max_address = pow(2, memory_width)-1
    for _ in range(amount):
        yield random.choice(("r")), hex(random.randint(0, max_address))

def instructions_from_trace(file: str):
    with open(file) as f:
        for line in f:
            yield line.split(",")