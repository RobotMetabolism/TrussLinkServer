import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard
#import signal
#import sys
VEL = 50
MIN = 16
MAX = 100
MID = 50
LMID = 25


'''
# Handling CTRL-C
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
'''
try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, [1, 2, 3, 4, 5, 6, 7], open_in_browser=True)

    while server.size() < 3:
        print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
        time.sleep(3)
        continue

    l1 = server.links[4]
    l2 = server.links[5]
    l3 = server.links[7]

    for count in range(20):

        l1.send_position_only(LMID, LMID)
        l2.send_position_only(MIN, MIN)
        l3.send_position_only(MIN, MIN)

        time.sleep(12)

        l2.send_position_only(MAX, MIN)
        l3.send_position_only(MAX, MIN)

        time.sleep(12)

        l1.send_position_only(MID, MID)
        l2.send_position_only(MIN, MAX)
        l3.send_position_only(MIN, MAX)

        time.sleep(12)


finally:
    server.close_server()
    my_dashboard.close()

exit()
