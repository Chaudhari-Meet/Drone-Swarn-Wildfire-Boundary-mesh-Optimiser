from tkinter import Tk, simpledialog
from Algorithms.Mesh_Generation import generate_mesh
from Algorithms.Area_Calculation import calculate_area
from Algorithms.Drone_Allocation import allocate_drones
from Algorithms.Path_Planning import (nearest_neighbor_path,calculate_path_distance)
from Algorithms.Performance_Analysis import (
    calculate_sequential_distance,
    calculate_total_distance,
    calculate_average_distance,
    calculate_longest_path,
    calculate_shortest_path
)
import matplotlib.pyplot as plt
from Visualization.Dashboard import update_dashboard, dashboard_card
from Visualization.Buttons import create_buttons
import json
import os
import glob
import re

# Global Variables
title_text = None
fig = plt.figure(figsize=(12, 8))
fig.suptitle("Draw Wildfire Boundary",fontsize=20,fontweight="bold",y=0.98)
ax = fig.add_axes([0.05, 0.20, 0.52, 0.65])
plt.subplots_adjust(top=0.88, bottom=0.25)
info_ax = fig.add_axes([0.66, 0.08, 0.32, 0.84])
info_ax.axis("off")

# show the current boundary index and total boundaries
boundary_label = fig.text(0.303,0.890,"",ha="center",va="center",fontsize=16,fontweight="bold")

# ============================================================
# APPLICATION STATE
# ============================================================

app_state = {

    # --------------------------------------------------------
    # FIGURE / UI
    # --------------------------------------------------------

    "fig": fig,
    "ax": ax,
    "info_ax": info_ax,

    "boundary_label": boundary_label,
    "title_text": title_text,


    # --------------------------------------------------------
    # BOUNDARY
    # --------------------------------------------------------

    "boundary": [],
    "boundary_completed": False,
    "boundary_points": 0,

    "current_boundary": -1,
    "saved_files": [],
    "current_dataset": "None",


    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    "current_area": None,


    # --------------------------------------------------------
    # MESH
    # --------------------------------------------------------

    "mesh": [],
    "mesh_nodes": 0,


    # --------------------------------------------------------
    # DRONES
    # --------------------------------------------------------

    "number_of_drones": 0,

    "drone_assignments": {},
    "drone_paths": {},
    "drone_distances": {},


    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    "performance_results": {}

}


# Mouse Click Function
def onclick(event):

    # --------------------------------------------------------
    # CHECK IF BOUNDARY IS ALREADY COMPLETED
    # --------------------------------------------------------

    if app_state["boundary_completed"]:
        return

    # --------------------------------------------------------
    # CHECK IF CLICK IS INSIDE GRAPH
    # --------------------------------------------------------

    if event.inaxes != app_state["ax"]:
        return

    if event.xdata is None or event.ydata is None:
        return

    # --------------------------------------------------------
    # GET CLICK COORDINATES
    # --------------------------------------------------------

    x = round(event.xdata, 2)
    y = round(event.ydata, 2)

    # --------------------------------------------------------
    # ADD POINT TO BOUNDARY
    # --------------------------------------------------------

    app_state["boundary"].append((x, y))

    app_state["boundary_points"] = len(
        app_state["boundary"]
    )

    # --------------------------------------------------------
    # DRAW POINT
    # --------------------------------------------------------

    app_state["ax"].scatter(
        x,
        y,
        color="blue",
        s=50
    )

    # --------------------------------------------------------
    # DRAW POINT NUMBER
    # --------------------------------------------------------

    app_state["ax"].text(
        x + 0.5,
        y + 0.5,
        str(len(app_state["boundary"])),
        fontsize=10,
        color="black"
    )

    # --------------------------------------------------------
    # DRAW LINE BETWEEN POINTS
    # --------------------------------------------------------

    if len(app_state["boundary"]) > 1:

        x1, y1 = app_state["boundary"][-2]

        app_state["ax"].plot(
            [x1, x],
            [y1, y],
            color="red",
            linewidth=2
        )

    # --------------------------------------------------------
    # UPDATE DISPLAY
    # --------------------------------------------------------

    app_state["fig"].canvas.draw_idle()

