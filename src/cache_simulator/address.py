def get_address_format(memory_size: int, page_size: int, cache_size: int, line_per_set: int = 1):
    address_legnth = memory_size.bit_length() - 1
    offset_length = page_size.bit_length() - 1
    total_lines = cache_size // page_size
    if total_lines == line_per_set: # fully-associative mapping
        index_length = 0
        tag = address_legnth - offset_length
        return address_legnth, tag, index_length, offset_length
    elif line_per_set == 1: # direct mapping
        page_num = total_lines.bit_length() - 1
        tag = address_legnth - (page_num + offset_length)
        return address_legnth, tag, page_num, offset_length
    else: # set-associative mapping
        set_num = (total_lines // line_per_set).bit_length() - 1
        tag = address_legnth - (set_num + offset_length)
        return address_legnth, tag, set_num, offset_length


def apply_address_format(address: str, memory_size: int, page_size: int, cache_size: int):
    address_length, tag, page_num, offset_length = get_address_format(memory_size, page_size, cache_size)
    # Assume address is given in hex (0xbbbb)
    address_bin = bin(int(address[2:], 16))[2:].zfill(address_length)
 
    tag_bits = address_bin[0:tag]
    line_bits = address_bin[tag:tag + page_num]
    offset_bits = address_bin[tag + page_num:]

    return tag_bits, line_bits, offset_bits


