from memory import Memory
from cache import Cache
from address import apply_address_format
from instructions import rng_instructions
from replacements import swap_page, random_replacement, replace_unused

class SimulationEngine:
    mapping_strategy = ["direct", "fully-associtive", "set-associative"]
    replacement_algorithum = ["FIFO", "LRU", "LFU", "random"]

    def __init__(self, memory_size: int, page_size: int, cache_size: int, num_instruction: int, mapping: str, replacement: str= None):
        if mapping not in self.mapping_strategy:
            raise AttributeError(f"Invalid mapping strategy is given : {mapping}")
        if mapping == "direct" and replacement is not None:
            raise AttributeError("Replacement algorithm cannot be used with direct mapping")
        if replacement is not None and replacement not in self.replacement_algorithum:
            raise AttributeError(f"Invalid replacement algorithm is given: {replacement}")
        self._memory_size = memory_size
        self._page_size = page_size
        self._cache_size = cache_size
        self._mapping = mapping
        self._replacement = replacement
        self._num_instruction = num_instruction
        self._memory = Memory(self._memory_size, self._page_size)
        self._cache = Cache(self._cache_size, self._page_size)
        self._hit_counter = 0

    def simulate(self):
        for instruction, addr in rng_instructions(self._num_instruction, self._memory_size):
            tag_bits, line_bits, offset_bits = apply_address_format(addr, self._memory_size, self._page_size, self._cache_size)
            if instruction == "r":
                self._read_cache(tag_bits, line_bits)
            elif instruction == "w":
                pass
            else:
                raise ValueError(f"Invalid instruction : {instruction}")
            self._update_timestamp()
        print(f"Hit number : {self._hit_counter}")
        print(f"Missed number: {self._num_instruction - self._hit_counter}")

    def _read_cache(self, tag_bits: str, line_bits: str):
        if self._cache.check(tag_bits, line_bits):
            self._update_access_counter()
            self._hit_counter += 1
        else:
            if self._mapping == "direct":
                swap_page(self._cache, tag_bits, line_bits)
            else:
                self._do_replacement(tag_bits)

    def _do_replacement(self, tag_bits: str):
        victim = random_replacement(self._cache.cache[0])
        if victim is None:
            replace_unused(self._cache, tag_bits)
        else:
            swap_page(self._cache, tag_bits)

    def _update_access_counter(self):
        pass
    
    def _update_timestamp(self):
        pass