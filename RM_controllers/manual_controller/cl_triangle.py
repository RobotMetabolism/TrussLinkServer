# Author: Simon Kang simon.kang@columbia.edu
# Last updated: Nov 19, 2023
import threading

class Triangle:
    def __init__(self, server, link_ids=None, MIN_POS=22, MAX_POS=100, MID_POS=50):
        self.MIN_POS = MIN_POS
        self.MAX_POS = MAX_POS
        self.MID_POS = MID_POS
        self.LOW_MID_POS = 31
        self.HIGH_MID_POS = 75
        self.server = server
        self.t = 12

        # Get triangle links
        print("Initializing triangle...")
        if link_ids is None:
            self.link_ids = sorted(list(self.server.links.keys()))
        else:
            assert len(link_ids) == 3, "Triangle initialization error: number of links should be: 3"
            self.link_ids = link_ids
        print("Triangle Link IDs: ", self.link_ids)

        self.links = []
        for id in self.link_ids:
                self.links.append(self.server.links[id])
        self.back = self.links[0]
        self.left = self.links[1]
        self.right = self.links[2]

        self.event = threading.Event()
        self.event.set()
    
    def crawl(self, dir, steps=1):
        print(f"Triangle starts crawling...")
        for i in range(steps):
            if self.event.is_set(): break
            #self.back.send_position_only(self.LOW_MID_POS, self.LOW_MID_POS)
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            self.event.wait(self.t)

            if self.event.is_set(): break
            if dir == 1:
                self.left.send_position_only(self.MAX_POS, self.MIN_POS)
                self.right.send_position_only(self.MAX_POS, self.MIN_POS)
            elif dir == -1:
                self.left.send_position_only(self.MIN_POS, self.MAX_POS)
                self.right.send_position_only(self.MIN_POS, self.MAX_POS)
            #self.back.send_position_only(self.MID_POS, self.MID_POS)
            #self.back.send_position_only(65, 65)
            self.event.wait(self.t)

            if self.event.is_set(): break
            if dir == 1:
                self.back.send_position_only(self.MID_POS, self.MID_POS)
                self.left.send_position_only(self.MIN_POS, self.MAX_POS)
                self.right.send_position_only(self.MIN_POS, self.MAX_POS)
            elif dir == -1:
                self.back.send_position_only(self.MID_POS, self.MID_POS)
                self.left.send_position_only(self.MAX_POS, self.MIN_POS)
                self.right.send_position_only(self.MAX_POS, self.MIN_POS)
            self.event.wait(self.t)
        
        # this is to make sure the triangle gets back to the default position
        self.back.send_position_only(self.MIN_POS, self.MIN_POS)
        self.left.send_position_only(self.MIN_POS, self.MIN_POS)
        self.right.send_position_only(self.MIN_POS, self.MIN_POS)
        # crawling is done, set the event flag to true
        self.event.set()
    
    # def crawl_2(self, event, steps=100):
    #     print(f"Triangle starts crawling...")
    #     event.clear()
    #     for i in range(steps):
    #         if event.is_set(): return
    #         #self.back.send_position_only(self.LOW_MID_POS, self.LOW_MID_POS)
    #         self.back.send_position_only(self.MIN_POS, self.MIN_POS)
    #         self.left.send_position_only(self.MIN_POS, self.MIN_POS)
    #         self.right.send_position_only(self.MIN_POS, self.MIN_POS)
    #         event.wait(self.t)

    #         if event.is_set(): return
    #         self.left.send_position_only(self.MIN_POS, self.MAX_POS)
    #         self.back.send_position_only(self.MAX_POS, self.MIN_POS)
    #         #self.back.send_position_only(self.MID_POS, self.MID_POS)
    #         #self.back.send_position_only(65, 65)
    #         event.wait(self.t)

    #         if event.is_set(): return
    #         self.right.send_position_only(self.MID_POS, self.MID_POS)
    #         self.back.send_position_only(self.MIN_POS, self.MAX_POS)
    #         self.left.send_position_only(self.MAX_POS, self.MIN_POS)
    #         event.wait(self.t)
    
    # def crawl_3(self, event, steps=100):
    #     print(f"Triangle starts crawling...")
    #     event.clear()
    #     for i in range(steps):
    #         if event.is_set(): return
    #         self.back.send_position_only(self.MIN_POS, self.MIN_POS)
    #         self.left.send_position_only(self.MIN_POS, self.MIN_POS)
    #         self.right.send_position_only(self.MIN_POS, self.MIN_POS)
    #         event.wait(self.t)

    #         if event.is_set(): return
    #         self.right.send_position_only(self.MIN_POS, self.MAX_POS)
    #         self.back.send_position_only(self.MIN_POS, self.MAX_POS)
    #         #self.back.send_position_only(self.MID_POS, self.MID_POS)
    #         #self.back.send_position_only(65, 65)
    #         event.wait(self.t)

    #         if event.is_set(): return
    #         self.left.send_position_only(self.MID_POS, self.MID_POS)
    #         self.right.send_position_only(self.MAX_POS, self.MIN_POS)
    #         self.back.send_position_only(self.MAX_POS, self.MIN_POS)

    def rotate(self, dir, steps=1):

        print("Triangle rotating")
        for i in range(steps):
            #print(f'rotating with pivot link {pivot.device_id}')
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)

            if dir == 'ccw':
                print("rotating counter clockwise")
                self.event.wait(self.t)
                self.left.send_position_only(self.MIN_POS, self.MAX_POS)
                self.right.send_position_only(self.MAX_POS, self.MIN_POS)
                self.back.send_position_only(self.MAX_POS, self.MIN_POS)
                self.event.wait(self.t)
                self.back.send_position_only(self.MIN_POS, self.MAX_POS)
            elif dir == 'cw':
                print("rotating clockwise")
                self.event.wait(self.t)
                self.left.send_position_only(self.MAX_POS, self.MIN_POS)
                self.right.send_position_only(self.MIN_POS, self.MAX_POS)
                self.back.send_position_only(self.MIN_POS, self.MAX_POS)
                self.event.wait(self.t)
                self.back.send_position_only(self.MAX_POS, self.MIN_POS)

            self.event.wait(self.t)

        # this is to make sure the triangle gets back to the default position
        self.back.send_position_only(self.MIN_POS, self.MIN_POS)
        self.left.send_position_only(self.MIN_POS, self.MIN_POS)
        self.right.send_position_only(self.MIN_POS, self.MIN_POS)
        # rotating is done, set the event flag to true
        self.event.set()
    