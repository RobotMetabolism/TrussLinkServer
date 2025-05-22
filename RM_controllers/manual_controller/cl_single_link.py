import threading


# Qi's version

class SingleLink:
    def __init__(self, link, link_id=None, MIN_POS=22, MAX_POS=100):
        self.MIN_POS = MIN_POS
        self.MAX_POS = MAX_POS
        self.link = link
        self.name = "" if link_id is None else f"P{link_id - 1}"
        self.event = threading.Event()
        self.event.set()
        # newly implmented pose 
        self.pose
    
    def crawl(self, dir=0, steps=100):
        print(f"link {self.name} start crawling in SRV{dir} direction")
        self.event.clear()
        for i in range(steps):
            if self.event.is_set(): return
            if dir:
                self.link.send_position_only(self.MIN_POS, self.MAX_POS)
            else:
                self.link.send_position_only(self.MAX_POS, self.MIN_POS)
            self.event.wait(12)

            if self.event.is_set(): return
            if dir:
                self.link.send_position_only(self.MAX_POS, self.MIN_POS)
            else:
                self.link.send_position_only(self.MIN_POS, self.MAX_POS)
            self.event.wait(12)

            if self.event.is_set(): return
            self.link.send_position_only(self.MIN_POS, self.MIN_POS)
            self.event.wait(12)

    # link it with the retinas.
    def get_pose():

    def apply_control(control_val):
        # Using the control value to adjust the position in some way.
        # This is a dummy logic for demonstration purposes.
        adjustment = control_val * 0.01
        x, y, z = self.get_pose() # will get centorid and e
        x += adjustment
        y += adjustment
        self.pose = (x, y, z)  # Assuming pose is a tuple (x, y, z)
        self.link.send_position_only(x, y)  # Updating the position


        # if the distance between goal_pos and link_pos is increasing again

        # elif < 0.05




# class SingleLink:
#     def __init__(self, server, link_id, MIN_POS=22, MAX_POS=100, MID_POS=50):
#         self.server = server
#         self.link_id = link_id
#         self.MIN_POS = MIN_POS
#         self.MAX_POS = MAX_POS
#         self.MID_POS = MID_POS
#         self.current_pos = MID_POS

#     def send_position_only(self, pos_x, pos_y):
#         # this method sends position commands to the server for this link
#         print(f"Sending position for link {self.link_id} to {pos_x}, {pos_y}")
#         # Assuming there's a method in the server to receive this command:
#         self.server.send_position(self.link_id, pos_x, pos_y)
#         self.current_pos = (pos_x, pos_y)

#     def get_position(self):
#         # Fetch current position from the server (if required) or return local copy
#         return self.current_pos

#     def move_to(self, pos_x, pos_y):
#         # Moves the link to the given position
#         self.send_position_only(pos_x, pos_y)

