import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from pynput import keyboard
from pynput.keyboard import Key, Listener, KeyCode
import linknetworking as linknetworking
import RM_dashboard.dashboard as dashboard
from time import sleep


class DeltaController:
    def __init__(self, server=None, base_radius=13):
        self.server = server
        self.link_ids = sorted(list(server.links.keys()))
        # end-effector link
        self.end_effector = server.links[self.link_ids[0]]
        # top links
        self.link1 = server.links[self.link_ids[1]]
        self.link2 = server.links[self.link_ids[2]]
        self.link3 = server.links[self.link_ids[3]]

        # initialize delta robot
        self.MIN_LINK = 27
        self.MAX_LINK = 27 + 16
        self.MIN_POS = 22
        self.RELEASE_POS = 0
        self.MAX_POS = 100
        self.base_radius = base_radius
        self.base_l1, self.base_l2, self.base_l3 = self.calculate_base(self.base_radius)
        self.reset()
        # self.l_1 = self.l_2 = self.l_3 = (self.MIN_LINK + self.MAX_LINK) / 2
        # self.l_4 = self.MIN_LINK
        # self.update_srv_pos()
        # self.x, self.y, self.z = self.forward_kinematics()
        # self.end_effector_srv1 = self.MIN_POS
        # self.end_effector_srv0 = self.RELEASE_POS
        # self.send_srv_commands()

        # Set up keyboard listener
        self.listener =  Listener(
                on_press=self.on_press,
                on_release=self.on_release)


    def run(self):
        self.listener.start()
        while True:
            sleep(0.1)
    
    def execute_command(self, key):
        print("---------------------------------------")
        x_old = self.x
        y_old = self.y
        z_old = self.z
        if type(key) != keyboard.KeyCode:
            print("unrecognized key")
            return

        k = key.char
        if k == 'w':
            print("moving in +y direction")
            self.y += 2
            if self.inverse_kinematics() < 0:
                self.y -= 2
        elif k == 's':
            print("moving in -y direction")
            self.y -= 2
            if self.inverse_kinematics() < 0:
                self.y += 2
        elif k == 'a':
            print("moving in -x direction")
            print(self.x)
            self.x -= 2
            print(self.x)
            if self.inverse_kinematics() < 0:
                self.x += 2
        elif k == 'd':
            print("moving in +x direction")
            self.x += 2
            if self.inverse_kinematics() < 0:
                self.x -= 2
        elif k == 'q':
            self.end_effector_srv1 = min(self.end_effector_srv1 + 5, self.MAX_POS)
            print("moving in -z direction")
        elif k == 'e':
            self.end_effector_srv1 = max(self.end_effector_srv1 - 5, self.MIN_POS)
            print("moving in +z direction")
        elif k == 'z':
            print("ready to pick up")
            self.end_effector_srv0 = self.MIN_POS
        elif k == 'x':
            print("releasing...")
            self.end_effector_srv0 = self.RELEASE_POS
        elif k == 'r':
            self.reset()
        else:
            print("unrecognized key")
            return

        print(f"({x_old:.1f}, {y_old:.1f}, {z_old:.1f}) ---> ({self.x:.1f}, {self.y:.1f}, {self.z:.1f})")
        self.update_srv_pos()
        self.print_srv_commands()
        self.send_srv_commands()

    def reset(self):
        print("reset")
        self.l_1 = self.l_2 = self.l_3 = (self.MIN_LINK + self.MAX_LINK) / 2
        self.l_4 = self.MIN_LINK
        self.update_srv_pos()
        self.x, self.y, self.z = self.forward_kinematics()
        self.end_effector_srv1 = self.MIN_POS
        self.end_effector_srv0 = self.RELEASE_POS
        self.send_srv_commands()
        
    def update_srv_pos(self):
        self.l1_srv = int(self.real2command(self.l_1))
        self.l2_srv = int(self.real2command(self.l_2))
        self.l3_srv = int(self.real2command(self.l_3))
    
    def send_srv_commands(self):
        self.link1.send_position_only(self.l1_srv, self.l1_srv)
        self.link2.send_position_only(self.l2_srv, self.l2_srv)
        self.link3.send_position_only(self.l3_srv, self.l3_srv)
        self.end_effector.send_position_only(self.end_effector_srv0, self.end_effector_srv1)

    def print_srv_commands(self):
        print(f"updated servo positions: \n l1_srv: ({self.l1_srv},{self.l1_srv}),\n" \
              f"l2_srv: ({self.l2_srv},{self.l2_srv}),\n" \
              f"l3_srv: ({self.l3_srv},{self.l3_srv}),\n" \
              f"l4_srv: ({self.end_effector_srv0}, {self.end_effector_srv1})\n")

    # define contact points of three upper links with base plate
    def calculate_base(self, base_radius):
        base_l1 = (-0.5 * base_radius * np.sqrt(3), -0.5 * base_radius, 0)
        base_l2 = (0.5 * base_radius * np.sqrt(3), -0.5 * base_radius, 0)
        base_l3 = (0, base_radius, 0)
        print(f"base point 1: ({base_l1[0]:.1f}, {base_l1[1]:.1f}, {base_l1[2]:.1f})")
        print(f"base point 2: ({base_l2[0]:.1f}, {base_l2[1]:.1f}, {base_l2[2]:.1f})")
        print(f"base point 3: ({base_l3[0]:.1f}, {base_l3[1]:.1f}, {base_l3[2]:.1f})")
        return base_l1, base_l2, base_l3

    def forward_kinematics(self):
        # Known values
        x_1, y_1, z_1 = self.base_l1
        x_2, y_2, z_2 = self.base_l2
        x_3, y_3, z_3 = self.base_l3

        def equations(variables):
            x, y, z = variables
            eq1 = (x - x_1)**2 + (y - y_1)**2 + (z - z_1)**2 - self.l_1**2
            eq2 = (x - x_2)**2 + (y - y_2)**2 + (z - z_2)**2 - self.l_2**2
            eq3 = (x - x_3)**2 + (y - y_3)**2 + (z - z_3)**2 - self.l_3**2
            
            return [eq1, eq2, eq3]

        # Initial guess for (x, y, z)
        initial_guess = (0, 0, -2)

        # Solve the system of equations
        x, y, z = fsolve(equations, initial_guess)
        print(f"intersection point: ({x:.1f}cm, {y:.1f}cm, {z:.1f}cm)")
        return x, y, z

    def inverse_kinematics(self):
        x_t, y_t, z_t = self.x, self.y, self.z
        x_1, y_1, z_1 = self.base_l1
        x_2, y_2, z_2 = self.base_l2
        x_3, y_3, z_3 = self.base_l3

        # Calculate the required lengths
        l_1 = np.sqrt((x_t - x_1)**2 + (y_t - y_1)**2 + (z_t - z_1)**2)
        l_2 = np.sqrt((x_t - x_2)**2 + (y_t - y_2)**2 + (z_t - z_2)**2)
        l_3 = np.sqrt((x_t - x_3)**2 + (y_t - y_3)**2 + (z_t - z_3)**2)

        print(f"l1: {l_1:.1f}cm, l2:{l_2:.1f}cm, l3:{l_3:.1f}cm")
        if self.MIN_LINK <= l_1 <= self.MAX_LINK and self.MIN_LINK <= l_2 <= self.MAX_LINK and self.MIN_LINK <= l_3 <= self.MAX_LINK:
            self.l_1 = l_1
            self.l_2 = l_2
            self.l_3 = l_3
            return 1
        else:
            return -1

    # from real distance in cm to position command value
    def real2command(self, l):
        return (l - 27) / 16 * 78 + 22

    # from position command value to real distance in cm 
    def command2real(self, l):
        return max(0, (l - 22)) * 16 / 78 + 27

    def pick_event_method(self, event):
        ind = event.ind[0]
        x, y, z = event.artist._offsets3d
        print(x[ind], y[ind], z[ind])

    def plot_ground_plane(self, ax, h=82, w=50, l=50):
        xx = [-1*w/2, -1*w/2, w/2, w/2, -1*w/2]
        yy = [-1*l/2, l/2, l/2, -1*l/2, -1*l/2]
        zz = [-1*h, -1*h, -1*h, -1*h, -1*h]
        ax.plot(xx, yy, zz)
    
    def on_press(self, key):
        self.execute_command(key)

    def on_release(self, key):
        return
    

