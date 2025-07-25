import os
from math import sqrt
import numpy as np
import cv2
import pupil_apriltags as dt_apriltags


######################
## GLOBAL CONSTANTS ##
######################


# Define world tags and their locations in world frame
WORLD_TAGS = {
    575: np.array([0, 0, 0]),
    576: None,
    577: None,
    578: np.array([0.3, 0, 0]),
    579: None,
    580: None,
    581: np.array([0, 0.3, 0]),
    582: None,
    583: None,
    584: None,
    585: None,
    586: np.array([0.3, 0.3, 0])
}

# Define link and the attached 12 apriltags in link frame
H = 0.010 # 10cm
R = 0.02 # 2cm
R_prime = sqrt(3) * R

# Define link tags and their lcoations in link frame
# LINK_TAGS = {
#     # UPPER EDGE TAGS
#     1: [R, 0, H/2],
#     2: [R/2, R_prime/2, H/2],
#     3: [-R/2, R_prime/2, H/2],
#     4: [-R, 0, H/2],
#     5: [-R/2, -R_prime/2, H/2],
#     6: [R/2, -R_prime/2, H/2],
#     # BOTTOM EDGE TAGS
#     7: [R, 0, -H/2],
#     8: [R/2, R_prime/2, -H/2],
#     9: [-R/2, R_prime/2, -H/2],
#     10: [-R, 0, -H/2],
#     11: [-R/2, -R_prime/2, -H/2],
#     12: [R/2, -R_prime/2, -H/2],
# }

world_tag_size = 0.055 # 55mm
april_tag_size = 0.017

# Tag Corner Coordinates in Tag Frame
obj_pts_square = np.array([
    [-april_tag_size/2, -april_tag_size/2, 0],
    [ april_tag_size/2, -april_tag_size/2, 0],
    [-april_tag_size/2,  april_tag_size/2, 0],
    [ april_tag_size/2,  april_tag_size/2, 0],
])

#############
## CLASSES ##
#############


