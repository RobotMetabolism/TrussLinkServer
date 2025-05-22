# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Edits: Simon Kang simon.kang@columbia.edu
# Last updated: Nov 10, 2023
import threading

class SingleLink:
    def __init__(self, link, link_id=None, MIN_POS=22, MAX_POS=100):
        self.MIN_POS = MIN_POS
        self.MAX_POS = MAX_POS

        # link is RobotLink instance 
        self.link = link
        # link_id is used to set the name
        self.name = "" if link_id is None else f"P{link_id}"
        self.event = threading.Event()
        self.event.set()
    
    # changed steps to 5 for CL controller
    # was initially 100
    def crawl(self, dir=0, steps=1):
        print(f"link {self.name} start crawling in SRV{dir} direction")
        # self.event.clear() # internal flag is set to false, so wait() will block
        for i in range(steps):
            # crawling pauses when internal flag is set, makes it exit the loop
            if self.event.is_set(): break # break out of the loop
            if dir:
                self.link.send_position_only(self.MIN_POS, self.MAX_POS)
            elif dir == -1:
                self.link.send_position_only(self.MAX_POS, self.MIN_POS)
            self.event.wait(12)

            if self.event.is_set(): break
            if dir:
                self.link.send_position_only(self.MAX_POS, self.MIN_POS)
            elif dir == -1:
                self.link.send_position_only(self.MIN_POS, self.MAX_POS)
            self.event.wait(12)

            if self.event.is_set(): break
            self.link.send_position_only(self.MIN_POS, self.MIN_POS)
            self.event.wait(12)

        self.link.send_position_only(self.MIN_POS, self.MIN_POS)
        self.event.set()
    

        

