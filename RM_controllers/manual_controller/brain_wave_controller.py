import pickle
import sys
sys.path.append('/home/robotmetabolism/Downloads/particleTrussServer-master/RM_controllers-main/manual_controller/')
sys.path.append("/home/robotmetabolism/Downloads/particleTrussServer-master")
from linknetworking import LinkServer
from cl_triangle import Triangle

import socket
from time import sleep
import threading


class BrainWaveController:

    def __init__(self, server= None, substructure = "Triangle"):
        print("initialing controller")

        self.server = server
        self.links = []  # RobotLink instances

        self.link_ids = sorted(list(server.links.keys()))
        
        for id in self.link_ids:
            # Add instance of robot link to self.links list
            # these are robot link instances links[0] = RobotLink instance
            self.links.append(server.links[id]) 

        print("self.links: ", self.links)
        print("Link IDs: ", self.link_ids)


        self.substructure = substructure
        self.triangle = None
        
        if substructure == "Triangle":
            self.triangle = Triangle(self.server, link_ids = self.link_ids[:3])


    def run(self):
        # debug_print("running...")

        print("running...")
        #server_ip = '192.168.16.1'
        server_ip = '192.168.0.205'
        # I'm assuming this is the port the bw server is running on (for BW Data)
        bw_server_port = 12345

        # setting up client socket to receive data from BW
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, bw_server_port))

            while True:
                print("True")
                data = s.recv(4096)
                if not data:
                    break
                self.control_robot(data)

                sleep(1)

        self.server.close_server()


    def control_robot(self, decoded_data):

        command = pickle.loads(decoded_data)
        print(f"Received command: {command}")

        if self.substructure == "Triangle":

            # self.triangle intializes with .event as set
            # triangle can only crawl or rotate if .event is set
            if self.triangle.event.is_set():

                if command == "tongue":
                    self.triangle.event.clear()
                    t = threading.Thread(target=self.triangle.crawl, args=(1, 1), daemon=True)
                    t.start()
                    
                elif command == "feet":
                    self.triangle.event.clear()
                    t = threading.Thread(target=self.triangle.rotate, args=('cw', 1), daemon=True)
                    t.start()

        else:
            print("triangle is still crawling or rotating, please wait...")


def main(nr_links):

    try:

        server = LinkServer(host='', port=54657, log=False)
        print(server)
        print(server.links)

        # my_dashboard = dashboard.Dashboard(server, list(range(35)), open_in_browser=True)
        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
        
        bwctrl = BrainWaveController(server)
        bwctrl.run()

    except Exception as exception:
        print(exception)


if __name__ == '__main__':
    nr_links = 3 # for triangle
    main(nr_links)