# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Last updated: Oct 23, 2022
from time import sleep

class DiamondWithATail:
    def __init__(self, server, link_ids=None, MIN_POS=22, MAX_POS=100, MID_POS=50) -> None:
        
        self.MIN_POS = MIN_POS
        self.MAX_POS = MAX_POS
        self.MID_POS = MID_POS
        self.server = server
        self.t = 12

        # Get diamond with a tail links
        print("Initializing diamond with a tail...")
        if link_ids is None:
            self.link_ids = sorted(list(self.server.links.keys()))
        else:
            assert len(link_ids) == 6, "Tetrahedron initialization error: number of links should be six"
            self.link_ids = link_ids
        print("Tetrahedron Link IDs: ", self.link_ids)

        self.links = []
        for id in self.link_ids:
                self.links.append(self.server.links[id])
    
    # contract all links
    def contract(self):
        for l in self.links:
            l.send_position_only(self.MIN_POS, self.MIN_POS)
    
    # crawl one step in the bl, br (bottom-left, bottom-right) direction
    def crawl_step(self, event, links=None):
        if links is None:
            bl, br, mid, fl, fr, tail = self.links
        else:
            fl, fr, mid, bl, br, tail = links
        
        # if event.is_set(): return
        # tail.send_position_only(self.MAX_POS, self.MIN_POS)
        # fl.send_position_only(self.MAX_POS, self.MIN_POS)
        # fr.send_position_only(self.MAX_POS, self.MIN_POS)
        # bl.send_position_only(self.MAX_POS, self.MIN_POS)
        # br.send_position_only(self.MAX_POS, self.MIN_POS)
        # event.wait(12)


        if event.is_set(): return
        # fl.send_position_only(self.MIN_POS, self.MAX_POS)
        # fr.send_position_only(self.MIN_POS, self.MAX_POS)
        # bl.send_position_only(self.MIN_POS, self.MAX_POS)
        # br.send_position_only(self.MIN_POS, self.MAX_POS)
        # mid.send_position_only(self.MAX_POS, self.MAX_POS)
        # tail.send_position_only(self.MAX_POS, self.MAX_POS)
        bl.send_position_only(self.MIN_POS, self.MIN_POS)
        br.send_position_only(self.MIN_POS, self.MIN_POS)
        fl.send_position_only(self.MAX_POS, self.MAX_POS)
        fr.send_position_only(self.MAX_POS, self.MAX_POS)
        mid.send_position_only(self.MIN_POS, self.MIN_POS)
        tail.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)

        if event.is_set(): return
        bl.send_position_only(self.MAX_POS, self.MIN_POS)
        br.send_position_only(self.MAX_POS, self.MIN_POS)
        fl.send_position_only(self.MAX_POS, self.MIN_POS)
        fr.send_position_only(self.MAX_POS, self.MIN_POS)
        mid.send_position_only(75, 75)
        event.wait(12)

        if event.is_set(): return
        bl.send_position_only(self.MIN_POS, self.MAX_POS)
        br.send_position_only(self.MIN_POS, self.MAX_POS)
        fl.send_position_only(self.MAX_POS, self.MIN_POS)
        fr.send_position_only(self.MAX_POS, self.MIN_POS)
        event.wait(12)

        if event.is_set(): return
        bl.send_position_only(self.MIN_POS, self.MIN_POS)
        br.send_position_only(self.MIN_POS, self.MIN_POS)
        tail.send_position_only(self.MAX_POS, self.MIN_POS)
        event.wait(12)

        if event.is_set(): return
        fl.send_position_only(self.MIN_POS, self.MAX_POS)
        fr.send_position_only(self.MIN_POS, self.MAX_POS)
        tail.send_position_only(self.MIN_POS, self.MAX_POS)
        event.wait(12)

        if event.is_set(): return
        bl.send_position_only(self.MAX_POS, self.MIN_POS)
        br.send_position_only(self.MAX_POS, self.MIN_POS)
        fl.send_position_only(self.MIN_POS, self.MIN_POS)
        fr.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)

        # if event.is_set(): return
        # self.contract()
        # tail.send_position_only(self.MAX_POS, self.MIN_POS)
        # mid.send_position_only(self.MIN_POS, self.MIN_POS)
        # event.wait(12)
    
    # crawl one step in the bl, br (bottom-left, bottom-right) direction
    def crawl_left_step(self, event, links=None):
        if links is None:
            bl, br, mid, fl, fr, tail = self.links
        else:
            fl, fr, mid, bl, br, tail = links
        
        if event.is_set(): return
        tail.send_position_only(self.MAX_POS, self.MIN_POS)
        fl.send_position_only(self.MAX_POS, self.MIN_POS)
        fr.send_position_only(self.MAX_POS, self.MIN_POS)
        bl.send_position_only(self.MAX_POS, self.MIN_POS)
        br.send_position_only(self.MAX_POS, self.MIN_POS)
        mid.send_position_only(self.MAX_POS, self.MAX_POS)
        #tail.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)

        # if event.is_set(): return
        #tail.send_position_only(self.MAX_POS, self.MIN_POS)
        # event.wait(12)

        if event.is_set(): return
        fl.send_position_only(self.MIN_POS, self.MAX_POS)
        fr.send_position_only(self.MIN_POS, self.MAX_POS)
        bl.send_position_only(self.MIN_POS, self.MAX_POS)
        br.send_position_only(self.MIN_POS, self.MAX_POS)
        mid.send_position_only(self.MIN_POS, self.MIN_POS)
        tail.send_position_only(self.MAX_POS, self.MAX_POS)
        event.wait(12)

        # if event.is_set(): return
        # bl.send_position_only(self.MIN_POS, self.MIN_POS)
        # br.send_position_only(self.MIN_POS, self.MIN_POS)
        # mid.send_position_only(self.MIN_POS, self.MIN_POS)
        # event.wait(12)

        if event.is_set(): return
        self.contract()
        tail.send_position_only(self.MAX_POS, self.MIN_POS)
        event.wait(12)
    
    # crawl continuously
    def crawl(self, event, links=None, steps=100):
        print("Diamond with a tail crawling...")
        for i in range(steps):
            print(f"DWAT crawl: step {i+1}")
            self.crawl_step(event, links=links)
            if event.is_set(): return
    
    # crawl continuously
    def crawl_left(self, event, links=None, steps=100):
        print("Diamond with a tail crawling...")
        for i in range(steps):
            print(f"DWAT crawl: step {i+1}")
            self.crawl_left_step(event, links=links)
            if event.is_set(): return

    def sleep(self, t=12):
        sleep(t)