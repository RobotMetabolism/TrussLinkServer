# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Last updated: Jan 1, 2023

from pynput.keyboard import Key, Listener, KeyCode
from pynput import keyboard
import linknetworking as linknetworking
import RM_dashboard.dashboard as dashboard
import argparse
from time import sleep
import logging, sys
from tetrahedron import Tetrahedron
from diamond_with_a_tail import DiamondWithATail
from single_link import SingleLink
from triangle import Triangle
import threading
from evdev import InputDevice #to detect numLock state

#param: selected servos
#mode: expand or contract

MAX_POS = 100
MIN_POS = 22
ZERO_POS = 0
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ManualController:
    def __init__(self, server=None, substructure=None, end_effectors=[], mode="Sticky"):
        print("initializing controller")
        self.is_sticky = mode == "Sticky"
        
        # Get server links
        self.server = server
        self.links = [] #RobotLink instances
        self.single_links = [] #SingleLink instances
        self.end_effectors = end_effectors
        self.single_link_crawl_dir = 0
        self.link_ids = sorted(list(server.links.keys()))

        for idx, id in enumerate(self.link_ids):
            if id in end_effectors:
                self.end_effectors.append(idx) # define which links are end effectors 
            self.links.append(server.links[id])
            self.single_links.append(SingleLink(server.links[id], link_id=id))
        print("Link IDs: ", self.link_ids)

        # set up keyboard device to detect if numlock is on
        # add user to the input group to gain access to /dev/input/
        # sudo usermod -a -G input <user>
        keyboard_dev_dir = f"/dev/input/by-path/platform-i8042-serio-0-event-kbd"
        self.keyboard_dev = InputDevice(keyboard_dev_dir) # your keyboard device

        # Set up robot structure
        self.substructure = substructure
        self.tetrahedron = Tetrahedron(self.server, link_ids = self.link_ids[:6]) if substructure == "Tetrahedron" else None
        self.diamond_with_a_tail = DiamondWithATail(self.server, link_ids = self.link_ids[:6]) if substructure == "DWAT" else None
        self.triangle = Triangle(self.server, link_ids=self.link_ids[:3]) if substructure == "Triangle" else None

        # clear link states
        self.reset()
        debug_print("manual controller initialized")

        # For interrupting command execution
        self.event = threading.Event()
        self.event.set()

        # Set up keyboard listener
        self.listener =  Listener(
                on_press=self.on_press,
                on_release=self.on_release)
        self.listener.start()

    def reset(self):
        self.link_states = {}
        self.link_states_pretty = {}
        self.current_keys = set()

    def run(self):
        debug_print('running..."')
        while True:
            current_keys_copy = self.current_keys.copy() # so that Set doesn't change during parsing iteration
            self._command_parse(current_keys_copy) # get all current commands
            sleep(0.5)

    def _command_parse(self, keys):
        print("parsing...")
        selected_links = []
        state = 0
        mode = -1
        param = -1
        srv = [0,0]
        dirs = {'/': 0, '*': 1}
        global_commands = {"+": (1, 1, 2), '-': (1, 0, 2)}

        key_actions = {
            't': (self.tetrahedron.topple, {"dir": 0, "tail": self.links[-1]}),
            'y': (self.tetrahedron.topple, {"dir": 1, "tail": self.links[-1]}),
            'u': (self.tetrahedron.topple, {"dir": 2, "tail": self.links[-1]}),
            'c': ({"Tetrahedron": (self.tetrahedron.crawl, {"dir": 0}),
                "DWAT": (self.diamond_with_a_tail.crawl, {}),
                "Triangle": (self.triangle.crawl_1, {})}[self.substructure]),
            'v': ({"Tetrahedron": (self.tetrahedron.crawl, {"dir": 1}),
                "DWAT": (self.diamond_with_a_tail.crawl_left, {}),
                "Triangle": (self.triangle.crawl_2, {})}[self.substructure]),
            'b': ({"Tetrahedron": (self.tetrahedron.crawl, {"dir": 2}),
                "Triangle": (self.triangle.crawl_3, {})}[self.substructure]),
            'd': ({"Tetrahedron": (self.tetrahedron.crawl, {"dir": 0, "is_ratchet": True, "single_link": self.links[-1]}),
                "DWAT": (self.diamond_with_a_tail.crawl, {})}[self.substructure]),
            'f': (self.tetrahedron.crawl, {"dir": 1, "is_ratchet": True, "single_link": self.links[-1]}),
            'g': (self.tetrahedron.crawl, {"dir": 2, "is_ratchet": True, "single_link": self.links[-1]}),
            'r': (self.tetrahedron.reset_rachet, {"dir": 1, "single_link": self.links[-1]}),
            'o': (self.triangle.rotate, {"dir": 'ccw'}),
            'p': (self.triangle.rotate, {"dir": 'cw'}),
        }

        for k in keys:
            if type(k) == keyboard.KeyCode:
                try:
                    k_val = k.char #type str

                    # change single link crawling direction
                    if (k_val in dirs) and self.is_numlock_on():
                        self.single_link_crawl_dir = dirs[k_val]
                        print(f"changing crawling direction to SRV{self.single_link_crawl_dir}")
                        return
                    
                    # select links
                    if k_val.isdigit():
                        selected_links.append(int(k_val) - 1)
                    
                    # contract or expand all
                    if k_val in global_commands:
                        selected_links = [idx for idx in range(len(self.link_ids))]
                        state, mode, param = global_commands[k_val]
                    
                    # execute gait
                    if k_val in key_actions:
                        action, params = key_actions[k_val]
                        debug_print(f"detecting {k_val}")
                        self.event.clear()
                        action(self.event, **params)
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
                if self.single_links[l].event.is_set():
                    t = threading.Thread(target=self.single_links[l].crawl, args=(self.single_link_crawl_dir, 100), daemon=True)
                    t.start()
                else:
                    self.single_links[l].event.set()
                    print(f"Stopping link P{self.link_ids[l] - 1}")
            return

        # check which servos are being activated
        param_dict = {[1, 1]: 2, [1, 0]: 0, [0, 1]: 1}
        param = param_dict[srv]

        #check invalid command
        if ((not state) or (len(selected_links) == 0) or (mode == -1)):
            if self.is_sticky:
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

    def _execute_state(self, links_idx, state):
        regular_links = []
        end_effectors = []

        regular_links = [i for i in links_idx if i not in self.end_effectors]
        end_effectors = [i for i in links_idx if i in self.end_effectors]

        srv0_pos, srv1_pos = self.state_to_pos_command(state, srv0_min=MIN_POS)
        self._set_link_pos(regular_links, srv0_pos, srv1_pos)
        srv0_pos, srv1_pos = self.state_to_pos_command(state, srv0_min=ZERO_POS)
        self._set_link_pos(end_effectors, srv0_pos, srv1_pos)

    def _set_link_pos(self, link_idx, srv0_pos, srv1_pos):  
        for i in link_idx:
            link_id = self.link_ids[i]
            current_srv0_pos, current_srv1_pos = self.link_states_pretty.get(link_id, (MIN_POS, MIN_POS))

            updated_srv0_pos = srv0_pos if srv0_pos is not None else current_srv0_pos
            updated_srv1_pos = srv1_pos if srv1_pos is not None else current_srv1_pos

            self.link_states_pretty[link_id] = updated_srv0_pos, updated_srv1_pos
            self.links[i].send_position_only(updated_srv0_pos, updated_srv1_pos)
            
    def state_to_pos_command(self, state, srv0_min=22):
        state, mode, param = state
        MAX_POS = 100
        MIN_POS = 22
    
        pos_map = {
            (1, 0): (MAX_POS, None),
            (1, 1): (None, MAX_POS),
            (1, 2): (MAX_POS, MAX_POS),
            (0, 0): (srv0_min, None),
            (0, 1): (None, MIN_POS),
            (0, 2): (srv0_min, MIN_POS),
        }
        
        srv0_pos, srv1_pos = pos_map.get((mode, param), (None, None))
        return (srv0_pos, srv1_pos)
    
    def on_press(self, key):
        if key in self.current_keys: return
        self.current_keys.add(key)
        if key == KeyCode.from_char('s'):
            self.reset()
            self.event.set()
            for link in self.single_links:
                link.event.set()
            debug_print("stopping...")

    def on_release(self, key):
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
        if 'LED_NUML' in active_LEDs:
            return True
        return False

def main(nr_links):
    try:
        # Initialize Server
        server = linknetworking.get_default_server()

        my_dashboard = dashboard.Dashboard(server, list(range(35)), open_in_browser=True)
        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
            continue
        

        debug_print("STARTING SCRIPTS!!!!!")
        # Initialize manual controller
        mnctrl = ManualController(server)
        mnctrl.run()
    except Exception as e:
        print(e)
    
    finally:
        server.close_server()
        my_dashboard.close()
        exit()
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Select nr of links to manually control')
    parser.add_argument(dest='nr_links', type=int, help="An integer argument")
    args = parser.parse_args()
    nr_links = args.nr_links

    #nr_links = 4
    main(nr_links)

