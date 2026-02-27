def get_address_format(memory_size: int, page_size: int, cache_size: int):
    address_length = memory_size.bit_length() - 1
    offset_length = page_size.bit_length() - 1
    line_number_length = cache_size / offset_length
    page_num = address_length - offset_length
    tag = address_length - line_number_length
    
    return address_length, offset_length, line_number_length, page_num, tag

def apply_address_format(address: int, memory_size: int, page_size: int, cache_size: int):
    address_length, offset_length, line_number_length, page_num, tag = get_address_format(memory_size, page_size, cache_size)

    

    return address_tag, set_number, offset

    
