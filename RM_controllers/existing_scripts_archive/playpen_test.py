import server.linknetworking as linknetworking
import time
import server.dashboard as dashboard
from server.linknetworking import ListMaker as LM


def get_list_from_fourier(fourier_series):
    """
    :param fourier_series: parameters for the fourier function
    :return: list of position values of fourier function every 100 milliseconds
    """
    return []


N = 3           # Number of links
server = linknetworking.get_default_server()


while server.size() < 3:
    print("Waiting for links to connect. Currently {} links are connected.".format(server.size()))
    time.sleep(1)
    continue


L = server.links.values()   # IDs of Links
my_dashboard = dashboard.Dashboard(server, L, open_in_browser=True)


thetas = {}
start_time = server.get_server_time() + 2   # All Links will start in 2 seconds

for link in L:
    random_fourier = None  # Need to generate random fourier parameters
    positions = get_list_from_fourier(random_fourier)

    list = LM.HEAD(100, start_time)

    for position in positions:
        list += LM.POSVEL(position, positions, 100, 100, 0.1)

    list += LM.TAIL()
    thetas[link] = list

    server.links[link].send_list(thetas[link])


time.sleep(120)

server.close_server()
my_dashboard.close()
