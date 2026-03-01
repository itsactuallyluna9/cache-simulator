import random
from typing import Optional
from cache import CacheLine, Cache
from memory import Memory

def random_replacement(cache_set: list[CacheLine]) -> int:
    victim_index = random.randrange(len(cache_set))
    return victim_index

def least_recently_used(cache_set: list[CacheLine]) -> int:
    least_used = cache_set[0]
    victim_index = 0
    for index, line in enumerate(cache_set):
        if line.used_timestamp < least_used.used_timestamp:
            least_used = line
            victim_index = index
    return victim_index

def least_frequently_used(cache_set: list[CacheLine]) -> int:
    least_used = cache_set[0]
    victim_index = 0
    for index, line in enumerate(cache_set):
        if line.access_counter < least_used.access_counter:
            least_used = line
            victim_index = index
    return victim_index

def first_in_first_out(cache_set: list[CacheLine]) -> int:
    first = cache_set[0]
    victim_index = 0
    for index, line in enumerate(cache_set):
        if line.swapped_timestamp < first.swapped_timestamp:
            first = line
            victim_index = index
    return victim_index
            

def swap_page(cache: Cache, tag_bits: str, set_index: int, line_index:int, clock: int):
    line = cache.cache[set_index][line_index] # line_index=0 when direct
    line.tag = tag_bits
    line.invalid = False
    line.swapped_timestamp = clock
    line.used_timestamp = clock
    return line