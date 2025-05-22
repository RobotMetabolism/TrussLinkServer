# Author: Qi (Meiqi) Zhao mz2651@columbia.edu
# Last updated: Jan 1, 2023

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# def plot_tetrahedron(ax, links):
# 	ax.clear()

# 	vertices = [(0, 0, 2.0*np.sqrt(2)/np.sqrt(3)),
# 		(1, -1.0/np.sqrt(3), 0), 
# 		(-1, -1.0/np.sqrt(3), 0), 
# 		(0, 2.0/np.sqrt(3), 0)]
	
# 	# ul, ur, ub, bl, br, bf 
# 	edges = [(0, 2), (0, 3), (0, 1), (1, 2), (1, 3), (2, 3)]

# 	for idx, edge in enumerate(edges):
# 		xs = [vertices[edge[0]][0], vertices[edge[1]][0]]
# 		ys = [vertices[edge[0]][1], vertices[edge[1]][1]]
# 		zs = [vertices[edge[0]][2], vertices[edge[1]][2]]
# 		ax.plot(xs, ys, zs, color=links[idx].color)
# 		ax.text(np.average(xs), np.average(ys), np.average(zs), f'P{links[idx].id}', size=8, zdir=None, 
# 				ha="center", va="center",
# 				bbox=dict(boxstyle="circle",
# 					ec=links[idx].color,
# 					fc='lightgray',
# 				))
# 	#ax.grid(False)
# 	plt.tick_params(left = False, right = False, labelleft = False, labelbottom = False, bottom = False)

# 	# plt.draw() #nonblocking
# 	# plt.pause(1)

# 	plt.savefig('tetrahedron_config.png', bbox_inches='tight')


def tetrahedron_plotter(r_conn):
	# Initialize plot
	fig = plt.figure(figsize=(8, 8))
	ax = fig.add_subplot(111, projection='3d')

	# Create vertices and edges in plot
	vertices = [(0, 0, 2.0*np.sqrt(2)/np.sqrt(3)),
		(1, -1.0/np.sqrt(3), 0), 
		(-1, -1.0/np.sqrt(3), 0), 
		(0, 2.0/np.sqrt(3), 0)]
	# ul, ur, ub, bl, br, bf 
	edges = [(0, 2), (0, 3), (0, 1), (1, 2), (1, 3), (2, 3)]

	# Update tetrahedron plot
	while True:
		if r_conn.poll():
			ax.clear()
			links = r_conn.recv()
			for idx, edge in enumerate(edges):
				xs = [vertices[edge[0]][0], vertices[edge[1]][0]]
				ys = [vertices[edge[0]][1], vertices[edge[1]][1]]
				zs = [vertices[edge[0]][2], vertices[edge[1]][2]]
				ax.plot(xs, ys, zs, links[idx][1])
				ax.text(np.average(xs), np.average(ys), np.average(zs), f'P{links[idx][0]}', size=8, zdir=None, 
						ha="center", va="center",
						bbox=dict(boxstyle="circle",
							ec=links[idx][1],
							fc='lightgray',
						))
			#ax.grid(False)
			plt.tick_params(left = False, right = False, labelleft = False, labelbottom = False, bottom = False)
			plt.draw()
		plt.pause(5)