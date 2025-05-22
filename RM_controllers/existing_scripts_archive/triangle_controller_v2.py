import argparse
import time

VEL = 50
MIN = 20
MAX = 200
MID = 50
LMID = 25


def main(server, link_ids):
    try:

        print("GOT DEFAULT SERVER")

        # my_dashboard = dashboard.Dashboard(server, [1, 2, 3, 4, 5, 6, 7], open_in_browser=True)

        while server.size() < 3:
            print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
            time.sleep(0.1)
            continue

        print("STARTING SCRIPTS!!!!!")

        l1 = server.links[link_ids[0]]
        l2 = server.links[link_ids[1]]
        l3 = server.links[link_ids[2]]

        l1.send_position_only(0, 0)
        l3.send_position_only(0, 0)
        l2.send_position_only(0, 0)

        server.sleep(5)

        for count in range(3):

            # print(l1)
            # print(l2)
            # print(l3)

            l1.send_position_only(MIN, MIN)
            l3.send_position_only(MIN, MIN)
            l2.send_position_only(MIN, MIN)

            server.sleep(16)

            l1.send_position_only(60, 60)
            l3.send_position_only(MAX, MIN)
            l2.send_position_only(MAX, MIN)

            server.sleep(16)

            l1.send_position_only(MIN, MIN)

            server.sleep(16)

            l3.send_position_only(MIN, MAX)
            l2.send_position_only(MIN, MAX)

            server.sleep(16)

        print("ENDED CLEANLY")
    finally:
        server.close_server()
        # my_dashboard.close()

    exit()


def triangle_error_string(sim):
    return f'{sim.links[1].srv0_raw}: {sim.links[1].magnet0.activation}'


if __name__ == '__main__':

    from simulation import LinkServer
    server = LinkServer.get_default_server(1000, 2, my_error_string=triangle_error_string)
    from spawn import spawn_triangle
    triangle_links = spawn_triangle(server)
    server.start()
    main(server, triangle_links)

    # parser = argparse.ArgumentParser(description='Select if you want to run this script in simulation mode:')
    # parser.add_argument('--sim', dest='simulated', action='store_const',
    #                 const=1, default=0,
    #                 help='If this script should be run in simulation, then set the --sim flag')
    # args = parser.parse_args()
    #
    # if args.simulated:
    #     from simulation import LinkServer as SimServer
    #     server = SimServer.get_default_server()
    #     from simulation import spawn_triangle
    #     spawn_triangle(server)
    #     main( server )
    # else:
    #     from linknetworking import LinkServer as RealServer
    #     main( RealServer.get_default_server() )
