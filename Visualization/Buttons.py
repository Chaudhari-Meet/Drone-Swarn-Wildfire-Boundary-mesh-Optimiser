from matplotlib.widgets import Button

def create_buttons(
    fig,
    finish_boundary,
    save_boundary,
    undo_last_point,
    clear_boundary,
    previous_boundary,
    next_boundary,
    generate_mesh_button,
    calculate_area_button,
    allocate_drone_button,
    plan_paths_button,
    app_state
):
    # Buttons

    # ============================================================
    # NAVIGATION BUTTONS
    # ============================================================

    # Undo
    undo_ax = fig.add_axes([0.05, 0.87, 0.07, 0.045])
    undo_button = Button(undo_ax,"Undo")
    undo_button.on_clicked(undo_last_point)
    
    # Previous Button
    prev_ax = fig.add_axes([0.22, 0.87, 0.032, 0.045])
    prev_button = Button(prev_ax,"◀")
    prev_button.on_clicked(
        lambda event: previous_boundary(event, app_state)
    )
    
    # Next Button
    next_ax = fig.add_axes([0.35, 0.87, 0.032, 0.045])
    next_button = Button(next_ax,"▶")
    next_button.on_clicked(
        lambda event: next_boundary(event, app_state)
    )

    # Clear Button
    clear_ax = fig.add_axes([0.50, 0.87, 0.07, 0.045])
    clear_button = Button(clear_ax,"Clear")
    clear_button.on_clicked(clear_boundary)
    
    # ============================================================
    # ROW 1: BOUNDARY CONTROLS
    # ============================================================

    button_width = 0.12
    button_height = 0.055
    row1_y = 0.07
    row2_y = 0.014
    start_x = 0.14
    gap = 0.02
    
    # Finish Boundary
    finish_ax = fig.add_axes([start_x,row1_y, button_width, button_height])
    finish_button = Button(finish_ax,"Finish Boundary")
    finish_button.on_clicked(finish_boundary)
    
    # Save Boundary
    save_ax = fig.add_axes([start_x+ button_width + gap,row1_y,button_width,button_height])
    save_button = Button(save_ax,"Save Boundary")
    save_button.on_clicked(save_boundary)
    
    # Calculate Area
    area_ax = fig.add_axes([start_x+ 2 * button_width + 2 * gap,row1_y,button_width,button_height])
    area_button = Button(area_ax,"Calculate Area")
    area_button.on_clicked(calculate_area_button)
    
    # ============================================================
    # ROW 2: ANALYSIS CONTROLS
    # ============================================================
    
    # Generate Mesh
    mesh_ax = fig.add_axes([start_x,row2_y,button_width,button_height])
    mesh_button = Button(mesh_ax,"Generate Mesh")
    mesh_button.on_clicked(generate_mesh_button)
    
    # Allocate Drones
    drone_ax = fig.add_axes([start_x+ button_width + gap,row2_y,button_width,button_height])
    drone_button = Button(drone_ax,"Allocate Drones")
    drone_button.on_clicked(allocate_drone_button)
    
    # Plan Paths
    path_ax = fig.add_axes([start_x+ 2 * button_width + 2 * gap,row2_y,button_width,button_height])
    path_button = Button(path_ax,"Plan Paths")
    path_button.on_clicked(plan_paths_button)

    # Button colors
    for b in [
        finish_button,
        save_button,
        area_button,
        mesh_button,
        drone_button,
        path_button,
        undo_button,
        clear_button,
        prev_button,
        next_button,
    ]:
        b.label.set_fontsize(11)
        b.label.set_fontweight("bold")
        b.color = "#F3F3F3"
        b.hovercolor = "#CFE8FF"

    return {
        "clear": clear_button,
        "prev": prev_button,
        "next": next_button,
        "undo": undo_button,
        "finish": finish_button,
        "save": save_button,
        "area": area_button,
        "mesh": mesh_button,
        "drone": drone_button,
        "path": path_button
    }
