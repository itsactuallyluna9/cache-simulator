from simulation import SimulationEngine
memory_size = 64
page_size = 4
cach_size = 16
num_instruction = 200
mapping = "direct"
replacement = None
simlate = SimulationEngine(memory_size, page_size, cach_size, num_instruction, mapping, replacement)
simlate.simulate()