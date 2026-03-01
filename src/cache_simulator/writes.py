from memory import Memory
from cache import CacheLine
def write_through(memory: Memory, cache_line: CacheLine, offset_bits: str, page_index: int):
    page = memory.memory[page_index]
    page[offset_bits] = page.get(offset_bits, 0) + 1
    cache_line.written_offsets[offset_bits] = cache_line.written_offsets.get(offset_bits, 0) + 1

def write_back(cache_line: CacheLine, offset_bits: str):
    cache_line.written_offsets[offset_bits] = cache_line.written_offsets.get(offset_bits, 0) + 1
    cache_line.dirty = True

def flush_line(memory: Memory, cache_line: CacheLine, page_index: int):
    if not cache_line.dirty:
        return
    page = memory.memory[page_index]
    for offset, count in cache_line.written_offsets.items():
        page[offset] = page.get(offset, 0) + count
    cache_line.dirty = False
    cache_line.written_offsets.clear()
