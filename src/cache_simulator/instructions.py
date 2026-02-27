import random

def rng_instructions(amount: int, max_address: int):
    for _ in range(amount):
        yield random.choice(("r", "w")), random.randint(max_address)

def instructions_from_trace(file: str):
    with open(file) as f:
        for line in f:
            yield line.split(",")
