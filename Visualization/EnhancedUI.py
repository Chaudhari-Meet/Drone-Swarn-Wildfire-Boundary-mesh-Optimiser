"""
Enhanced UI for Drone Swarm Wildfire Response System.
Integrates data sources, drone simulation, risk analysis, and firefighter routing.
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)


def run_interactive_ui(system):
    """
    Launch interactive UI with the application system integrated.
    
    Args:
        system: WildfireResponseSystem instance
    """
    
    logger.info("Launching interactive UI...")
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "DRONE SWARM WILDFIRE RESPONSE & ROUTE OPTIMIZATION SYSTEM",
        fontsize=16,
        fontweight="bold",
        y=0.98
    )
    
    plt.subplots_adjust(
        left=0.05, right=0.95, top=0.93, bottom=0.15,
        hspace=0.4, wspace=0.3
    )
    
    # Create subplots
    ax_map = fig.add_subplot(1, 2, 1)
    ax_dashboard = fig.add_subplot(1, 2, 2)
    ax_dashboard.axis("off")
    
    # Button configuration
    buttons_config = [
        {"label": "1. Load Fire Data", "pos": [0.10, 0.05], "func": lambda e: on_load_fire_data(system, ax_map, ax_dashboard, fig)},
        {"label": "2. Generate Mesh", "pos": [0.25, 0.05], "func": lambda e: on_generate_mesh(system, ax_map, ax_dashboard, fig)},
        {"label": "3. Allocate Drones", "pos": [0.40, 0.05], "func": lambda e: on_allocate_drones(system, ax_map, ax_dashboard, fig)},
        {"label": "4. Optimize Paths", "pos": [0.55, 0.05], "func": lambda e: on_optimize_paths(system, ax_map, ax_dashboard, fig)},
        {"label": "5. Analyze Risk", "pos": [0.70, 0.05], "func": lambda e: on_analyze_risk(system, ax_map, ax_dashboard, fig)},
        {"label": "Full Mission", "pos": [0.85, 0.05], "func": lambda e: on_full_mission(system, ax_map, ax_dashboard, fig)},
    ]
    
    # Create buttons
    for config in buttons_config:
        ax_btn = fig.add_axes(config["pos"] + [0.12, 0.04])
        btn = Button(ax_btn, config["label"], color='#F3F3F3', hovercolor='#CFE8FF')
        btn.on_clicked(config["func"])
    
    # Initial dashboard
    update_dashboard(system, ax_dashboard)
    
    # Map initialization
    ax_map.set_xlim(-10, 110)
    ax_map.set_ylim(-10, 110)
    ax_map.set_xlabel("X Coordinate / Longitude")
    ax_map.set_ylabel("Y Coordinate / Latitude")
    ax_map.grid(True, alpha=0.3)
    ax_map.set_title("Wildfire Map & Drone Visualization")
    
    plt.show()


def update_dashboard(system, ax_dashboard):
    """Update dashboard with current system status."""
    ax_dashboard.clear()
    ax_dashboard.axis("off")
    ax_dashboard.set_xlim(0, 10)
    ax_dashboard.set_ylim(0, 10)
    
    status = system.get_system_status()
    
    # Title
    ax_dashboard.text(
        5, 9.5, "SYSTEM STATUS & DASHBOARD",
        ha="center", va="top", fontsize=14, fontweight="bold"
    )
    
    # Status line
    status_text = f"Status: {status['status']}"
    if status['data_source']:
        status_text += f" | Source: {status['data_source']}"
    
    ax_dashboard.text(5, 8.8, status_text, ha="center", fontsize=10)
    
    # Fire information
    y_pos = 8.2
    ax_dashboard.text(0.5, y_pos, "FIRE INFORMATION", fontsize=11, fontweight="bold")
    y_pos -= 0.5
    
    info_lines = [
        f"Observations: {status['fire_observations']}",
        f"Area: {status['fire_area_hectares']:.2f} ha",
        f"Boundary Points: {len(system.fire_boundary.boundary_points) if system.fire_boundary else 0}",
    ]
    
    for line in info_lines:
        ax_dashboard.text(1.0, y_pos, line, fontsize=9)
        y_pos -= 0.4
    
    # Mesh information
    y_pos -= 0.3
    ax_dashboard.text(0.5, y_pos, "MESH & COVERAGE", fontsize=11, fontweight="bold")
    y_pos -= 0.5
    
    info_lines = [
        f"Mesh Nodes: {status['mesh_nodes']}",
        f"Drones: {status['drones']}",
        f"Assignments: {status['drone_assignments']}",
    ]
    
    for line in info_lines:
        ax_dashboard.text(1.0, y_pos, line, fontsize=9)
        y_pos -= 0.4
    
    # Performance
    y_pos -= 0.3
    ax_dashboard.text(0.5, y_pos, "PERFORMANCE", fontsize=11, fontweight="bold")
    y_pos -= 0.5
    
    info_lines = [
        f"Total Distance: {status['optimized_distance']:.2f} m",
        f"Improvement: {status['improvement_percent']:.2f}%",
        f"Risk Zones: {status['risk_zones']}",
    ]
    
    for line in info_lines:
        ax_dashboard.text(1.0, y_pos, line, fontsize=9)
        y_pos -= 0.4
    
    # Detections
    y_pos -= 0.3
    ax_dashboard.text(0.5, y_pos, "DETECTIONS", fontsize=11, fontweight="bold")
    y_pos -= 0.5
    
    detections_text = f"Animals/Persons: {status['detections']}"
    ax_dashboard.text(1.0, y_pos, detections_text, fontsize=9)


def on_load_fire_data(system, ax_map, ax_dashboard, fig):
    """Load fire data handler."""
    logger.info("Loading fire data...")
    
    if system.load_fire_data():
        if system.process_fire_data():
            # Draw fire boundary
            if system.fire_boundary:
                boundary = system.fire_boundary.boundary_points
                xs = [p[0] for p in boundary] + [boundary[0][0]]
                ys = [p[1] for p in boundary] + [boundary[0][1]]
                
                ax_map.clear()
                ax_map.fill(xs, ys, color="orange", alpha=0.35, label="Fire Zone")
                ax_map.plot(xs, ys, "r-", linewidth=2, label="Fire Boundary")
                
                # Plot observations
                for obs in system.fire_observations[:50]:
                    ax_map.scatter(obs.latitude, obs.longitude, c="red", s=20, alpha=0.6)
                
                ax_map.set_xlim(min(xs) - 5, max(xs) + 5)
                ax_map.set_ylim(min(ys) - 5, max(ys) + 5)
                ax_map.legend()
                ax_map.grid(True, alpha=0.3)
            
            update_dashboard(system, ax_dashboard)
            fig.canvas.draw_idle()
            logger.info("Fire data loaded successfully")
        else:
            logger.error("Failed to process fire data")
    else:
        logger.error("Failed to load fire data")


def on_generate_mesh(system, ax_map, ax_dashboard, fig):
    """Generate mesh handler."""
    logger.info("Generating mesh...")
    
    if system.generate_mesh_coverage(spacing=5):
        # Redraw map with mesh
        if system.fire_boundary:
            boundary = system.fire_boundary.boundary_points
            xs = [p[0] for p in boundary] + [boundary[0][0]]
            ys = [p[1] for p in boundary] + [boundary[0][1]]
            
            ax_map.clear()
            ax_map.fill(xs, ys, color="orange", alpha=0.35)
            ax_map.plot(xs, ys, "r-", linewidth=2)
            
            # Plot mesh nodes
            for node in system.mesh_nodes:
                ax_map.scatter(node[0], node[1], c="green", s=30, marker="+")
            
            ax_map.legend(["Mesh Nodes"])
            ax_map.grid(True, alpha=0.3)
        
        update_dashboard(system, ax_dashboard)
        fig.canvas.draw_idle()
        logger.info(f"Mesh generated: {len(system.mesh_nodes)} nodes")
    else:
        logger.error("Failed to generate mesh")


def on_allocate_drones(system, ax_map, ax_dashboard, fig):
    """Allocate drones handler."""
    logger.info("Allocating drones...")
    
    if system.allocate_drones(num_drones=10):
        # Redraw with drone assignments
        if system.fire_boundary:
            boundary = system.fire_boundary.boundary_points
            xs = [p[0] for p in boundary] + [boundary[0][0]]
            ys = [p[1] for p in boundary] + [boundary[0][1]]
            
            ax_map.clear()
            ax_map.fill(xs, ys, color="orange", alpha=0.35)
            ax_map.plot(xs, ys, "r-", linewidth=2)
            
            # Plot assigned nodes by drone with different colors
            colors = ['blue', 'green', 'purple', 'brown', 'cyan', 'magenta', 'yellow', 'pink', 'orange', 'olive']
            
            for drone_id, nodes in system.drone_assignments.items():
                color = colors[(drone_id - 1) % len(colors)]
                for node in nodes:
                    ax_map.scatter(node[0], node[1], c=color, s=40, marker="o", alpha=0.7)
            
            ax_map.grid(True, alpha=0.3)
        
        update_dashboard(system, ax_dashboard)
        fig.canvas.draw_idle()
        logger.info(f"Drones allocated: {len(system.drones)}")
    else:
        logger.error("Failed to allocate drones")


def on_optimize_paths(system, ax_map, ax_dashboard, fig):
    """Optimize paths handler."""
    logger.info("Optimizing paths...")
    
    if system.optimize_drone_paths(use_two_opt=True):
        # Draw paths
        if system.fire_boundary and system.drone_paths:
            boundary = system.fire_boundary.boundary_points
            xs = [p[0] for p in boundary] + [boundary[0][0]]
            ys = [p[1] for p in boundary] + [boundary[0][1]]
            
            ax_map.clear()
            ax_map.fill(xs, ys, color="orange", alpha=0.35)
            ax_map.plot(xs, ys, "r-", linewidth=2)
            
            # Plot paths
            colors = ['blue', 'green', 'purple', 'brown', 'cyan', 'magenta', 'yellow', 'pink', 'orange', 'olive']
            
            for drone_id, path in system.drone_paths.items():
                if len(path) > 1:
                    color = colors[(drone_id - 1) % len(colors)]
                    path_x = [p[0] for p in path]
                    path_y = [p[1] for p in path]
                    ax_map.plot(path_x, path_y, color=color, linewidth=1.5, alpha=0.7)
            
            ax_map.grid(True, alpha=0.3)
        
        update_dashboard(system, ax_dashboard)
        fig.canvas.draw_idle()
        logger.info("Paths optimized successfully")
    else:
        logger.error("Failed to optimize paths")


def on_analyze_risk(system, ax_map, ax_dashboard, fig):
    """Analyze risk handler."""
    logger.info("Analyzing risk...")
    
    if system.analyze_risk():
        # Draw risk zones
        if system.risk_zones and system.fire_boundary:
            boundary = system.fire_boundary.boundary_points
            xs = [p[0] for p in boundary] + [boundary[0][0]]
            ys = [p[1] for p in boundary] + [boundary[0][1]]
            
            ax_map.clear()
            ax_map.fill(xs, ys, color="orange", alpha=0.35)
            ax_map.plot(xs, ys, "r-", linewidth=2)
            
            # Draw risk zones
            for zone in system.risk_zones:
                circle = plt.Circle(zone.center, zone.radius_m / 1000, 
                                   color='red', alpha=0.2 if zone.risk_level.value == "safe" else 0.5)
                ax_map.add_patch(circle)
            
            ax_map.grid(True, alpha=0.3)
        
        update_dashboard(system, ax_dashboard)
        fig.canvas.draw_idle()
        logger.info(f"Risk analysis complete: {len(system.risk_zones)} zones")
    else:
        logger.error("Failed to analyze risk")


def on_full_mission(system, ax_map, ax_dashboard, fig):
    """Run full mission handler."""
    logger.info("Running full mission...")
    
    if system.run_full_mission(num_drones=10, mesh_spacing=5):
        # Final visualization
        if system.fire_boundary and system.drone_paths:
            boundary = system.fire_boundary.boundary_points
            xs = [p[0] for p in boundary] + [boundary[0][0]]
            ys = [p[1] for p in boundary] + [boundary[0][1]]
            
            ax_map.clear()
            ax_map.fill(xs, ys, color="orange", alpha=0.35)
            ax_map.plot(xs, ys, "r-", linewidth=2.5)
            
            # Plot final paths
            colors = ['blue', 'green', 'purple', 'brown', 'cyan', 'magenta', 'yellow', 'pink', 'orange', 'olive']
            
            for drone_id, path in system.drone_paths.items():
                if len(path) > 1:
                    color = colors[(drone_id - 1) % len(colors)]
                    path_x = [p[0] for p in path]
                    path_y = [p[1] for p in path]
                    ax_map.plot(path_x, path_y, color=color, linewidth=2, alpha=0.8)
            
            # Plot detections
            for detection in system.detections:
                ax_map.scatter(detection.latitude, detection.longitude, 
                             c="yellow", s=100, marker="*", edgecolors="black")
            
            ax_map.grid(True, alpha=0.3)
            ax_map.set_title("MISSION COMPLETE - All Systems")
        
        update_dashboard(system, ax_dashboard)
        
        # Export report
        system.export_report()
        
        fig.canvas.draw_idle()
        logger.info("Full mission completed successfully!")
    else:
        logger.error("Mission execution failed")
