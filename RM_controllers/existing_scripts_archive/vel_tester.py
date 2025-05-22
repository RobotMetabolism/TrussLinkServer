import server.linknetworking as linknetworking
import server.dashboard as dashboard

server = linknetworking.get_default_server()


def p():
    # pause function
    global server
    for link in server.links:
        server.links[link].send_position_only(24, 24)


my_dashboard = dashboard.Dashboard(server, [4,5,7], open_in_browser=False)

while server.size() < 1:
    continue

start_time = server.get_server_time()+1

server.links[5].send_position_package(90, 90, 20, 20)
