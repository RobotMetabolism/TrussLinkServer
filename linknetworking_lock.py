from rmlprotocol import RMLPacker
import socket
import threading
import sys
import time
import logging

DEBUG = True

thread_Rlock = threading.RLock()
thread_lock = threading.Lock()

CLIENT_SOCKET_TIMEOUT = 15 # This is enough because communication is high frequency

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def safe_error_print(content):
    with thread_lock:
        eprint(*content)


def safe_print(content, my_end="\n"):
    if not DEBUG:
        return
    with thread_lock:
        print(content, end=my_end)


class LinkServer(threading.Thread):

    # A single object of this class will listen for Link Connection requests and then make new threads for each link

    def __init__(self, host, port, log=False):
        super().__init__()

        self.start_epoch_raw = time.time()
        self.start_epoch = int(time.time() + 0.5)
        self.log = log
        if self.log:
            logging.basicConfig(format='%(asctime)s - %(message)s', 
                                handlers=[
                                    logging.FileHandler("debug.log"),
                                    logging.StreamHandler()
                                ])
            logging.getLogger().setLevel(logging.INFO)
            logging.info(self.start_epoch)

        self.__is__running__ = True
        self.host = host
        self.port = port
        self.links = {}  # This will store all Link objects in a dictionary for device_name reference
        self.newest = None

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow same address to be used by multiple clients
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
        bound = False

        while not bound:
            try:
                safe_print("Trying to bind...")
                self.sock.bind((self.host, self.port))
                safe_print("Binded!")
                bound = True
            except OSError as e:
                time.sleep(1)

        self.start()

    def get_server_time(self):
        return int(time.time() + 0.5) - self.start_epoch

    def get_server_time_raw(self):
        return time.time() - self.start_epoch_raw

    def run(self):
        try:
            self.sock.listen(256)  # maximum number of clients in cue
            while self.__is__running__:
                try:
                    csock, caddr = self.sock.accept()
                except ConnectionAbortedError as e:
                    safe_error_print("Interrupted sock.accept due to server closing")

                safe_print("Accepted new Link")
                self.newest = RobotLink((csock, caddr), self)  # instantiate new client thread
                safe_print("Created new RobotLink Object")

        finally:
            self.close_server()

    # This function returns the size (number of links) in the dictionary

    def size(self):
        return len(self.links)

    # This function interrupts run thread loop
    # It also closes each link object in dictionary
    # It finally closes the listening socket

    def close_server(self):
        self.__is__running__ = False
        self.sock.close()
        all_device_ids = list(self.links.keys())

        for device_id in all_device_ids:
            if device_id in self.links:
                link = self.links[device_id]
                link.close_link()
        safe_print("Closed all links... Server has been closed.")


