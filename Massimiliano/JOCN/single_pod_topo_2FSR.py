# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : sansingh

import numpy as np
import sys
# from graph_topology import get_topo_reconfig
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

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


def get_topo_reconfig(traffic_matrix, num_port, wave_capacity):
    num_tors_v = int(np.sqrt(traffic_matrix.shape[0]))
    num_tors_h = num_tors_v
    num_tors = num_tors_h*num_tors_v
    # get flat multi-POD topology
    G, connectivity_h, connetivity_v = get_graph(num_tors_v, num_tors_h)
    num_inport_h = num_port * np.ones(num_tors)
    num_inport_v = num_port * np.ones(num_tors)
    num_outport_h = num_port * np.ones(num_tors)
    num_outport_v = num_port * np.ones(num_tors)

    # determine the topology
    weight_matrix = traffic_matrix.copy()
    topology = np.zeros(shape=(num_tors, num_tors))
    # tp = 1
    # te = 1
    record_node = np.zeros(shape=(num_tors, num_tors))
    weight_matrix[weight_matrix == 0] = -sys.maxsize
    while ((sum(num_inport_h>0) > 1 and sum(num_outport_h>0) > 1) or
           (sum(num_inport_v>0) > 1 and sum(num_outport_v>0) > 1))\
            and np.max(np.max(weight_matrix)) != -sys.maxsize:
        src_node = np.argmax(weight_matrix)//num_tors
        dst_node = np.argmax(weight_matrix)%num_tors
        # src_node
        path = nx.shortest_path(G, source=src_node, target=dst_node, weight="weight", method='bellman-ford')
        total = 0
        for node1, node2 in zip(path, path[1:]):
            if connectivity_h[node1, node2] == 1 and num_outport_h[node1]> 0 and num_inport_h[node2]> 0:
                total += 1
            elif connetivity_v[node1, node2] == 1 and num_outport_v[node1]> 0 and num_inport_v[node2]> 0:
                total += 1

        if total == len(path)-1:
            for node1, node2 in zip(path, path[1:]):
                if connectivity_h[node1, node2] == 1:
                    num_outport_h[node1] = num_outport_h[node1] - 1
                    num_inport_h[node2] = num_inport_h[node2] - 1
                    num_outport_h[node2] = num_outport_h[node2] - 1
                    num_inport_h[node1] = num_inport_h[node1] - 1
                elif connetivity_v[node1, node2] == 1:
                    num_outport_v[node1] = num_outport_v[node1] - 1
                    num_inport_v[node2] = num_inport_v[node2] - 1
                    num_outport_v[node2] = num_outport_v[node2] - 1
                    num_inport_v[node1] = num_inport_v[node1] - 1

                if record_node[node1, node2] == 0:
                    record_node[node1, node2] = 1
                    record_node[node2, node1] = 1
                topology[node1, node2] = topology[node1, node2] + 1
                topology[node2, node1] = topology[node2, node1] + 1
            # topology
            weight_matrix[src_node, dst_node] = weight_matrix[src_node, dst_node] - wave_capacity
            weight_matrix[dst_node, src_node] = weight_matrix[dst_node, src_node] - wave_capacity

        else:
            weight_matrix[src_node, dst_node] = -sys.maxsize
            weight_matrix[dst_node, src_node] = -sys.maxsize
    # allocate remaining ports
    aa = np.where(num_outport_h > 0)[0]
    for i in aa:
        for j in aa[np.where(aa==i)[0][0]:]:
            if connectivity_h[i, j] > 0 and num_outport_h[i] > 0 and num_outport_h[j] > 0: # num_outport is changing
                port_add = min(num_outport_h[i], num_outport_h[j])
                topology[i, j] = topology[i, j] + port_add
                topology[j, i] = topology[j, i] + port_add
                num_outport_h[i] = num_outport_h[i] - port_add
                num_outport_h[j] = num_outport_h[j] - port_add

    aa = np.where(num_outport_v > 0)[0]
    for i in aa:
        for j in aa[np.where(aa==i)[0][0]:]:
            if connetivity_v[i, j] > 0 and num_outport_v[i] > 0 and num_outport_v[j] > 0:
                port_add = min(num_outport_v[i], num_outport_v[j])
                topology[i, j] = topology[i, j] + port_add
                topology[j, i] = topology[j, i] + port_add
                num_outport_v[i] = num_outport_v[i] - port_add
                num_outport_v[j] = num_outport_v[j] - port_add


    return topology, connectivity_h + connetivity_v


# tm = np.array([[0.0, 10.0, 10.0, 10.0], [10.0, 0.0, 10.0, 10.0], [10.0, 10.0, 0.0, 10.0], [10.0, 10.0, 10.0, 0.0]])
# tm = np.array([[0.0, 0.01, 0.4, 0.0], [0.01, 0.0, 0.01, 0.01], [0.4, 0.01, 0.0, 0.07], [0.0, 0.01, 0.07, 0.0]])
# dst_path = "/work/netbench_reconfig/reconfig_topo/"
src_path = "/work/Python_work/resources/"
dst_path = "/work/netbench_reconfig_JLT/reconfig_topo/"
filename = "tor_heatmap_AMR_MiniApp_n1728_dumpi-1.csv" #"ar_predicted_new_1234.csv
out_filename = 'topo_feconfig_mp64.topology' # topo_a2a_mp64 , topo_reconfig_mp64_AMR_2FSR
all2all = False #True
FSR = "1" # "1", "2"
with open(src_path+filename, "r") as f:
    tm_all = pd.read_csv(f, header=None, dtype=float) #f.read()
    for run_num in range(0, 1): #len(tm_all)): # take only 1 out of 20 tm
        # tm = np.array(tm_all.iloc[run_num,:])
        # num_tors = int(np.sqrt(tm.shape[0]))
        # tm = tm.reshape(num_tors, num_tors)
        tm = np.array(tm_all)
        np.fill_diagonal(tm, 0)
        tm = tm/np.sum(np.sum(tm))
        num_tors = len(tm)

        num_port = int(np.sqrt(num_tors)) #- 1
        wave_capacity = 50 # Gbps
        fixed_capacity = 50
        # tm_g_0 = reshape(tm, num_tors, num_tors).'
        topo, connectivity = get_topo_reconfig(tm, num_port, wave_capacity)
        # enable  next line for all2all topo_a2a_mp16.topology
        if all2all == True:
            topo = connectivity
        if FSR == "1":
            fixed_capacity = 0
            wave_capacity = 2*wave_capacity
            nr_edges = np.sum(np.sum(topo > 0))
        else:
            nr_edges = np.sum(np.sum(connectivity > 0))
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
                if connectivity[i,j] != 0 and i < j and int(topo[i, j]*wave_capacity +fixed_capacity)>0:
                    f.write(str(i) + ' ' + str(j) + ' ' + str(int(topo[i, j]*int(wave_capacity)+ int(fixed_capacity))) + '\n')
                    f.write(str(j) + ' ' + str(i) + ' ' + str(int(topo[j, i]*int(wave_capacity)+ int(fixed_capacity))) + '\n')
        f.close()
