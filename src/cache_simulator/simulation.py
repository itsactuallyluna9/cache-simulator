from memory import Memory
from cache import Cache, CacheLine
from address import apply_address_format
from instructions import rng_instructions
from replacements import swap_page, random_replacement, replace_unused, least_frequently_used

class SimulationEngine:
    mapping_strategy = ["direct", "fully-associative", "set-associative"]
    replacement_algorithum = ["FIFO", "LRU", "LFU", "random"]

    def __init__(self, memory_size: int, page_size: int, cache_size: int, num_instruction: int, mapping: str, replacement: str= None, line_per_set: int=1):
        if mapping == "direct":
            self._num_set = cache_size // page_size
            self._line_per_set = 1
        elif mapping == "fully-associative":
            self._num_set = 1
            self._line_per_set = cache_size // page_size
        elif mapping == "set-associative":
            self._num_set = (cache_size // page_size) // line_per_set
            self._line_per_set = line_per_set
        else:
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
        self._cache = Cache(self._cache_size, self._page_size, self._num_set, self._line_per_set)
        self._hit_counter = 0

    def simulate(self):
        for instruction, addr in rng_instructions(self._num_instruction, self._memory_size):
            tag_bits, line_bits, offset_bits = apply_address_format(addr, self._memory_size, self._page_size, self._cache_size, self._line_per_set)
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
            self._hit_counter += 1
        else:
            if self._mapping == "direct":
                swap_page(self._cache, tag_bits, line_bits)
            else:
                if self._mapping == "fully-associative":
                    victim_set = self._cache.cache[0]
                elif self._mapping == "set-associative":
                    set_index = int(line_bits, 2)
                    victim_set = self._cache.cache[set_index]
                self._do_replacement(victim_set, tag_bits)

    def _do_replacement(self, victim_set: list[CacheLine], tag_bits: str):
        if self._replacement == "random":
            victim, victim_index = random_replacement(victim_set)
        elif self._replacement == "LFU":
            victim, victim_index = least_frequently_used(victim_set)
        elif self._replacement == "LRU":
            pass
        elif self._replacement == "FIFO":
            pass
        else:
            raise ValueError(f"Unknown replacement policy : {self._replacement}")
        
        if victim.tag == "":
            replace_unused(self._cache.cache[0], tag_bits)
        else:
            swap_page(self._cache, tag_bits, set_bits=None, line_index=victim_index)

        
    
    def _update_timestamp(self):
        pass