# initial script for the implementation of closed loop controller for a single link
# Author: Simon Kang, simon.kang@columbia.edu
# Last updated: Jan 16, 2024

import sys
sys.path.append('/home/simonhwk/RobotMetabolism/particleTrussServer')
from time import sleep

# server script
import linknetworking as linknetworking

import RM_dashboard.dashboard as dashboard
import RM_Retinas.main as retinas

# from shared_resources import retinas_data_lock
import threading
import numpy as np

from single_link import SingleLink
from cl_triangle import Triangle
from cl_tetrahedron import Tetrahedron

# from particleTrussServer.RM_control instances have names which are link_id-1
# SingleLink.link is a RobotLink instance

MAX_POS = 100
MIN_POS = 22

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ClosedLoopController:
    ### Change the substructure according to the structure ###
    def __init__(self, server=None, substructure="Tetrahedron"):
        print("initializing controller")

        # Create an attribute for the server, this is the database for all the links
        self.server = server

        self.first_call = True # for the first call of get_retinas_data()

        self.links = [] # RobotLink instances

        self.single_links = [] # SingleLink instances
        self.single_link_crawl_dir = 0

        # Get sorted link ids of the robot links from the server
        self.link_ids = sorted(list(server.links.keys()))
        print("Link IDs: ", self.link_ids)

        # Set up a substructure
        self.substructure = substructure
        self.triangle = None
        self.tetrahedron = None

        # Goal flag
        self.goal_pos = (0,-0.31,0) # initial, for now
        self.reached_goal = False
        self.renewed_goal = False

        for id in self.link_ids:
            # Add instance of robot link to self.links
            # these are robot link instances links[0] = RobotLink instance
            self.links.append(server.links[id]) 

            # Initializing the server will create RobotLink instance for each link
            # RobotLink is a class for server related script
            # RobotLink class is used to communicate and send_position_only() commands.

            # Add instance of SinglelLink to self.single_links list
            # these instances have names which are link_id-1
            # SingleLink.link is a RobotLink instance
            # SingleLink.event.set() means that the link is not crawling (wait() will not block, so it will exit crawl() function)
            # SingleLink.event is a threading.Event() instance
            # SingleLink.event.clear() means that the link is crawling (wait() will block, so it will not exit crawl() function)
            if self.substructure == "SingleLink":
                self.single_links.append(SingleLink(server.links[id], link_id=id))
                # self.single_link = SingleLink(self.server, link_id = self.link_ids[:1])

        if substructure == "Triangle":
            self.triangle = Triangle(self.server, link_ids = self.link_ids[:3])
        
        elif substructure == "Tetrahedron":
            self.tetrahedron = Tetrahedron(self.server, link_ids = self.link_ids[:6])

        debug_print("closed loop controller initialized")

        # Start retinas thread, daemon=True means that it will exit when main thread exits
        self.retinas_thread = threading.Thread(target=self.run_retinas, daemon=True)
        self.retinas_thread.start()

        # for interupting crawling command execution
        # when event is set, wait() will not block, so it will exit crawl() function
        # self.event = threading.Event()
        # self.event.set()


    ## RETINAS THREAD
    def run_retinas(self):
        try:
           retinas.retinas_thread()
           
        except Exception as e:
            print(f"Retinas thread encountered an error: {e}")


    def start_retinas_thread(self):
        self.retinas_thread = threading.Thread(target=self.run_retinas, daemon=True)
        self.retinas_thread.start()


    def run(self):
        debug_print("running...")

        # self.start_retinas_thread() # start retinas initially
        
        while True:

            if not self.retinas_thread.is_alive():

                print("Retinas thread is not alive. Restarting...")
                # some code to clear up the shared retinas_data variable

                self.start_retinas_thread()
                sleep(15)

            # update current position
            # Now unused, since we are concurrently running retinas thread
            self.get_retinas_data()


            if self.substructure == "SingleLink":

                # Simultaneous Looking, check if error is within threshold
                need_to_crawl = self.compute_error()

                if need_to_crawl:
                    self.get_crawl_direction()
                    self.send_control_signal()
                else:
                    self.stop_crawling()
            

            elif self.substructure == "Triangle":

                # Simultaneous Looking, check if error is within threshold
                need_to_crawl = self.compute_positional_error_2D()

                if need_to_crawl:
                    self.get_crawl_direction_2D()
                    if abs(self.pos_error) >= 0.15: # when the pos_error is greater than 10 cm
                        self.compute_rotational_error_2D()
                        self.get_rotation_direction_2D()
                    elif abs(self.pos_error) < 0.15:
                        self.rotation_dir = "none"
                    self.send_control_signal_2D()
                else:
                    self.stop_crawling_2D()


            elif self.substructure == "Tetrahedron":
                
                if self.reached_goal == False:

                    # Simultaneous Looking, check if error is within threshold
                    need_to_crawl = self.compute_positional_error_3D()
                    if need_to_crawl:
                        self.get_crawl_direction_3D()
                        # If within 20 cm of goal, do not rotate
                        # for fetch we don't need roation so we disable it by setting the threshold to 10m
                        if abs(self.pos_error) >= 0.2:
                            self.compute_rotational_error_3D()
                            self.get_rotation_direction_3D()
                        elif abs(self.pos_error) < 0.2:
                            self.rotation_dir = "none"
                        self.send_control_signal_3D()
                    else:
                        self.stop_crawling_3D()
                        sleep(12)
                        self.reached_goal = True
                        self.tetrahedron.first_goal = True

                elif self.reached_goal == True:

                    if self.renewed_goal == False:
                        # clear event so it can topple
                        self.tetrahedron.event.clear() # set event to false
                        self.tetrahedron.topple()
                        print("topple done, sleeping for 1 seconds")
                        sleep(1)
                        # self.tetrahedron.event.set() # set event to true, so rotate can 

                        # set a renewed, goal_pos
                        self.renewed_goal = True
                        self.goal_pos = (30,-0.31,0)

                        # reset reached_goal flag
                        self.reached_goal = False

                    # renewed_goal is True, so it will crawl to the renewed goal_pos
                    else: # reached goal & is the second goal
                        self.stop_crawling_3D()
                        print("Second goal reached, Final Destination Reached")
                        sleep(180) # wait for 1800 seconds

                
                    
            # some code to exit thread. t.join() will block until thread terminates
            # ***********
            # currrently it's like stop look
            # make it into take a look while your crawling
            # when done crawling, change clear threading event
            # if need to crawl and event is set, event.clear() then start crawling

            sleep(1)


    def get_retinas_data(self):
    #     # need code for link_ids
    #     # example data output:
    #     # Retinas Data: {14: {'centroid': (0.07075065509265721, -0.25456650387591034, -0.006115126794151505), 'upper_tip': (0.0661878744825622, -0.12189110264311516, -0.006363823172106285), 'bottom_tip': (0.0739161034182324, -0.3872434322078592, -0.005942559671453702)}, 27: {'centroid': (-0.039358557112312426, -0.3067775513973511, -0.007710847828674004), 'upper_tip': (-0.14441187533361854, -0.22561379025196532, -0.004528841218400862), 'bottom_tip': (0.06256502012369594, -0.38719045751225095, -0.029468024342761343)}, 28: {'centroid': (-0.05971829872306564, -0.15776486656692912, 0.00017834033160955427), 'upper_tip': (0.06682388485606405, -0.11963764268972249, -0.012150906144081696), 'bottom_tip': (-0.18591261856793334, -0.1950202811738458, -0.0019136376144052929}})
    #     print(retinas.retinas_data)

        if self.first_call:
            print("Initial wait for 15 seconds for retinas to start up...")
            sleep(15)  # Wait for 15 seconds on the first call
            self.first_call = False  # Set the flag to False after the first wait

        while True:
            if hasattr(retinas, 'retinas_data') and retinas.retinas_data is not None:
                # self.goal_pos = (0,-0.31,0) # for now

                print("Retinas Data:", retinas.retinas_data)
                # Written this way, so it works for multiple links as well.
                self.link_positions = []
                self.upper_tips = []
                self.bottom_tips = []


                for id in self.link_ids:
                    # self.link_positions.append(retinas.retinas_data[id]['centroid'])
                    try:
                        if id in retinas.retinas_data and 'centroid' in retinas.retinas_data[id]:
                            centroid = retinas.retinas_data[id]['centroid']
                            if centroid is not None and len(centroid) == 3:  # Assuming centroid should be a tuple of 3 values
                                self.link_positions.append(centroid)
                                self.upper_tips.append(retinas.retinas_data[id]['upper_tip'])
                                self.bottom_tips.append(retinas.retinas_data[id]['bottom_tip'])
                            else:
                                print(f"Invalid centroid data for link ID {id}: {centroid}")
                        else:
                            print(f"Data for link ID {id} not found in retinas data.")
                    except Exception as e:
                        print(f"Error processing data for link ID {id}: {e}")

                self.curr_pos = np.mean(self.link_positions, axis=0)
                print(f"CENTROID: {self.curr_pos}")

                break

            else:
                print("Retinas data not available yet.")
                sleep(5)  # Wait for 5 seconds before trying again
        

            # self.curr_pos = retinas.curr_pos() # get curr position
            # self.goal_pos = retinas.goal_pos() # get goal position, since goal_pos can change


