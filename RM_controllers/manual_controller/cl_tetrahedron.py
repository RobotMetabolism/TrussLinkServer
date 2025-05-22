# Author: Simon Kang simon.kang@columbia.edu
# Last updated: Jan 28, 2024

import threading
from time import sleep
from utils import tetrahedron_plotter
from multiprocessing import Process, Pipe

class Vertex:
    
    def __init__(self, id):
        self.links = []
        self.id = id # this is the id for the vertex
        self.cw = True #clockwise or counterclockwise

    def set_links(self, links, cw=True):
        # assert condition, error_message
        assert len(links) == 3, f"a tetrahedron vertex can only have 3 links: {len(links)} links given"
        self.links = links
        self.cw = cw

class Link:
    def __init__(self, link, id, vertex_1, vertex_2, color='black'):
        self.link = link #link object
        self.id = id #link id, EX: P17
        self.srv0 = vertex_1 # Vertex instance at srv0 
        self.srv1 = vertex_2 # Vertex instance at srv1
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
        self.first_goal = False

        # Get tetrahedron links
        print("Initializing tetrahedron...")
        if link_ids is None:
            self.link_ids = sorted(list(self.server.links.keys()))
        else:
            assert len(link_ids) == 6, "Tetrahedron initialization error: number of links should be six"
            self.link_ids = link_ids
        print("Tetrahedron Link IDs: ", self.link_ids)

        # self.links: robot link instances, self.links_id: link id number
        self.links = []
        for id in self.link_ids:
                self.links.append(self.server.links[id])
        
        # Set up tetrahedron as graph
                
        # Set up vertices
        self.vertex_1 = Vertex(1)
        self.vertex_2 = Vertex(2)
        self.vertex_3 = Vertex(3) 
        self.vertex_4 = Vertex(4)

        # Set up links: basically link instances with link ids and corresponding vertices
        # It will be used to calculate the pose of the tetrahedron
        self.l0 = Link(self.links[0], self.link_ids[0], self.vertex_1, self.vertex_2, 'darkorange')
        self.l1 = Link(self.links[1], self.link_ids[1], self.vertex_1, self.vertex_3, 'dodgerblue')
        self.l2 = Link(self.links[2], self.link_ids[2], self.vertex_1, self.vertex_4, 'yellowgreen')
        self.l3 = Link(self.links[3], self.link_ids[3], self.vertex_4, self.vertex_2, 'mediumpurple')
        self.l4 = Link(self.links[4], self.link_ids[4], self.vertex_4, self.vertex_3, 'palevioletred')
        self.l5 = Link(self.links[5], self.link_ids[5], self.vertex_3, self.vertex_2, 'gold')

        # Set up the initial configuration, each vertex has three associated links
        self.vertex_1.set_links([self.l0, self.l1, self.l2], cw=True)
        self.vertex_2.set_links([self.l0, self.l3, self.l5], cw=True)
        # cw is false because it is needed for the assignment of roles (ub, ul, lr, bf, bl, br) with these vertices as the top vertex
        self.vertex_3.set_links([self.l1, self.l4, self.l5], cw=False)
        self.vertex_4.set_links([self.l2, self.l3, self.l4], cw=False)

        # Initialize tetrahedron pose
        # v1 is the top vertex
        self.top_vertex = self.vertex_1
        
        # Initialize plot
        # Two-way commnuication channel using a pipe.
        # r_conn receving end of the pipe, s_conn is the sending end of the pipe\
        # receiver connection and sender connection
        # used for inter-process communication
        r_conn, s_conn = Pipe()

        p = Process(target=tetrahedron_plotter, args=(r_conn,))
        p.start()
        self.plotter = s_conn

        # Sending Initial Plot Data
        links, _ = self.calculate_pose(dir=2) # initial pose as dir 2
        link_info = [(l.id, l.color) for l in links]
        self.plotter.send(link_info)

        # Initialize event
        self.event = threading.Event()
        self.event.set()

    
    # contract all links
    def contract(self):
        self.set_all(self.MIN_POS)

    # set position for all links    
    def set_all(self, position, exclude=[]):
        for l in self.links:
            if l not in exclude:
                l.send_position_only(position, position)


    # crawl continuously
    def crawl(self, dir=2, steps=1, links=None, flip=None):
        crawl_func = self.crawl_backward
        
        if self.first_goal:
            dir = 0


        #calculate pose
        link_edges, flip = self.calculate_pose(dir) #the returned links are edges in graph, not RobotLinks
        ul, ur, ub, bl, br, bf = link_edges
        links = [ul.link, ur.link, ub.link, bl.link, br.link, bf.link]
        print("pose calculated")
        print(f"Tetrahedron crawling in P{ub.id} direction...")
        #start crawling
        for i in range(steps):
            print(f"Tetrahedron crawl: step {i+1}")
            crawl_func(links, flip)
            if self.event.is_set(): break

        # this is to make sure the tetrahedron gets back to the default position
        self.contract()

        # since crawling is complete, set the event flag to true to indicate that the crawling is finished.
        self.event.set()


    def rotate(self, dir, steps=1, links=None, flip=None):

        #calculate pose
        link_edges, flip = self.calculate_pose(2) #the returned links are edges in graph, not RobotLinks
        ul, ur, ub, bl, br, bf = link_edges
        links = [ul.link, ur.link, ub.link, bl.link, br.link, bf.link]

        print("pose calculated")
        print(f"Tetrahedron rotating P{ub.id-1} direction...")

        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip

        #print if flipped
        print(f"ub_flip: {ub_flip}, ul_flip: {ul_flip}, ur_flip: {ur_flip}, bl_flip: {bl_flip}, br_flip: {br_flip}")

        for i in range(steps):
            #print(f'rotating with pivot link {pivot.device_id}')
            bl.send_position_only(self.MIN_POS, self.MIN_POS)
            br.send_position_only(self.MIN_POS, self.MIN_POS)
            bf.send_position_only(self.MIN_POS, self.MIN_POS)

            if dir == 'ccw':
                print("rotate")
                self.event.wait(self.t)
                # bl.send_position_only(self.MAX_POS, self.MIN_POS)
                # br.send_position_only(self.MIN_POS, self.MAX_POS)
                # bf.send_position_only(self.MAX_POS, self.MIN_POS) # CORRECT
                if bl_flip:
                    bl.send_position_only(self.MIN_POS, self.MAX_POS)
                else:
                    bl.send_position_only(self.MAX_POS, self.MIN_POS)
                    # bl.send_position_only(self.MID_POS, self.MIN_POS)
                if br_flip:
                    br.send_position_only(self.MIN_POS, self.MAX_POS)
                else:
                    br.send_position_only(self.MAX_POS, self.MIN_POS)

                # modified the crawling motion
                bf.send_position_only(self.MID_POS, self.MID_POS)

                if ul_flip:
                    ur.send_position_only(self.MAX_POS, self.MAX_POS)
                else:
                    ul.send_position_only(self.MAX_POS, self.MAX_POS)
                # ub.send_position_only(self.MIN_POS, self.MAX_POS)
                self.event.wait(self.t)
                # bl.send_position_only(self.MIN_POS, self.MAX_POS)
                # br.send_position_only(self.MAX_POS, self.MIN_POS)
                # bf.send_position_only(self.MIN_POS, self.MAX_POS)

                if bl_flip:
                    bl.send_position_only(self.MAX_POS, self.MIN_POS)
                else:
                    bl.send_position_only(self.MIN_POS, self.MAX_POS)
                    # bl.send_position_only(self.MIN_POS, self.MID_POS)
                if br_flip:
                    br.send_position_only(self.MAX_POS, self.MIN_POS)
                else:
                    br.send_position_only(self.MIN_POS, self.MAX_POS)

                # to help with a push
                if ub_flip:
                    ub.send_position_only(self.MIN_POS, self. MAX_POS)
                else:    
                    ub.send_position_only(self.MIN_POS, self. MAX_POS)
                
                self.event.wait(12)

                if self.event.is_set(): return
                self.contract()
                self.event.wait(12)


            elif dir == 'cw':
                print("rotating")
                self.event.wait(self.t)
                # bl.send_position_only(self.MAX_POS, self.MIN_POS)
                # br.send_position_only(self.MIN_POS, self.MAX_POS)
                # bf.send_position_only(self.MAX_POS, self.MIN_POS) # CORRECT
                if bl_flip:
                    bl.send_position_only(self.MIN_POS, self.MAX_POS)
                else:
                    bl.send_position_only(self.MAX_POS, self.MIN_POS)
                    # bl.send_position_only(self.MID_POS, self.MIN_POS)
                if br_flip:
                    br.send_position_only(self.MIN_POS, self.MAX_POS)
                else:
                    br.send_position_only(self.MAX_POS, self.MIN_POS)

                # modified the crawling motion

                bf.send_position_only(self.MID_POS, self.MID_POS)

                ur.send_position_only(self.MAX_POS, self.MAX_POS)
                # ub.send_position_only(self.MIN_POS, self.MAX_POS)
                self.event.wait(self.t)
                # bl.send_position_only(self.MIN_POS, self.MAX_POS)
                # br.send_position_only(self.MAX_POS, self.MIN_POS)
                # bf.send_position_only(self.MIN_POS, self.MAX_POS)

                if bl_flip:
                    bl.send_position_only(self.MAX_POS, self.MIN_POS)
                else:
                    bl.send_position_only(self.MIN_POS, self.MAX_POS)
                    # bl.send_position_only(self.MIN_POS, self.MID_POS)
                if br_flip:
                    br.send_position_only(self.MAX_POS, self.MIN_POS)
                else:
                    br.send_position_only(self.MIN_POS, self.MAX_POS)

                # to help with a push    
                ub.send_position_only(self.MIN_POS, self. MAX_POS)
                
                self.event.wait(12)

                if self.event.is_set(): return
                self.contract()
                self.event.wait(12)

            # if dir == 'ccw':
            #     print("rotating counter clockwise")
            #     self.event.wait(self.t)
            #     bl.send_position_only(self.MIN_POS, self.MAX_POS)
            #     br.send_position_only(self.MAX_POS, self.MIN_POS)
            #     bf.send_position_only(self.MAX_POS, self.MIN_POS)
            #     self.event.wait(self.t)
            #     bf.send_position_only(self.MIN_POS, self.MAX_POS)
            # elif dir == 'cw':
            #     print("rotating clockwise")
            #     self.event.wait(self.t)
            #     bl.send_position_only(self.MAX_POS, self.MIN_POS)
            #     br.send_position_only(self.MIN_POS, self.MAX_POS)
            #     bf.send_position_only(self.MIN_POS, self.MAX_POS)
            #     self.event.wait(self.t)
            #     bf.send_position_only(self.MAX_POS, self.MIN_POS)

            # self.event.wait(self.t)

        # this is to make sure the triangle gets back to the default position
        bf.send_position_only(self.MIN_POS, self.MIN_POS)
        bl.send_position_only(self.MIN_POS, self.MIN_POS)
        br.send_position_only(self.MIN_POS, self.MIN_POS)
        # rotating is done, set the event flag to true
        self.event.set()


    def calculate_pose(self, dir=2):

        # identify upper links
        ub = self.top_vertex.links[dir]

        if self.top_vertex.cw:
            # Initial Setup
            ul = self.top_vertex.links[(dir+1)%3] # tetrahedron.Link() instance, self.l0 -> L1
            ur = self.top_vertex.links[(dir+2)%3] # tetrahedron.Link() instance, self.l1 -> L2
        else:
            ur = self.top_vertex.links[(dir+1)%3]
            ul = self.top_vertex.links[(dir+2)%3]

        # get two bottom front vertices, the bottom front link is the link connecting them
        bf = None

        # ul.srv0.id means the vertex id at srv0 position of the link ul
        # ul.srv1.id means the vertex id at srv1 position of the link ul

        # if the vertex id at srv0 position of the link ul is not the top vertex id, then the vertex id at srv0 position of the link ul is the bottom front vertex
        # is it if ul.srv0.id != self.top_vertex.id, it means that the vertex id at srv0 position of the link ul is not the top vertex id, which means 

        # check if this is flipped ul or not flipped ul 
        # else is only activated if it has flipped and top vertex has changed
        # that means ul is now the flipped version, which is L5 -> V4 is at srv0 and V3 is at srv1
        # and ur is L4 -> V4 is at srv0 and V2 is at srv1
        # that means code should be changed to


        vertex_1 = ul.srv0 if ul.srv0.id != self.top_vertex.id else ul.srv1
        vertex_2 = ur.srv0 if ur.srv0.id != self.top_vertex.id else ur.srv1

        vertex_link_ids = [l.id for l in vertex_1.links]
        # identify bottom front link
        for l in vertex_2.links:
            if l.id in vertex_link_ids:
                bf = l
                break
        assert bf is not None, "Error: couldn't identify bottom front link for toppling"

        # identify bottom left and bottom right links
        ub_bottom_vertex = ub.srv0 if ub.srv0.id != self.top_vertex.id else ub.srv1
        bl = None
        br = None

        for l in ub_bottom_vertex.links:
            #print(l.id)
            if l.id != ub.id:
                v_front = l.srv0 if l.srv0.id != ub_bottom_vertex.id else l.srv1
                front_v_ids = [l.id for l in v_front.links]
                if (ul.id in front_v_ids):
                    bl = l
                elif (ur.id in front_v_ids):
                    br = l
        assert bl is not None, "Error: couldn't identify bottom left link for toppling"
        assert br is not None, "Error: couldn't identify bottom right link for toppling"

        # calculate orientation of each link
        ub_flip = ub.srv0.id != self.top_vertex.id # check serv0 vertex of upper back link
        ul_flip = ul.srv0.id != self.top_vertex.id
        ur_flip = ur.srv0.id != self.top_vertex.id
        bl_flip = bl.srv0.id != ub_bottom_vertex.id
        br_flip = br.srv0.id != ub_bottom_vertex.id
        # print("upper back link: ", ub.id)
        # print("upper back bottom vertex: ", ub_bottom_v.id)
        # print("bl v0: ", bl.v0.id)
        # print("br v0: ", br.v0.id)
        links = [ul, ur, ub, bl, br, bf] # links is a list of RobotLink instances
        flip = [ub_flip, ul_flip, ur_flip, bl_flip, br_flip] # flip is a list of boolean values indicating whether the link is flipped or not
        for l in links:
            print(l.id)
        print(flip)

        print(f"ub: P{ub.id}, ul: P{ul.id}, ur: P{ur.id}, bl: P{bl.id}, br: P{br.id}, bf: P{bf.id}")
        print(f"ub_flip: {ub_flip}, ul_flip: {ul_flip}, ur_flip: {ur_flip}, bl_flip: {bl_flip}, br_flip: {br_flip}")
        return links, flip
    

    def topple(self, dir=2, tail=None):
        #calculate pose
        link_edges, flip = self.calculate_pose(dir)  #the returned links are edges in graph, not RobotLinks
        ul, ur, ub, bl, br, bf = link_edges
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip

        print(f"toppling in the P{ul.id}-P{ur.id} direction...")
        print(f"ub: P{ub.id}, ul: P{ul.id}, ur: P{ur.id}, bl: P{bl.id}, br: P{br.id}, bf: P{bf.id}")
        print(f"ub_flip: {ub_flip}, ul_flip: {ul_flip}, ur_flip: {ur_flip}, bl_flip: {bl_flip}, br_flip: {br_flip}")


        # set new top vertex after topple
        self.top_vertex = ub.srv0 if ub.srv0.id != self.top_vertex.id else ub.srv1

        # plot new configuration
        ################################
        # why is dir 0 rather than 2 -> since it flipped, dir indicates...
        ################################
        links, _ = self.calculate_pose(dir=2)
        link_info = [(l.id, l.color) for l in links]
        self.plotter.send(link_info)


        # execute topple
        links = [ul.link, ur.link, ub.link, bl.link, br.link, bf.link]
        self.execute_topple(links, flip)


    # topple in the ul-ur (upper-left, upper-right) direction
    def execute_topple(self, links, flip, bf_pos=100, tail=None):
        print("Toppling tetrahedron...")
        print("flag -1")
        # BF_POS = int(input('bottom front link (default: 80): \n')) # ERROR LINE
        BF_POS = bf_pos
        print("flag 0.1")
        # topple_value = int(input('upper back link (default: 88): \n'))
        print("flag 0.2")
        ul, ur, ub, bl, br, bf = links
        print("flag 0.3")
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        #bf_pos = 87
        print("flag 0")
        # expand
        if self.event.is_set(): 
            print("flag 0.5")
            return
        if ul_flip:
            ul.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            print("flag 1")
            ul.send_position_only(self.MIN_POS, self.MAX_POS)
        if ur_flip:
            print("flag 2")
            ur.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MAX_POS)
        print("flag 3")
        bf.send_position_only(BF_POS, BF_POS)
        self.event.wait(self.t)

        # topple
        topple_value = 88 # used to be 90
        if self.event.is_set(): return
        if ub_flip:
            ub.send_position_only(self.MAX_POS, topple_value)
        else:
            ub.send_position_only(topple_value, self.MAX_POS)
        
        if tail is not None:
            self.event.wait(3)
            tail.send_position_only(self.MAX_POS, self.MIN_POS)
        self.event.wait(self.t)

        print("flag 4")

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

        if self.event.is_set(): return
        self.contract()
        self.event.wait(self.t)
        print("flag 5")

        self.event.set() # set event to true to indicate that the topple is finished


        
    # crawl one step in the bl, br (bottom-left, bottom-right) direction
    def crawl_forward(self, links, flip):
        print("crawling step")
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        

        if self.event.is_set(): return
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
        self.event.wait(12)

        if self.event.is_set(): return
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
        self.event.wait(12)

        if self.event.is_set(): return
        self.contract()
        self.event.wait(12)

    def crawl_backward(self, links, flip):
        print("crawling step")
        ul, ur, ub, bl, br, bf = links
        ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        
        if self.event.is_set(): return
        if ul_flip:
            ul.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ul.send_position_only(self.MIN_POS, self.MAX_POS)
        if ur_flip:
            ur.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MAX_POS)

        if bl_flip:
            bl.send_position_only(self.MIN_POS, self.MAX_POS)
        else:
            bl.send_position_only(self.MAX_POS, self.MIN_POS)
            # bl.send_position_only(self.MID_POS, self.MIN_POS)
        if br_flip:
            br.send_position_only(self.MIN_POS, self.MAX_POS)
        else:
            br.send_position_only(self.MAX_POS, self.MIN_POS)

        # modified the crawling motion

        bf.send_position_only(self.MID_POS, self.MID_POS)

        self.event.wait(12)
        
        if self.event.is_set(): return
        if bl_flip:
            bl.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            bl.send_position_only(self.MIN_POS, self.MAX_POS)
            # bl.send_position_only(self.MIN_POS, self.MID_POS)
        if br_flip:
            br.send_position_only(self.MAX_POS, self.MIN_POS)
        else:
            br.send_position_only(self.MIN_POS, self.MAX_POS)

        if ul_flip:
            ul.send_position_only(self.MID_POS, self.MIN_POS)
        else:
            ul.send_position_only(self.MIN_POS, self.MID_POS)
        if ur_flip:
            ur.send_position_only(self.MID_POS, self.MIN_POS)
        else:
            ur.send_position_only(self.MIN_POS, self.MID_POS)
        # to help with a push    
        ub.send_position_only(self.MAX_POS, self. MAX_POS)
        self.event.wait(12)

        if self.event.is_set(): return
        self.contract()
        self.event.wait(12)


    # def crawl_backward_original(self, links, flip):
    #     print("crawling step")
    #     ul, ur, ub, bl, br, bf = links
    #     ub_flip, ul_flip, ur_flip, bl_flip, br_flip = flip
        
    #     if self.event.is_set(): return
    #     if ul_flip:
    #         ul.send_position_only(self.MAX_POS, self.MIN_POS)
    #     else:
    #         ul.send_position_only(self.MIN_POS, self.MAX_POS)
    #     if ur_flip:
    #         ur.send_position_only(self.MAX_POS, self.MIN_POS)
    #     else:
    #         ur.send_position_only(self.MIN_POS, self.MAX_POS)

    #     if bl_flip:
    #         bl.send_position_only(self.MAX_POS, self.MIN_POS)
    #     else:
    #         bl.send_position_only(self.MIN_POS, self.MAX_POS)
    #     if br_flip:
    #         br.send_position_only(self.MAX_POS, self.MIN_POS)
    #     else:
    #         br.send_position_only(self.MIN_POS, self.MAX_POS)

    #     bf.send_position_only(self.MID_POS, self.MID_POS)

    #     self.event.wait(12)
        
    #     if self.event.is_set(): return
    #     if bl_flip:
    #         bl.send_position_only(self.MIN_POS, self.MAX_POS)
    #     else:
    #         bl.send_position_only(self.MAX_POS, self.MIN_POS)
    #     if br_flip:
    #         br.send_position_only(self.MIN_POS, self.MAX_POS)
    #     else:
    #         br.send_position_only(self.MAX_POS, self.MIN_POS)

    #     if ul_flip:
    #         ul.send_position_only(self.MID_POS, self.MIN_POS)
    #     else:
    #         ul.send_position_only(self.MIN_POS, self.MID_POS)
    #     if ur_flip:
    #         ur.send_position_only(self.MID_POS, self.MIN_POS)
    #     else:
    #         ur.send_position_only(self.MIN_POS, self.MID_POS)
    #     self.event.wait(12)

    #     if self.event.is_set(): return
    #     self.contract()
    #     self.event.wait(12)