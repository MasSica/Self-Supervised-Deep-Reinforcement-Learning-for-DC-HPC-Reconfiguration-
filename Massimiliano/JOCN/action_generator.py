"""
given the size of the network and the total traffic matrix generates a set of 50 actions 
"""

from topology import TopologyGenerator
import random 
import networkx as nx 
import copy
import time 
import numpy as np

def action_generator(num_tors_h,num_tors_v, tm):
    print('generating actions')
    num_actions = 4 # number of actions in addition to optimal 
    num_worst = 15
    tp = TopologyGenerator(num_tors_v, num_tors_h)
    actions = []

    optimal_topo, adjacency = tp.get_topo_optimal(tm)
    actions.append(optimal_topo)
    
    #add worst topology, U will add a certain number of these 
    for _ in range(num_worst):
        actions.append(np.array([[0]*(num_tors_h*num_tors_v)]*(num_tors_h*num_tors_v)))

    # modify optimal action to extend action space, remove one edge per iteration  

    for _ in range(num_actions):
        mtx = copy.deepcopy(adjacency)
        u = random.randrange(num_tors_h)
        v = random.randrange(num_tors_h)
        if mtx[u][v] != 0:
            mtx[u][v] = 0
            mtx[v][u] = 0
            actions.append(mtx)
        else:
            mtx[u+1][v+1] = 0
            mtx[v+1][u+1] = 0
            actions.append(mtx)

    with open('actions.txt','w') as f:
        f.write(str(actions))

    return actions    

"""
topo = TopologyGenerator(2,2)
tm = [[0, 0, 70.0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
G = topo.get_graph()
action_generator(G,2,2,tm)
"""    

