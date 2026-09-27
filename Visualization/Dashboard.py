import math
from matplotlib.patches import FancyBboxPatch

# --------------------------------------------------------
# Dashboard Card
# --------------------------------------------------------

def dashboard_card(info_ax, x, y, w, h, title,
                   facecolor,
                   edgecolor):

    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02",
        linewidth=2,
        facecolor=facecolor,
        edgecolor=edgecolor
    )

    info_ax.add_patch(card)

    info_ax.text(
        x + w/2,
        y + h - 0.035,
        title,
        fontsize=13,
        fontweight="bold",
        ha="center",
        va="center",
        color="#202020"
    )

def update_dashboard(
    info_ax,
    fig,
    area,
    current_dataset,
    boundary_points,
    mesh_nodes,
    drone_assignments,
    drone_distances,
    performance_results
):

    info_ax.clear()
    info_ax.axis("off")
    info_ax.set_xlim(0,1)
    info_ax.set_ylim(0,1)

    # =========================================================
    # DATA
    # =========================================================

    if area is not None:
        hectares = area / 10000
        acres = hectares * 2.47105
        area_value = f"{area:.2f}"
        area_feet = area * 10.7639
    else:
        hectares = 0
        acres = 0
        area_value = "--"
        area_feet = 0

    # =========================================================
    # TITLE
    # =========================================================

    info_ax.text(
        0.50,
        0.975,
        "WILDFIRE ANALYTICS DASHBOARD",
        fontsize=16,
        fontweight="bold",
        ha="center",
        color="#1B1B1B"
    )

    # =====================================================
    # CARD LAYOUT
    # =====================================================

    dashboard_card(
        info_ax,
        0.04,
        0.69,
        0.41,
        0.19,
        "CALCULATED AREA",
        "#FFF8E8",
        "#D9A300"
    )

    dashboard_card(
        info_ax,
        0.55,
        0.69,
        0.41,
        0.19,
        "PROJECT INFO",
        "#EEF6FF",
        "#3E82C4"
    )

    dashboard_card(
        info_ax,
        0.04,
        0.45,
        0.41,
        0.18,
        "UNIT CONVERSION",
        "#F8F8F8",
        "#8C8C8C"
    )

    dashboard_card(
        info_ax,
        0.55,
        0.45,
        0.41,
        0.18,
        "PATH OPTIMIZATION",
        "#FFF2F2",
        "#B22222"
    )

    dashboard_card(
        info_ax,
        0.04,
        0.04,
        0.92,
        0.34,
        "DRONE PERFORMANCE",
        "#F5FFF5",
        "#228B22"
    )

    # =========================================================
    # AREA CARD
    # =========================================================

    info_ax.text(
        0.25,
        0.785,
        f"{area_value} m²",
        fontsize=11,
        ha="center"
    )

    # =========================================================
    # PROJECT CARD
    # =========================================================

    info_ax.text(
        0.75,
        0.79,
        f"Dataset : {current_dataset}",
        fontsize=11,
        ha="center"
    )

    info_ax.text(
        0.75,
        0.755,
        f"Boundary Points : {boundary_points}",
        fontsize=11,
        ha="center"
    )

    info_ax.text(
        0.75,
        0.72,
        f"Mesh Nodes : {mesh_nodes}",
        fontsize=11,
        ha="center"
    )

    # =========================================================
    # UNIT CONVERSION
    # =========================================================

    info_ax.text(
        0.25,
        0.55,
        f"Square feet : {area_feet:.2f}",
        fontsize=11,
        ha="center"
    )

    info_ax.text(
        0.25,
        0.52,
        f"Hectares : {hectares:.4f}",
        fontsize=11,
        ha="center"
    )

    info_ax.text(
        0.25,
        0.49,
        f"Acres : {acres:.4f}",
        fontsize=11,
        ha="center"
    )

    # =========================================================
    # PATH OPTIMIZATION
    # =========================================================

    if performance_results:

        info_ax.text(
            0.75,
            0.55,
            f"Baseline : {performance_results['sequential_total']:.2f}",
            fontsize=11,
            ha="center"
        )

        info_ax.text(
            0.75,
            0.52,
            f"Optimized : {performance_results['optimized_total']:.2f}",
            fontsize=11,
            ha="center"
        )

        info_ax.text(
            0.75,
            0.49,
            f"Reduction : {performance_results['improvement']:.2f}%",
            fontsize=11,
            ha="center"
        )

    # =========================================================
    # DRONE PERFORMANCE
    # =========================================================

    if drone_distances:

        drones = list(drone_distances.items())
        n=math.ceil(len(drones)/2)

        left = drones[:n]
        right = drones[n:]

        y = 0.24
        info_ax.text(
            0.03,
            0.29,
            "Drones",
            fontsize=10
        )
        info_ax.text(
            0.16,
            0.29,
            "Nodes",
            fontsize=10
        )
        info_ax.text(
            0.28,
            0.29,
            "Distances",
            fontsize=10
        )
        for drone_id, distance in left:

            nodes = len(drone_assignments.get(drone_id, []))

            info_ax.text(
                0.06,
                y,
                f"D{drone_id}",
                fontsize=8,
            )

            info_ax.text(
                0.15,
                y,
                f"{nodes} Nodes",
                fontsize=8
            )

            info_ax.text(
                0.31,
                y,
                f"{distance:.2f}",
                fontsize=8
            )

            y -= 0.05

        y = 0.24
        info_ax.text(
            0.53,
            0.29,
            "Drone",
            fontsize=10
        )
        info_ax.text(
            0.66,
            0.29,
            "Nodes",
            fontsize=10
        )
        info_ax.text(
            0.78,
            0.29,
            "Distances",
            fontsize=10
        )
        for drone_id, distance in right:

            nodes = len(drone_assignments.get(drone_id, []))

            info_ax.text(
                0.56,
                y,
                f"D{drone_id}",
                fontsize=8,
            )

            info_ax.text(
                0.65,
                y,
                f"{nodes} Nodes",
                fontsize=8
            )

            info_ax.text(
                0.81,
                y,
                f"{distance:.2f}",
                fontsize=8
            )

            y -= 0.05

    fig.canvas.draw_idle()