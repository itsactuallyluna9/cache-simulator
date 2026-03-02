import csv
import dearpygui.dearpygui as dpg


class CacheSimulatorGUI:
    def __init__(self):
        # simulation components
        self.engine = None
        self.access_pattern = []  # list of (address_hex, method) tuples

        # execution state
        self.current_step = 0  # index into access_pattern
        self.is_running = False  # full simulation in progress

        # trace management
        self.execution_trace = []  # keep last 1000
        self.max_trace_entries = 1000
        self.trace_log_file = None  # for continuous writing

        # cache visualization
        self.selected_set = 0  # currently selected set for detailed view
        self.cache_cell_size = 30  # size of each cell in heat map

        # GUI widgets
        self.config_widgets = {}
        self.status_widgets = {}

        # DearPyGUI setup
        dpg.create_context()
        dpg.create_viewport(title="Cache Simulator", width=1600, height=900)
        dpg.setup_dearpygui()

    def _convert_to_bytes(self, value: int, unit: str) -> int:
        """Convert size with unit to bytes."""
        multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        return value * multipliers[unit]

    def _update_n_ways_max(self):
        """Update the available N-ways options based on cache and page size."""
        try:
            # check if all required widgets exist
            if "n_ways" not in self.config_widgets:
                return
            if not dpg.does_item_exist(self.config_widgets["n_ways"]):
                return

            cache_size = self._convert_to_bytes(
                dpg.get_value(self.config_widgets["cache_size"]),
                dpg.get_value(self.config_widgets["cache_unit"]),
            )
            page_size = self._convert_to_bytes(
                dpg.get_value(self.config_widgets["page_size"]),
                dpg.get_value(self.config_widgets["page_unit"]),
            )

            # calculate max possible ways (total cache lines)
            max_ways = cache_size // page_size

            # generate power-of-2 values up to max_ways
            available_ways = []
            power = 0
            while 2**power <= max_ways:
                available_ways.append(str(2**power))
                power += 1

            # update combo box items
            current_value = dpg.get_value(self.config_widgets["n_ways"])
            dpg.configure_item(self.config_widgets["n_ways"], items=available_ways)

            # if current value is no longer valid, set to largest available
            if current_value not in available_ways:
                dpg.set_value(
                    self.config_widgets["n_ways"],
                    available_ways[-1] if available_ways else "1",
                )
        except Exception as _:
            pass

    def _get_simulation_config(self) -> dict:
        """Extract configuration from GUI widgets for SimulationEngine."""
        ram_size = self._convert_to_bytes(
            dpg.get_value(self.config_widgets["ram_size"]),
            dpg.get_value(self.config_widgets["ram_unit"]),
        )

        page_size = self._convert_to_bytes(
            dpg.get_value(self.config_widgets["page_size"]),
            dpg.get_value(self.config_widgets["page_unit"]),
        )

        cache_size = self._convert_to_bytes(
            dpg.get_value(self.config_widgets["cache_size"]),
            dpg.get_value(self.config_widgets["cache_unit"]),
        )

        # map gui strings to engine values
        mapping_map = {
            "Direct Mapping": "direct",
            "N-Way Set Associative": "set_associative",
            "Fully Associative": "fully_associative",
        }

        replacement_map = {
            "Random Replacement": "random",
            "Least Recently Used (LRU)": "LRU",
            "Least Frequently Used (LFU)": "LFU",
            "First In First Out (FIFO)": "FIFO",
        }

        write_map = {"Write-Through": "write_through", "Write-Back": "write_back"}

        mapping_str = dpg.get_value(self.config_widgets["mapping_policy"])
        mapping = mapping_map[mapping_str]

        replacement_str = dpg.get_value(self.config_widgets["replacement_policy"])
        # don't pass replacement for direct mapping - breaks for reasons i dont have time to find
        replacement = (
            None if mapping == "direct" else replacement_map.get(replacement_str)
        )

        write_str = dpg.get_value(self.config_widgets["write_policy"])
        write_policy = write_map[write_str]

        n_ways = int(dpg.get_value(self.config_widgets["n_ways"]))

        return {
            "memory_size": ram_size,
            "page_size": page_size,
            "cache_size": cache_size,
            "mapping": mapping,
            "write_policy": write_policy,
            "replacement": replacement,
            "line_per_set": n_ways if mapping == "set_associative" else 1,
        }

    def _add_trace_entry(self, trace_dict: dict):
        """Add trace entry with memory limit."""
        # add to in-memory trace (with limit)
        self.execution_trace.append(trace_dict)
        if len(self.execution_trace) > self.max_trace_entries:
            self.execution_trace.pop(0) # remove oldest

        # write to file if enabled
        if self.trace_log_file:
            self.trace_writer.writerow(
                [
                    self.current_step,
                    trace_dict.get("clock", 0),
                    trace_dict["address"],
                    trace_dict["tag_bits"],
                    int(trace_dict["set_bits"], 2) if trace_dict["set_bits"] else 0,
                    trace_dict["offset_bits"],
                    trace_dict["method"].upper(),
                    "HIT" if trace_dict["hit"] else "MISS",
                    trace_dict["reason"],
                ]
            )

    def _calculate_update_interval(self, total_steps: int) -> int:
        """Calculate how often to update progress bar."""
        # i want my program to be *responsive*, damnit!
        if total_steps < 100:
            return 1
        elif total_steps < 10000:
            return max(1, total_steps // 100)  # Every 1%
        else:
            return 100  # Every 100 steps

    def generate_access_pattern(self):
        """Generate random access pattern from GUI configuration."""
        from .instructions import generate_random_pattern

        try:
            num_reads = dpg.get_value(self.config_widgets["num_reads"])
            num_writes = dpg.get_value(self.config_widgets["num_writes"])
            seed = dpg.get_value(self.config_widgets["rng_seed"])

            # get memory size from RAM config
            ram_size = self._convert_to_bytes(
                dpg.get_value(self.config_widgets["ram_size"]),
                dpg.get_value(self.config_widgets["ram_unit"]),
            )

            # get locality parameters (convert percentages to 0.0-1.0)
            temporal_locality = (
                dpg.get_value(self.config_widgets["temporal_locality"]) / 100.0
            )
            spatial_locality = (
                dpg.get_value(self.config_widgets["spatial_locality"]) / 100.0
            )
            stride_size = dpg.get_value(self.config_widgets["stride_size"])
            working_set_size = (
                dpg.get_value(self.config_widgets["working_set_size"]) / 100.0
            )
            working_set_focus = (
                dpg.get_value(self.config_widgets["working_set_focus"]) / 100.0
            )
            hotspot_count = dpg.get_value(self.config_widgets["hotspot_count"])
            hotspot_intensity = (
                dpg.get_value(self.config_widgets["hotspot_intensity"]) / 100.0
            )
            history_size = dpg.get_value(self.config_widgets["history_size"])

            # generate pattern
            self.access_pattern = generate_random_pattern(
                num_reads=num_reads,
                num_writes=num_writes,
                memory_size=ram_size,
                seed=seed,
                temporal_locality=temporal_locality,
                spatial_locality=spatial_locality,
                stride_size=stride_size,
                working_set_size=working_set_size,
                working_set_focus=working_set_focus,
                hotspot_count=hotspot_count,
                hotspot_intensity=hotspot_intensity,
                history_size=history_size,
            )

            # update status
            dpg.set_value(
                self.status_widgets["pattern_status"],
                f"Generated {len(self.access_pattern)} random accesses",
            )
            dpg.set_value(
                self.status_widgets["accesses_queued"],
                f"Accesses Queued: {len(self.access_pattern)}",
            )

            # enable simulation buttons
            dpg.configure_item(self.status_widgets["run_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=True)

        except Exception as e:
            dpg.set_value(
                self.status_widgets["pattern_status"],
                f"Error generating pattern: {str(e)}",
            )
            print(f"Pattern generation error: {e}")
            import traceback

            traceback.print_exc()

    def randomize_seed(self):
        import random

        new_seed = random.randint(0, 2**32 - 1) # might as well...
        dpg.set_value(self.config_widgets["rng_seed"], new_seed)

    def apply_locality_preset(self, preset_name):
        """Apply locality preset configurations."""
        # going to be honest, these are best guesses.
        # math checks out, at least in theory
        presets = {
            "none": {
                "temporal_locality": 0,
                "spatial_locality": 0,
                "stride_size": 1,
                "working_set_size": 100,
                "working_set_focus": 80,
                "hotspot_count": 0,
                "hotspot_intensity": 0,
                "history_size": 100,
            },
            "high_temporal": {
                "temporal_locality": 70,
                "spatial_locality": 10,
                "stride_size": 64,
                "working_set_size": 50,
                "working_set_focus": 90,
                "hotspot_count": 0,
                "hotspot_intensity": 0,
                "history_size": 500,
            },
            "high_spatial": {
                "temporal_locality": 10,
                "spatial_locality": 80,
                "stride_size": 64,
                "working_set_size": 100,
                "working_set_focus": 80,
                "hotspot_count": 0,
                "hotspot_intensity": 0,
                "history_size": 100,
            },
            "hotspot": {
                "temporal_locality": 30,
                "spatial_locality": 20,
                "stride_size": 64,
                "working_set_size": 100,
                "working_set_focus": 80,
                "hotspot_count": 5,
                "hotspot_intensity": 70,
                "history_size": 200,
            },
            "realistic": {
                "temporal_locality": 50,
                "spatial_locality": 40,
                "stride_size": 64,
                "working_set_size": 30,
                "working_set_focus": 85,
                "hotspot_count": 2,
                "hotspot_intensity": 40,
                "history_size": 250,
            },
        }

        if preset_name in presets:
            preset = presets[preset_name]
            for key, value in preset.items():
                if key in self.config_widgets:
                    dpg.set_value(self.config_widgets[key], value)

    def load_csv_callback(self, sender, app_data):
        """Callback for CSV file loading."""
        from .instructions import load_csv_pattern

        file_path = app_data["file_path_name"]

        try:
            self.access_pattern = load_csv_pattern(file_path)

            dpg.set_value(
                self.status_widgets["pattern_status"],
                f"Loaded {len(self.access_pattern)} accesses from CSV",
            )
            dpg.set_value(
                self.status_widgets["accesses_queued"],
                f"Accesses Queued: {len(self.access_pattern)}",
            )

            # enable simulation buttons
            dpg.configure_item(self.status_widgets["run_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=True)
        except Exception as e:
            dpg.set_value(
                self.status_widgets["pattern_status"], f"Error loading CSV: {str(e)}"
            )

    def run_simulation(self):
        """Run complete simulation with progress updates."""
        from .simulation import SimulationEngine

        if not self.access_pattern:
            dpg.set_value(
                self.status_widgets["sim_status"], "[X] No access pattern loaded"
            )
            return

        try:
            # create engine
            config = self._get_simulation_config()
            self.engine = SimulationEngine(**config)

            # reset state
            self.current_step = 0
            self.execution_trace = []
            self.is_running = True

            # open trace file if checkbox enabled
            write_full_trace = self.config_widgets.get("write_full_trace")
            if write_full_trace and dpg.get_value(write_full_trace):
                from datetime import datetime

                filename = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                self.trace_log_file = open(filename, "w", newline="")
                self.trace_writer = csv.writer(self.trace_log_file)
                self.trace_writer.writerow(
                    [
                        "Step",
                        "Clock",
                        "Address",
                        "Tag",
                        "Set",
                        "Offset",
                        "Method",
                        "Hit",
                        "Reason",
                    ]
                )

            # update UI state
            dpg.set_value(self.status_widgets["sim_status"], "[*] Running")
            dpg.configure_item(self.status_widgets["run_btn"], enabled=False)
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=False)
            dpg.configure_item(self.status_widgets["reset_btn"], enabled=True)

            # run simulation
            total_steps = len(self.access_pattern)
            update_interval = self._calculate_update_interval(total_steps)

            for i, (address, method) in enumerate(self.access_pattern):
                if not self.is_running:
                    break

                # execute step
                trace = self.engine.step_instruction(address, method)
                trace["step"] = i
                self._add_trace_entry(trace)

                self.current_step += 1

                # periodic progress update
                if i % update_interval == 0 or i == total_steps - 1:
                    progress = self.current_step / total_steps
                    dpg.set_value(self.status_widgets["progress_bar"], progress)
                    dpg.set_value(
                        self.status_widgets["current_step"],
                        f"Step: {self.current_step} / {total_steps}",
                    )

            # cleanup
            if self.trace_log_file:
                self.trace_log_file.close()
                self.trace_log_file = None

            # final update
            self.is_running = False
            dpg.set_value(self.status_widgets["sim_status"], "[OK] Complete")
            dpg.configure_item(self.status_widgets["run_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["export_btn"], enabled=True)

            # update all visualizations
            self._update_all_visualizations()

        except Exception as e:
            # cleanup trace file if open
            if self.trace_log_file:
                self.trace_log_file.close()
                self.trace_log_file = None

            # update status with error
            dpg.set_value(self.status_widgets["sim_status"], f"[X] Error: {str(e)}")

            # re-enable buttons
            dpg.configure_item(self.status_widgets["run_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["reset_btn"], enabled=True)

            print(f"Simulation error: {e}")
            import traceback

            traceback.print_exc()

    def step_simulation(self):
        """Execute one simulation step."""
        from .simulation import SimulationEngine

        try:
            # create engine on first step
            if self.engine is None:
                if not self.access_pattern:
                    dpg.set_value(
                        self.status_widgets["sim_status"],
                        "[X] No access pattern loaded",
                    )
                    return

                config = self._get_simulation_config()
                self.engine = SimulationEngine(**config)
                self.current_step = 0
                self.execution_trace = []

            # check if done
            if self.current_step >= len(self.access_pattern):
                dpg.set_value(self.status_widgets["sim_status"], "[OK] Complete")
                dpg.configure_item(self.status_widgets["pause_btn"], enabled=False)
                return

            # execute one step
            address, method = self.access_pattern[self.current_step]
            trace = self.engine.step_instruction(address, method)
            trace["step"] = self.current_step
            self._add_trace_entry(trace)

            self.current_step += 1

            # update progress
            progress = self.current_step / len(self.access_pattern)
            dpg.set_value(self.status_widgets["progress_bar"], progress)
            dpg.set_value(
                self.status_widgets["current_step"],
                f"Step: {self.current_step} / {len(self.access_pattern)}",
            )

            # update all visualizations
            self._update_all_visualizations()

            # update status
            dpg.set_value(self.status_widgets["sim_status"], "[>] Stepping")
            dpg.configure_item(self.status_widgets["pause_btn"], enabled=True)
            dpg.configure_item(self.status_widgets["reset_btn"], enabled=True)
            dpg.configure_item(
                self.status_widgets["export_btn"], enabled=len(self.execution_trace) > 0
            )

        except Exception as e:
            # update status with error
            dpg.set_value(self.status_widgets["sim_status"], f"[X] Error: {str(e)}")

            print(f"Step simulation error: {e}")
            import traceback

            traceback.print_exc()

    def reset_simulation(self):
        """Reset simulation state while keeping pattern."""
        if self.engine:
            self.engine.reset()

        self.current_step = 0
        self.execution_trace = []
        self.is_running = False

        # reset progress
        dpg.set_value(self.status_widgets["progress_bar"], 0.0)
        dpg.set_value(self.status_widgets["current_step"], "Step: N/A")
        dpg.set_value(self.status_widgets["sim_status"], "[ ] Ready")

        # clear visualizations
        self._clear_all_visualizations()

        # update button states - keep step enabled if pattern exists
        dpg.configure_item(self.status_widgets["run_btn"], enabled=True)
        dpg.configure_item(
            self.status_widgets["pause_btn"], enabled=len(self.access_pattern) > 0
        )
        dpg.configure_item(self.status_widgets["reset_btn"], enabled=False)
        dpg.configure_item(self.status_widgets["export_btn"], enabled=False)

    def export_results(self):
        """Export simulation results to CSV."""
        if not self.execution_trace:
            dpg.set_value(self.status_widgets["sim_status"], "[X] No data to export")
            return

        from datetime import datetime

        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(
                    [
                        "Step",
                        "Clock",
                        "Address",
                        "Tag",
                        "Set",
                        "Offset",
                        "Method",
                        "Hit",
                        "Reason",
                    ]
                )

                # Write all stored trace entries
                for entry in self.execution_trace:
                    writer.writerow(
                        [
                            entry["step"],
                            entry.get("clock", 0),
                            entry["address"],
                            entry["tag_bits"],
                            int(entry["set_bits"], 2) if entry["set_bits"] else 0,
                            entry["offset_bits"],
                            entry["method"].upper(),
                            "HIT" if entry["hit"] else "MISS",
                            entry["reason"],
                        ]
                    )

            dpg.set_value(
                self.status_widgets["sim_status"], f"[OK] Exported to {filename}"
            )

        except Exception as e:
            dpg.set_value(
                self.status_widgets["sim_status"], f"[X] Export failed: {str(e)}"
            )

    def _update_all_visualizations(self):
        """Update all visualization panels."""
        if not self.engine:
            return

        self._update_statistics()
        self._update_current_address()
        self._update_trace_table()
        self._update_cache_visualization()

    def _update_cache_visualization(self):
        """Update cache state heat map and detailed view."""
        if not self.engine:
            return

        try:
            cache_state = self.engine.get_cache_state()
            self._draw_cache_heatmap(cache_state)
            self._update_cache_details(cache_state)
        except Exception as e:
            print(f"[ERROR] Error updating cache visualization: {e}")
            import traceback

            traceback.print_exc()

    def _draw_cache_heatmap(self, cache_state):
        """Draw heat map of cache state."""
        if not dpg.does_item_exist("heatmap_container"):
            return

        # clear existing drawings
        children = dpg.get_item_children("heatmap_container", slot=1) or []
        for child in children:
            dpg.delete_item(child)

        num_sets = len(cache_state)
        if num_sets == 0:
            return

        lines_per_set = len(cache_state[0])

        # update slider range
        if dpg.does_item_exist("cache_set_slider"):
            dpg.configure_item("cache_set_slider", max_value=max(0, num_sets - 1))
            dpg.set_value("cache_set_slider", self.selected_set)

        # get the most recently accessed line (if any)
        current_set = None
        current_way = None
        if self.execution_trace:
            last_trace = self.execution_trace[-1]
            if last_trace.get("set_bits"):
                current_set = int(last_trace["set_bits"], 2)
                # find which way was accessed by matching tag
                tag_bits = last_trace.get("tag_bits", "")
                if current_set < len(cache_state):
                    for way_idx, line in enumerate(cache_state[current_set]):
                        if not line.invalid and line.tag == tag_bits:
                            current_way = way_idx
                            break

        # calculate grid dimensions
        cell_size = self.cache_cell_size
        padding = 5
        label_width = 50  # space for set number labels on the left
        max_cols = min(lines_per_set, 20)  # max 20 columns visible

        # calculate canvas size to show all sets
        canvas_width = padding * 2 + label_width + max_cols * (cell_size + 2)
        canvas_height = padding * 2 + num_sets * (cell_size + 2)

        # create drawing canvas
        with dpg.drawlist(
            width=canvas_width,
            height=canvas_height,
            parent="heatmap_container",
            tag="cache_heatmap",
        ):
            # draw row labels and grid for all sets
            for set_idx in range(num_sets):
                # draw set number label on the left
                label_y = padding + set_idx * (cell_size + 2) + cell_size // 2
                dpg.draw_text(
                    (5, label_y - 6),  # center vertically
                    f"Set {set_idx}",
                    color=(180, 180, 180),
                    size=11,
                    parent="cache_heatmap",
                )

                for way_idx in range(max_cols):
                    if way_idx >= lines_per_set:
                        continue

                    line = cache_state[set_idx][way_idx]

                    # calculate position (offset by label_width)
                    x = padding + label_width + way_idx * (cell_size + 2)
                    y = padding + set_idx * (cell_size + 2)

                    # determine color based on state
                    if line.invalid:
                        color = (100, 100, 100)  # gray - invalid/empty
                    elif line.dirty:
                        color = (200, 200, 0)  # yellow - dirty
                    else:
                        color = (0, 200, 0)  # green - valid & clean

                    # brighten if this is the currently accessed line
                    if set_idx == current_set and way_idx == current_way:
                        if line.dirty:
                            color = (255, 255, 100)  # bright yellow
                        else:
                            color = (100, 255, 100)  # bright green

                    # draw cell
                    dpg.draw_rectangle(
                        (x, y),
                        (x + cell_size, y + cell_size),
                        color=color,
                        fill=color,
                        parent="cache_heatmap",
                        tag=f"cache_cell_{set_idx}_{way_idx}",
                    )

                    # draw border
                    border_color = (
                        (255, 255, 255)
                        if set_idx == self.selected_set
                        else (50, 50, 50)
                    )
                    border_thickness = 2 if set_idx == self.selected_set else 1
                    dpg.draw_rectangle(
                        (x, y),
                        (x + cell_size, y + cell_size),
                        color=border_color,
                        thickness=border_thickness,
                        parent="cache_heatmap",
                    )

    def _select_cache_set(self, set_idx):
        """Select a cache set for detailed view."""
        self.selected_set = set_idx
        if self.engine:
            self._update_cache_visualization()

    def _update_cache_details(self, cache_state):
        """Update detailed view of selected cache set."""
        if not dpg.does_item_exist("cache_detail_table"):
            return

        # clear existing rows
        children = dpg.get_item_children("cache_detail_table", slot=1) or []
        for child in children:
            dpg.delete_item(child)

        # check if selected set is valid
        if self.selected_set >= len(cache_state):
            return

        selected_set_lines = cache_state[self.selected_set]
        current_clock = self.engine._clock if self.engine else 0

        # add rows for each way in the selected set
        for way_idx, line in enumerate(selected_set_lines):
            with dpg.table_row(parent="cache_detail_table"):
                dpg.add_text(str(way_idx))

                if line.invalid:
                    dpg.add_text("-", color=(150, 150, 150))
                    dpg.add_text("-", color=(150, 150, 150))
                    dpg.add_text("-", color=(150, 150, 150))
                    dpg.add_text("-", color=(150, 150, 150))
                else:
                    # tag (show first 8 chars)
                    tag_display = (
                        line.tag[:8] + "..." if len(line.tag) > 8 else line.tag
                    )
                    dpg.add_text(tag_display)

                    # dirty
                    dirty_text = "YES" if line.dirty else "NO"
                    dirty_color = (200, 200, 0) if line.dirty else (0, 200, 0)
                    dpg.add_text(dirty_text, color=dirty_color)

                    # access count
                    dpg.add_text(str(line.access_counter))

                    # age (cycles since last use)
                    age = (
                        current_clock - line.used_timestamp if current_clock > 0 else 0
                    )
                    dpg.add_text(str(age))

    def _update_statistics(self):
        """Update statistics panel."""
        if not self.engine:
            return

        try:
            stats = self.engine.get_statistics()

            # total accesses
            if dpg.does_item_exist("stat_total_accesses"):
                dpg.set_value("stat_total_accesses", str(stats["total_accesses"]))
            if dpg.does_item_exist("stat_reads"):
                dpg.set_value(
                    "stat_reads", str(stats["read_hits"] + stats["read_misses"])
                )
            if dpg.does_item_exist("stat_writes"):
                dpg.set_value(
                    "stat_writes", str(stats["write_hits"] + stats["write_misses"])
                )

            # overall performance
            total = stats["total_accesses"]
            if total > 0:
                hit_pct = stats["hit_rate"] * 100
                miss_pct = stats["miss_rate"] * 100
                if dpg.does_item_exist("stat_hits"):
                    dpg.set_value(
                        "stat_hits", f"{stats['total_hits']} ({hit_pct:.1f}%)"
                    )
                if dpg.does_item_exist("stat_misses"):
                    dpg.set_value(
                        "stat_misses", f"{stats['total_misses']} ({miss_pct:.1f}%)"
                    )
                if dpg.does_item_exist("stat_hit_ratio"):
                    dpg.set_value("stat_hit_ratio", f"{hit_pct:.1f}%")
            else:
                if dpg.does_item_exist("stat_hits"):
                    dpg.set_value("stat_hits", "0 (0.0%)")
                if dpg.does_item_exist("stat_misses"):
                    dpg.set_value("stat_misses", "0 (0.0%)")
                if dpg.does_item_exist("stat_hit_ratio"):
                    dpg.set_value("stat_hit_ratio", "0.0%")

            # read performance
            total_reads = stats["read_hits"] + stats["read_misses"]
            if total_reads > 0:
                read_hit_pct = (stats["read_hits"] / total_reads) * 100
                read_miss_pct = (stats["read_misses"] / total_reads) * 100
                if dpg.does_item_exist("stat_read_hits"):
                    dpg.set_value(
                        "stat_read_hits", f"{stats['read_hits']} ({read_hit_pct:.1f}%)"
                    )
                if dpg.does_item_exist("stat_read_misses"):
                    dpg.set_value(
                        "stat_read_misses",
                        f"{stats['read_misses']} ({read_miss_pct:.1f}%)",
                    )
            else:
                if dpg.does_item_exist("stat_read_hits"):
                    dpg.set_value("stat_read_hits", "0 (0.0%)")
                if dpg.does_item_exist("stat_read_misses"):
                    dpg.set_value("stat_read_misses", "0 (0.0%)")

            # write performance
            total_writes = stats["write_hits"] + stats["write_misses"]
            if total_writes > 0:
                write_hit_pct = (stats["write_hits"] / total_writes) * 100
                write_miss_pct = (stats["write_misses"] / total_writes) * 100
                if dpg.does_item_exist("stat_write_hits"):
                    dpg.set_value(
                        "stat_write_hits",
                        f"{stats['write_hits']} ({write_hit_pct:.1f}%)",
                    )
                if dpg.does_item_exist("stat_write_misses"):
                    dpg.set_value(
                        "stat_write_misses",
                        f"{stats['write_misses']} ({write_miss_pct:.1f}%)",
                    )
            else:
                if dpg.does_item_exist("stat_write_hits"):
                    dpg.set_value("stat_write_hits", "0 (0.0%)")
                if dpg.does_item_exist("stat_write_misses"):
                    dpg.set_value("stat_write_misses", "0 (0.0%)")

            # evictions and writebacks
            if dpg.does_item_exist("stat_evictions"):
                dpg.set_value("stat_evictions", str(stats.get("evictions", 0)))
            if dpg.does_item_exist("stat_writebacks"):
                dpg.set_value("stat_writebacks", str(stats.get("writebacks", 0)))

            # average access time calculation
            # assumptions: cache hit = 1 cycle, memory access = 100 cycles
            # we never did get that chart...
            if dpg.does_item_exist("stat_avg_time"):
                if total > 0:
                    cache_hit_time = 1
                    memory_access_time = 100
                    avg_time = stats["hit_rate"] * cache_hit_time + stats[
                        "miss_rate"
                    ] * (cache_hit_time + memory_access_time)
                    dpg.set_value("stat_avg_time", f"{avg_time:.2f} cycles")
                else:
                    dpg.set_value("stat_avg_time", "0.0 cycles")
        except Exception as e:
            print(f"Error updating statistics: {e}")

    def _update_current_address(self):
        """Update current address breakdown display."""
        if not self.execution_trace:
            return

        try:
            trace = self.execution_trace[-1]

            # address
            if dpg.does_item_exist("current_address_text"):
                dpg.set_value(
                    "current_address_text", f"Address: {trace.get('address', 'N/A')}"
                )

            # bit breakdown
            tag_bits = trace.get("tag_bits", "")
            set_bits = trace.get("set_bits", "")
            offset_bits = trace.get("offset_bits", "")

            tag_int = int(tag_bits, 2) if tag_bits else 0
            set_int = int(set_bits, 2) if set_bits else 0
            offset_int = int(offset_bits, 2) if offset_bits else 0

            if dpg.does_item_exist("tag_bits_text"):
                dpg.set_value("tag_bits_text", f"Tag: 0b{tag_bits} ({tag_int})")
            if dpg.does_item_exist("set_bits_text"):
                dpg.set_value("set_bits_text", f"Set: 0b{set_bits} ({set_int})")
            if dpg.does_item_exist("offset_bits_text"):
                dpg.set_value(
                    "offset_bits_text", f"Offset: 0b{offset_bits} ({offset_int})"
                )

            # result
            result = "HIT [+]" if trace.get("hit", False) else "MISS [-]"
            if dpg.does_item_exist("result_text"):
                dpg.set_value("result_text", f"{result} - {trace.get('reason', '')}")
        except Exception as e:
            print(f"Error updating current address: {e}")

    def _update_trace_table(self):
        """Update execution trace table (last 20 entries)."""
        if not dpg.does_item_exist("trace_table"):
            return

        try:
            # get all current children (rows)
            children = dpg.get_item_children("trace_table", slot=1) or []

            # delete all existing rows
            for child in children:
                dpg.delete_item(child)

            # show last 20
            recent = self.execution_trace[-20:]

            for entry in recent:
                with dpg.table_row(parent="trace_table"):
                    dpg.add_text(str(entry.get("clock", 0)))
                    dpg.add_text(entry.get("address", ""))

                    tag_bits = entry.get("tag_bits", "")
                    dpg.add_text(
                        tag_bits[:16] + "..." if len(tag_bits) > 16 else tag_bits
                    )

                    set_bits = entry.get("set_bits", "0")
                    dpg.add_text(str(int(set_bits, 2) if set_bits else 0))

                    offset_bits = entry.get("offset_bits", "")
                    dpg.add_text(
                        offset_bits[:16] + "..."
                        if len(offset_bits) > 16
                        else offset_bits
                    )

                    dpg.add_text(entry.get("method", "").upper())
                    dpg.add_text("[+]" if entry.get("hit", False) else "[-]")
                    dpg.add_text(entry.get("reason", "")[:50])  # Truncate
        except Exception as e:
            print(f"[ERROR] Error updating trace table: {e}")
            import traceback

            traceback.print_exc()

    def _clear_all_visualizations(self):
        """Clear all visualization displays."""
        # i'm sorry for this.
        # i keep running into a edge case where sometimes, rarely, the items dont exist.
        # im almost out of time, its gotta be this way...
        # im sorry...
        
        # address breakdown
        if dpg.does_item_exist("current_address_text"):
            dpg.set_value("current_address_text", "No address yet")
        if dpg.does_item_exist("tag_bits_text"):
            dpg.set_value("tag_bits_text", "Tag: -")
        if dpg.does_item_exist("set_bits_text"):
            dpg.set_value("set_bits_text", "Set: -")
        if dpg.does_item_exist("offset_bits_text"):
            dpg.set_value("offset_bits_text", "Offset: -")
        if dpg.does_item_exist("result_text"):
            dpg.set_value("result_text", "")

        # statistics
        if dpg.does_item_exist("stat_total_accesses"):
            dpg.set_value("stat_total_accesses", "0")
        if dpg.does_item_exist("stat_reads"):
            dpg.set_value("stat_reads", "0")
        if dpg.does_item_exist("stat_writes"):
            dpg.set_value("stat_writes", "0")
        if dpg.does_item_exist("stat_hits"):
            dpg.set_value("stat_hits", "0 (0.0%)")
        if dpg.does_item_exist("stat_misses"):
            dpg.set_value("stat_misses", "0 (0.0%)")
        if dpg.does_item_exist("stat_hit_ratio"):
            dpg.set_value("stat_hit_ratio", "0.0%")
        if dpg.does_item_exist("stat_read_hits"):
            dpg.set_value("stat_read_hits", "0 (0.0%)")
        if dpg.does_item_exist("stat_read_misses"):
            dpg.set_value("stat_read_misses", "0 (0.0%)")
        if dpg.does_item_exist("stat_write_hits"):
            dpg.set_value("stat_write_hits", "0 (0.0%)")
        if dpg.does_item_exist("stat_write_misses"):
            dpg.set_value("stat_write_misses", "0 (0.0%)")
        if dpg.does_item_exist("stat_evictions"):
            dpg.set_value("stat_evictions", "0")
        if dpg.does_item_exist("stat_writebacks"):
            dpg.set_value("stat_writebacks", "0")
        if dpg.does_item_exist("stat_avg_time"):
            dpg.set_value("stat_avg_time", "0.0 cycles")

        # trace table
        if dpg.does_item_exist("trace_table"):
            children = dpg.get_item_children("trace_table", slot=1) or []
            for child in children:
                dpg.delete_item(child)

        # cache visualization
        if dpg.does_item_exist("heatmap_container"):
            children = dpg.get_item_children("heatmap_container", slot=1) or []
            for child in children:
                dpg.delete_item(child)

        if dpg.does_item_exist("cache_detail_table"):
            children = dpg.get_item_children("cache_detail_table", slot=1) or []
            for child in children:
                dpg.delete_item(child)

    def build_gui(self):
        with dpg.window(label="Cache Simulator", tag="main_window", no_close=True):
            with dpg.group(horizontal=True):
                # MARK: Left Sidebar
                with dpg.child_window(width=400, tag="sidebar"):
                    with dpg.collapsing_header(
                        label="Memory Configuration", default_open=True
                    ):
                        with dpg.group(horizontal=True):
                            self.config_widgets["ram_size"] = dpg.add_input_int(
                                width=150,
                                min_clamped=True,
                                default_value=32,
                                min_value=1,
                            )
                            self.config_widgets["ram_unit"] = dpg.add_combo(
                                ("B", "KB", "MB", "GB"),
                                width=100,
                                default_value="GB",
                                label="RAM Size",
                            )

                        with dpg.group(horizontal=True):
                            self.config_widgets["page_size"] = dpg.add_input_int(
                                width=150,
                                min_clamped=True,
                                default_value=4,
                                min_value=1,
                                callback=lambda s, a: self._update_n_ways_max(),
                            )
                            self.config_widgets["page_unit"] = dpg.add_combo(
                                ("B", "KB", "MB", "GB"),
                                width=100,
                                default_value="KB",
                                label="Page Size",
                                callback=lambda s, a: self._update_n_ways_max(),
                            )

                        with dpg.group(horizontal=True):
                            self.config_widgets["cache_size"] = dpg.add_input_int(
                                width=150,
                                min_clamped=True,
                                default_value=16,
                                min_value=1,
                                callback=lambda s, a: self._update_n_ways_max(),
                            )
                            self.config_widgets["cache_unit"] = dpg.add_combo(
                                ("B", "KB", "MB", "GB"),
                                width=100,
                                default_value="MB",
                                label="Cache Size",
                                callback=lambda s, a: self._update_n_ways_max(),
                            )

                        self.config_widgets["mapping_policy"] = dpg.add_combo(
                            (
                                "Direct Mapping",
                                "N-Way Set Associative",
                                "Fully Associative",
                            ),
                            label="Mapping Policy",
                            default_value="N-Way Set Associative",
                            width=250,
                        )

                        self.config_widgets["n_ways"] = dpg.add_combo(
                            items=[
                                "1",
                                "2",
                                "4",
                                "8",
                                "16",
                                "32",
                                "64",
                                "128",
                                "256",
                                "512",
                                "1024",
                                "2048",
                                "4096",
                            ],
                            default_value="4",
                            label="N (for N-Way)",
                            width=250,
                        )

                        self.config_widgets["replacement_policy"] = dpg.add_combo(
                            (
                                "Random Replacement",
                                "Least Recently Used (LRU)",
                                "Least Frequently Used (LFU)",
                                "First In First Out (FIFO)",
                            ),
                            label="Replacement Policy",
                            default_value="Least Recently Used (LRU)",
                            width=250,
                        )

                        self.config_widgets["write_policy"] = dpg.add_combo(
                            ("Write-Through", "Write-Back"),
                            label="Write Policy",
                            default_value="Write-Back",
                            width=250,
                        )

                    # MARK: Access Pattern Input
                    with dpg.collapsing_header(
                        label="Access Patterns", default_open=True
                    ):
                        # CSV, or Random Generation
                        dpg.add_button(
                            label="Select CSV File",
                            callback=lambda: dpg.show_item("file_dialog"),
                        )

                        dpg.add_separator(label="OR")

                        self.config_widgets["num_reads"] = dpg.add_input_int(
                            label="Number of Reads",
                            width=200,
                            min_clamped=True,
                            default_value=1000,
                            min_value=0,
                        )
                        self.config_widgets["num_writes"] = dpg.add_input_int(
                            label="Number of Writes",
                            width=200,
                            min_clamped=True,
                            default_value=500,
                            min_value=0,
                        )

                        with dpg.group(horizontal=True):
                            self.config_widgets["rng_seed"] = dpg.add_input_int(
                                label="RNG Seed",
                                width=200,
                                min_clamped=True,
                                default_value=42,
                            )
                            dpg.add_button(
                                label="Randomize Seed",
                                callback=lambda: self.randomize_seed(),
                            )

                        # Locality Settings
                        # i should make this better, but theres no time!
                        with dpg.collapsing_header(
                            label="Locality Settings", default_open=False
                        ):
                            with dpg.group(horizontal=True):
                                self.config_widgets["temporal_locality"] = (
                                    dpg.add_slider_int(
                                        label="Temporal Locality (%)",
                                        default_value=0,
                                        min_value=0,
                                        max_value=100,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Probability of reusing a recently accessed address.\n"
                                        "Higher values create more temporal locality, improving cache hit rates\n"
                                        "for workloads that frequently reuse the same data."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["spatial_locality"] = (
                                    dpg.add_slider_int(
                                        label="Spatial Locality (%)",
                                        default_value=0,
                                        min_value=0,
                                        max_value=100,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Probability of accessing addresses near the previous access.\n"
                                        "Simulates sequential or strided memory access patterns common in\n"
                                        "array traversals and streaming workloads."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["stride_size"] = dpg.add_slider_int(
                                    label="Stride Size (bytes)",
                                    default_value=64,
                                    min_value=1,
                                    max_value=256,
                                    width=200,
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Distance in bytes between spatially local accesses.\n"
                                        "Common values: 64 (cache line), 4/8 (array elements),\n"
                                        "or powers of 2 for strided access patterns."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["working_set_size"] = (
                                    dpg.add_slider_int(
                                        label="Working Set Size (%)",
                                        default_value=100,
                                        min_value=1,
                                        max_value=100,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Percentage of total memory space to confine accesses to.\n"
                                        "Smaller working sets fit better in cache, simulating programs\n"
                                        "that operate on a limited subset of data at once."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["working_set_focus"] = (
                                    dpg.add_slider_int(
                                        label="Working Set Focus (%)",
                                        default_value=80,
                                        min_value=50,
                                        max_value=100,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Probability that accesses stay within the working set bounds.\n"
                                        "Lower values allow occasional accesses outside the working set,\n"
                                        "simulating cache pollution from infrequent operations."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["hotspot_count"] = (
                                    dpg.add_slider_int(
                                        label="Hotspot Count",
                                        default_value=0,
                                        min_value=0,
                                        max_value=10,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Number of frequently accessed 'hot' memory regions.\n"
                                        "Simulates workloads with popular data structures like\n"
                                        "hash tables, counters, or frequently called code paths."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["hotspot_intensity"] = (
                                    dpg.add_slider_int(
                                        label="Hotspot Intensity (%)",
                                        default_value=50,
                                        min_value=0,
                                        max_value=100,
                                        width=200,
                                    )
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Probability of accessing hotspot regions vs random addresses.\n"
                                        "Higher values concentrate accesses on hotspots, creating\n"
                                        "highly skewed access distributions."
                                    )

                            with dpg.group(horizontal=True):
                                self.config_widgets["history_size"] = dpg.add_input_int(
                                    label="History Size",
                                    default_value=100,
                                    min_value=1,
                                    min_clamped=True,
                                    width=200,
                                )
                                dpg.add_text("(?)", color=(0, 255, 0))
                                with dpg.tooltip(dpg.last_item()):
                                    dpg.add_text(
                                        "Number of recent addresses to remember for temporal locality.\n"
                                        "Larger values allow reuse of older addresses, while smaller\n"
                                        "values focus on very recent accesses only."
                                    )

                            dpg.add_separator()
                            dpg.add_text("Presets:", color=(200, 200, 200))
                            with dpg.group(horizontal=True):
                                dpg.add_button(
                                    label="No Locality",
                                    callback=lambda: self.apply_locality_preset("none"),
                                )
                                dpg.add_button(
                                    label="High Temporal",
                                    callback=lambda: self.apply_locality_preset(
                                        "high_temporal"
                                    ),
                                )
                                dpg.add_button(
                                    label="High Spatial",
                                    callback=lambda: self.apply_locality_preset(
                                        "high_spatial"
                                    ),
                                )
                            with dpg.group(horizontal=True):
                                dpg.add_button(
                                    label="Hotspot",
                                    callback=lambda: self.apply_locality_preset(
                                        "hotspot"
                                    ),
                                )
                                dpg.add_button(
                                    label="Realistic Mix",
                                    callback=lambda: self.apply_locality_preset(
                                        "realistic"
                                    ),
                                )

                        dpg.add_button(
                            label="Generate Access Pattern",
                            callback=lambda: self.generate_access_pattern(),
                        )

                        self.config_widgets["write_full_trace"] = dpg.add_checkbox(
                            label="Write full trace to file during simulation",
                            default_value=False,
                        )

                        dpg.add_separator()

                        self.status_widgets["pattern_status"] = dpg.add_text(
                            "No Pattern Loaded"
                        )
                        self.status_widgets["accesses_queued"] = dpg.add_text(
                            "Accesses Queued: 0"
                        )

                    # MARK: Simulation Controls
                    with dpg.collapsing_header(
                        label="Simulation Controls", default_open=True
                    ):
                        self.status_widgets["run_btn"] = dpg.add_button(
                            label="Run Simulation (Full)",
                            width=-1,
                            callback=lambda: self.run_simulation(),
                        )
                        with dpg.group(horizontal=True):
                            self.status_widgets["pause_btn"] = dpg.add_button(
                                label="Step",
                                callback=lambda: self.step_simulation(),
                                enabled=False,
                            )
                            self.status_widgets["reset_btn"] = dpg.add_button(
                                label="Reset",
                                callback=lambda: self.reset_simulation(),
                                enabled=False,
                            )

                        self.status_widgets["sim_status"] = dpg.add_text("[ ] Ready")
                        self.status_widgets["progress_bar"] = dpg.add_progress_bar(
                            default_value=0.0, width=-1
                        )
                        self.status_widgets["current_step"] = dpg.add_text("Step: N/A")

                        dpg.add_separator()

                        self.status_widgets["export_btn"] = dpg.add_button(
                            label="Export Results (CSV)",
                            width=-1,
                            callback=lambda: self.export_results(),
                            enabled=False,
                        )

                # MARK: Main View
                with dpg.child_window(tag="main_view"):
                    with dpg.collapsing_header(
                        label="Current Address", default_open=True
                    ):
                        dpg.add_text("No address yet", tag="current_address_text")
                        with dpg.group(horizontal=True):
                            dpg.add_text("Tag: -", tag="tag_bits_text")
                            dpg.add_spacer(width=20)
                            dpg.add_text("Set: -", tag="set_bits_text")
                            dpg.add_spacer(width=20)
                            dpg.add_text("Offset: -", tag="offset_bits_text")
                        dpg.add_text("", tag="result_text")

                    # MARK: Cache State Visualization
                    with dpg.collapsing_header(label="Cache State", default_open=True):
                        # legend at the top
                        with dpg.group(horizontal=True):
                            dpg.add_text("Legend: ", color=(200, 200, 200))
                            dpg.add_text("[  ]", color=(100, 100, 100))
                            dpg.add_text("Empty ")
                            dpg.add_text("[  ]", color=(0, 200, 0))
                            dpg.add_text("Valid+Clean ")
                            dpg.add_text("[  ]", color=(200, 200, 0))
                            dpg.add_text("Valid+Dirty ")
                            dpg.add_text("[  ]", color=(100, 255, 100))
                            dpg.add_text("Current Access")

                        with dpg.child_window(
                            height=600,
                            horizontal_scrollbar=True,
                            tag="heatmap_container",
                        ):
                            pass

                        dpg.add_separator()

                        dpg.add_slider_int(
                            label="Select Set to View Details",
                            tag="cache_set_slider",
                            default_value=0,
                            min_value=0,
                            max_value=0,
                            width=400,
                            callback=lambda s, v: self._select_cache_set(v),
                        )

                        with dpg.table(
                            header_row=True,
                            tag="cache_detail_table",
                            borders_innerH=True,
                            borders_outerH=True,
                            borders_innerV=True,
                            borders_outerV=True,
                            scrollY=True,
                            height=150,
                        ):
                            dpg.add_table_column(label="Way")
                            dpg.add_table_column(label="Tag")
                            dpg.add_table_column(label="Dirty")
                            dpg.add_table_column(label="Accesses")
                            dpg.add_table_column(label="Age (cycles)")

                    # MARK: Statistics Panel
                    with dpg.collapsing_header(label="Statistics", default_open=True):
                        with dpg.group(horizontal=True):
                            with dpg.group():
                                dpg.add_text("Total Accesses:")
                                dpg.add_text("  Reads:")
                                dpg.add_text("  Writes:")
                                dpg.add_spacer(height=5)
                                dpg.add_text("Cache Performance:")
                                dpg.add_text("  Hits:")
                                dpg.add_text("  Misses:")
                                dpg.add_text("  Hit Ratio:")

                            dpg.add_spacer(width=10)

                            with dpg.group():
                                dpg.add_text("0", tag="stat_total_accesses")
                                dpg.add_text("0", tag="stat_reads")
                                dpg.add_text("0", tag="stat_writes")
                                dpg.add_spacer(height=5)
                                dpg.add_text("")
                                dpg.add_text("0 (0.0%)", tag="stat_hits")
                                dpg.add_text("0 (0.0%)", tag="stat_misses")
                                dpg.add_text("0.0%", tag="stat_hit_ratio")

                            dpg.add_spacer(width=30)

                            with dpg.group():
                                dpg.add_text("Read Performance:")
                                dpg.add_text("  Read Hits:")
                                dpg.add_text("  Read Misses:")
                                dpg.add_spacer(height=5)
                                dpg.add_text("Write Performance:")
                                dpg.add_text("  Write Hits:")
                                dpg.add_text("  Write Misses:")

                            dpg.add_spacer(width=10)

                            with dpg.group():
                                dpg.add_text("")
                                dpg.add_text("0 (0.0%)", tag="stat_read_hits")
                                dpg.add_text("0 (0.0%)", tag="stat_read_misses")
                                dpg.add_spacer(height=5)
                                dpg.add_text("")
                                dpg.add_text("0 (0.0%)", tag="stat_write_hits")
                                dpg.add_text("0 (0.0%)", tag="stat_write_misses")

                            dpg.add_spacer(width=30)

                            with dpg.group():
                                dpg.add_text("Memory Operations:")
                                dpg.add_text("  Evictions:")
                                dpg.add_text("  Write-Backs:")
                                dpg.add_text("  Avg Access Time:")

                            dpg.add_spacer(width=10)

                            with dpg.group():
                                dpg.add_text("")
                                dpg.add_text("0", tag="stat_evictions")
                                dpg.add_text("0", tag="stat_writebacks")
                                dpg.add_text("0.0 cycles", tag="stat_avg_time")
                    with dpg.collapsing_header(
                        label="Execution Trace (Last 20 Accesses)", default_open=True
                    ):
                        with dpg.table(
                            header_row=True,
                            tag="trace_table",
                            borders_innerH=True,
                            borders_outerH=True,
                            borders_innerV=True,
                            borders_outerV=True,
                            scrollY=True,
                            height=200,
                            policy=dpg.mvTable_SizingStretchProp,
                        ):
                            dpg.add_table_column(label="Time")
                            dpg.add_table_column(label="Address")
                            dpg.add_table_column(label="Tag")
                            dpg.add_table_column(label="Set")
                            dpg.add_table_column(label="Offset")
                            dpg.add_table_column(label="R/W")
                            dpg.add_table_column(label="Hit")
                            dpg.add_table_column(label="Reason")

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.load_csv_callback,
            tag="file_dialog",
            width=700,
            height=400,
        ):
            dpg.add_file_extension("*.csv", color=(255, 0, 255, 255))
            dpg.add_file_extension(".*")

    def run(self):
        self.build_gui()
        # set initial n_ways max value after widgets are created
        self._update_n_ways_max()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


def gui_main():
    app = CacheSimulatorGUI()
    app.run()
