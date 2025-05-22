import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class Tetrahedron:
    def __init__(self):
        # Vertices of a regular tetrahedron
        self.vertices = np.array([
            [1, 1, 1],
            [-1, -1, 1],
            [-1, 1, -1],
            [1, -1, -1]
        ]) / np.sqrt(3)
        # Edges between the vertices
        self.edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    def topple(self):
        # Determine the axis of rotation for toppling (edge between vertices 0 and 1)
        edge_vector = self.vertices[1] - self.vertices[0]
        axis_of_rotation = edge_vector / np.linalg.norm(edge_vector)

        # Angle of rotation
        theta = np.arccos(1 / np.sqrt(3))  # Angle for rotating to the next face

        # Create rotation matrix
        c, s = np.cos(theta), np.sin(theta)
        t = 1 - c
        x, y, z = axis_of_rotation
        rotation_matrix = np.array([
            [t*x*x + c,   t*x*y - z*s, t*x*z + y*s],
            [t*x*y + z*s, t*y*y + c,   t*y*z - x*s],
            [t*x*z - y*s, t*y*z + x*s, t*z*z + c]
        ])

        # Rotate vertices
        self.vertices = np.dot(self.vertices - self.vertices[0], rotation_matrix.T) + self.vertices[0]


def plot_tetrahedron(tetrahedron, title="Tetrahedron"):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for edge in tetrahedron.edges:
        xs, ys, zs = zip(*tetrahedron.vertices[list(edge)])
        ax.plot(xs, ys, zs, color='b')
    
    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()

def main():
    # Create a tetrahedron
    tetra = Tetrahedron()

    # Plot before toppling
    plot_tetrahedron(tetra, "Tetrahedron Before Topple")

    # Topple the tetrahedron
    tetra.topple()

    # Plot after toppling
    plot_tetrahedron(tetra, "Tetrahedron After Topple")

if __name__ == "__main__":
    main()