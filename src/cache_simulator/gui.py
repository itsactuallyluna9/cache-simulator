import dearpygui.dearpygui as dpg

def add_value_with_unit(label, default_int=1, default_unit="B"):
    with dpg.group(horizontal=True):
        dpg.add_input_int(width=250, min_clamped=True, default_value=default_int)
        dpg.add_combo(("B", "KB", "MB", "GB"), width=250, default_value=default_unit, label=label)

def gui_main():
    dpg.create_context()
    dpg.create_viewport()
    dpg.setup_dearpygui()

    with dpg.window(label="Cache Simulator", tag="Cache Simulator"):
        add_value_with_unit("RAM Size", 32, "GB")
        add_value_with_unit("Page Size", 4, "KB")
        add_value_with_unit("Cache Size", 16, "MB")
        dpg.add_combo(("Direct Mapping", "N-Way Set Associative Mapping", "Fully Associative Mapping"), label="Mapping Policy")
        dpg.add_slider_int(min_value=1, max_value=12, clamped=True, default_value=4, label="N")
        dpg.add_text("Replacement Policy")

        dpg.add_button(label="Start")
        dpg.add_button(label="Step")
        dpg.add_button(label="Benchmark")
        

    dpg.show_viewport()
    dpg.set_primary_window("Cache Simulator", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