if __name__ == '__main__':

    nr_links = 4
    try:
        #connect to links
        server = linknetworking.get_default_server()
        my_dashboard = dashboard.Dashboard(server, list(range(35)), open_in_browser=True)
        while server.size() < nr_links:
            print(f"Waiting for links to connect. Currently {server.size()} of {nr_links} links are connected.")
            sleep(1)
            continue
        
        robot_controller = DeltaController(server=server)
        robot_controller.run()
        
        # # initialize figure
        # fig = plt.figure()
        # ax = fig.add_subplot(projection='3d')
        # ax.view_init(0, 150)
        
        # # plot ground plane
        # plot_ground_plane(ax, h=82)
        # print("ground plane added")

        # print("servo positions:", real2command(np.array([l_11, l_22, l_33])))
        # x_1, y_1, z_1 = base_l1
        # x_2, y_2, z_2 = base_l2
        # x_3, y_3, z_3 = base_l3
        
        # ax.plot([x_1, x], [y_1, y], [z_1, z], c='blue')
        # ax.plot([x_2, x], [y_2, y], [z_2, z], c='blue')
        # ax.plot([x_3, x], [y_3, y], [z_3, z], c='blue')
        # ax.plot([x_4, x], [y_4, y], [z_4, z], c='blue')
        # #ax.scatter(np.random.rand(10), np.random.rand(10), np.random.rand(10), c=np.random.rand(10),
        # #cmap='hot', picker=5, s=100)
        # #fig.canvas.mpl_connect('pick_event', pick_event_method)
        # plt.show()
        

    except Exception as e:
        print(e)
    
    finally:
        # server.close_server()
        # my_dashboard.close()
        exit()
