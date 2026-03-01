from memory import Memory
from cache import CacheLine
def write_through(memory: Memory, cache_line: CacheLine, offset_bits: str):
    memory.memory.append(offset_bits)
    cache_line.written_offsets.append(offset_bits)

def write_back(cache_line: CacheLine, offset_bits: str):
    cache_line.written_offsets.append(offset_bits)
    cache_line.dirty = True

def flush_line(memory: Memory, cach):
    pass
