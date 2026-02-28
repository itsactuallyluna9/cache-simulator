import random
from typing import Optional
from cache import CacheLine, Cache
from memory import Memory

def random_replacement(cache_set: list[CacheLine]) -> CacheLine:
    return random.choice(cache_set)

def least_recently_used(cache_set: list[CacheLine]) -> CacheLine:
    least_used = cache_set[0]
    for line in cache_set[1:]:
        if line.used_timestamp < least_used.used_timestamp:
            least_used = line
    return least_used

def least_frequently_used(cache_set: list[CacheLine]) -> CacheLine:
    least_used = cache_set[0]
    for line in cache_set[1:]:
        if line.access_counter < least_used.access_counter:
            least_used = line
    return least_used

def first_in_first_out(cache_set: list[CacheLine]) -> CacheLine:
    first = cache_set[0]
    for line in cache_set[1:]:
        if line.swapped_timestamp < first.swapped_timestamp:
            first = line
    return first

def replace_unused(cache_set: list[CacheLine]) -> Optional[CacheLine]:
    for line in cache_set:
        if line.invalid:
            return line
    return None

def swap_page(cache: Cache,tag_bits: str,set_bits: str=None, line_index:int=0):
    set_index = 0 if set_bits is None else int(set_bits, 2) 
    line = cache.cache[set_index][line_index]
    line.tag = tag_bits
    line.invalid = False

