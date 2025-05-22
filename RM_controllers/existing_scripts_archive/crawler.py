import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard

try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, [1, 2, 3, 4, 5, 6, 7], open_in_browser=True)

    while server.size() < 1:
        continue

    VEL = 50
    print()
    print()
    for step in range(3):
        print("30 30")
        server.links[4].send_position_package(24, 24, VEL, VEL)
        time.sleep(20)
        print("30 100")
        server.links[4].send_position_package(24, 100, VEL, VEL)
        time.sleep(20)
        print("100 30")
        server.links[4].send_position_package(100, 24, VEL, VEL)
        time.sleep(20)
finally:
    server.close_server()

    my_dashboard.close()

exit()
