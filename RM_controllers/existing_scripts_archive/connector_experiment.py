import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard

def send_pos_to_all_lnk(server, pos0, pos1):
    print(f"Set All Links To {pos0} {pos1}")
    for lnk in server.links.keys():
        if server.links[lnk].bat_status == -1:
            print("INACTIVE: ", lnk)
            continue
        #print(f"Set Link {lnk} {pos0} {pos1}")
        server.links[lnk].send_position_package(pos0, pos1, VEL, VEL)


try:
    server = linknetworking.get_default_server()

    my_dashboard = dashboard.Dashboard(server, range(1,14), open_in_browser=True)

    while server.size() < 7:
        continue

    VEL = 50
    while(True):
        send_pos_to_all_lnk(server, 24, 24)
        time.sleep(17)

        send_pos_to_all_lnk(server, 24, 100)
        time.sleep(17)

        send_pos_to_all_lnk(server, 100, 24)
        time.sleep(17)
finally:
    server.close_server()

    my_dashboard.close()

exit()
