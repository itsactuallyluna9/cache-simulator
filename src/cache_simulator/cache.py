from dataclasses import dataclass
from .address import apply_address_format

@dataclass
class CacheLine:
    tag: int = 0
    dirty: bool = False # we should update memory
    invalid: bool = True

    access_counter: int = 0
    used_timestamp: int = 0
    swapped_timestamp: int = 0

class Cache:
    cache: list[list[CacheLine]]

    def __init__(self, cache_size: int, page_size: int, mapping: str, num_lines: int = 1):
        self.mapping = mapping
        self.cache = []
        self.page_size = page_size
        for ith_set in range(cache_size // page_size):
            line_set = []
            for ith_line in range(num_lines):
                line_set.append(CacheLine())
            self.cache.append(line_set)

    def check(self, address: int) -> bool:
        tag, set_num, _offset = apply_address_format(address)
        for line in self.cache[set_num]:
            if line.tag == tag and not line.invalid:
                return True
        return False
