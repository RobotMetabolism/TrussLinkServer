# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Edits: Simon Kang simon.kang@columbia.edu
# Last updated: Dec 7, 2023

from pynput.keyboard import Key, Listener, KeyCode
from pynput import keyboard


# import linknetworking as linknetworking
import sys
# add particleTrussServer dir to system path
sys.path.append('/home/simonhwk/RobotMetabolism/particleTrussServer')
import linknetworking as linknetworking


import RM_dashboard.dashboard as dashboard
# parses command-line  arguments
import argparse
# pause execution for a specified amount of time
from time import sleep

import logging
from tetrahedron import Tetrahedron
from diamond_with_a_tail import DiamondWithATail
from single_link import SingleLink
from triangle import Triangle
import threading
from evdev import InputDevice #to detect numLock state


#param: selected servos
#mode: expand or contract

# maximum and minimum positinos for the servos
MAX_POS = 100
MIN_POS = 22

DEBUG = True
LISTEN = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ManualController:
    def __init__(self, server=None, substructure="Triangle", mode="Sticky"):
        print("initializing controller")
        if mode == "Sticky":
            self.is_sticky = True
        else:
            self.is_sticky = False
        
        # Get server links, this is the data base of all the links
        self.server = server
        self.links = [] #RobotLink instances
        self.single_links = [] #SingleLink instances
        self.single_link_crawl_dir = 0

        # get link ids
        self.link_ids = sorted(list(server.links.keys()))

        for id in self.link_ids:
            # Add instance of robot link to self.links list
            # these are RobotLink instances
            self.links.append(server.links[id])

            # Add instance of SingleLink to self.single_links list
            # SingleLink.link is a RobotLink instance
            # SingleLink.event.set() means that the link is not crawling (wait() will not block, so it will exit crawl() function)
            # SingleLink.event is a threading.Event() instance
            # SingleLink.event.clear() means that the link is crawling (wait() will block, so it will not exit crawl() function)
            self.single_links.append(SingleLink(server.links[id], link_id=id))

        print("Link IDs: ", self.link_ids)  

        # set up keyboard device to detect if numlock is on
        # add user to the input group to gain access to /dev/input/
        # sudo usermod -a -G input <user>
        keyboard_dev_dir = f"/dev/input/by-path/platform-i8042-serio-0-event-kbd"
        self.keyboard_dev = InputDevice(keyboard_dev_dir) # your keyboard device

        # Set up tetrahedron or diamond with a tail
        self.tetrahedron = None
        self.diamond_with_a_tail = None
        self.triangle = None
        self.substructure = substructure
        
        if substructure == "Tetrahedron":
            self.tetrahedron = Tetrahedron(self.server, link_ids = self.link_ids[:6])
        elif substructure == "DWAT":
            self.diamond_with_a_tail = DiamondWithATail(self.server, link_ids = self.link_ids[:6])
        elif substructure == "Triangle":
            self.triangle = Triangle(self.server, link_ids=self.link_ids[:3])

        self.reset()
        debug_print("manual controller initialized")

        # For interrupting crawling execution
        self.event = threading.Event()
        self.event.set()

        # Set up keyboard listener
        self.listener =  Listener(
                on_press=self.on_press,
                on_release=self.on_release)
        
        # starts new thread for listener
        # when a key is pressed or released, the listener thread detects
        # this event and calls the corresponding callback function that was defined
        # When the Listener was created, in the provided script it's self.on_press
        # and self.on_release

        self.listener.start()

    def reset(self):
        # a dictionary that maps each link name to its current state
        self.link_states = {}
        self.link_states_pretty = {}
        self.current_keys = set()

    def run(self):
        debug_print("running...")

        # listens to keyboard input and parsing them into commands for the robot.
        while True:
            current_keys_copy = self.current_keys.copy() # so that Set doesn't change during parsing iteration
            self._command_parse(current_keys_copy) # get all current commands
            sleep(0.5)

    # interprets the current set of pressed keys and sends corresponding commands to the robot
    def _command_parse(self, keys):
        print("parsing...")
        selected_links = []
        state = 0
        mode = -1
        param = -1
        srv = [0,0]
        #debug_print(f"parsing keys... {keys}" )
        for k in keys:
            # if k == keyboard.Key.num_lock:
            #     print("detected numlock")
            #     print('keycode: ', str(k.value))
            #     print('keysym num: ', k.keysym_num)
            #     continue
            if type(k) == keyboard.KeyCode:
                try:
                    k_val = k.char #type str
                    if (k_val == '/') and self.is_numlock_on():
                        self.single_link_crawl_dir = 0
                        print("changing crawling direction to SRV0")
                        return
                    if (k_val == '*') and self.is_numlock_on():
                        self.single_link_crawl_dir = 1
                        print("changing crawling direction to SRV1")
                        return
                    if k_val.isdigit():
                        selected_links.append(int(k_val) - 1)
                    if k_val == '-':
                        debug_print("contracting all")
                        selected_links = [idx for idx in range(len(self.link_ids))]
                        state = 1
                        mode = 0    
                        param = 2
                    if k_val == '+':
                        debug_print("expanding all")
                        selected_links = [idx for idx in range(len(self.link_ids))]
                        state = 1
                        mode = 1
                        param = 2
                    if k == KeyCode.from_char('t'): #topple 0
                        debug_print("detecting t")
                        self.event.clear()
                        self.tetrahedron.topple(self.event, dir=0, tail=self.links[-1])
                    if k == KeyCode.from_char('y'): #topple 1
                        debug_print("detecting y")
                        self.event.clear()
                        self.tetrahedron.topple(self.event, dir=1, tail=self.links[-1])
                    if k == KeyCode.from_char('u'): #topple 2
                        debug_print("detecting u")
                        self.event.clear()
                        self.tetrahedron.topple(self.event, dir=2, tail=self.links[-1])
                    if k == KeyCode.from_char('c'): #crawl 0
                        self.event.clear()
                        if self.substructure == "Tetrahedron":
                            self.tetrahedron.crawl(self.event, dir=0)
                        elif self.substructure == "DWAT":
                            self.diamond_with_a_tail.crawl(self.event)
                        elif self.substructure == "Triangle":
                            self.triangle.crawl_1(self.event)
                    if k == KeyCode.from_char('v'): #crawl 1
                        #assert self.substructure == "Tetrahedron", f"{self.substructure} cannot crawl in this direction"
                        self.event.clear()
                        if self.substructure == "Tetrahedron":
                            self.tetrahedron.crawl(self.event, dir=1)
                        elif self.substructure == "Triangle":
                            self.triangle.crawl_2(self.event)
                        elif self.substructure == "DWAT":
                            self.diamond_with_a_tail.crawl_left(self.event)
                    if k == KeyCode.from_char('b'): #crawl 2
                        #assert self.substructure == "Tetrahedron", f"{self.substructure} cannot crawl in this direction"
                        self.event.clear()
                        if self.substructure == "Tetrahedron":
                            self.tetrahedron.crawl(self.event, dir=2)
                        elif self.substructure == "Triangle":
                            self.triangle.crawl_3(self.event)
                    if k == KeyCode.from_char('d'): #ratchet crawl 0
                        self.event.clear()
                        if self.substructure == "Tetrahedron":
                            self.tetrahedron.crawl(self.event, dir=0, is_ratchet = True, single_link=self.links[-1])
                        elif self.substructure == "DWAT":
                            self.diamond_with_a_tail.crawl(self.event)
                    if k == KeyCode.from_char('f'): #ratchet crawl 1
                        assert self.substructure == "Tetrahedron", f"{self.substructure} cannot crawl in this direction"
                        self.event.clear()
                        self.tetrahedron.crawl(self.event, dir=1, is_ratchet = True, single_link=self.links[-1])
                    if k == KeyCode.from_char('g'): #ratchet crawl 2
                        assert self.substructure == "Tetrahedron", f"{self.substructure} cannot crawl in this direction"
                        self.event.clear()
                        self.tetrahedron.crawl(self.event, dir=2, is_ratchet = True, single_link=self.links[-1])
                    if k == KeyCode.from_char('r'): #reset rachet crawl
                        assert self.substructure == "Tetrahedron", f"{self.substructure} cannot do rachet crawl"
                        self.event.clear()
                        self.tetrahedron.reset_rachet(self.event, dir=1, single_link=self.links[-1])
                    if k == KeyCode.from_char('o'): #triangle rotate counterclockwise
                        assert self.substructure == "Triangle", f"{self.substructure} cannot rotate"
                        self.event.clear()
                        self.triangle.rotate(self.event, dir='ccw')
                    if k == KeyCode.from_char('p'): #triangle rotate clockwise
                        assert self.substructure == "Triangle", f"{self.substructure} cannot rotate"
                        self.event.clear()
                        self.triangle.rotate(self.event, dir='cw')
                except:
                    debug_print(f"unrecognized key: {k_val}")
                    continue
            if k == Key.up:
                state = 1
                mode = 1
            elif k == Key.down:
                state = 1
                mode = 0
            if k == Key.left:
                srv[0] = 1
            if k == Key.right:
                srv[1] = 1

        # if numlock is on, selected links start crawling 
        if self.is_numlock_on() and not(param == 2 and state==1): #contract/expand all still effective when numlock is on
            for l in selected_links:
                # if true (event.set()) it means that the link exits the crawl() function
                # this is defined in SingleLink class
                if self.single_links[l].event.is_set():
                    # the link was not crawling, so we make it crawl
                    t = threading.Thread(target=self.single_links[l].crawl, args=(self.single_link_crawl_dir, 100), daemon=True)
                    t.start()
                # if event is not set(it is crawling)
                # sets the event, which would stop the crawling action
                else:
                    self.single_links[l].event.set() 
                    # wait() will not block, so it will exit crawl() function
                    print(f"Stopping link P{self.link_ids[l]}")
            return

        # check which servos are being activated
        if srv[0] == 1 and srv[1] == 1:
            param = 2
        elif srv[0] == 1:
            param = 0
        elif srv[1] == 1:
            param = 1

        #debug_print(f"selected links: {selected_links}")

        #invalid command
        #param = -1: no servo selected
        #mode = -1: no servo positions provided
        #selected_links empty: no links selected
        
        if ((not state) or (len(selected_links) == 0) or (mode == -1)):
            if self.is_sticky:
                #selected_links, state, mode, param = self.last_command
                self._execute_sticky_states()
            return
        
        selected_links.sort()

        # execute states
        if self.is_sticky:
            for l in selected_links:
                self.link_states[l] = (state, mode, param)
            self._execute_sticky_states()
        else:
            self._execute_state(selected_links, (state, mode, param))
        return

    # def _update_sticky_states(self, links_idx, state):
    #     for l in links_idx:
    #         self.link_states[l] = state
    #         self.link_states_pretty[self.link_ids[l]] = self.state_to_pos_command(state)

    def _print_sticky_states(self, pretty=False):
        link_states = self.link_states_pretty if pretty else self.link_states
        print("------CURRENT COMMANDS-------")
        for l, s in link_states.items():
            print(f"link {l}: {s}")
        print("-----------------------------")    

    def _execute_sticky_states(self):
        for l, s in self.link_states.items():
            self._execute_state([l], s)
        self._print_sticky_states(pretty=True)

    # exectues a given state for the selected links.
    # the state includes whether to move the servos to a maximum or minimum position
    def _execute_state(self, links_idx, state):
        MIN_POS = 22
        
        # end effector
        # for i in links_idx:
        #     if (i < 1): MIN_POS = 0

        srv0_pos, srv1_pos = self.state_to_pos_command(state, srv0_min=MIN_POS)
        self._set_link_pos(links_idx, srv0_pos, srv1_pos)

    # translates a state description into servo positions(contraction)
    def state_to_pos_command(self, state, srv0_min=22):
        state, mode, param = state
        MAX_POS = 100
        MIN_POS = 22
        srv0_pos, srv1_pos = None, None
        if mode == 1:
            if param == 0:
                srv0_pos = MAX_POS
            elif param == 1:
                srv1_pos = MAX_POS
            elif param == 2:
                srv0_pos = MAX_POS
                srv1_pos = MAX_POS
        elif mode == 0:
            if param == 0:
                srv0_pos = srv0_min
            elif param == 1:
                srv1_pos = MIN_POS
            elif param == 2:
                srv0_pos = srv0_min
                srv1_pos = MIN_POS
        return (srv0_pos, srv1_pos)

    # sets the position of the servos for the specified links
    def _set_link_pos(self, link_idx, srv0_pos, srv1_pos):
        for i in link_idx:
            if self.link_ids[i] in self.link_states_pretty:
                srv0_pos = self.link_states_pretty[self.link_ids[i]][0] if srv0_pos is None else srv0_pos
                srv1_pos = self.link_states_pretty[self.link_ids[i]][1] if srv1_pos is None else srv1_pos
            else:
                srv0_pos = MIN_POS if srv0_pos is None else srv0_pos
                srv1_pos = MIN_POS if srv1_pos is None else srv1_pos
            self.link_states_pretty[self.link_ids[i]] = srv0_pos, srv1_pos # update states for sticky operation
            # debug_print(f"Sending position command ({srv0_pos,srv1_pos}) to link {self.link_ids[i]}")
            self.links[i].send_position_only(srv0_pos, srv1_pos)
            
    def on_press(self, key):
        if key in self.current_keys: return

        # adds the keys to self.current_keys
        self.current_keys.add(key)
        if key == KeyCode.from_char('s'):
            self.reset()
            self.event.set()
            for link in self.single_links:
                link.event.set()
            debug_print("stopping...")

    def on_release(self, key):
        #debug_print('{0} release'.format(key))
        #debug_print(f"current_keys: {current_keys}")
        if key not in self.current_keys:
            self.current_keys.clear()
        else:
            print('removing key: ', str(key))
            self.current_keys.remove(key)
        if key == Key.esc:
            debug_print("Stopped_listening")
            return False
        
    def is_numlock_on(self):
        active_LEDs = [v[0] for v in self.keyboard_dev.leds(verbose=True)]
        # Adding to work on Simon's computer : power LED counts as numlock LED	
        return False
    	#### IF YOU NEED NUMLOCK COMMENT THE RETURN ABOVE

        # if 'LED_NUML' in active_LEDs:
        #     return True
        # return False

def main(nr_links):
    try:
        # Initialize Server
        server = linknetworking.get_default_server()

        my_dashboard = dashboard.Dashboard(server, list(range(35)), open_in_browser=True)
        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
        

        debug_print("STARTING SCRIPTS!!!!!")
        # Initialize manual controller
        mnctrl = ManualController(server)
        mnctrl.run()
    except Exception as e:
        print(e)
    # finally:
    #     server.close_server()
    #     listener.join()
    #     my_dashboard.close()
    #     exit()
        



if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Select nr of links to manually control')
    # parser.add_argument('nr_links', type=int, help="An integer argument")
    # args = parser.parse_args()
    # nr_links = args.nr_links

    #nr_links = 3
    # nr_links = 1
    main(3)  
