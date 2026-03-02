# Cache Simulator
*CSC311 Assignment 3*

## Running
* Install `uv`
* Run `uv run cache-simulator`

Altertanively, any way you can install the package and then run the command `cache-simulator` is good. Instructions for `uv` are provided since the author of this README uses `uv`.

## Application Usage

### Setting Up the Simulation

1. First, on the left hand side, configure attributes about the memory, including the memory size, the page size, and what policies the memory uses, among other.
2. Next, still on the left hand side, either load a CSV file *or* randomly generate a series of instructions.
  * The CSV file is in the format `timestamp,address,method`. `timestamp` is currently unused. `address` is either a hexdecimal or decimal integer that indicates where the CPU is reading/writing to. `method` is either `r` or `w`, indicating `read` and `write` respectively.
  * For randomization, there is some advanced options under "Locality Settings", if desired. Remember to generate the list of addresses by hitting "Generate Access Pattern".
    * The checkbox underneath the button will write out the generated addresses to disk during the simulation.

### Running the Simulation
* In the Simulator Controls section, you can run the entire simulation by hitting "Run Simulation (Full)". This will run through the entire simulation, and then display the results on the right.
* You can also step through the simulation one memory access at a time by hitting "Step", with results appearing on the right after each step.
* The Export Results button will be enabled once there is data, and will output a CSV file with all of the generated data. This does not include a step-by-step log, which can be output via the checkbox in the randomization settings.
* You can reset the simulator by hitting "Reset". Please note that running the full simulation automatically resets the simulator, so in most cases it is not needed.

### Viewing Results

The entire right hand side is results. This includes:
* Current Address details
* The Cache State - showing which lines in the cache are empty, valid, or dirty at a glance. Individual sets can be inspected, showing its line number, the tag currently associated with the line, if the line contains data that needs to be written, the amount of accesses since the line was loaded, and the age of the line (in cycles).
* Various statistics about the simulator, including a breakdown of cache performace (detailing hits and misses), and memory operations. Please note: the average access time assumes that each cache access takes 1.0 cycles, and each memory cycle takes 100.0 cycles. This is not configurable.
* Execution trace - showing the last 20 accesses the CPU performed, and the cache's response to it.

## Credits
* Luna - GUI, Readme, Some Logic
* Chihiro - Most Logic, Write Support