######################################
############# 1D SCRIPT ##############
######################################


    def compute_error(self):
        print("computing error")
        threshold = 0.03 # within 3 cm of goal position
        # global x, y, z crawling direction -> throw away z

        # calculate error only for x-axis 
        self.error = self.goal_pos[0] - self.curr_pos[0]
        print("error: ", self.error)

        # when error is less than the threshold set to zero
        if (abs(self.error) < threshold):
            self.error = 0
            return False # No need to crawl
        return True # Need to crawl


    def stop_crawling(self):
        print("REACHED goal tag: stop crawling")
        # Stop crawling for all single links
        for single_link in self.single_links:
            # setting the event will stop the crawl method in SingleLink
            single_link.event.set()


    def get_crawl_direction(self):
        # BINARY CONTROL
        # print("adjusting control signal")
        if self.error > 0:
            self.single_link_crawl_dir = 1
        elif self.error < 0:
            self.single_link_crawl_dir = -1
        else:
            # No movement needed, this won't get executed.
            # Due to if statement in compute_error()
            self.single_link_crawl_dir = 0     


    # implementation for CL controller
    def send_control_signal(self):
        # make single_link parameter 
        print("determining control signal")
        
        if self.single_link_crawl_dir == 0:
            # No need for movement, so ensure all links are stopped
            for single_link in self.single_links:
                single_link.event.set()  # Stop crawling if it's currently happening
                print("stop crawling...")
            return
        
        for single_link in self.single_links:
            # this is the initial condition (it doesn't execute crawl(), currently at rest)
            # If the link is not currently crawling
            print("link is still crawling, try next time")
            if single_link.event.is_set():
                "EXECUTE Crawl()"  
                single_link.event.clear()  # set event to false() so it executes crawling
                t = threading.Thread(target=single_link.crawl, args=(self.single_link_crawl_dir, 1), daemon=True)
                t.start()


