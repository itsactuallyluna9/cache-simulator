class Memory:
    def __init__(self, memory_size: int, page_size: int):
        self.memory_size = memory_size
        self.pages = memory_size // page_size
        self.page_size = page_size
        self.memory = [{} for _ in range(self.pages)]