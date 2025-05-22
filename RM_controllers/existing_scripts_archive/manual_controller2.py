from pynput.keyboard import Key, Listener
from pynput import keyboard
from pynput.keyboard import Key
import linknetworking as linknetworking
import RM_dashboard.dashboard as dashboard
import argparse
from time import sleep
import logging, sys


#param: selected servos
#mode: expand or contract

MAX_POS = 100
MIN_POS = 22

DEBUG = True
def debug_print(msg):
    if DEBUG:
        print(msg)

class ManualController:
    def __init__(self, server=None, mode="Sticky"):
        print("initializing controller")
        if mode == "Sticky":
            self.is_sticky = True
        else:
            self.is_sticky = False
        
        self.server = server
        self.links = []
        self.link_ids = sorted(list(server.links.keys()))
        for id in self.link_ids:
            self.links.append(server.links[id])
        print("Link IDs: ", self.link_ids)

        # self.link_ids = [6, 7, 8, 9, 10, 11]
        self.link_states = {}
        self.link_states_pretty = {}
        debug_print("manual controller initialized")


    def run(self):
        debug_print('running..."')
        while True:
            self._command_parse() # get all current commands
            sleep(0.5)


    def _command_parse(self):
        global current_keys
        selected_links = []
        state = 0
        mode = -1
        param = -1
        srv = [0,0]
        #debug_print(f"parsing keys... {current_keys}" )
        for k in current_keys:
            
            if type(k) == keyboard.KeyCode:
                try:
                    k_val = str(k)[1:-1]
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
                except:
                    debug_print("unrecognized key")
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

    def _execute_state(self, links_idx, state):
        srv0_pos, srv1_pos = self.state_to_pos_command(state)
        self._set_link_pos(links_idx, srv0_pos, srv1_pos)

    def _set_link_pos(self, link_idx, srv0_pos, srv1_pos):
        for i in link_idx:
            if self.link_ids[i] in self.link_states_pretty:
                srv0_pos = self.link_states_pretty[self.link_ids[i]][0] if srv0_pos is None else srv0_pos
                srv1_pos = self.link_states_pretty[self.link_ids[i]][1] if srv1_pos is None else srv1_pos
            else:
                srv0_pos = MIN_POS if srv0_pos is None else srv0_pos
                srv1_pos = MIN_POS if srv1_pos is None else srv1_pos
            self.link_states_pretty[self.link_ids[i]] = srv0_pos, srv1_pos # update states for sticky operation
            debug_print(f"Sending position command ({srv0_pos,srv1_pos}) to link {self.link_ids[i]}")
            self.links[i].send_position_only(srv0_pos, srv1_pos)
            
        
    
    def state_to_pos_command(self, state):
        state, mode, param = state

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
                srv0_pos = MIN_POS
            elif param == 1:
                srv1_pos = MIN_POS
            elif param == 2:
                srv0_pos = MIN_POS
                srv1_pos = MIN_POS
        return (srv0_pos, srv1_pos)
#
# Keybaord Tracking Code
#
current_keys = set()
def on_press(key):
    global current_keys
    if key in current_keys:
        return
        #debug_print(f"current keys: {current_keys}")
        #debug_print('{0} repeated'.format(key))
    else:
        current_keys.add(key)

def on_release(key):
    global current_keys
    #debug_print('{0} release'.format(key))
    #debug_print(f"current_keys: {current_keys}")
    
    if key not in current_keys:
        current_keys.clear()
    else:
        current_keys.remove(key)
    if key == Key.esc:
        # Stop listener
        debug_print("Stopped_listening")
        return False
    

def main(nr_links):
    try:
        # Collect events until released
        listener =  Listener(
                on_press=on_press,
                on_release=on_release)
        listener.start()

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
    finally:
        server.close_server()
        listener.join()
        my_dashboard.close()
        exit()
        



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Select nr of links to manually control')
    parser.add_argument(dest='nr_links', type=int, help="An integer argument")
    args = parser.parse_args()
    nr_links = args.nr_links

    main(nr_links)