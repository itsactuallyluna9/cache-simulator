from memory import Memory
from cache import Cache, CacheLine
from address import apply_address_format
from instructions import rng_instructions
from replacements import swap_page, random_replacement,least_frequently_used, least_recently_used, first_in_first_out

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
        clock = 0
        for instruction, addr in rng_instructions(self._num_instruction, self._memory_size):
            tag_bits, line_bits, offset_bits = apply_address_format(addr, self._memory_size, self._page_size, self._cache_size, self._line_per_set)
            if instruction == "r":
                self._read_cache(tag_bits, line_bits, clock)
            elif instruction == "w":
                pass
            else:
                raise ValueError(f"Invalid instruction : {instruction}")
            clock += 1
        print(f"Hit number : {self._hit_counter}")
        print(f"Missed number: {self._num_instruction - self._hit_counter}")

    def _read_cache(self, tag_bits: str, line_bits: str, clock: int):
        if self._cache.check(tag_bits, line_bits, clock):
            self._hit_counter += 1
        else:
            if self._mapping == "direct":
                set_index=int(line_bits, 2)
                swap_page(self._cache, tag_bits, set_index=set_index, line_index=0, clock=clock)
            else:
                if self._mapping == "fully-associative":
                    set_index = 0
                elif self._mapping == "set-associative":
                    set_index = int(line_bits, 2)
                self._do_replacement(tag_bits, set_index, clock)

    def _do_replacement(self, tag_bits: str, set_index, clock:int):
        victim_set = self._cache.cache[set_index]
        for index, line in enumerate(victim_set):
            if line.invalid:
                swap_page(self._cache, tag_bits, set_index=set_index, line_index=index, clock=clock)
                return
        if self._replacement == "random":
            victim_index = random_replacement(victim_set)
        elif self._replacement == "LFU":
            victim_index = least_frequently_used(victim_set)
        elif self._replacement == "LRU":
            victim_index = least_recently_used(victim_set)
        elif self._replacement == "FIFO":
            victim_index = first_in_first_out(victim_set)
        else:
            raise ValueError(f"Unknown replacement policy : {self._replacement}")
        
        swap_page(self._cache, tag_bits, set_index=set_index, line_index=victim_index, clock=clock)
