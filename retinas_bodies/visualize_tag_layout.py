from re import I
import numpy as np
import math
from retinas.pose import Pose
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(description='Visualize apriltag layout on a physical link in 3D.\n \
    Usage: python visualize_tag_layout.py --tag=<TAG_NUMBER>')
parser.add_argument('--tag', nargs='?', default=1, type=int)
args = parser.parse_args()
TAG_NUM = args.tag

LINK_RADIUS = 0.034/2
TAG_Z = 0.05575
TAG_LENGTH = 0.017
TAG_HALF_LENGTH = TAG_LENGTH / 2

def get_tag_points():
    base_pose = Pose(math.pi/2, 0, 0, 0, -LINK_RADIUS, 0)
    rotate_face = Pose(0,0,math.pi/2,0,0,0)
    tag_centers = np.zeros((12, 3))
    tag_patches = [] # tag corner points
    TAG_POINTS = np.array([
            [-TAG_HALF_LENGTH,  TAG_HALF_LENGTH, 0, 1],
            [ TAG_HALF_LENGTH,  TAG_HALF_LENGTH, 0, 1],
            [ TAG_HALF_LENGTH, -TAG_HALF_LENGTH, 0, 1],
            [-TAG_HALF_LENGTH, -TAG_HALF_LENGTH, 0 ,1]])
    tag_center = np.array([0, 0, 0, 1])

    for side in range(6):
        # transformation matrices from tag frame coords to link frame coords
        degrees = side * -60
        radians = math.radians(degrees)
        rotation = Pose(0,0,radians, 0,0,0)
        p = rotation @ base_pose
        T0 = Pose(p.rvec, (p.tvec[0], p.tvec[1], p.tvec[2]-TAG_Z)) @ rotate_face
        T1 = Pose(p.rvec, (p.tvec[0], p.tvec[1], p.tvec[2]+TAG_Z)) @ rotate_face

        # get tag center positions
        tag0 = np.dot(T0.matrix, tag_center)[:3]*100
        tag1 = np.dot(T1.matrix, tag_center)[:3]*100
        tag_centers[side, :] = tag0
        tag_centers[side + 6, :] = tag1

        # get tag corner positions
        tag0_corners = [np.dot(T0.matrix, TAG_POINTS[i, :])[:3]*100 for i in range(4)]
        tag1_corners = [np.dot(T1.matrix, TAG_POINTS[i, :])[:3]*100 for i in range(4)]
        tag_patches.append(tag0_corners)
        tag_patches.append(tag1_corners)
        
    return tag_centers, tag_patches


if __name__ == '__main__':
    tag_centers, tag_patches = get_tag_points()
    
    fig = plt.figure(figsize=(15, 15))
    ax = fig.add_subplot(111, projection='3d')

    # draw tag center dots
    for i in range(12):
        t = tag_centers[i]
        ax.scatter(t[0], t[1], t[2], color='coral' if i < 6 else 'dodgerblue')
        ax.text(t[0], t[1], t[2], str(TAG_NUM * 12 + i), size=15, zorder=1, color='k')
    
    # draw the hexagonal prism formed by them for better visualization
    ax.add_collection3d(Poly3DCollection([tag_centers[:6, :], tag_centers[6:, :]], edgecolor='gray', linestyles='--', linewidths=1, alpha=0))
    for i in range(6):
        ax.plot3D([tag_centers[i, 0], tag_centers[i + 6, 0]], 
                [tag_centers[i, 1], tag_centers[i + 6, 1]], 
                [tag_centers[i, 2], tag_centers[i + 6, 2]],
                ls='--', c='gray', alpha=0.5)

    # draw link local frame axes
    ax.text(0, 0, 1, 'z', size=15, zorder=1, color='blue') 
    ax.quiver(0, 0, 0, 0, 0, 1, color = 'blue', alpha = .8, lw = 1)
    ax.text(1, 0, 0, 'x', size=15, zorder=1, color='red') 
    ax.quiver(0, 0, 0, 1, 0, 0, color = 'red', alpha = .8, lw = 1)
    ax.text(0, 1, 0, 'y', size=15, zorder=1, color='green')
    ax.quiver(0, 0, 0, 0, 1, 0, color = 'green', alpha = .8, lw = 1)

    # label srv0 and srv1 ends
    ax.text(0, 0, -9, 'Srv0', size=20, zorder=1, color='k')
    ax.text(0, 0, 9, 'Srv1', size=20, zorder=1, color='k')

    # draw apriltags
    ax.add_collection3d(Poly3DCollection(tag_patches, linewidths=1, alpha=0.2))

    # draw corner dots on apriltags
    corner_colors = ['red', 'orange', 'yellow', 'green']
    for i in range(len(tag_patches)):
        t = tag_patches[i]
        for j in range(len(t)):
            c = t[j]
            ax.scatter(c[0], c[1], c[2], color=corner_colors[j], label=f"corner {j}" if i==0 else '')

    # plot config
    ax.set_xlabel('x (cm)')
    ax.set_ylabel('y (cm)')
    ax.set_zlabel('z (cm)')
    ax.set_title(f'Apriltags layout on Link P{TAG_NUM}')
    for d in 'xyz':
        getattr(ax, f'set_{d}lim')(-6, 6)
    ax.legend()
    ax.grid(False)
    plt.show()