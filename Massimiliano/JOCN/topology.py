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
        G = nx.Graph()
        G.add_nodes_from(list(range(nr_tor)))
        pos = {}
        edges = []
        radius = 3
        weights = np.ones((self.num_tors_v, self.num_tors_h))
        self.connectivity_h = np.zeros((num_tors, num_tors))
        self.connectivity_v = np.zeros((num_tors, num_tors))

        for i in range(self.num_tors_v):
            for j in range(self.num_tors_h-1):
                pos[self.num_tors_v*i+j] = [radius * np.cos((self.num_tors_v*i+j) * 2*np.pi / nr_tor), radius * np.sin((self.num_tors_v*i+j) * 2*np.pi / nr_tor)]
                # pos[num_tors_v*i+j] = [j, i]
                for k in range(self.num_tors_h-j-1):
                # add horizontal edges
                    G.add_edge(self.num_tors_h*i+j, self.num_tors_h*i+j+k+1, weight=weights[i, j])
                    self.connectivity_h[self.num_tors_h*i+j, self.num_tors_h*i+j+k+1] = 1
                    self.connectivity_h[self.num_tors_h * i + j + k + 1, self.num_tors_h * i + j] = 1
                    # edges.append([num_tors_h*i+j, num_tors_h*i+j+k+1, weights[i, j]])
                    # add vertical edges
                    G.add_edge(i + self.num_tors_h * j, i+self.num_tors_h *(j +k+ 1), weight=weights[i, j])
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