class Tag:
    def __init__(self, frame, tag, R_camera_to_world, t_camera_to_world, tag_size):
        # self.mtx = mtx
        # self.dist = dist
        self.frame = frame
        self.tag = tag
        self.R_camera_to_world = R_camera_to_world
        self.t_camera_to_world = t_camera_to_world
        self.tag_size = tag_size
        self.tf_tag_corners = np.array([
        [-tag_size/2, -tag_size/2, 0],
        [ tag_size/2, -tag_size/2, 0],
        [ tag_size/2,  tag_size/2, 0],
        [-tag_size/2,  tag_size/2, 0]
        ])
        
        #frame, tag, R_avg_camera_to_world, t_avg_camera_to_world, tag_size
    
    # def draw_original_tag_boundary(self):
    #     # Draw detected corners without transformation for comparison
    #     corners = self.tag.corners.astype(int)
    #     cv2.polylines(self.frame, [corners], True, (0,255,0), 2)

    #     return None
    
    def draw_tag_boundary(self):

        # Tag Frame to Camera Frame Transformation for Corners
        cf_tag_corners, _ = cv2.projectPoints(self.tf_tag_corners, self.tag.pose_R, self.tag.pose_t, mtx, dist)
        cf_tag_corners = cf_tag_corners.reshape(-1, 2).astype(int)

        # Draw the tag boundary in green
        for i in range(4):
            cv2.line(self.frame, tuple(cf_tag_corners[i]), tuple(cf_tag_corners[(i+1)%4]), (255, 0, 0), 2)

        return cf_tag_corners # tag corners in camera frame

    def draw_axes(self):

         # Define the 3D points for XYZ axes
        axis_length = 0.05  
        obj_pts_axes = np.array([
            [0, 0, 0],         
            [axis_length, 0, 0],  
            [0, axis_length, 0],  
            [0, 0, axis_length]   
        ])

        # Tag Frame to Camera Frame Transformation for Axes
        img_pts_axes, _ = cv2.projectPoints(obj_pts_axes, self.tag.pose_R, self.tag.pose_t, mtx, dist)
        img_pts_axes = img_pts_axes.reshape(-1, 2).astype(int)

        # Draw the transformed XYZ axes on to the Camera Frame
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
        for i in range(1, 4):
            cv2.line(self.frame, tuple(img_pts_axes[0]), tuple(img_pts_axes[i]), colors[i-1], 2)

        return None

    def draw_linkbody(self, link_tag_id, servo_extension = 0):
        
        # if link frame id is from 0 to 5 -> UPPER
        if (0 <= link_tag_id <= 5):
            linkbody_pts = np.array([
            [0.047, 0, 0.016], # centroid
            [-(0.085+servo_extension), 0, 0.016] # upper tip (servo unextended) 
            ])
        # if link frame id is from 6 to 11 -> BOTTOM
        elif(6 <= link_tag_id <= 11):
            linkbody_pts = np.array([
            [-0.047, 0, 0.016], # centroid
            [0.085+servo_extension, 0, 0.016] # bottom tip (servo unextended) 
            ])

        cf_linkbody_pts, _ = cv2.projectPoints(linkbody_pts, self.tag.pose_R, self.tag.pose_t, mtx, dist)
        cf_linkbody_pts = cf_linkbody_pts.reshape(-1, 2).astype(int)
        
        print("Shape of cf_linkbody_pts:", cf_linkbody_pts.shape)

        for pt in cf_linkbody_pts:
            neon_green = (57, 255, 20)
            # Draw the transformed centroid and tips! as a circle
            cv2.circle(self.frame, tuple(pt), 5, neon_green, -1)

        return cf_linkbody_pts

    def compute_tranformation(self):

        # initialization
        R_tag_to_world = None
        t_tag_to_world = None

        if self.R_camera_to_world is not None and self.t_camera_to_world is not None:
            # Will obtain tag_to_world transformation
            # To compute the tag's pose in world frame

            R_tag_to_world = np.dot(self.R_camera_to_world, self.tag.pose_R)
            t_tag_to_world = np.dot(self.R_camera_to_world, self.tag.pose_t) + self.t_camera_to_world

            print("R_tag_to_world:", R_tag_to_world)
            print("t_tag_to_world:", t_tag_to_world)

            if np.any(np.isnan(R_tag_to_world)) or np.any(np.isnan(t_tag_to_world)):
                print("Warning: Transformation matrices contain NaN values!")

        return R_tag_to_world, t_tag_to_world


    def project_to_world(self, R_tag_to_world, t_tag_to_world, cf_tag_corners, cf_linkbody_pts = None, link_tag_id = None, servo_extension = 0):

        # Only execute linkbody related code if both camera_linkbody_pts and link_tag_id are provided
        if cf_linkbody_pts is not None and link_tag_id is not None:

            # if link frame id is from 0 to 5 -> UPPER
            if (0 <= link_tag_id <= 5):
                linkbody_pts = np.array([
                [0.047, 0, 0.016], # centroid
                [-(0.085+servo_extension), 0, 0.016] # upper tip (servo unextended) 
                ])
            # if link frame id is from 6 to 11 -> BOTTOM
            elif(6 <= link_tag_id <= 11):
                linkbody_pts = np.array([
                [-0.047, 0, 0.016], # centroid
                [0.085+servo_extension, 0, 0.016] # bottom tip (servo unextended) 
                ])

            linkbody_pts_world = np.dot(R_tag_to_world, linkbody_pts.T).T + t_tag_to_world.T

            centroid_world = linkbody_pts_world[0]
            tip_world = linkbody_pts_world[1]

            centroid_str = f"Centroid: X: {centroid_world[0]*100:.1f}, Y: {centroid_world[1]*100:.1f}, Z: {centroid_world[2]*100:.1f}"
            tip_str = f"Tip: X: {tip_world[0]*100:.1f}, Y: {tip_world[1]*100:.1f}, Z: {tip_world[2]*100:.1f}"

            # centroid and tip points in camera frame
            centroid_camera = cf_linkbody_pts[0]
            tip_camera = cf_linkbody_pts[1]

            # display world coordinates on the camera frame cordinates (since our view is in camera frame)
            offset_y = 20  # vertical offset for text placement
            cv2.putText(self.frame, centroid_str, (centroid_camera[0] - 60, centroid_camera[1] - offset_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(self.frame, tip_str, (tip_camera[0] - 60, tip_camera[1] - offset_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2, cv2.LINE_AA)
        
        # Set a static offset for the text, e.g., 10 pixels above the tag center.
        cf_tag_center = np.mean(cf_tag_corners, axis=0).astype(int)
        text_offset = 10

        # Display the pose estimation coordinates relative to the world frame ABOVE the tag
        world_pos_str = f"X: {(t_tag_to_world[0][0])*100:.1f}, Y: {(t_tag_to_world[1][0])*100:.1f}, Z: {(t_tag_to_world[2][0])*100:.1f}"
        cv2.putText(self.frame, world_pos_str, (cf_tag_center[0] - 60, cf_tag_center[1] - text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2, cv2.LINE_AA)

        #####################################################
        # HAVE TO ADD PART FOR TAG TO WORLD FOR THE CENTROID AND TIP POINTS AS WELL ALSO FOR X - AXES####
        #####################################################
        return None

   

class LinkTags:
    def __init__(self):
        self.tags = {}
    
    def append(self, tag):
        # link_tag_id is from 1 to 12
        link_tag_id = tag.tag_id % 12
        # link_id : 14
        # tag_id : link_id*12 + 11

        if link_tag_id not in self.tags:
            self.tags[link_tag_id] = {}
        
        self.tags[link_tag_id] = {
            'pose_t': tag.pose_t, # translation of the pose estimate
            'pose_R': tag.pose_R, # center of the detection in image coordinates
            'center': tag.center, # rotation matrix of the pose estimate
            'pose_err' : tag.pose_err # object-space error of the estimation
        }
    
    def get_link_tag_id(self, link_tag_id):
        self.tags.get(link_tag_id, {})

    # this function should calculate the link's pose from the detected apriltags. position of the link is the centroid of the link and the orientation is the orientation of the link
    def pose_estimation(self):

        for link_tag_id, link_tag in self.tags.items():
            # Get link frame tag position
            link_frame_tag_position = LINK_TAGS[link_tag_id]
            
            # Get pose of the tag in camera frame
            t_link_to_camera = link_tag['pose_t']
            R_link_to_camera = link_tag['pose_R']
            
            # Transform the tag's position from link frame to camera frame
            t_link = np.dot(R_link_to_camera, link_frame_tag_position) + t_link_to_camera
            
            
            center = link_tag['center']
            pose_err = link_tag['pose_err']
        

            # first perform some operation to obtain the centroid of the link from the detected tags, also use LINK_TAGS
            # Apply transformation to move from link frame to the world frame
            # values[pose_t] = (,,)
            
#     for link in links.values():
#         for link_tag_id, values in link.tags.items():
            
#         pos = link.tags[link_tag_id]['pose_t']
#         link.tags 

    def draw_pose(link_pose):


        return None


####################
## INITIALIZATION ##
####################


# Video capture setup
display_width = 1920
display_height = 1080
cap = cv2.VideoCapture(4)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)  # Width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)  # Height

# Loading calibration results
calib_file = os.path.join("particleTrussServer/RM_Retinas/assets/calibration", "calibration_data.npz")

# The path when pwd is RM_Retinas
# calib_file = os.path.join("assets/calibration", 'calibration_data.npz')

if os.path.exists(calib_file):
    with np.load(calib_file) as X:
        mtx, dist, rvecs, tvecs = X['mtx'], X['dist'], X['rvecs'], X['tvecs']
        print(f"mtx: {mtx}")
        print(f"dist: {dist}")
        print(f"rvecs: {rvecs}")
        print(f"tvecs: {tvecs}")
else:
    print("Calibration data does not exist. Please run calibration.py first")
    exit()

# Extract camera_params, which are focal lengths and optical center each in x, y direction
fx = mtx[0,0]
fy = mtx[1,1]
cx = mtx[0,2]
cy = mtx[1,2]
camera_params = (fx, fy, cx, cy)

# Create an AprilTag detector
detector = dt_apriltags.Detector(searchpath=['apriltags'],
                                    families='tag36h11',
                                    nthreads=1,
                                    quad_decimate=1.0,
                                    quad_sigma=0.0,
                                    refine_edges=1,
                                    decode_sharpening=0.25,
                                    debug=0)

# link number and related TagPose instances
# data collection and organization for later compute
# DATA STRUCTURE
# links  = { link_num : LinkFrameTags instances for the link_num }
# these instances have related tags as values{ 'link_num'.tags[link_frame_tag_id] }
# 17.tags[value between 1 ~ 12] returns a dictionary for that tag
# 17.tags[1] = {
#     'pose_t': tag.pose_t,
#     'pose_R': tag.pose_R,
#     'center': tag.center
# }

links = {}


#######################
## UTILITY FUNCTIONS ##
#######################

def get_camera_to_world_transform(tag):
    # Invert the transformation, since we need camera -> world
    R_inv = np.transpose(tag.pose_R)
    t_inv = -np.dot(R_inv, tag.pose_t)
    return R_inv, t_inv

def average_transforms(transforms):
    average_R = np.mean([R for R, t in transforms], axis=0)
    average_t = np.mean([t for R, t in transforms], axis=0)
    return average_R, average_t

def validate_world_position(tag, t_tag_to_world, frame, tag_index):
    # Extract the tag's estimated position in the world frame
    estimated_position = t_tag_to_world.flatten()
    
    # Get the tag's true position from the WORLD_TAGS dictionary
    true_position = WORLD_TAGS.get(tag.tag_id)
    
    if true_position is not None:
        # Compute the difference between estimated and true position
        difference = true_position - estimated_position
        error_distance = np.linalg.norm(difference)

        display_text = f"Tag {tag.tag_id} Diff: {difference*100} Euclidean Distance: {(error_distance*100):.4f} cm"

        vertical_position = 30 + tag_index * 30
        position = (frame.shape[1] - 600, vertical_position)
        cv2.putText(frame, display_text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
           
        return difference
    return None

def compute_reprojection_error(tag):
    
    # Reproject the tag corners using the estimated pose
    img_pts_reprojected, _ = cv2.projectPoints(obj_pts_square, tag.pose_R, tag.pose_t, mtx, dist)
    img_pts_reprojected = img_pts_reprojected.reshape(-1, 2)

    # Compute the distance between reprojected corners and detected corners
    error = np.linalg.norm(img_pts_reprojected - tag.corners, axis=1)
    avg_error = np.mean(error)
    
    return avg_error


def main():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect AprilTags in the frame
        result_world_tags = detector.detect(gray, True, camera_params, world_tag_size)
        result_april_tags = detector.detect(gray, True, camera_params, april_tag_size)

        R_camera_to_world = None
        t_camera_to_world = None

        for tag in result_world_tags:
            # If the detected tag is the origin (tag ID 575), use its transformation as the world frame  
            if tag.tag_id == 575:
                    R_camera_to_world, t_camera_to_world = get_camera_to_world_transform(tag)

        # If we found the world tag, use its transformation for all other tags. 
        # Otherwise, skip world frame computations for this frame.
        if R_camera_to_world is not None and t_camera_to_world is not None:
            world_tag_counter = 0

            for tag in result_world_tags:
                if tag.tag_id in WORLD_TAGS:
                    detected_world_tag = Tag(frame, tag, R_camera_to_world, t_camera_to_world, world_tag_size)
                    # t_tag_to_world = draw_pose(frame, tag, R_camera_to_world, t_camera_to_world, world_tag_size)
                    cf_tag_corners = detected_world_tag.draw_tag_boundary()
                    detected_world_tag.draw_axes()
                    R_tag_to_world, t_tag_to_world = detected_world_tag.compute_tranformation()
                    detected_world_tag.project_to_world(R_tag_to_world, t_tag_to_world, cf_tag_corners)

                    if tag.tag_id is not None:
                        validate_world_position(tag, t_tag_to_world, frame, world_tag_counter)
                        world_tag_counter += 1
            
            for tag in result_april_tags:
                if tag.tag_id not in WORLD_TAGS:
                    
                    link_num = tag.tag_id // 12 # Link Number starts with P0
                    link_tag_id = tag.tag_id % 12
                    
                    detected_tag = Tag(frame, tag, R_camera_to_world, t_camera_to_world, april_tag_size)
                    # detected_tag.draw_original_boundary()
                    cf_tag_corners = detected_tag.draw_tag_boundary()
                    detected_tag.draw_axes()
                    cf_linkbody_pts = detected_tag.draw_linkbody(link_tag_id)

                    R_tag_to_world, t_tag_to_world = detected_tag.compute_tranformation()
                    detected_tag.project_to_world(R_tag_to_world, t_tag_to_world, cf_tag_corners, cf_linkbody_pts, link_tag_id)

                    # logic for storing tag pose data to LinkPose instances
                    if link_num not in links:
                        links[link_num] = LinkTags()
                    
                    links[link_num].append(tag)
                    # links[link_num].get_link_tag_id(link_tag_id)

            # this part is reserved for TRIANGLE POSE AND ESTIMATION
            # for link in links.values():
            #     link_pose = link.pose_estimation()
            #     link.draw_pose(link_pose)

            # now we have all data stored in links
            # for LinkTags Instance in links, we must calculate the center and the axes
            # using the predefined LINK_TAGS
            # links_pose = link_pose_estimation(links)

            # After all the calculations, draw link pose [pos and orientation and highlight as neon green]
            # draw_link_pose()

        frame_resized = cv2.resize(frame, (display_width, display_height))
        cv2.imshow("AprilTags Pose Estimation", frame_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
