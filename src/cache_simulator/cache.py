from dataclasses import dataclass
from address import apply_address_format

@dataclass
class CacheLine:
    tag: str = ""
    dirty: bool = False # we should update memory
    invalid: bool = True
    access_counter: int = 0 # update when hit
    used_timestamp: int = 0 # update when hit and swapped
    swapped_timestamp: int = 0 # update when swapped

class Cache:
    cache: list[list[CacheLine]]

    def __init__(self, cache_size: int, page_size: int, num_set:int, lines_per_set:int):
        self.cache = []
        self.page_size = page_size
        for ith_set in range(num_set):
            line_set = []
            for ith_line in range(lines_per_set):
                line_set.append(CacheLine())
            self.cache.append(line_set)

    def check(self, tag_bits: str, set_bits: str, clock: int)->bool:
        if set_bits == "": # fully-associative
            for set in self.cache:
                for line in set:
                    if line.tag == tag_bits and not line.invalid:
                        line.access_counter += 1
                        line.used_timestamp = clock
                        return True
            return False
        else:
            set_index = int(set_bits, 2)
            set = self.cache[set_index]
            for line in set:
                if line.tag == tag_bits and not line.invalid:
                    line.access_counter += 1
                    line.used_timestamp = clock
                    return True
            return False     