from glob import glob
import re
import os
import matplotlib.pyplot as plt
from Data import Load_Boundary

def plot_boundary(boundary):

    x = [point[0] for point in boundary]
    y = [point[1] for point in boundary]

    # Close the polygon
    x.append(boundary[0][0])
    y.append(boundary[0][1])

    plt.figure(figsize=(8,8))

    # Boundary Line
    plt.plot(x, y,
             color='red',
             linewidth=3,
             label="Wildfire Boundary")

    # Fire Area
    plt.fill(x, y,
             color='orange',
             alpha=0.4,
             label="Fire Area")

    # Boundary Nodes
    plt.scatter(x[:-1], y[:-1],
                color='blue',
                s=50,
                zorder=5,
                label="Boundary Points")

    # Number every boundary point
    for i, point in enumerate(boundary):
        plt.text(point[0]+0.5,
                 point[1]+0.5,
                 str(i))

    plt.title("Drone Swarm Wildfire Monitoring System")

    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")

    plt.legend()

    plt.grid(True)

    plt.axis("equal")

    plt.show()

saved_files = sorted(
    glob.glob("data/*.json"),
    key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group())
)

if len(saved_files) > 0:
    current_boundary = len(saved_files) - 1
    Load_Boundary(current_boundary)