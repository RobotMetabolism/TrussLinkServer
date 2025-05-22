import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard
from server.linknetworking import ListMaker as LM

VEL = 50 # mm / 10s

MIN = 16
MAX = 100
MID = 50
LMID = 25

try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, [13], open_in_browser=True)

    while server.size() < 1:
        print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
        time.sleep(1)
        continue

    input()
finally:
    server.close_server()
    my_dashboard.close()

exit()