# Finish Boundary
def finish_boundary(event):

    # --------------------------------------------------------
    # CHECK IF ALREADY COMPLETED
    # --------------------------------------------------------

    if app_state["boundary_completed"]:
        return

    # --------------------------------------------------------
    # CHECK MINIMUM POINTS
    # --------------------------------------------------------

    if len(app_state["boundary"]) < 3:
        print("Minimum 3 points required.")
        return

    # --------------------------------------------------------
    # MARK BOUNDARY AS COMPLETED
    # --------------------------------------------------------

    app_state["boundary_completed"] = True

    app_state["boundary_points"] = len(
        app_state["boundary"]
    )

    # --------------------------------------------------------
    # GET BOUNDARY COORDINATES
    # --------------------------------------------------------

    xs = [
        point[0]
        for point in app_state["boundary"]
    ]

    ys = [
        point[1]
        for point in app_state["boundary"]
    ]

    # --------------------------------------------------------
    # CLOSE POLYGON
    # --------------------------------------------------------

    xs_closed = xs + [xs[0]]
    ys_closed = ys + [ys[0]]

    # --------------------------------------------------------
    # DRAW CLOSED BOUNDARY
    # --------------------------------------------------------

    app_state["ax"].plot(
        xs_closed,
        ys_closed,
        color="red",
        linewidth=2,
        label="Wildfire Boundary"
    )

    # --------------------------------------------------------
    # FILL WILDFIRE REGION
    # --------------------------------------------------------

    app_state["ax"].fill(
        xs,
        ys,
        color="orange",
        alpha=0.35,
        label="Wildfire Region"
    )

    # --------------------------------------------------------
    # LEGEND
    # --------------------------------------------------------

    app_state["ax"].legend(
        loc="upper right",
        fontsize=9,
        frameon=True
    )

    # --------------------------------------------------------
    # UPDATE DISPLAY
    # --------------------------------------------------------

    app_state["fig"].canvas.draw_idle()

    print("\nBoundary Completed!")

