# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Last updated: Dec 13, 2022
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

        # Get tetrahedron links
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
        self.left = self.links[0]
        self.right = self.links[1]
        self.back = self.links[2]
    
    def crawl_1(self, event, steps=100):
        print(f"Triangle starts crawling...")
        event.clear()
        for i in range(steps):
            if event.is_set(): return
            #self.back.send_position_only(self.LOW_MID_POS, self.LOW_MID_POS)
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            event.wait(self.t)

            if event.is_set(): return
            self.left.send_position_only(self.MAX_POS, self.MIN_POS)
            self.right.send_position_only(self.MAX_POS, self.MIN_POS)
            #self.back.send_position_only(self.MID_POS, self.MID_POS)
            #self.back.send_position_only(65, 65)
            event.wait(self.t)

            if event.is_set(): return
            self.back.send_position_only(self.MID_POS, self.MID_POS)
            self.left.send_position_only(self.MIN_POS, self.MAX_POS)
            self.right.send_position_only(self.MIN_POS, self.MAX_POS)
            event.wait(self.t)
    
    def crawl_2(self, event, steps=100):
        print(f"Triangle starts crawling...")
        event.clear()
        for i in range(steps):
            if event.is_set(): return
            #self.back.send_position_only(self.LOW_MID_POS, self.LOW_MID_POS)
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            event.wait(self.t)

            if event.is_set(): return
            self.left.send_position_only(self.MIN_POS, self.MAX_POS)
            self.back.send_position_only(self.MAX_POS, self.MIN_POS)
            #self.back.send_position_only(self.MID_POS, self.MID_POS)
            #self.back.send_position_only(65, 65)
            event.wait(self.t)

            if event.is_set(): return
            self.right.send_position_only(self.MID_POS, self.MID_POS)
            self.back.send_position_only(self.MIN_POS, self.MAX_POS)
            self.left.send_position_only(self.MAX_POS, self.MIN_POS)
            event.wait(self.t)
    
    def crawl_3(self, event, steps=100):
        print(f"Triangle starts crawling...")
        event.clear()
        for i in range(steps):
            if event.is_set(): return
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            event.wait(self.t)

            if event.is_set(): return
            self.right.send_position_only(self.MIN_POS, self.MAX_POS)
            self.back.send_position_only(self.MIN_POS, self.MAX_POS)
            #self.back.send_position_only(self.MID_POS, self.MID_POS)
            #self.back.send_position_only(65, 65)
            event.wait(self.t)

            if event.is_set(): return
            self.left.send_position_only(self.MID_POS, self.MID_POS)
            self.right.send_position_only(self.MAX_POS, self.MIN_POS)
            self.back.send_position_only(self.MAX_POS, self.MIN_POS)

    def rotate(self, event, dir='ccw'):
        event.clear()

        print("Triangle rotating")
        for i in range(100):
            #print(f'rotating with pivot link {pivot.device_id}')
            self.left.send_position_only(self.MIN_POS, self.MIN_POS)
            self.right.send_position_only(self.MIN_POS, self.MIN_POS)
            self.back.send_position_only(self.MIN_POS, self.MIN_POS)

            if dir == 'ccw':
                event.wait(self.t)
                self.left.send_position_only(self.MIN_POS, self.MAX_POS)
                self.right.send_position_only(self.MAX_POS, self.MIN_POS)
                self.back.send_position_only(self.MAX_POS, self.MIN_POS)
                event.wait(self.t)
                self.back.send_position_only(self.MIN_POS, self.MAX_POS)
            elif dir == 'cw':
                event.wait(self.t)
                self.left.send_position_only(self.MAX_POS, self.MIN_POS)
                self.right.send_position_only(self.MIN_POS, self.MAX_POS)
                self.back.send_position_only(self.MIN_POS, self.MAX_POS)
                event.wait(self.t)
                self.back.send_position_only(self.MAX_POS, self.MIN_POS)

            event.wait(self.t)
    