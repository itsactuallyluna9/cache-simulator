import random


def rng_instructions(amount: int, memory_size: int):
    memory_width = memory_size.bit_length() - 1
    max_address = pow(2, memory_width) - 1
    for _ in range(amount):
        yield random.choice(("r", "w")), hex(random.randint(0, max_address))


def instructions_from_trace(file: str):
    with open(file) as f:
        for line in f:
            yield line.split(",")


def generate_random_pattern(
    num_reads: int,
    num_writes: int,
    memory_size: int,
    seed=None,
    temporal_locality=0.0,
    spatial_locality=0.0,
    stride_size=1,
    working_set_size=1.0,
    working_set_focus=0.8,
    hotspot_count=0,
    hotspot_intensity=0.5,
    history_size=100,
) -> list[tuple[str, str]]:
    """
    Generate random interleaved read/write pattern with locality of reference.

    Args:
        num_reads: Number of read operations
        num_writes: Number of write operations
        memory_size: Size of memory in bytes
        seed: Optional RNG seed for reproducibility
        temporal_locality: 0.0-1.0, probability of reusing recent addresses
        spatial_locality: 0.0-1.0, probability of accessing nearby addresses
        stride_size: Stride in bytes for spatial locality
        working_set_size: 0.0-1.0, fraction of memory that forms working set
        working_set_focus: 0.5-1.0, probability of accessing within working set
        hotspot_count: Number of hot memory regions
        hotspot_intensity: 0.0-1.0, extra probability of accessing hotspots
        history_size: Number of recent addresses to remember for temporal locality

    Returns:
        List of (address_hex, method) tuples
        e.g., [("0x1A2B", "r"), ("0x5F3C", "w"), ...]
    """
    if seed is not None:
        random.seed(seed)

    # calculate max address based on actual memory size
    max_address = memory_size - 1

    # setup working set bounds
    working_set_range = int(memory_size * working_set_size)
    working_set_start = random.randint(0, max(0, memory_size - working_set_range))
    working_set_end = min(working_set_start + working_set_range, max_address)

    # setup hotspots
    hotspots = []
    if hotspot_count > 0:
        hotspot_size = max(
            1, memory_size // (hotspot_count * 10)
        )  # each hotspot is ~10% of its fair share
        for _ in range(hotspot_count):
            hotspot_start = random.randint(0, max(0, max_address - hotspot_size))
            hotspots.append((hotspot_start, hotspot_start + hotspot_size))

    # address history for temporal locality
    address_history = []
    last_address = None

    def generate_address():
        nonlocal last_address

        # check temporal locality - reuse recent address
        if (
            temporal_locality > 0
            and address_history
            and random.random() < temporal_locality
        ):
            addr = random.choice(address_history)
            last_address = addr
            return addr

        # check spatial locality - generate near last address
        if (
            spatial_locality > 0
            and last_address is not None
            and random.random() < spatial_locality
        ):
            # generate address within stride distance
            offset = random.randint(-stride_size * 4, stride_size * 4)
            addr = max(0, min(max_address, last_address + offset))
            last_address = addr

            # add to history
            address_history.append(addr)
            if len(address_history) > history_size:
                address_history.pop(0)

            return addr

        # check hotspot targeting
        if hotspots and random.random() < hotspot_intensity:
            hotspot_start, hotspot_end = random.choice(hotspots)
            addr = random.randint(hotspot_start, hotspot_end)
            last_address = addr

            # add to history
            address_history.append(addr)
            if len(address_history) > history_size:
                address_history.pop(0)

            return addr

        # check working set focus
        if random.random() < working_set_focus:
            addr = random.randint(working_set_start, working_set_end)
        else:
            addr = random.randint(0, max_address)

        last_address = addr

        # add to history
        address_history.append(addr)
        if len(address_history) > history_size:
            address_history.pop(0)

        return addr

    # generate reads and writes
    pattern = []
    for _ in range(num_reads):
        addr = hex(generate_address())
        pattern.append((addr, "r"))

    for _ in range(num_writes):
        addr = hex(generate_address())
        pattern.append((addr, "w"))

    # shuffle!!
    random.shuffle(pattern)

    return pattern


def load_csv_pattern(file_path: str) -> list[tuple[str, str]]:
    """
    Load access pattern from CSV file.

    CSV format: timestamp, address, method
    (timestamp is currently ignored)

    Args:
        file_path: Path to CSV file

    Returns:
        List of (address_hex, method) tuples
    """
    import csv

    pattern = []
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                # parse address - handle both hex and decimal
                address_str = row[1].strip()
                if address_str.startswith("0x") or address_str.startswith("0X"):
                    address = address_str  # already hex
                else:
                    address = hex(int(address_str))  # convert decimal to hex

                method = row[2].strip().lower()

                if method in ["r", "w"]:
                    pattern.append((address, method))

    return pattern
