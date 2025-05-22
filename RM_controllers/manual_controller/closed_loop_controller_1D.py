# initial script for the implementation of closed loop controller for a single link
# Author: Simon Kang, simon.kang@columbia.edu
# Last updated: Nov 13, 2023

import sys
sys.path.append('/home/simonhwk/RobotMetabolism/particleTrussServer')
from time import sleep

# this is for the server
import linknetworking as linknetworking

import RM_dashboard.dashboard as dashboard
import RM_Retinas.main as retinas

from single_link import SingleLink
# from shared_resources import retinas_data_lock
import threading
import numpy as np

MAX_POS = 100
MIN_POS = 22

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ClosedLoopController:
    def __init__(self, server=None, substructure = "SingleLink", mode="Sticky"):
        print("initializing controller")

        # if mode == "Sticky":
        #     self.is_sticky = True
        # else:
        #     self.is_sticky = False

        # Get server links, this is the data base of all the links
        self.server = server

        self.first_call = True # for the first call of get_retinas_data()


        self.links = [] # RobotLink instances
        self.single_links = [] # SingleLink instances
        self.single_link_crawl_dir = 0

        # get sorted link ids
        # there are basically all the link_ids
        self.link_ids = sorted(list(server.links.keys()))

        for id in self.link_ids:
            # Add instance of robot link to self.links list
            # these are robot link instances links[0] = RobotLink instance
            self.links.append(server.links[id]) 

            # Add instance of SinglelLink to self.single_links list
            # these instances have names which are link_id-1
            # SingleLink.link is a RobotLink instance
            # SingleLink.event.set() means that the link is not crawling (wait() will not block, so it will exit crawl() function)
            # SingleLink.event is a threading.Event() instance
            # SingleLink.event.clear() means that the link is crawling (wait() will block, so it will not exit crawl() function)
            self.single_links.append(SingleLink(server.links[id], link_id=id))

        print("Link IDs: ", self.link_ids)

        # substructure
        self.substructure = substructure

        # RECHECK IF THIS PART WILL BE NEEDED
        # if substructure == "SingleLink":
        #     self.single_link = SingleLink(self.server, link_id = self.link_ids[:1])

        # self.reset()
        debug_print("closed loop controller initialized")

        # Start retinas thread, daemon=True means that it will exit when main thread exits
        self.retinas_thread = threading.Thread(target=self.run_retinas, daemon=True)
        self.retinas_thread.start()

        # for interupting crawling command execution
        # when event is set, wait() will not block, so it will exit crawl() function
        # self.event = threading.Event()
        # self.event.set()


    def start_retinas_thread(self):
        self.retinas_thread = threading.Thread(target=self.run_retinas, daemon=True)
        self.retinas_thread.start()

    ## RETINAS THREAD
    def run_retinas(self):
        try:
           retinas.retinas_thread()
        except Exception as e:
            print(f"Retinas thread encountered an error: {e}")

    # clears the current state of the controller
    # def reset(self):
        # a dictionary that maps each link id to its current state
        # self.link_states = {}
        # self.link_states_pretty = {}
        # ######## new for CL ######### empty action sequence
        # self.current_action = set()

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

            # Simultaneous Looking, check if error is within threshold
            need_to_crawl = self.compute_error()

            if need_to_crawl:
                self.adjust_control_signal()
                self.send_control_signal()
            else:
                self.stop_crawling()

            # ADJUST SLEEP FOR CL CONTROLLER. Preferrably, like (12+12+12)*5 seconds +?
            
            
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
                print("Retinas Data:", retinas.retinas_data)
                # Written this way, so it works for multiple links as well.
                link_positions = []
                # print("where is it failing, flag 1")

                for id in self.link_ids:
                    link_positions.append(retinas.retinas_data[id]['centroid'])
                # print("where is it failing, flag 2")
                self.curr_pos = np.mean(link_positions, axis=0)
                print(self.curr_pos)
                self.goal_pos = (0,0,0) # for now

                break

            else:
                print("Retinas data not available yet.")
                sleep(5)  # Wait for 5 seconds before trying again
        

            # self.curr_pos = retinas.curr_pos() # get curr position
            # self.goal_pos = retinas.goal_pos() # get goal position, since goal_pos can change

    def compute_error(self):
        print("computing error")
        threshold = 0.03 # within 5 cm of goal position
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

    def adjust_control_signal(self):
        # BINARY CONTROL
        # print("adjusting control signal")
        if self.error > 0:
            self.single_link_crawl_dir = 1
        elif self.error < 0:
            self.single_link_crawl_dir = 0
        else:
            # No movement needed, this won't get executed.
            # Due to if statement in compute_error()
            self.single_link_crawl_dir = -1       

    # implementation for CL controller
    def send_control_signal(self):
        # make single_link parameter 
        print("determining control signal")
        
        if self.single_link_crawl_dir == -1:
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

    nr_links = 1

    main(nr_links)


