import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard
from server.linknetworking import ListMaker as LM

VEL = 50
MIN = 16
MAX = 100
MID = 50
LMID = 25

server = linknetworking.get_default_server()

my_dashboard = dashboard.Dashboard(server, [4, 5, 7], open_in_browser=True)

while server.size() < 1:
    print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
    time.sleep(3)
    continue

list_back = LM.HEAD(3, server.get_server_time()+1)
list_back += LM.POSVEL(LMID, LMID, 100, 100, 24)
list_back += LM.POSVEL(MID, MID, 100, 100, 12)
list_back += LM.TAIL()

list_side = LM.HEAD(3, server.get_server_time()+1)
list_side += LM.POSVEL(MIN, MIN, 50, 50, 20)
list_side += LM.POSVEL(MAX, MIN, 50, 50, 20)
list_side += LM.POSVEL(MIN, MAX, 50, 50, 20)
list_side += LM.TAIL()

# server.links[4].send_list(list_side)
server.links[5].send_list(list_side)
# server.links[7].send_list(list_back)

time.sleep(110)
server.close_server()
