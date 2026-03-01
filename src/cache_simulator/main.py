#%%
from simulation import SimulationEngine
memory_size = 64
page_size = 4
cach_size = 16
num_instruction = 200
mapping = "fully_associative"
replacement = "FIFO"
write_policy = "write_through"
simlate = SimulationEngine(memory_size, page_size, cach_size, num_instruction, mapping, write_policy=write_policy, replacement=replacement, line_per_set=2)
simlate.simulate()
# %%
