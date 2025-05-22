import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard
from server.linknetworking import ListMaker as LM

server = linknetworking.get_default_server()

my_dashboard = dashboard.Dashboard(server, [4], open_in_browser=True)

while server.size() < 1:
    continue

VEL = 50
MIN = 16
MAX = 100
MID = 50
LMID = 25

list_walk = LM.HEAD(10, server.get_server_time()+1)
list_walk += LM.POSVEL(MIN, MIN, 100, 100, 15)
list_walk += LM.POSVEL(MIN, MAX, 100, 100, 15)
list_walk += LM.POSVEL(MAX, MIN, 100, 100, 15)
list_walk += LM.TAIL()

server.links[4].send_list(list_walk)

if __name__ == '__main__':
    input()

    server.close_server()
