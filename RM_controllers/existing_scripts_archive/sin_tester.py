import server.linknetworking as linknetworking
import server.dashboard as dashboard

server = linknetworking.get_default_server()


def p(p_pos = 20):
    # pause function
    global server
    for link in server.links:
        server.links[link].send_position_only(p_pos, p_pos)


my_dashboard = dashboard.Dashboard(server, [4, 5, 7], open_in_browser=False)

while server.size() < 1:
    continue

start_time = server.get_server_time()+1
a0 = 42
x0 = 58
ps0 = 0
p0 = 32000
a1 = 42
x1 = 58
ps1 = 0
p1 = 32000

server.links[4].send_sinusoidal_package(start_time, a0, x0, ps0, p0, a1, x1, ps1, p1)
server.links[5].send_sinusoidal_package(start_time+16, a0, x0, ps0, p0, a1, x1, ps1, p1)
server.links[7].send_sinusoidal_package(start_time+16, a0, x0, ps0, p0, a1, x1, ps1, p1)
