import math
import numpy as np

from retinas.pose import Pose
import retinas.objects as objects


LINK_RADIUS = 0.034/2
TAG_Z = 0.05575
TAG_LENGTH = 0.017


def get_link_object(link_id):

    tag0_id = link_id*12

    base_pose = Pose(math.pi/2, 0, 0, 0, -LINK_RADIUS, 0)

    rotate_face = Pose(0,0,math.pi/2,0,0,0)

    tag_dict = {}    

    for side in range(6):
        degrees = side * -60
        radians = math.radians(degrees)
        rotation = Pose(0,0,radians, 0,0,0)

        p = rotation @ base_pose
        tag_dict[tag0_id+side+0] = Pose(p.rvec, (p.tvec[0], p.tvec[1], p.tvec[2]-TAG_Z)) @ rotate_face
        tag_dict[tag0_id+side+6] = Pose(p.rvec, (p.tvec[0], p.tvec[1], p.tvec[2]+TAG_Z)) @ rotate_face
    
    TAG_HALF_LENGTH = TAG_LENGTH / 2

    TAG_POINTS = np.array([
        [-TAG_HALF_LENGTH,  TAG_HALF_LENGTH, 0, 1],
        [ TAG_HALF_LENGTH,  TAG_HALF_LENGTH, 0, 1],
        [ TAG_HALF_LENGTH, -TAG_HALF_LENGTH, 0, 1],
        [-TAG_HALF_LENGTH, -TAG_HALF_LENGTH, 0 ,1],
    ])

    point_dict = {}

    for tag_id in tag_dict:
        for a in range(4):
            point_dict[tag_id, a] = (tag_dict[tag_id].matrix @ TAG_POINTS[a].T).T[:3]


    return objects.RetinaBody(f"Link {link_id}", point_dict)


if __name__ == '__main__':

    import plotly.graph_objects as go

    point_dict = get_link_object(0).point_dict

    corner_colors = [
        (255,255,0), # Y
        (255,0,0),   # R
        (0,255,0),   # G
        (0,0,255)    # B
    ]
    xs = []
    ys = []
    zs = []
    cs = []
    names = []
    for key, point in point_dict.items():
        print(point)
        xs.append(point[0])
        ys.append(point[1])
        zs.append(point[2])
        cs.append(corner_colors[key[1]]) #key[1]
        names.append("{}:{}".format(key[0], key[1]))


    fig = go.Figure(data=[go.Scatter3d(x=np.array(xs), y=np.array(ys), z=np.array(zs), text=names,
                                       mode='markers',marker=dict(size=8, color=cs))])
    fig.show()



"""

import math
import numpy as np
from camera_tracking.pose import *
import plotly.graph_objects as go

LINK_RADIUS = 0.034/2
TAG_Z = 0.05575
LINK_TAG_LENGTH = 0.017    # meters

LINK_TAG_POSES = {}

base_rvec, base_tvec = (math.pi/2, 0, 0), [[0], [-LINK_RADIUS], [0]]
base_pose = get_4x4_from_vectors(np.array(base_rvec), np.array(base_tvec))

rotate_face = get_4x4_from_vectors(np.array((0, 0., 0)), np.array([[0], [0], [0]]))

base_pose = rotate_face @ base_pose

for side in range(6):
    degrees = side * -60   # degrees
    radians = math.radians(degrees)
    rotation_transform = get_4x4_from_vectors(np.array([0, 0, radians]),
                                              np.array([[0, 0, 0]]).T)

    LINK_TAG_POSES[side+0] = rotation_transform @ base_pose
    LINK_TAG_POSES[side+0][2][3] += -TAG_Z
    LINK_TAG_POSES[side+6] = rotation_transform @ base_pose
    LINK_TAG_POSES[side+6][2][3] += TAG_Z

LINK_TAG_HALF_LENGTH = LINK_TAG_LENGTH / 2

LINK_TAG_FORMAT = np.array([[[-LINK_TAG_HALF_LENGTH, LINK_TAG_HALF_LENGTH, 0,1]],
                               [[LINK_TAG_HALF_LENGTH, LINK_TAG_HALF_LENGTH, 0,1]],
                               [[LINK_TAG_HALF_LENGTH, -LINK_TAG_HALF_LENGTH, 0,1]],
                               [[-LINK_TAG_HALF_LENGTH, -LINK_TAG_HALF_LENGTH, 0,1]]])

LINK_POINTS = {}

reflect_permute = [1,2,3,0]

for tag_number in LINK_TAG_POSES:
    for a in range(4):
        LINK_POINTS[tag_number, reflect_permute[a]] = LINK_TAG_POSES[tag_number] @ LINK_TAG_FORMAT[a].T

# print(LINK_TAG_POSES[0] @ np.array([[0],[0],[0],[1]]))
# print(LINK_TAG_POSES[1] @ np.array([[0],[0],[0],[1]]))
# print(LINK_TAG_POSES[2] @ np.array([[0],[0],[0],[1]]))
# print(LINK_TAG_POSES[3] @ np.array([[0],[0],[0],[1]]))
# print(LINK_TAG_POSES[4] @ np.array([[0],[0],[0],[1]]))
# print(LINK_TAG_POSES[5] @ np.array([[0],[0],[0],[1]]))


def get_link_tag_info(tag_id, corner):
    return tag_id//12, tag_id%12, LINK_POINTS[tag_id%12, corner][:3, 0]


if __name__ == '__main__':
    corner_colors = [
        (255,255,0), # Y
        (255,0,0),   # R
        (0,255,0),   # G
        (0,0,255)    # B
    ]
    xs = []
    ys = []
    zs = []
    cs = []
    names = []
    for key, point in LINK_POINTS.items():
        print(point)
        xs.append(point[0][0])
        ys.append(point[1][0])
        zs.append(point[2][0])
        cs.append(corner_colors[key[1]]) #key[1]
        names.append("{}:{}".format(key[0], key[1]))


    fig = go.Figure(data=[go.Scatter3d(x=np.array(xs), y=np.array(ys), z=np.array(zs), text=names,
                                       mode='markers',marker=dict(size=8, color=cs))])
    fig.show()

"""