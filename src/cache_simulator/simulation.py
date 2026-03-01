from memory import Memory
from cache import Cache, CacheLine
from address import apply_address_format
from instructions import rng_instructions
from writes import write_through, write_back
from replacements import swap_page, random_replacement,least_frequently_used, least_recently_used, first_in_first_out

class SimulationEngine:
    mapping_strategy = ["direct", "fully_associative", "set_associative"]
    replacement_algorithum = ["FIFO", "LRU", "LFU", "random"]
    write_policy = ["write_back", "write_through"]

    def __init__(self, memory_size: int, page_size: int, cache_size: int, num_instruction: int, mapping: str, write_policy : str,replacement: str= None, line_per_set: int=1):
        if mapping == "direct":
            self._num_set = cache_size // page_size
            self._line_per_set = 1
        elif mapping == "fully_associative":
            self._num_set = 1
            self._line_per_set = cache_size // page_size
        elif mapping == "set_associative":
            self._num_set = (cache_size // page_size) // line_per_set
            self._line_per_set = line_per_set
        else:
            raise AttributeError(f"Invalid mapping strategy is given : {mapping}")
        
        if mapping == "direct" and replacement is not None:
            raise AttributeError("Replacement algorithm cannot be used with direct mapping")
        if replacement is not None and replacement not in self.replacement_algorithum:
            raise AttributeError(f"Invalid replacement algorithm is given: {replacement}")
        
        if write_policy not in self.write_policy:
            raise ArithmeticError(f"Invalid write policy is given : {write_policy}")
        self._memory_size = memory_size
        self._page_size = page_size
        self._cache_size = cache_size
        self._mapping = mapping
        self._replacement = replacement
        self._write_policy = write_policy
        self._num_instruction = num_instruction
        self._memory = Memory(self._memory_size, self._page_size)
        self._cache = Cache(self._cache_size, self._page_size, self._num_set, self._line_per_set)
        self._read_hit = 0
        self._read_miss = 0
        self._write_hit = 0
        self._write_miss = 0

    def simulate(self):
        clock = 0
        for instruction, addr in rng_instructions(self._num_instruction, self._memory_size):
            tag_bits, set_bits, offset_bits = apply_address_format(addr, self._memory_size, self._page_size, self._cache_size, self._line_per_set)
            hit = self._cache.check(tag_bits, set_bits, clock)
            if instruction == "r":
                if hit:
                    self._read_hit += 1
                else:
                    self._read_miss += 1
                    self._handle_miss(tag_bits, set_bits, clock)
            elif instruction == "w":
                if hit:
                    self._write_hit += 1
                else:
                    self._write_miss += 1
                    line = self._handle_miss(tag_bits, set_bits, clock)
                self._write_cache(line, offset_bits)
            else:
                raise ValueError(f"Invalid instruction: {instruction}")
            clock += 1
        print(f"Read hits: {self._read_hit}, misses: {self._read_miss}")
        print(f"Write hits: {self._write_hit}, misses: {self._write_miss}")

    def _handle_miss(self, tag_bits: str, set_bits: str, clock: int):
        if self._mapping == "direct":
            set_index=int(set_bits, 2)
            line = swap_page(self._cache, tag_bits, set_index=set_index, line_index=0, clock=clock)
        else:
            if self._mapping == "fully_associative":
                set_index = 0
            elif self._mapping == "set_associative":
                set_index = int(set_bits, 2)
            line = self._do_replacement(tag_bits, set_index, clock)
        return line
    
    def _do_replacement(self, tag_bits: str, set_index, clock:int):
        victim_set = self._cache.cache[set_index]
        for index, line in enumerate(victim_set):
            if line.invalid:
                line = swap_page(self._cache, tag_bits, set_index=set_index, line_index=index, clock=clock)
                return line
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
        
        line = swap_page(self._cache, tag_bits, set_index=set_index, line_index=victim_index, clock=clock)

        return line

    def _write_cache(self, line: CacheLine, offset_bits: str):
        if self._write_policy == "write_through":
            write_through(self._memory, line, offset_bits)
        elif self._write_policy == "write_back":
            write_back(self, line, offset_bits)