class RobotLink(threading.Thread):

    # An object of this class will be instantiated for each link that connects to the server
    # The thread will close automatically when the connection is broken

    def __init__(self, connection, server, log=False):
        super().__init__()
        self.__is__running__ = True
        self.connection = connection[0]
        self.addr = connection[1]
        
        self.connection.settimeout(CLIENT_SOCKET_TIMEOUT)

        self.server = server
        self.log = log
        self.device_id = None
        self.device_status = None
        self.srv0_pos = None
        self.srv1_pos = None
        self.srv0_raw = None
        self.srv1_raw = None
        self.bat_status = None
        self.srv0_vel = None
        self.srv1_vel = None
        self.MAX_VEL = None

        self.version = None

        self.srv0_min_ms = None
        self.srv0_max_ms = None

        self.srv1_min_ms = None
        self.srv1_max_ms = None

        self.srv0_raw_min = None
        self.srv0_raw_max = None

        self.srv1_raw_min = None
        self.srv1_raw_max = None

        self.received_package_queue = []

        self.executing_command_checksum = 0

        self.last_sent_package = None
        self.current_command_checksum = 0

        self.start()

    def receive_package(self):
        checksum_verified = False
        while not checksum_verified:
            header = self.connection.recv(2)
            length, package_type = RMLPacker.decode_header(header)
            body = self.connection.recv(length)
            footer = self.connection.recv(2)

            checksum_verified = RMLPacker.verify_checksum(header, body, footer)

            # if not checksum_verified:
            #     # negative_ack_package = RMLPacker.make_ack_package(0)
            #     # self.connection.send(negative_ack_package)

        # positive_ack_package = RMLPacker.make_ack_package(255)
        # self.connection.send(positive_ack_package)

        # safe_print("PACKAGE from "+str(self.device_id)+": " + str(package_type))
        # safe_print(bytearray(header).hex())
        # safe_print(bytearray(body).hex())
        # safe_print(bytearray(footer).hex())

        received_package = RMLPacker.decode(package_type, body)
        return received_package, package_type.decode("ASCII")

    def run(self):
        try:

            # When Link Thread begins, Hello package is expected.

            package, package_type = self.receive_package()

            if package_type != "H":  # Check if package is indeed Hello, else quit
                raise AssertionError("Hello package not received. Closing Link Object")

            self.device_id = package[0]
            self.MAX_VEL = package[1]

            if self.device_id in self.server.links:
                safe_print("Overwriting existing link " + str(self.device_id))
                self.server.links[self.device_id].close_link()

            self.server.links[self.device_id] = self

            safe_print("Sending epoch...")
            self.send_epoch_package()

            safe_print("P" + str(self.device_id) + " said Hello. Total is " + str(self.server.size()) + ". Sent epoch!")

            while self.__is__running__:
                package, package_type = self.receive_package()

                if package_type == "C":
                    pass

                elif package_type == "U":
                    self.device_status = package[0].decode("ASCII")
                    self.srv0_pos = package[1]
                    self.srv1_pos = package[2]
                    self.srv0_raw = package[3]
                    self.srv1_raw = package[4]
                    self.bat_status = (package[5]-25) # shifting values so 0 = change battery immediately
                    self.srv0_vel = package[6]
                    self.srv1_vel = package[7]
                    self.executing_command_checksum = package[8]
                    if self.log:
                        logging.info((self.device_id, self.current_command_checksum, self.executing_command_checksum))
                    if self.executing_command_checksum != self.current_command_checksum:
                        #print('executing command different from sent command, link ID: ', self.device_id)
                        self.send_package(self.last_sent_package, self.current_command_checksum)

            self.connection.close()

        except socket.timeout as e:
            safe_error_print(str(e))
            safe_error_print("Link " + str(self.device_id) + " timed out")

        except Exception as e:
            safe_print(e)

        finally:
            self.close_link()
            self.connection.close()

    # The functions below accept parameters and send them to the link.
    # They return whether the package was successfully sent

    def send_package(self, header_and_body, checksum):
        # safe_print("Sending... ")
        with thread_Rlock:
            self.last_sent_package = header_and_body
            if type(checksum) == type(b''):
                self.current_command_checksum = int.from_bytes(checksum, byteorder="big")
            else:
                self.current_command_checksum = checksum
                checksum = int(checksum).to_bytes(2, 'big')

            # safe_print(bytearray(checksum).hex())
            # MODIFIED PART
            try:
                result = self.connection.send(header_and_body + checksum[1:2] + checksum[0:1])
                return result == len(header_and_body + checksum)
            except OSError as e:
                print(f"Error sending data: {e}")

            # END OF MODIFICATION
            # result = self.connection.send(header_and_body + checksum[1:2] + checksum[0:1])
            # return result == len(header_and_body + checksum)

    def send_calibrate_package(self):
        header_and_body, checksum = RMLPacker.make_calibrate_package()
        return self.send_package(header_and_body, checksum)

    def send_position_package(self, srv0_pos, srv1_pos, srv0_vel, srv1_vel):
        (self.srv0_pos, self.srv1_pos, self.srv0_vel, self.srv1_vel) = (srv0_pos, srv1_pos, srv0_vel, srv1_vel)
        header_and_body, checksum = RMLPacker.make_position_package(srv0_pos, srv1_pos, srv0_vel, srv1_vel)
        return self.send_package(header_and_body, checksum)

    def send_sinusoidal_package(self, start_time, a0, x0, ps0, p0, a1, x1, ps1, p1):
        header_and_body, checksum = RMLPacker.make_sinusoidal_package(start_time, a0, x0, ps0, p0, a1, x1, ps1, p1)
        return self.send_package(header_and_body, checksum)

    def send_walk_package(self, nr_steps):
        header_and_body, checksum = RMLPacker.make_walk_package(nr_steps)
        return self.send_package(header_and_body, checksum)

    def send_epoch_package(self):
        header_and_body, checksum = RMLPacker.make_epoch_package(self.server.start_epoch)
        return self.send_package(header_and_body, checksum)

    def send_position_only(self, srv0_pos, srv1_pos):
        return self.send_position_package(srv0_pos, srv1_pos, 100, 100)

    def send_list(self, body):
        header_and_body, checksum = RMLPacker.make_list(body)
        return self.send_package(header_and_body, checksum)

    # This function interrupts run thread loop
    # It also closes the connection socket
    # It also removes self from server dictionary

    def close_link(self):
        self.__is__running__ = False
        if self.device_id in self.server.links:
            self.server.links.pop(self.device_id)
            self.connection.close()
        safe_print("Closed Link " + str(self.device_id))


class ListMaker:

    @staticmethod
    def HEAD(nr_repeat, list_start_time):
        return RMLPacker.make_list_header(nr_repeat, list_start_time)

    @staticmethod
    def POSVEL(srv0_pos, srv1_pos, srv0_vel, srv1_vel, duration):
        return RMLPacker.make_list_position(srv0_pos, srv1_pos, srv0_vel, srv1_vel, duration)

    @staticmethod
    def SIN(start_time, period, duration):
        return RMLPacker.make_list_sin(start_time, period, duration)

    @staticmethod
    def TAIL():
        return bytes([0]) + b'E'


DEFAULT_PORT = 54657  # "LINKS"
DEFAULT_HOST = ''     # my_ip()


def get_default_server(log=False):
    return LinkServer(DEFAULT_HOST, DEFAULT_PORT, log)
