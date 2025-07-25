import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard

VEL = 50
MIN = 16
MAX = 100
MID = 50
LMID = 25


try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, [1, 2, 3, 4, 5, 6, 7, 8, 13], open_in_browser=True)

    while server.size() < 1:
        print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
        time.sleep(3)
        continue

    l1 = server.links[8]
    # l2 = server.links[5]
    # l3 = server.links[7]

    l1.send_position_only(MIN, MIN)
    # l2.send_position_only(MIN, MIN)
    # l3.send_position_only(MIN, MIN)

    time.sleep(16)

finally:
    server.close_server()
    my_dashboard.close()

exit()