######################################
############# 2D SCRIPT ##############
######################################


    def compute_positional_error_2D(self): # will implement rest after considering rotation
        threshold = 0.04 # within 4 cm of goal position
        # calculate error for x and y axis
        self.error_x = self.goal_pos[0] - self.curr_pos[0]
        self.error_y = self.goal_pos[1] - self.curr_pos[1]
        # get the norm of the error
        self.pos_error = np.linalg.norm([self.error_x, self.error_y])
        print("pos_error: ", self.pos_error)

        # when error is less than the threshold set to zero
        if (abs(self.pos_error) < threshold):
            self.pos_error = 0
            return False
        return True
    

    def compute_rotational_error_2D(self):
        
        if self.substructure == "Triangle":
                
            # get the directional vector for the triangle
            # vector from the back link to the centroid of the triangle(curr_pos)
            triangle_vector = self.curr_pos - self.link_positions[0]
            # get the unit vector
            unit_vector_triangle = triangle_vector / np.linalg.norm(triangle_vector)

            # obtain vector from curr_pos to goal_pos
            vector_to_goal = self.goal_pos - self.curr_pos
            # get the unit vector
            unit_vector_to_goal = vector_to_goal / np.linalg.norm(vector_to_goal)

            # get the angle between the two vectors
            dot_product = np.dot(unit_vector_triangle, unit_vector_to_goal)
            self.rot_error = np.arccos(dot_product)

            # get the cross product to determine the direction of rotation
            cross_product = np.cross(unit_vector_triangle, unit_vector_to_goal)
            # print("cross_product_z: ", cross_product_z)
            cross_product_z = cross_product[2]

            if cross_product_z > 0:
                self.rot_error = self.rot_error
            elif cross_product_z < 0:
                self.rot_error = -self.rot_error
            else:
                self.rot_error = 0

            print("rot_error(ang): ",  np.degrees(self.rot_error))


    def get_crawl_direction_2D(self):
        # BINARY CONTROL
        # print("adjusting control signal")
        if self.pos_error > 0:
            self.triangle_crawl_dir = 1
        elif self.pos_error < 0:
            self.triangle_crawl_dir = -1
        else:
            # No movement needed, this won't get executed.
            # Due to if statement in compute_error()
            self.triangle_crawl_dir = 0


    def get_rotation_direction_2D(self):
        # threshold is 30 degrees, field of view is 60 degrees
        # rot_error increases as the triangle gets closer
        threshold = np.pi/6

        if threshold < self.rot_error:
            # it should be clockwise or counter clockwise
            self.rotation_dir = "cw"
        elif self.rot_error < -threshold:
            self.rotation_dir = "ccw"
        else:
            self.rotation_dir = "none"


    def send_control_signal_2D(self):
        # make single_link parameter 
        print("determining control signal")
        
        # if self.triangle_crawl_dir == 0:
        #     # No need for movement, so ensure all links are stopped
        #     for single_link in self.single_links:
        #         single_link.event.set()
        #         print("stop crawling...")
        #     return

        # check if crawling is still happening
        if self.triangle.event.is_set():
            if self.rotation_dir != "none":
                self.triangle.event.clear()
                # print(f"EXECUTE Triangle Rotate(): {self.rotation_dir} ")
                t = threading.Thread(target=self.triangle.rotate, args=(self.rotation_dir, 1), daemon=True)
                t.start()
                # wait until the triangle is done rotating
                # t.join()
            else: # no need to rotate so crawl
                self.triangle.event.clear()
                "EXECUTE Crawl()"
                t = threading.Thread(target=self.triangle.crawl, args=(self.triangle_crawl_dir, 1), daemon=True)
                t.start()
        else:
            print("triangle is still crawling, try next time")


    def stop_crawling_2D(self):
        print("REACHED goal tag: stop crawling")

        # Stop crawling for triangle
        self.triangle.event.set()


