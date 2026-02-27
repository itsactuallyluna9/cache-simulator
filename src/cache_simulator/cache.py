from dataclasses import dataclass

@dataclass
class CacheLine:
    tag: int = 0
    dirty: bool = True # we should update memory
    invalid: bool = True

    access_counter = 0
    used_timestamp = 0
    swapped_timestamp = 0

class Cache:
    cache: list[list[CacheLine]]

    def __init__(self, cache_size: int, page_size: int, num_lines: int = 1):
        self.cache = []
        for ith_set in range(cache_size // page_size):
            line_set = []
            for ith_line in range(num_lines):
                line_set.append(CacheLine())
            self.cache.append(line_set)

