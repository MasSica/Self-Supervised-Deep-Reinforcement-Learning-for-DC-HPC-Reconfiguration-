"""This file contains the class implementing 
a customizable datacenter network topology with one OCS"""

# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : sansingh

import numpy as np
import sys
# from graph_topology import get_topo_reconfig
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# generate 2D HyperX fiber (link) connectivity graph
def get_graph(num_tors_v, num_tors_h):
    nr_tor = num_tors_v*num_tors_h
    G = nx.Graph()
    G.add_nodes_from(list(range(nr_tor)))
    pos = {}
    edges = []
    radius = 3
    weights = np.ones((num_tors_v,num_tors_h))
    connetivity_h = np.zeros((num_tors, num_tors))
    connetivity_v = np.zeros((num_tors, num_tors))
    for i in range(num_tors_v):
        for j in range(num_tors_h-1):
            pos[num_tors_v*i+j] = [radius * np.cos((num_tors_v*i+j) * 2*np.pi / nr_tor), radius * np.sin((num_tors_v*i+j) * 2*np.pi / nr_tor)]
            # pos[num_tors_v*i+j] = [j, i]
            for k in range(num_tors_h-j-1):
            # add horizontal edges
                G.add_edge(num_tors_h*i+j, num_tors_h*i+j+k+1, weight=weights[i, j])
                connetivity_h[num_tors_h*i+j, num_tors_h*i+j+k+1] = 1
                connetivity_h[num_tors_h * i + j + k + 1, num_tors_h * i + j] = 1
                # edges.append([num_tors_h*i+j, num_tors_h*i+j+k+1, weights[i, j]])
                # add vertical edges
                G.add_edge(i + num_tors_h * j, i+num_tors_h *(j +k+ 1), weight=weights[i, j])
                connetivity_v[i + num_tors_h * j, i+num_tors_h *(j +k+ 1)] = 1
                connetivity_v[i + num_tors_h * (j + k + 1), i + num_tors_h * j] = 1
                # edges.append([i + num_tors_h * j, i+num_tors_h *( j +k+ 1), weights[i, j]])
        pos[num_tors_v*i+j+1] = [radius * np.cos((num_tors_v*i+j+1) * 2*np.pi / nr_tor), radius * np.sin((num_tors_v*i+j+1) * 2*np.pi / nr_tor)]
    # nx.draw(G, pos, node_color="grey", with_labels=True)
    # plt.pause(0.001)
    # plt.show()
    return G, connetivity_h, connetivity_v



if __name__ == "__main__":
    #src_path = "/work/Python_work/resources/"
    dst_path = "."
    out_filename = 'topo_a2a_mp64.topology' # topo_a2a_mp64 , topo_reconfig_mp64_AMR_2FSR

    # Here we are building a square ToR topology 
    num_tors_v = 2
    num_tors_h = num_tors_v
    num_tors = num_tors_h*num_tors_v

    # get flat multi-POD topology
    G, connectivity_h, connetivity_v = get_graph(num_tors_v, num_tors_h)
    num_port = int(np.sqrt(num_tors)) #- 1

    connectivity = connectivity_h + connetivity_v
    # enable  next line for all2all topo_a2a_mp16.topology
    topo = connectivity
    wave_capacity = 100
    nr_edges = np.sum(np.sum(topo > 0))

    # output to the link file , topo_reconfig_mp64_{}.topology
    f = open(dst_path+out_filename,'w') # .format(filename[12:-4]),'w')
    f.write('# Reconfigured topology \n\n')
    f.write('# Details \n')
    f.write('|V|='+ str(num_tors)+'\n')
    f.write('|E|='+ str(nr_edges) + '\n')
    f.write('ToRs=set(')
    for i in range(num_tors):
        if i != num_tors-1:
            f.write(str(i) + ",")
        elif i == num_tors-1:
                f.write(str(i) + ')')

    f.write('\n')

    f.write('Servers=set(')
    for i in range(num_tors):
        if i != num_tors-1:
            f.write(str(i) + ',')
        elif i == num_tors-1:
            f.write(str(i) + ')')


    f.write('\n')
    f.write('Switches=set() \n\n')
    f.write('# Links \n')

    for i in range(num_tors):
        for j in range(num_tors):
            if connectivity[i,j] != 0 and i < j :
                f.write(str(i) + ' ' + str(j) + ' ' + str(int(topo[i, j]*int(wave_capacity))) + '\n')
                f.write(str(j) + ' ' + str(i) + ' ' + str(int(topo[j, i]*int(wave_capacity))) + '\n')
    f.close()


