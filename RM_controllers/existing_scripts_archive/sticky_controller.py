from itsdangerous import NoneAlgorithm
from pynput.keyboard import Key, Listener
from pynput import keyboard
from pynput.keyboard import Key
import linknetworking as linknetworking
import RM_dashboard.dashboard as dashboard
import argparse
from time import sleep
import csv

#param: selected servos
#mode: expand or contract

MAX_POS = 100
MIN_POS = 0
DEBUG = False
def debug_print(*args):
    if DEBUG:
        print(args)

class ManualController:
    def __init__(self, server=None):
        print("initializing controller")
        
        self.server = server
        self.links = []
        self.link_ids = sorted(list(server.links.keys()))
        for id in self.link_ids:
            self.links.append(server.links[id])
        print("Link IDs: ", self.link_ids)
        self.link_ids = [0, 11, 21]
        self.link_states = dict()
        self.link_pos = dict()
        self._log_buffer = []
        self.play_mode = 0
        self.MAX_STATE_BUFFER_SIZE = 4
        self._state_idx = 0
        self._link_states_buffer = [[] for i in range(self.MAX_STATE_BUFFER_SIZE)]

        self.srv0_pos = 0
        self.srv1_pos = 0
        self.last_command = ([], 1, 0, 2)
        print("manual controller initialized")


    def run(self):
        while True:
            self._command_parse() # get all current commands
            sleep(1)


    def _command_parse(self):
        global current_keys
        selected_links = []
        state = 0
        mode = -1
        param = -1
        srv = [0,0]
        self.play_mode = 0
        #print("parsing keys...", current_keys)
        for k in current_keys:
            if type(k) == keyboard.KeyCode: # removed keyboard._xorg.KeyCode
                try:
                    selected_links.append(int(str(k)[1:-1]))
                except:
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
        print(selected_links)
        debug_print("selected links: ", selected_links)

        #invalid command
        #param = -1: no servo selected
        #mode = -1: no servo positions provided
        #selected_links empty: no links selected
        if ((not state) or (len(selected_links) == 0) or (mode == -1)):
            selected_links, state, mode, param = self.last_command
        else:
            selected_links.sort()
            self.last_command = (selected_links, state, mode, param)
        self._execute_state(selected_links, (state, mode, param))
        


    def _execute_state(self, links_idx, state):
        self._set_link_pos(links_idx, state)
        # if not link_id in self.server.links:
        #     return -1
        # if state[0]:
        #     self._set_link_pos(link_id, state)

    def _set_link_pos(self, link_idx, state):
        state, mode, param = state

        srv0_pos, srv1_pos = 0, 0
        
        if mode == 1:
            debug_print("expanding something")
            if param == 0:
                srv0_pos = MAX_POS
            elif param == 1:
                srv1_pos = MAX_POS
            elif param == 2:
                srv0_pos = MAX_POS
                srv1_pos = MAX_POS
        elif mode == 0:
            debug_print("contracting something")
            if param == 0:
                srv0_pos = MIN_POS
            elif param == 1:
                srv1_pos = MIN_POS
            elif param == 2:
                srv0_pos = MIN_POS
                srv1_pos = MIN_POS
        self.srv0_pos, self.srv1_pos = srv0_pos, srv1_pos

        for i in link_idx:
            self.links[i].send_position_only(srv0_pos, srv1_pos)
            print(f"Sending position command ({srv0_pos,srv1_pos}) to link {self.link_ids[i]}")
#
# Keybaord Tracking Code
#
current_keys = set()
def on_press(key):
    global current_keys
    if key in current_keys:
        return
        #print("current keys: ", current_keys)
        #print('{0} repeated'.format(key))
    else:
        current_keys.add(key)

def on_release(key):
    global current_keys
    #print('{0} release'.format(key))
    #print("current_keys: ", current_keys)
    current_keys.remove(key)
    if key == Key.esc:
        # Stop listener
        print("Stopped_listening")
        return False

def main(nr_links):
    try:
        # Initialize Server
        server = linknetworking.get_default_server()

        my_dashboard = dashboard.Dashboard(server, list(range(34)), open_in_browser=True)

        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
            continue

        # Collect events until released
        listener =  Listener(
                on_press=on_press,
                on_release=on_release)
        listener.setDaemon(True)
        listener.start()

        print("STARTING SCRIPTS!!!!!")
        # Initialize manual controller
        mnctrl = ManualController(server)
        mnctrl.run()
    finally:
        print("FINALLY")
        from IPython import embed; embed()
        if server is not None:
            server.close_server()
        if listener is not None:
            listener.join()
        if my_dashboard is not None:
            my_dashboard.close()
        exit()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Select nr of links to manually control')
    parser.add_argument(dest='nr_links', type=int, help="An integer argument")
    args = parser.parse_args()
    nr_links = args.nr_links

    main(nr_links)