######################################
############# 3D SCRIPT ##############
######################################


    def compute_positional_error_3D(self): # will implement rest after considering rotation
        threshold = 0.05 # within 10 cm of goal position
        # # calculate error for x and y axis
        # self.error_x = self.goal_pos[0] - self.curr_pos[0]
        # self.error_y = self.goal_pos[1] - self.curr_pos[1]
        # self.error_z = self.goal_pos[2] - self.curr_pos[2]
        # # get the norm of the error
        # self.pos_error = np.linalg.norm([self.error_x, self.error_y, self.error_z])
        # print("pos_error: ", self.pos_error)

        # we only pick the highest link, which is L6, as the reference
        self.error_x = self.goal_pos[0] - self.link_positions[-1][0]
        self.error_y = self.goal_pos[1] - self.link_positions[-1][1]
        self.error_z = self.goal_pos[2] - self.link_positions[-1][2]

        # get the norm of the error
        self.pos_error = np.linalg.norm([self.error_x, self.error_y, self.error_z])

        print("tet_pos_error: ", self.pos_error)

        # when error is less than the threshold set to zero
        if (abs(self.pos_error) < threshold):
            self.pos_error = 0
            return False
        return True
    

    def compute_rotational_error_3D(self):
        
        if self.substructure == "Tetrahedron":
                

            # get the directional vector for the triange
            # vector from the back link to the centroid of the triangle(curr_pos)
            print("self.linkpositions: ", self.link_positions)
            print("self.upper_tips: ", self.upper_tips)
            print("self.bottom_tips: ", self.bottom_tips)

            upper_tip = np.array(self.upper_tips[-1])
            print(type(upper_tip))
            print("upper_tip: ", upper_tip)
            if np.all(np.isnan(upper_tip)):
                bottom_tip = np.array(self.bottom_tips[-1]) 
                bf_vector = bottom_tip - self.link_positions[-1]
                print("bf_vector: ", bf_vector)
                # +90 degrees ccw rotation transformation
                tetrahedron_vector = bf_vector @ np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
                print("tetrahedron_vector: ", tetrahedron_vector)
            else:
                bf_vector = upper_tip - self.link_positions[-1]
                print("bf_vector: ", bf_vector)
                # -90 degrees cw rotation transformation
                tetrahedron_vector = bf_vector @ np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
                print("tetrahedron_vector: ", tetrahedron_vector)

            # get the unit vector
            unit_vector_tetrahedron = tetrahedron_vector / np.linalg.norm(tetrahedron_vector)

            # obtain vector from curr_pos to goal_pos
            vector_to_goal = self.goal_pos - np.array(self.link_positions[-1])
            # get the unit vector
            unit_vector_to_goal = vector_to_goal / np.linalg.norm(vector_to_goal)

            # get the angle between the two vectors
            dot_product = np.dot(unit_vector_tetrahedron, unit_vector_to_goal)
            self.rot_error = np.arccos(dot_product)

            # get the cross product to determine the direction of rotation
            cross_product = np.cross(unit_vector_tetrahedron, unit_vector_to_goal)
            # print("cross_product_z: ", cross_product_z)
            # print(type(cross_product))
            # print("cross_product: ", cross_product)
            cross_product_z = cross_product[2]

            # print(type(cross_product_z))
            # print("cross_product_z: ", cross_product_z)
            if cross_product_z > 0:
                self.rot_error = self.rot_error
            elif cross_product_z < 0:
                self.rot_error = -self.rot_error
            else:
                self.rot_error = 0

            print("rot_error(ang): ",  np.degrees(self.rot_error))


    def get_crawl_direction_3D(self):
        # print("adjusting control signal")
        if self.pos_error > 0:
            self.tetrahedron_crawl_dir = 2
        elif self.pos_error < 0:
            self.tetrahedron_crawl_dir = 2
        else:
            # No movement needed, this won't get executed.
            # Due to if statement in compute_error()
            self.tetrahedron_crawl_dir = 2


    def get_rotation_direction_3D(self):
        # threshold is 30 degrees, field of view is 60 degrees
        # rot_error increases as the triangle gets closer
        threshold = np.pi/6

        if threshold < self.rot_error:
            # it should be clockwise or counter clockwise
            self.rotation_dir = "ccw"
        elif self.rot_error < -threshold:
            self.rotation_dir = "cw"
        else:
            self.rotation_dir = "none"


    def send_control_signal_3D(self):
        # make single_link parameter 
        print("determining control signal")

        # check if crawling is finished (event flag would be set)
        if self.tetrahedron.event.is_set(): # event is true
            if self.rotation_dir != "none":
                self.tetrahedron.event.clear() # event is false, event.wait() will block
                # print(f"EXECUTE Tetrahedron Rotate(): {self.rotation_dir} ")
                t = threading.Thread(target=self.tetrahedron.rotate, args=(self.rotation_dir,), daemon=True)
                t.start()
                # wait until the tetrahedron is done rotating
                # t.join()
            else: # no need to rotate so crawl
                self.tetrahedron.event.clear() 
                "EXECUTE Crawl()"
                t = threading.Thread(target=self.tetrahedron.crawl, args=(self.tetrahedron_crawl_dir,), daemon=True)
                t.start()
        else:
            print("tetrahedron is still crawling, try next time")


    def stop_crawling_3D(self):
        print("REACHED goal tag: stop crawling")

        # Stop crawling for tetrahedron
        self.tetrahedron.event.set()



def main(nr_links):
    try:
        # Intialize Server
        server = linknetworking.get_default_server()

        my_dashboard = dashboard.Dashboard(server, list(range(35)), open_in_browser=True)
        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
        
        debug_print("Starting scripts...")
        # Initialize closed loop controller

        clctrl = ClosedLoopController(server)
        clctrl.run()

    except Exception as exception:
        print(exception)


if __name__ == '__main__':

    nr_links = 6

    main(nr_links)


