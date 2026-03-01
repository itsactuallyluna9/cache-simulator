from simulation import SimulationEngine
memory_size = 64
page_size = 4
cach_size = 16
num_instruction = 200
mapping = "set-associative"
replacement = "random"
simlate = SimulationEngine(memory_size, page_size, cach_size, num_instruction, mapping, replacement, line_per_set=2)
simlate.simulate()
