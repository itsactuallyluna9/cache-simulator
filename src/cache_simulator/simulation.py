from memory import Memory
from cache import Cache
from address import apply_address_format
from instructions import rng_instructions
from replacements import swap_page

def simulate():
    page_size = 4
    memory_size = 64
    cache_size = 16
    mapping = "direct"

    memory = Memory(memory_size, page_size)
    cache = Cache(cache_size, page_size, mapping)
  

    hit_counter = 0
    num_instruction = 200
    # Direct mapping
    for instruction, addr in rng_instructions(num_instruction, memory_size):
        tag_bits, line_bits, offset_bits = apply_address_format(addr, memory_size, page_size, cache_size)
        if instruction == "r":
            if cache.check(tag_bits, line_bits):
                hit_counter+=1
            else:
                swap_page(cache, tag_bits, line_bits)
        elif instruction == "w":
            pass
        else:
            raise ValueError(f"Invalid instruction : {instruction}")

    print(f"Hit number: {hit_counter}")
    print(f"Missed number: {num_instruction-hit_counter}")

        
                
        

if __name__ == "__main__":
    simulate()

