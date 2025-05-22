# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Last updated: Jan 1, 2023
from time import sleep
from utils import tetrahedron_plotter
from multiprocessing import Process, Pipe

class Vertex:
    def __init__(self, id):
        self.links = []
        self.id = id
        self.cw = True #clockwise or counterclockwise

    def set_links(self, links, cw=True):
        assert len(links) == 3, f"a tetrahedron vertex can only have 3 links: {len(links)} links given"
        self.links = links
        self.cw = cw

class Link:
    def __init__(self, link, id, v0, v1, color='black'):
        self.id = id #link id
        self.link = link #link object
        self.v0 = v0 #srv0 vertex
        self.v1 = v1 #srv1 vertex
        self.color = color # link color for plotting
    

class Tetrahedron:
    def __init__(self, server, link_ids=None, MIN_POS=22, MAX_POS=100, MID_POS=50) -> None:
        
        self.MIN_POS = MIN_POS
        self.MAX_POS = MAX_POS
        self.MID_POS = MID_POS
        self.LOW_MID_POS = 31
        self.HIGH_MID_POS = 75
        self.server = server
        self.t = 12

        # Get tetrahedron links
        print("Initializing tetrahedron...")
        if link_ids is None:
            self.link_ids = sorted(list(self.server.links.keys()))
        else:
            assert len(link_ids) == 6, "Tetrahedron initialization error: number of links should be six"
            self.link_ids = link_ids
        print("Tetrahedron Link IDs: ", self.link_ids)

        self.links = []
        for id in self.link_ids:
                self.links.append(self.server.links[id])
        
        # Set up tetrahedron as graph
        self.v1 = Vertex(1)
        self.v2 = Vertex(2)
        self.v3 = Vertex(3) 
        self.v4 = Vertex(4)
        self.l0 = Link(self.links[0], self.link_ids[0], self.v1, self.v2, 'darkorange')
        self.l1 = Link(self.links[1], self.link_ids[1], self.v1, self.v3, 'dodgerblue')
        self.l2 = Link(self.links[2], self.link_ids[2], self.v1, self.v4, 'yellowgreen')
        self.l3 = Link(self.links[3], self.link_ids[3], self.v4, self.v2, 'mediumpurple')
        self.l4 = Link(self.links[4], self.link_ids[4], self.v4, self.v3, 'palevioletred')
        self.l5 = Link(self.links[5], self.link_ids[5], self.v3, self.v2, 'gold')
        self.v1.set_links([self.l0, self.l1, self.l2], cw=True)
        self.v2.set_links([self.l0, self.l3, self.l5], cw=True)
        self.v3.set_links([self.l1, self.l4, self.l5], cw=False)
        self.v4.set_links([self.l2, self.l3, self.l4], cw=False)

        # Initialize tetrahedron pose
        self.top_vertex = self.v1
        
        # Initialize plot
        r_conn, s_conn = Pipe()
        p = Process(target=tetrahedron_plotter, args=(r_conn,))
        p.start()
        self.plotter = s_conn

        # Plot initial configuration
        links, _ = self.calculate_pose(dir=0)
        link_info = [(l.id, l.color) for l in links]
        self.plotter.send(link_info)

    
    # contract all links
    def contract(self):
        self.set_all(self.MIN_POS)

    # set position for all links    
    def set_all(self, position, exclude=[]):
        for l in self.links:
            if l not in exclude:
                l.send_position_only(position, position)
    
    def topple(self, event, dir=2, tail=None):
        #calculate pose
        link_edges, flip = self.calculate_pose(dir)  #the returned links are edges in graph, not RobotLinks
        ul, ur, ub, bl, br, bf = link_edges
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip

        # set new top vertex after topple
        self.top_vertex = ub.v0 if ub.v0.id != self.top_vertex.id else ub.v1

        # plot new configuration
        links, _ = self.calculate_pose(dir=0)
        link_info = [(l.id, l.color) for l in links]
        self.plotter.send(link_info)

        print(f"toppling in the P{ul.id}-P{ur.id} direction...")
        print(f"ub: P{ub.id}, ul: P{ul.id}, ur: P{ur.id}, bl: P{bl.id}, br: P{br.id}, bf: P{bf.id}")
        print(f"ub_flip: {ub_flip}, ul_flip: {ul_flip}, ur_flip: {ur_flip}, bl_flip: {bl_flip}, br_flip: {br_flip}")
        # execute topple
        links = [ul.link, ur.link, ub.link, bl.link, br.link, bf.link]
        self.execute_topple(event, links, flip)

        
    # topple in the ul-ur (upper-left, upper-right) direction
    def execute_topple(self, event, links, flip, bf_pos=80, tail=None):
        print("Toppling tetrahedron...")
        BF_POS = int(input('bottom front link (default: 80): \n'))
        topple_value = int(input('upper back link (default: 88): \n'))
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        #bf_pos = 87

        # expand
        if event.is_set(): return
        if ul_flip:
            ul.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ul.send_position_only(self.MIN_POS, self.MAX_POS)
        if ur_flip:
            ur.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MAX_POS)
        bf.send_position_only(BF_POS, BF_POS)
        event.wait(self.t)

        # topple
        #topple_value = 88 # used to be 90
        if event.is_set(): return
        if ub_flip:
            ub.send_position_only(self.MAX_POS, topple_value)
        else:
            ub.send_position_only(topple_value, self.MAX_POS)
        
        if tail is not None:
            event.wait(3)
            tail.send_position_only(self.MAX_POS, self.MIN_POS)
        event.wait(self.t)

        # if event.is_set(): return
        # if bl_flip:
        #     bl.send_position_only(self.MIN_POS, self.MAX_POS)
        # else:
        #     bl.send_position_only(self.MAX_POS, self.MIN_POS)
        # if br_flip:
        #     br.send_position_only(self.MIN_POS, self.MAX_POS)
        # else:
        #     br.send_position_only(self.MAX_POS, self.MIN_POS)
        # bl.send_position_only(self.MAX_POS, self.MAX_POS)
        # br.send_position_only(self.MAX_POS, self.MAX_POS)
        # ub.send_position_only(self.MAX_POS, self.MAX_POS)
        # event.wait(self.t)

        if event.is_set(): return
        self.contract()
        event.wait(self.t)
        

    def calculate_pose(self, dir):
        # identify upper links
        ub = self.top_vertex.links[dir]
        if self.top_vertex.cw:
            ul = self.top_vertex.links[(dir+1)%3]
            ur = self.top_vertex.links[(dir+2)%3]
        else:
            ur = self.top_vertex.links[(dir+1)%3]
            ul = self.top_vertex.links[(dir+2)%3]
        #get two bottom front vertices, the bottom front link is the link connecting them
        bf = None
        v1 = ul.v0 if ul.v0.id != self.top_vertex.id else ul.v1
        v2 = ur.v0 if ur.v0.id != self.top_vertex.id else ur.v1
        v1_link_ids = [l.id for l in v1.links]
        # identify bottom front link
        for l in v2.links:
            if l.id in v1_link_ids:
                bf = l
                break
        assert bf is not None, "Error: couldn't identify bottom front link for toppling"

        # identify bottom left and bottom right links
        ub_bottom_v = ub.v0 if ub.v0.id != self.top_vertex.id else ub.v1
        bl = None
        br = None
        for l in ub_bottom_v.links:
            #print(l.id)
            if l.id != ub.id:
                v_front = l.v0 if l.v0.id != ub_bottom_v.id else l.v1
                front_v_ids = [l.id for l in v_front.links]
                if (ul.id in front_v_ids):
                    bl = l
                elif (ur.id in front_v_ids):
                    br = l
        assert bl is not None, "Error: couldn't identify bottom left link for toppling"
        assert br is not None, "Error: couldn't identify bottom right link for toppling"

        # calculate orientation of each link
        ub_flip = ub.v0.id != self.top_vertex.id
        ul_flip = ul.v0.id != self.top_vertex.id
        ur_flip = ur.v0.id != self.top_vertex.id
        bl_flip = bl.v0.id != ub_bottom_v.id
        br_flip = br.v0.id != ub_bottom_v.id
        # print("upper back link: ", ub.id)
        # print("upper back bottom vertex: ", ub_bottom_v.id)
        # print("bl v0: ", bl.v0.id)
        # print("br v0: ", br.v0.id)
        links = [ul, ur, ub, bl, br, bf]
        flip = [ub_flip, ul_flip, ur_flip, bl_flip, br_flip]
        for l in links:
            print(l.id)
        print(flip)
        return links, flip
        

    
    # crawl one step in the bl, br (bottom-left, bottom-right) direction
    def crawl_step(self, event, links, flip):
        print("crawling step")
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        

        if event.is_set(): return
        if bl_flip:
            bl.send_position_only(self.MIN_POS, self.MAX_POS)
        else:
            bl.send_position_only(self.MAX_POS, self.MIN_POS)
        if br_flip:
            br.send_position_only(self.MIN_POS, self.MAX_POS)
        else:
            br.send_position_only(self.MAX_POS, self.MIN_POS)
        
        bf.send_position_only(self.MID_POS, self.MID_POS)

        if ul_flip:
            ul.send_position_only(self.MID_POS, self.MIN_POS)
        else:
            ul.send_position_only(self.MIN_POS, self.MID_POS)
        if ur_flip:
            ur.send_position_only(self.MID_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MID_POS)
        event.wait(12)

        if event.is_set(): return
        if ul_flip:
            ul.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ul.send_position_only(self.MIN_POS, self.MAX_POS)
        if ur_flip:
            ur.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MAX_POS)

        if bl_flip:
            bl.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            bl.send_position_only(self.MIN_POS, self.MAX_POS)
        if br_flip:
            br.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            br.send_position_only(self.MIN_POS, self.MAX_POS)
        event.wait(12)

        if event.is_set(): return
        self.contract()
        event.wait(12)
    
    # crawl continuously
    def crawl(self, event, dir=2, links=None, steps=100, is_ratchet = False, single_link=None):
        crawl_func = self.ratchet_crawl if is_ratchet else self.crawl_step
        #crawl_func = self.ratchet_crawl_flat if is_ratchet else self.crawl_step

        #calculate pose
        link_edges, flip = self.calculate_pose(dir) #the returned links are edges in graph, not RobotLinks
        ul, ur, ub, bl, br, bf = link_edges
        links = [ul.link, ur.link, ub.link, bl.link, br.link, bf.link]
        print("pose calculated")
        if is_ratchet:
            print(f"rachet crawling in P{ub.id-1} direction...")
            crawl_func(event, links, flip, single_link, steps)
        else:
            print(f"Tetrahedron crawling in P{ub.id-1} direction...")
            #start crawling
            for i in range(steps):
                print(f"Tetrahedron crawl: step {i+1}")
                crawl_func(event, links, flip)
                if event.is_set(): return
    
    # tiny crawl motion for ratched configuration tetrahedron
    def ratchet_crawl(self, event, links, flip, single_link, steps=1):
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        print("start rachet crawling")

        if event.is_set(): return
        self.set_all(self.MID_POS)
        single_link.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)

        if event.is_set(): return
        ul.send_position_only(self.MAX_POS, 60-15)
        ur.send_position_only(self.MAX_POS, 60+15)
        bf.send_position_only(self.MAX_POS, 75)
        # ul.send_position_only(self.MAX_POS, 40)
        # ur.send_position_only(self.MAX_POS, 40)
        # bf.send_position_only(self.MAX_POS, self.MAX_POS)

        if br_flip:
            br.send_position_only(self.MAX_POS, self.MID_POS)
        else:
            #br.send_position_only(self.MID_POS, self.MAX_POS)
            br.send_position_only(self.MID_POS, self.MAX_POS)
        if bl_flip:
            bl.send_position_only(self.MAX_POS, self.MID_POS)
        else:
            #bl.send_position_only(self.MID_POS, self.MAX_POS)
            bl.send_position_only(self.MID_POS, self.MAX_POS)
        event.wait(9)

        for i in range(steps):
            if event.is_set(): return
            single_link.send_position_only(self.MAX_POS-20, self.MID_POS)
            event.wait(8)


            if event.is_set(): return
            single_link.send_position_only(45, self.MIN_POS)
            event.wait(8)
    # tiny crawl motion for ratched configuration tetrahedron
    
    def ratchet_crawl_flat(self, event, links, flip, single_link, steps=1):
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        print("start rachet crawling")

        if event.is_set(): return
        self.set_all(self.MID_POS)
        single_link.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)

        if event.is_set(): return
        ub.send_position_only(self.MAX_POS, self.MAX_POS)
        bf.send_position_only(self.MAX_POS, self.MAX_POS)

        if br_flip:
            br.send_position_only(self.MID_POS, self.MAX_POS)
        else:
            br.send_position_only(self.MAX_POS, self.MID_POS)
        if bl_flip:
            bl.send_position_only(self.MID_POS, self.MAX_POS)
        else:
            bl.send_position_only(self.MAX_POS, self.MID_POS)
        event.wait(12)

        for i in range(steps):

            if event.is_set(): return
            single_link.send_position_only(self.MAX_POS, self.MIN_POS)
            event.wait(12)


            if event.is_set(): return
            single_link.send_position_only(self.MIN_POS, self.MIN_POS)
            event.wait(12)

    #reset to rachet crawl initial position
    def reset_rachet(self, event, dir=2, links=None, single_link=None):
        #calculate pose
        # link_edges, flip = self.calculate_pose(dir) #the returned links are edges in graph, not RobotLinks
        # links = [e.link for e in link_edges]
        # ul, ur, ub, bl, br, bf = links
        
        print("reset rachet crawl")
        if event.is_set(): return
        self.set_all(self.MID_POS)
        single_link.send_position_only(self.MIN_POS, self.MIN_POS)
        event.wait(12)
    
    def plot_config(self, link_edges):
        ul, ur, ub, bl, br, bf = link_edges
        
        
        
        

    def sleep(self, t=12):
        sleep(t)