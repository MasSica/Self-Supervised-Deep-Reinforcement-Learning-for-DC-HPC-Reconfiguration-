
# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : sansingh, massica

"""This file contains the class implementing 
a customizable datacenter network topology with one OCS"""

import numpy as np
import sys
# from graph_topology import get_topo_reconfig
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt



class TopologyGenerator:
    def __init__(self, num_tors_v, num_tors_h ) -> None:
        self.dst_path = "."
        self.out_filename = 'topo_a2a_mp64.topology'
        self.num_tors_v = num_tors_v # produce square topology
        self.num_tors_h = num_tors_v
        self.num_tors = num_tors_h*num_tors_v
        self.num_port = int(np.sqrt(self.num_tors)) #- 1
        self.wave_capacity = 100
        self.connectivity = 0
        self.topo = 0
        self.nr_edges = 0

    def write_to_file(self):
        f = open(self.dst_path+ self.out_filename,'w') # .format(filename[12:-4]),'w')
        f.write('# Reconfigured topology \n\n')
        f.write('# Details \n')
        f.write('|V|='+ str(self.num_tors)+'\n')
        f.write('|E|='+ str(self.nr_edges) + '\n')
        f.write('ToRs=set(')
        for i in range(self.num_tors):
            if i != self.num_tors-1:
                f.write(str(i) + ",")
            elif i == self.num_tors-1:
                    f.write(str(i) + ')')

        f.write('\n')

        f.write('Servers=set(')
        for i in range(self.num_tors):
            if i != self.num_tors-1:
                f.write(str(i) + ',')
            elif i == self.num_tors-1:
                f.write(str(i) + ')')


        f.write('\n')
        f.write('Switches=set() \n\n')
        f.write('# Links \n')

        for i in range(self.num_tors):
            for j in range(self.num_tors):
                if self.connectivity[i,j] != 0 and i < j :
                    f.write(str(i) + ' ' + str(j) + ' ' + str(int(self.topo[i, j]*int(self.wave_capacity))) + '\n')
                    f.write(str(j) + ' ' + str(i) + ' ' + str(int(self.topo[j, i]*int(self.wave_capacity))) + '\n')
        f.close()

    # generate 2D HyperX fiber (link) connectivity graph
    def get_graph(self):
        nr_tor = self.num_tors_v* self.num_tors_h
        num_tors = self.num_tors_h* self.num_tors_v # temporary 
        G = nx.DiGraph()
        G.add_nodes_from(list(range(nr_tor)))
        pos = {}
        edges = []
        radius = 3
        weights = np.full((self.num_tors_v, self.num_tors_h), self.wave_capacity)  # represents the bandwidth
        self.connectivity_h = np.zeros((num_tors, num_tors))
        self.connectivity_v = np.zeros((num_tors, num_tors))

        for i in range(self.num_tors_v):
            for j in range(self.num_tors_h-1):
                pos[self.num_tors_v*i+j] = [radius * np.cos((self.num_tors_v*i+j) * 2*np.pi / nr_tor), radius * np.sin((self.num_tors_v*i+j) * 2*np.pi / nr_tor)]
                # pos[num_tors_v*i+j] = [j, i]
                for k in range(self.num_tors_h-j-1):
                # add horizontal edges
                    G.add_edge(self.num_tors_h*i+j, self.num_tors_h*i+j+k+1, weight=weights[i, j])
                    G.add_edge(self.num_tors_h*i+j+k+1,self.num_tors_h*i+j, weight=weights[i, j])
                    #print(f"added edge {(self.num_tors_h*i+j, self.num_tors_h*i+j+k+1)}")
                    #print(f"added edge {(self.num_tors_h*i+j+k+1,self.num_tors_h*i+j)}")
                    self.connectivity_h[self.num_tors_h*i+j, self.num_tors_h*i+j+k+1] = 1
                    self.connectivity_h[self.num_tors_h * i + j + k + 1, self.num_tors_h * i + j] = 1
                    # edges.append([num_tors_h*i+j, num_tors_h*i+j+k+1, weights[i, j]])
                    # add vertical edges
                    G.add_edge(i + self.num_tors_h * j, i+self.num_tors_h *(j +k+ 1), weight=weights[i, j])
                    G.add_edge(i+self.num_tors_h *(j +k+ 1), i + self.num_tors_h * j, weight=weights[i, j])
                    self.connectivity_v[i + self.num_tors_h * j, i+self.num_tors_h *(j +k+ 1)] = 1
                    self.connectivity_v[i + self.num_tors_h * (j + k + 1), i + self.num_tors_h * j] = 1
                    # edges.append([i + num_tors_h * j, i+num_tors_h *( j +k+ 1), weights[i, j]])
            pos[self.num_tors_v*i+j+1] = [radius * np.cos((self.num_tors_v*i+j+1) * 2*np.pi / nr_tor), radius * np.sin((self.num_tors_v*i+j+1) * 2*np.pi / nr_tor)]
        
        
        
        #nx.draw(G, pos, node_color="grey", with_labels=True)
        #plt.pause(0.001)
        #plt.show()

        # additional instance variables 
        self.nr_edges = np.sum(np.sum(self.topo > 0))
        self.connectivity = self.connectivity_h + self.connectivity_v
        self.topo = self.connectivity

        return G, self.connectivity_h, self.connectivity_v


    def get_reconfig_graph(self, toplogy_matrix):
        print('--------- GETTING NEW TOPOLOGY ------------')
        #print(toplogy_matrix)
        G = nx.DiGraph()
        nr_tor = self.num_tors_v* self.num_tors_h
        G = nx.DiGraph()
        G.add_nodes_from(list(range(nr_tor)))

        for i in range(len(toplogy_matrix)):
            for j in range(len(toplogy_matrix[0])):
                if toplogy_matrix[i][j] == 1:
                    G.add_edge(i, j, weight=100)
        print("-------new edges-----------")
        print(G.edges)
        return G

    
    def get_topo_optimal(self, tm, num_port=1, wave_capacity=100):
        num_tors_v = self.num_tors_h
        num_tors_h = self.num_tors_v
        num_tors = num_tors_h*num_tors_v

        traffic_matrix=np.array([np.array(x) for x in tm])

        # get flat multi-POD topology
        G, connectivity_h, connetivity_v = self.get_graph()
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