# Calculate Area Button
def calculate_area_button(event):

    # --------------------------------------------------------
    # CHECK BOUNDARY
    # --------------------------------------------------------

    if not app_state["boundary_completed"]:
        print("Finish the boundary first!")
        return

    # --------------------------------------------------------
    # CALCULATE AREA
    # --------------------------------------------------------

    app_state["current_area"] = calculate_area(
        app_state["boundary"]
    )

    # --------------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------------

    update_dashboard(
        app_state["info_ax"],
        app_state["fig"],
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    app_state["fig"].canvas.draw_idle()

    print(
        f"Wildfire Area : "
        f"{app_state['current_area']:.2f} square units"
    )

# Undo Last Point
def undo_last_point(event):

    # --------------------------------------------------------
    # CHECK IF BOUNDARY IS COMPLETED
    # --------------------------------------------------------

    if app_state["boundary_completed"]:
        print("Boundary already completed.")
        return

    # --------------------------------------------------------
    # CHECK IF THERE IS A POINT TO REMOVE
    # --------------------------------------------------------

    if not app_state["boundary"]:
        print("No points to undo.")
        return

    # --------------------------------------------------------
    # REMOVE LAST POINT
    # --------------------------------------------------------

    app_state["boundary"].pop()

    app_state["boundary_points"] = len(
        app_state["boundary"]
    )

    # --------------------------------------------------------
    # REDRAW GRAPH
    # --------------------------------------------------------

    app_state["ax"].clear()

    app_state["ax"].set_xlim(0, 100)
    app_state["ax"].set_ylim(0, 100)

    app_state["ax"].set_xlabel("X Coordinate")
    app_state["ax"].set_ylabel("Y Coordinate")

    app_state["ax"].grid(True)

    # --------------------------------------------------------
    # REDRAW REMAINING POINTS AND LINES
    # --------------------------------------------------------

    for i, (x, y) in enumerate(
        app_state["boundary"]
    ):

        app_state["ax"].scatter(
            x,
            y,
            color="blue",
            s=50
        )

        app_state["ax"].text(
            x + 0.5,
            y + 0.5,
            str(i + 1),
            fontsize=10,
            color="black"
        )

        if i > 0:

            x1, y1 = app_state["boundary"][i - 1]

            app_state["ax"].plot(
                [x1, x],
                [y1, y],
                color="red",
                linewidth=2
            )

    # --------------------------------------------------------
    # REDRAW
    # --------------------------------------------------------

    app_state["fig"].canvas.draw_idle()

    print("Last point removed.")

# Clear Boundary
def clear_boundary(event):

    # --------------------------------------------------------
    # CLEAR GRAPH
    # --------------------------------------------------------

    app_state["ax"].clear()

    app_state["ax"].set_xlim(0, 100)
    app_state["ax"].set_ylim(0, 100)

    app_state["ax"].set_xlabel("X Coordinate")
    app_state["ax"].set_ylabel("Y Coordinate")

    app_state["ax"].grid(True)

    # --------------------------------------------------------
    # RESET BOUNDARY STATE
    # --------------------------------------------------------

    app_state["boundary"].clear()

    app_state["boundary_completed"] = False
    app_state["boundary_points"] = 0
    app_state["current_area"] = None

    # --------------------------------------------------------
    # RESET MESH STATE
    # --------------------------------------------------------

    app_state["mesh"].clear()
    app_state["mesh_nodes"] = 0

    # --------------------------------------------------------
    # RESET DRONE STATE
    # --------------------------------------------------------

    app_state["drone_assignments"].clear()
    app_state["drone_paths"].clear()
    app_state["drone_distances"].clear()

    app_state["number_of_drones"] = 0

    # --------------------------------------------------------
    # RESET PERFORMANCE
    # --------------------------------------------------------

    app_state["performance_results"].clear()

    # --------------------------------------------------------
    # RESET DATASET
    # --------------------------------------------------------

    app_state["current_dataset"] = "None"

    # --------------------------------------------------------
    # RESET TITLE / LABEL
    # --------------------------------------------------------

    if app_state["title_text"] is not None:
        try:
            app_state["title_text"].remove()
        except:
            pass

        app_state["title_text"] = None

    if app_state["boundary_label"] is not None:
        app_state["boundary_label"].set_text("")

    # --------------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------------

    update_dashboard(
        app_state["info_ax"],
        app_state["fig"],
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    # --------------------------------------------------------
    # REDRAW
    # --------------------------------------------------------

    app_state["fig"].canvas.draw_idle()

    print("Boundary Cleared")

# Save Boundary
def save_boundary(event):

    # --------------------------------------------------------
    # CHECK IF BOUNDARY IS COMPLETED
    # --------------------------------------------------------

    if not app_state["boundary_completed"]:
        print("Finish the boundary first!")
        return

    # --------------------------------------------------------
    # CHECK BOUNDARY
    # --------------------------------------------------------

    if len(app_state["boundary"]) < 3:
        print("No valid boundary.")
        return

    # --------------------------------------------------------
    # CREATE DATA FOLDER
    # --------------------------------------------------------

    os.makedirs("data", exist_ok=True)

    # --------------------------------------------------------
    # FIND NEXT DATASET NUMBER
    # --------------------------------------------------------

    existing_files = glob.glob("data/Data*.json")

    numbers = []

    for file in existing_files:

        match = re.search(
            r"Data(\d+)\.json",
            os.path.basename(file)
        )

        if match:
            numbers.append(
                int(match.group(1))
            )

    if numbers:
        next_number = max(numbers) + 1
    else:
        next_number = 1

    filename = f"data/Data{next_number}.json"

    # --------------------------------------------------------
    # SAVE BOUNDARY
    # --------------------------------------------------------

    with open(filename, "w") as file:

        json.dump(
            {
                "boundary": app_state["boundary"]
            },
            file,
            indent=4
        )

    # --------------------------------------------------------
    # UPDATE APPLICATION STATE
    # --------------------------------------------------------

    app_state["saved_files"] = sorted(
        glob.glob("data/Data*.json"),
        key=lambda x: int(
            re.search(
                r"Data(\d+)",
                os.path.basename(x)
            ).group(1)
        )
    )

    app_state["current_boundary"] = (
        len(app_state["saved_files"]) - 1
    )

    app_state["current_dataset"] = (
        os.path.basename(filename)
    )

    # --------------------------------------------------------
    # UPDATE NAVIGATION LABEL
    # --------------------------------------------------------

    if app_state["boundary_label"] is not None:

        app_state["boundary_label"].set_text(
            f"{app_state['current_boundary'] + 1} / "
            f"{len(app_state['saved_files'])}"
        )

    # --------------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------------

    update_dashboard(
        app_state["info_ax"],
        app_state["fig"],
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    app_state["fig"].canvas.draw_idle()

    print("\nBoundary saved successfully!")
    print(filename)

# Load Boundary
def load_boundary(index, app_state):

    # ============================================================
    # GET DATA FROM APP STATE
    # ============================================================

    fig = app_state["fig"]
    ax = app_state["ax"]
    info_ax = app_state["info_ax"]

    saved_files = app_state["saved_files"]

    boundary_label = app_state["boundary_label"]
    title_text = app_state["title_text"]

    # ============================================================
    # CHECK SAVED FILES
    # ============================================================

    if len(saved_files) == 0:
        print("No saved boundaries found.")
        return

    if index < 0 or index >= len(saved_files):
        return

    # ============================================================
    # LOAD SELECTED DATASET
    # ============================================================

    app_state["current_boundary"] = index

    with open(saved_files[index], "r") as file:
        data = json.load(file)

    boundary = [
        tuple(point)
        for point in data["boundary"]
    ]

    # ============================================================
    # RESET ANALYSIS DATA
    # ============================================================

    app_state["boundary"] = boundary

    app_state["boundary_completed"] = True

    app_state["current_area"] = None

    app_state["mesh"] = []
    app_state["mesh_nodes"] = 0

    app_state["drone_assignments"] = {}
    app_state["drone_paths"] = {}
    app_state["drone_distances"] = {}

    app_state["performance_results"] = {}

    # ============================================================
    # UPDATE DATASET INFORMATION
    # ============================================================

    app_state["current_dataset"] = os.path.basename(
        saved_files[index]
    )

    app_state["boundary_points"] = len(boundary)

    app_state["current_area"] = calculate_area(
        boundary
    )

    # ============================================================
    # CLEAR GRAPH
    # ============================================================

    ax.clear()

    ax.set_title("")

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

    ax.grid(True)

    # ============================================================
    # DRAW WILDFIRE BOUNDARY
    # ============================================================

    xs = [point[0] for point in boundary]
    ys = [point[1] for point in boundary]

    xs_closed = xs + [xs[0]]
    ys_closed = ys + [ys[0]]

    ax.fill(
        xs_closed,
        ys_closed,
        color="orange",
        alpha=0.35
    )

    ax.plot(
        xs_closed,
        ys_closed,
        color="red",
        linewidth=2
    )

    # ============================================================
    # DRAW BOUNDARY VERTICES
    # ============================================================

    for i, (x, y) in enumerate(boundary):

        ax.scatter(
            x,
            y,
            color="blue",
            s=50
        )

        ax.text(
            x + 0.5,
            y + 0.5,
            str(i + 1)
        )

    # ============================================================
    # UPDATE TITLE / NAVIGATION LABEL
    # ============================================================

    if title_text:
        title_text.remove()

        app_state["title_text"] = None

    boundary_label.set_text(
        f"{app_state['current_boundary'] + 1} / "
        f"{len(saved_files)}"
    )

    # ============================================================
    # UPDATE DASHBOARD
    # ============================================================

    update_dashboard(
        info_ax,
        fig,
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    # ============================================================
    # REDRAW
    # ============================================================

    fig.canvas.draw_idle()

# Previous Boundary
def previous_boundary(event, app_state):

    current_boundary = app_state["current_boundary"]

    if current_boundary > 0:

        load_boundary(
            current_boundary - 1,
            app_state
        )

# Next Boundary
def next_boundary(event, app_state):

    current_boundary = app_state["current_boundary"]
    saved_files = app_state["saved_files"]

    if current_boundary < len(saved_files) - 1:

        load_boundary(
            current_boundary + 1,
            app_state
        )

# Mesh Generation
def generate_mesh_button(event):

    # --------------------------------------------------------
    # CHECK BOUNDARY
    # --------------------------------------------------------

    if not app_state["boundary_completed"]:
        print("Finish the boundary first!")
        return

    if len(app_state["boundary"]) < 3:
        print("No valid boundary.")
        return

    # --------------------------------------------------------
    # GENERATE MESH
    # --------------------------------------------------------

    generated_mesh = generate_mesh(
        app_state["boundary"]
    )

    # --------------------------------------------------------
    # STORE MESH IN APP STATE
    # --------------------------------------------------------

    app_state["mesh"] = generated_mesh

    app_state["mesh_nodes"] = len(
        app_state["mesh"]
    )

    # --------------------------------------------------------
    # DRAW MESH
    # --------------------------------------------------------

    for x, y in app_state["mesh"]:

        app_state["ax"].scatter(
            x,
            y,
            color="black",
            s=20,
            zorder=5
        )

    # --------------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------------

    update_dashboard(
        app_state["info_ax"],
        app_state["fig"],
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    app_state["fig"].canvas.draw_idle()

    print(
        f"Mesh Generated: "
        f"{app_state['mesh_nodes']} nodes"
    )

# Drone Allocation
def allocate_drone_button(event):

    def allocate_drone_button(event):

        print(">>> ALLOCATE DRONES BUTTON CLICKED")

        if len(app_state["mesh"]) == 0:
            print("Generate the mesh first.")
            return
    # --------------------------------------------------------
    # CHECK MESH
    # --------------------------------------------------------

    if len(app_state["mesh"]) == 0:
        print("Generate the mesh first.")
        return

    # --------------------------------------------------------
    # ASK NUMBER OF DRONES
    # --------------------------------------------------------

    root = Tk()
    root.withdraw()

    number_of_drones = simpledialog.askinteger(
        "Drone Allocation",
        "Enter number of drones:",
        minvalue=1
    )

    root.destroy()

    if number_of_drones is None:
        return

    # --------------------------------------------------------
    # STORE NUMBER OF DRONES
    # --------------------------------------------------------

    app_state["number_of_drones"] = number_of_drones

    # --------------------------------------------------------
    # ALLOCATE MESH NODES
    # --------------------------------------------------------

    app_state["drone_assignments"] = allocate_drones(
        app_state["mesh"],
        app_state["number_of_drones"]
    )

    # --------------------------------------------------------
    # DISPLAY ALLOCATION
    # --------------------------------------------------------

    print("\nDrone Allocation:")

    for drone, nodes in app_state["drone_assignments"].items():

        print(
            f"Drone {drone}: "
            f"{len(nodes)} mesh nodes"
        )

    # --------------------------------------------------------
    # DRAW DRONE ALLOCATION
    # --------------------------------------------------------

    draw_drone_allocation()

# Draw Drone Allocation
def draw_drone_allocation():

    # ============================================================
    # GET DATA FROM APP STATE
    # ============================================================

    ax = app_state["ax"]
    fig = app_state["fig"]

    boundary = app_state["boundary"]
    drone_assignments = app_state["drone_assignments"]

    # ============================================================
    # CLEAR GRAPH
    # ============================================================

    ax.clear()

    # ============================================================
    # WILDFIRE BOUNDARY
    # ============================================================

    xs = [point[0] for point in boundary]
    ys = [point[1] for point in boundary]

    xs_closed = xs + [xs[0]]
    ys_closed = ys + [ys[0]]

    # Fill wildfire region
    ax.fill(
        xs_closed,
        ys_closed,
        color="orange",
        alpha=0.35,
        label="Wildfire Region"
    )

    # Boundary line
    ax.plot(
        xs_closed,
        ys_closed,
        color="red",
        linewidth=2.5,
        label="Wildfire Boundary"
    )

    # ============================================================
    # BOUNDARY VERTICES AND NUMBERS
    # ============================================================

    for i, (x, y) in enumerate(boundary):

        # Vertex
        ax.scatter(
            x,
            y,
            color="blue",
            s=50,
            zorder=20
        )

        # Vertex number
        ax.text(
            x + 0.8,
            y + 0.8,
            str(i + 1),
            fontsize=10,
            color="black",
            zorder=21
        )

    # ============================================================
    # DRAW DRONE MESH NODES
    # ============================================================

    drone_colors = [
        "blue",
        "green",
        "purple",
        "brown",
        "cyan",
        "magenta"
    ]

    for drone_id, nodes in drone_assignments.items():

        color = drone_colors[
            (drone_id - 1) % len(drone_colors)
        ]

        for x, y in nodes:

            ax.scatter(
                x,
                y,
                color=color,
                s=30,
                zorder=10
            )

    # ============================================================
    # GRAPH SETTINGS
    # ============================================================

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

    ax.grid(True)

    # ============================================================
    # LEGEND OUTSIDE THE GRAPH
    # ============================================================

    from matplotlib.lines import Line2D

    legend_elements = []

    for drone_id in drone_assignments:

        color = drone_colors[
            (drone_id - 1) % len(drone_colors)
        ]

        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label=f"Drone {drone_id}",
                markerfacecolor=color,
                markersize=8
            )
        )

    ax.legend(
        handles=legend_elements,
        title="Drone Allocation",
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        fontsize=9
    )

    # ============================================================
    # REDRAW
    # ============================================================

    fig.canvas.draw_idle()

# plan path
def plan_paths_button(event):

    # --------------------------------------------------------
    # CHECK AREA
    # --------------------------------------------------------

    if app_state["current_area"] is None:
        print("Calculate the area first.")
        return

    # --------------------------------------------------------
    # CHECK DRONE ALLOCATION
    # --------------------------------------------------------

    if len(app_state["drone_assignments"]) == 0:
        print("Allocate drones first.")
        return

    # --------------------------------------------------------
    # RESET PATH DATA
    # --------------------------------------------------------

    app_state["drone_paths"] = {}
    app_state["drone_distances"] = {}

    # --------------------------------------------------------
    # CALCULATE PATH FOR EACH DRONE
    # --------------------------------------------------------

    for drone_id, nodes in app_state["drone_assignments"].items():

        path = nearest_neighbor_path(nodes)

        distance = calculate_path_distance(path)

        app_state["drone_paths"][drone_id] = path

        app_state["drone_distances"][drone_id] = distance

    # --------------------------------------------------------
    # DRAW DRONE PATHS
    # --------------------------------------------------------

    draw_drone_paths()

    # --------------------------------------------------------
    # COMPARE PATH PERFORMANCE
    # --------------------------------------------------------

    compare_path_performance()

    # --------------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------------

    update_dashboard(
        app_state["info_ax"],
        app_state["fig"],
        app_state["current_area"],
        app_state["current_dataset"],
        app_state["boundary_points"],
        app_state["mesh_nodes"],
        app_state["drone_assignments"],
        app_state["drone_distances"],
        app_state["performance_results"]
    )

    # --------------------------------------------------------
    # REDRAW
    # --------------------------------------------------------

    app_state["fig"].canvas.draw_idle()

# Drone paths
def draw_drone_paths():

    # --------------------------------------------------------
    # GET DATA FROM APP STATE
    # --------------------------------------------------------

    ax = app_state["ax"]
    fig = app_state["fig"]
    drone_paths = app_state["drone_paths"]

    # --------------------------------------------------------
    # DRAW EACH DRONE PATH
    # --------------------------------------------------------

    for drone_id, path in drone_paths.items():

        if len(path) < 2:
            continue

        x_values = [
            point[0]
            for point in path
        ]

        y_values = [
            point[1]
            for point in path
        ]

        ax.plot(
            x_values,
            y_values,
            linewidth=2,
            label=f"Drone {drone_id} Path",
            zorder=8
        )

    # --------------------------------------------------------
    # REDRAW
    # --------------------------------------------------------

    fig.canvas.draw_idle()

# compare path performance
def compare_path_performance():

    # --------------------------------------------------------
    # CHECK DRONE ALLOCATION
    # --------------------------------------------------------

    if len(app_state["drone_assignments"]) == 0:
        print("Allocate drones first.")
        return

    # --------------------------------------------------------
    # CHECK DRONE PATHS
    # --------------------------------------------------------

    if len(app_state["drone_distances"]) == 0:
        print("Plan the drone paths first.")
        return

    # --------------------------------------------------------
    # CALCULATE SEQUENTIAL DISTANCES
    # --------------------------------------------------------

    sequential_distances = {}

    for drone_id, nodes in app_state["drone_assignments"].items():

        sequential_distances[drone_id] = (
            calculate_sequential_distance(nodes)
        )

    sequential_total = calculate_total_distance(
        sequential_distances
    )

    # --------------------------------------------------------
    # CALCULATE OPTIMIZED DISTANCE
    # --------------------------------------------------------

    optimized_total = calculate_total_distance(
        app_state["drone_distances"]
    )

    # --------------------------------------------------------
    # CALCULATE IMPROVEMENT
    # --------------------------------------------------------

    improvement = 0.0

    if sequential_total > 0:

        improvement = (
            (sequential_total - optimized_total)
            / sequential_total
        ) * 100

    # --------------------------------------------------------
    # STORE PERFORMANCE RESULTS
    # --------------------------------------------------------

    app_state["performance_results"] = {

        "sequential_total": sequential_total,

        "optimized_total": optimized_total,

        "improvement": improvement
    }

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    print("\nPATH COMPARISON")
    print("----------------------------")

    print(
        f"Sequential Distance : "
        f"{sequential_total:.2f} units"
    )

    print(
        f"Nearest Neighbor    : "
        f"{optimized_total:.2f} units"
    )

    print(
        f"Distance Reduction  : "
        f"{improvement:.2f}%"
    )

#buttons Functions
buttons = create_buttons(
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
)
# Window Settings

ax.set_title("Draw Wildfire Boundary")
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xlabel("X Coordinate")
ax.set_ylabel("Y Coordinate")
ax.grid(True)
fig.canvas.toolbar.pack_forget()  # Hide the default toolbar
fig.canvas.mpl_connect("button_press_event",onclick)

# ============================================================
# LOAD ALL SAVED BOUNDARIES
# ============================================================

saved_files = sorted(
    glob.glob("data/*.json"),
    key=lambda x: int(
        re.search(r"\d+", os.path.basename(x)).group()
    )
)

app_state["saved_files"] = saved_files

if len(saved_files) > 0:

    current_boundary = len(saved_files) - 1

    app_state["current_boundary"] = current_boundary

    load_boundary(
        current_boundary,
        app_state
    )
plt.show()