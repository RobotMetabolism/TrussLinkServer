import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard

VEL = 50
MIN = 16
MAX = 100
MID = 50
LMID = 25


class Tetrahedron:

    def __init__(self, l01, l02, l03, l12, l23, l31):
        self.tetra = {
             "01": (l01, 0),
             "02": (l02, 0),
             "03": (l03, 0),
             "12": (l12, 0),
             "23": (l23, 0),
             "31": (l31, 0),
                 }

    def tip(self, tetra_links):
        base_back_left = tetra_links[0]
        base_back_right = tetra_links[1]
        base_front = tetra_links[2]
        top_back_center = tetra_links[3]
        top_front_left = tetra_links[4]
        top_front_right = tetra_links[5]

        # # CONTRACT ALL
        # for l in tetra_links:
        #     l[0].send_position_only(MIN, MIN)
        # time.sleep(12)

        # EXPAND BASE
        base_front[0].send_position_only(70, 70)
        if top_front_left[1]:
            top_front_left[0].send_position_only(MAX, MIN)
        else:
            top_front_left[0].send_position_only(MIN, MAX)

        if top_front_right[1]:
            top_front_right[0].send_position_only(MAX, MIN)
        else:
            top_front_right[0].send_position_only(MIN, MAX)

        time.sleep(12)

        # TOPPLE
        if top_back_center[1]:
            top_back_center[0].send_position_only(MAX, 90)
        else:
            top_back_center[0].send_position_only(90, MAX)
        time.sleep(12)

        # Upright again
        if base_back_right[1]:
            base_back_right[0].send_position_only(MIN, MAX)
        else:
            base_back_right[0].send_position_only(MAX, MIN)

        if base_back_left[1]:
            base_back_left[0].send_position_only(MIN, MAX)
        else:
            base_back_left[0].send_position_only(MAX, MIN)
        time.sleep(12)

        # MAKE TOP SYMMETRIC
        if top_back_center[1]:
            top_back_center[0].send_position_only(MAX, MIN)
        else:
            top_back_center[0].send_position_only(MIN, MAX)
        time.sleep(12)

        # CONTRACT ALL
        for l in tetra_links:
            l[0].send_position_only(MIN, MIN)
        time.sleep(12)

    def one_tip(self):

        t = self.tetra

        tetra_links = [
            (t["31"][0], not t["31"][1]),
            (t["12"][0], t["12"][1]),
            (t["23"][0], not t["23"][1]),
            (t["01"][0], t["01"][1]),
            (t["03"][0], t["03"][1]),
            (t["02"][0], t["02"][1])
        ]

        self.tip(tetra_links)

        new_tetra = {
            "01": (t["01"][0], not t["01"][1]),
            "02": (t["31"][0], not t["31"][1]),
            "03": (t["12"][0], t["12"][1]),
            "12": (t["03"][0], t["03"][1]),
            "23": (t["23"][0], not t["23"][1]),
            "31": (t["02"][0], not t["02"][1]),
        }
        self.tetra = new_tetra

        print(self.tetra)

    def two_tip(self):

        t = self.tetra

        tetra_links = [
            (t["12"][0], not t["12"][1]),
            (t["23"][0], t["23"][1]),
            (t["31"][0], t["31"][1]),
            (t["02"][0], t["02"][1]),
            (t["01"][0], t["01"][1]),
            (t["03"][0], t["03"][1]),
        ]

        self.tip(tetra_links)

        new_tetra = {
            "01": (t["23"][0], t["23"][1]),
            "02": (t["02"][0], not t["02"][1]),
            "03": (t["12"][0], t["12"][1]),
            "12": (t["03"][0], not t["03"][1]),
            "23": (t["01"][0], t["01"][1]),
            "31": (t["31"][0], not t["31"][1]),
        }
        self.tetra = new_tetra

        print(self.tetra)

    def three_tip(self):
        pass


try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, [4,5,6,7,8,13], open_in_browser=True)

    while server.size() < 6:
        print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
        time.sleep(0.1)
        continue

    L = [4,5,6,7,8,13]

    # 01, 02, 03, 12, 23, 31
    l4 = server.links[4]
    l8 = server.links[8]
    l13 = server.links[13]
    l6 = server.links[6]
    l5 = server.links[5]
    l7 = server.links[7]

    my_tetra = Tetrahedron(l4, l8, l13, l6, l5, l7)

    my_tetra.one_tip()
    my_tetra.one_tip()


finally:
    server.close_server()
    my_dashboard.close()

exit()




"""
# CONTRACT ALL
    for l in L:
        server.links[l].send_position_only(MIN, MIN)
    time.sleep(12)

    # EXPAND BASE
    base_front.send_position_only(70, 70)
    top_front_left.send_position_only(MIN, MAX)
    top_front_right.send_position_only(MIN, MAX)

    time.sleep(12)

    # TOPPLE
    top_back_center.send_position_only(85, MAX)
    time.sleep(12)

    # Upright again
    base_back_right.send_position_only(MAX, MIN)
    base_back_left.send_position_only(MAX, MIN)
    time.sleep(12)

    # MAKE TOP SYMMETRIC
    top_back_center.send_position_only(MIN, MAX)
    time.sleep(12)

    # CONTRACT ALL
    for l in L:
        server.links[l].send_position_only(MIN, MIN)
    time.sleep(12)
"""