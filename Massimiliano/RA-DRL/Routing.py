"""Here I will take care of routing in the data plane so that the DRL algorithm only has to care about OCS reconfig.
I am going to pick the first k shortest paths for each demand and choose the one with better capacity usage

Example of traffic matrix with 4 servers (Gbps)

1  0 0 100 0
2  0 0  0  50
3  0 0  0   0
4 40 0  0   0
   1 2  3  4

The traffic matrix is gathered from the servers and has the above shape saved in a pandas dataframe


Plus I know that the following ports are installed in the following switches

22, 18 -> br2
21,17 -> br1
24,20 -> br4
23, 19 -> br3

"""
import time

import networkx as nx
from collections import defaultdict
from Switch_communication import *


class Routing:

    def __init__(self, traffic_matrix):
        self.traffic_matrix = traffic_matrix
        self.credentials = json.load(open('credentials.json'))

    # this method will get the correct topology every time it is called and clear all the flows and reset the network
    def get_topology(self, ocs_matrix, delete):
        print('--------- GETTING NEW TOPOLOGY ------------')
        #11 12 13 14 are our servers

        if delete:
            for dpid in self.credentials["dpid"]:
                SwitchCom().del_all_flows(dpid)

        bandwidth = 10000000000 # 10Gbps is the currently configured max speed and gets reset in the code every time i call get toology!
        g = nx.DiGraph()

        g.add_edge(11, 1, bandwidth=bandwidth, ports=[None, 1], ocs="False") # 11 is vm1 and 1 is br1, ports[None, port 1 of bridge 1]
        g.add_edge(1, 11, bandwidth=bandwidth, ports=[1, None], ocs="False")

        #g.add_edge(1, 2, bandwidth=bandwidth, ports=[9, 10], ocs="False")
        #g.add_edge(2, 1, bandwidth=bandwidth, ports=[10, 9], ocs="False")

        #g.add_edge(1, 4, bandwidth=bandwidth, ports=[5, 6], ocs="False")
        #g.add_edge(4, 1, bandwidth=bandwidth, ports=[6, 5], ocs="False")

        g.add_edge(12, 2, bandwidth=bandwidth, ports=[None, 2], ocs="False")
        g.add_edge(2, 12, bandwidth=bandwidth, ports=[2, None], ocs="False")

        #g.add_edge(3, 4, bandwidth=bandwidth, ports=[12, 11], ocs=False)
        #g.add_edge(4, 3, bandwidth=bandwidth, ports=[11, 12], ocs=False)

        g.add_edge(3, 13, bandwidth=bandwidth, ports=[3, None], ocs=False)
        g.add_edge(13, 3, bandwidth=bandwidth, ports=[None, 3], ocs=False)

        g.add_edge(4, 14, bandwidth=bandwidth, ports=[4, None], ocs=False)
        g.add_edge(14, 4, bandwidth=bandwidth, ports=[None, 4], ocs=False)

        #g.add_edge(2, 3, bandwidth=bandwidth, ports=[7, 8], ocs=False)
        #g.add_edge(3, 2, bandwidth=bandwidth, ports=[8, 7], ocs=False)


        g.add_edge(15, 1, bandwidth=bandwidth, ports=[None, 13], ocs=False)  #vm8 is connected to br1 on port 13
        g.add_edge(1, 15, bandwidth=bandwidth, ports=[13,None], ocs=False)


        g.add_edge(16, 3, bandwidth=bandwidth, ports=[None, 14], ocs=False)  #vm7
        g.add_edge(3, 16, bandwidth=bandwidth, ports=[14, None], ocs=False)




        # dpid = data path id is a id for each bridge
        attrs = {11: {"dpid": None}, 12: {"dpid": None}, 14: {"dpid": None}, 13: {"dpid": None}, 15: {"dpid": None}, 16: {"dpid": None}, # these 11 to 16 are servers, so no dpid
                 1: {"dpid": self.credentials["dpid"][0]}, 4: {"dpid": self.credentials["dpid"][3]}, # 1 to 4 are bridges so we associate a dpid to the bridges
                 2: {"dpid": self.credentials["dpid"][1]}, 3: {"dpid": self.credentials["dpid"][2]}}

        nx.set_node_attributes(g, attrs) # setting the attributes


        #but first I will delete all the edges which have previously been added thanks to ocs (try to do this from matrix later on)

        for edge in g.edges.data():                 # edge is a tuple (u v dict)
            if edge[2]['ocs']== True:
                g.remove_edge(edge[0],edge[1])


        #I use a mapping in credentials to get the dpid ports connected to the ocs
        # this adds edges between bridges due to ocs
        k = 0
        h = 0
        for i in range(len(ocs_matrix)):
            for j in range(len(ocs_matrix[0])):
                if ocs_matrix[i][j] == 1:
                    # to make sure we reconsider each dpid twice
                    if i >= 4:
                        k = i - 4
                    else:
                        k = i

                    if j >= 4:
                        h = j - 4
                    else:
                        h = j

                    print('adding edge '+str(k+1)+ ' '+str(h+1))
                    #g.add_edge(i + 1, j + 1, bandwidth=bandwidth, ports=[self.credentials["dpid_to_ocs_port"][g.nodes[j+1]["dpid"]], self.credentials["dpid_to_ocs_port"][g.nodes[i+1]["dpid"]]], ocs="True")
                    #g.add_edge(i + 1, j + 1, bandwidth=bandwidth, ports=[self.credentials["dpid_to_ocs_port"][g.nodes[i+1]["dpid"]], self.credentials["dpid_to_ocs_port"][g.nodes[j+1]["dpid"]]], ocs="True")
                    g.add_edge(k + 1, h + 1, bandwidth=bandwidth, ports=[self.credentials["ocs_index_port_in"][str(i)], self.credentials["ocs_index_port_in"][str(j)]], ocs="True")
                    g.add_edge(h + 1, k + 1, bandwidth=bandwidth, ports=[self.credentials["ocs_index_port_in"][str(j)], self.credentials["ocs_index_port_in"][str(i)]], ocs="True")
        return g

    # get dictionary of demands between ips
    def get_demand_dict(self):

        to_route = [tuple(['10.0.0.1', '10.0.0.2']), tuple(['10.0.0.1', '10.0.0.3']), tuple(['10.0.0.1', '10.0.0.4']), tuple(['10.0.0.2', '10.0.0.1']), tuple(['10.0.0.2', '10.0.0.3']),tuple(['10.0.0.2', '10.0.0.4']), tuple(['10.0.0.3', '10.0.0.1']), tuple(['10.0.0.3', '10.0.0.2']), tuple(['10.0.0.3', '10.0.0.4']), tuple(['10.0.0.4', '10.0.0.1']), tuple(['10.0.0.4', '10.0.0.2']), tuple(['10.0.0.4', '10.0.0.3'])]


        demand_dict = {} # demands between ips
        keys = []

        # we first need to extract the demands from the traffic matrix

        for i in range(len(self.traffic_matrix)):

            for j in range(len(self.traffic_matrix[0])):

                # If the matrix entry is different from zero we have some traffic going from i to j and I directly convert it to an ip

                if self.traffic_matrix[i][j] != 0:
                    if tuple([self.credentials['vm_credentials_map2'][str(i+11)], self.credentials['vm_credentials_map2'][str(j+11)]]) not in keys:
                        keys.append(tuple([self.credentials['vm_credentials_map2'][str(i+11)], self.credentials['vm_credentials_map2'][str(j+11)]]))

                    demand_dict[tuple([self.credentials['vm_credentials_map2'][str(i+11)],
                                       self.credentials['vm_credentials_map2'][str(j+11)]])] = []
                    demand_dict[tuple([self.credentials['vm_credentials_map2'][str(i+11)],
                                       self.credentials['vm_credentials_map2'][str(j+11)]])].append(self.traffic_matrix[i][j])

        # I need to make sure that there is a path for everything
        for elem in to_route:
            if elem not in keys:
                demand_dict[elem] = [100]
        # 10.0.0.7 and 8 are ips for new vms, we swap their demands because ips might be assigned inversely
        # iperf traffic from 8 to 7
        if tuple(['10.0.0.8', '10.0.0.7']) not in demand_dict:
            demand_dict[tuple(['10.0.0.8','10.0.0.7'])] = [self.traffic_matrix[5][4]]
            demand_dict[tuple(['10.0.0.7', '10.0.0.8'])] = [100]



        return demand_dict

    def reduce_band(self, path, g, size):

            prev = 0  # first node of path

            for i in range(1, len(path)):

                # careful I need to check link per link if the bandwidth is enough otherwise move to next path

                if g.edges[path[prev], path[i]]['bandwidth'] >= size:
                    print(f'---------- IS ALL GOOD ON {path[prev], path[i]}----------------')
                    g.edges[path[prev], path[i]]['bandwidth'] -= size  # reduce the bandwidth of the link since now we have used some of the availbale resources
                    new_band= g.edges[path[prev], path[i]]['bandwidth']
                    print(f'---------- NEW BAND {new_band} ----------------')
                    prev = i

                # if it is bigger still route and lets see what happens (!!!!!!!!!)
                else:
                    print(f'---------USING NEGATIVE BANDWIDTH ON {path[prev], path[i]}----------')
                    g.edges[path[prev], path[i]]['bandwidth'] = 0  # -= size    #reduce the bandwidth of the link since now we have used some of the availbale resources
                    prev = i


    # update the band without installing teh flows given the paths currently used in  the network
    def update_graph(self, g, current_paths):
        print('--------------------------------UPDATING GRAPH-------------------------------')
        demand_dict = self.get_demand_dict()
        for key in demand_dict.keys():
            for path in current_paths[key]:
                self.reduce_band(path, g, demand_dict[key][0])
                demand_dict[key][0] = 0 # here the second iperf flow traffic is ignored since I cannot distinguish the traffic needs of the two

    def find_path(self, start, end, g, size): # size : flow demand

        # I take as input the start node then destination node
        # first thing I get the k shortest paths
        try:
            paths_ret = nx.shortest_simple_paths(g, start, end)
            paths = []
            k = 5

            for counter, path in enumerate(paths_ret):
                paths.append(path)

                if counter == k - 1:
                    break

            # now I pick the shortest path which has the most bandwidth left

            best_path = []
            best_bandwidth = float('inf')

            path_memory = []

            for path in paths:
                bandwidth_available = 0
                prev = 0  # first node of path
                neg_band = False

                for i in range(1, len(path)):

                    # careful I need to check link per link if the bandwidth is enough otherwise move to next path

                    if g.edges[path[prev], path[i]]['bandwidth'] >= size:
                        bandwidth_available += g.edges[path[prev], path[i]]['bandwidth']
                        prev = i

                    else:

                        bandwidth_available += g.edges[path[prev], path[i]]['bandwidth']

                        # care for negative available bandwidth between bridges, avoid between vms
                        if tuple([path[prev], path[i]]) not in [tuple([1, 11]), tuple([11, 1]), tuple([2, 12]), tuple([12, 2]), tuple([3, 13]), tuple([13, 3]), tuple([4, 14]), tuple([14, 3])]:
                            neg_band = True

                        prev = i

                # I pick the path using less(NO) MORE bandwidth available (size constraint has been already checked link by link)
                path_memory.append(path)
          
                if bandwidth_available < best_bandwidth and not neg_band:
                    best_path = path.copy()
                    best_bandwidth = bandwidth_available

            if len(best_path) == 0:   # in case no non congested path was found we just route on the first onelllllll
                best_path= path_memory[0].copy()

            return best_path

        except:
            print(f'No path found between {start, end}')
            return []

    # to reset the band without installing the flows
    def reset_bandwidth(self, g):

        # reset bandwidth
        print('--------RESETTING BANDWIDTH---------')
        for edge in g.edges.data():
            edge[2]['bandwidth'] = 10000000000


    def get_flow_info_install(self, g, key, best_path, tcp_dst):
        # for each dpid in best path I install the flows
        i = 1
        prev = 0
        while i < len(best_path):

            if g.nodes[best_path[prev]]['dpid'] is None:
                # We only get the input port for the next datapath, since we are dealing with a server
                port_in = g[best_path[prev]][best_path[i]]['ports'][1]
                prev = i
                i += 1

            else:
                port_out = g[best_path[prev]][best_path[i]]['ports'][0]

                print('Installing flow on dpid: ' + str(
                    g.nodes[best_path[prev]]['dpid']) + ' ' + 'on input port ' + str(
                    port_in) + ' ' + 'to port ' + str(
                    port_out) + ' ' + 'from ip ' + str(
                    list(key)[0]) + ' ' + 'to ip ' + str(list(key)[1]))

                SwitchCom().edit_bidirectional_flows(action='ADD', dpid=int(g.nodes[best_path[prev]]['dpid']),
                                                     in_port=port_in,
                                                     out_port=port_out,
                                                     # to get the output port we need to consider the following flow
                                                     ip_src=list(key)[0], ip_dst=list(key)[1], tcp_dst=tcp_dst,
                                                     # i just put a  random number here, it is not important
                                                     priority=10)

                port_in = g[best_path[prev]][best_path[i]]['ports'][1]
                prev = i
                i += 1


   # this function also takes care of reducing the band and is always called on a new topology hence no need to reset

    def install_flow(self, g):



        # when I create the topology I delete all the flows so when i get here i have to start brand new

        best_paths = [] # this one contains all the paths used by only the DML
        best_paths_iperf = defaultdict(list)  # this one includes the iperf needed by update graph

        #get list of demands
        demand_dict = self.get_demand_dict()
        best_iperf_path = []

# ---------------------------IPERF STUFF ---------------------------------------------------------------------------

        print(f'pre iperf demand dict {demand_dict}')
        # here I have to take care of the possibility of having an iperf modified matrix above 1G

        iperf_size = 10000000000

        if tuple(['10.0.0.8', '10.0.0.7']) in list(demand_dict.keys()) and demand_dict[tuple(['10.0.0.8', '10.0.0.7'])][0] > 3000000000: #200000000 is 2gbit

            print('----------IPERF DETECTED -------------')


            if demand_dict[tuple(['10.0.0.8', '10.0.0.7'])][0] < iperf_size:
                demand_dict[tuple(['10.0.0.8', '10.0.0.7'])][0] = 0


            else:
                demand_dict[tuple(['10.0.0.8', '10.0.0.7'])][0] = 0 #-= iperf_size  # get rid of the iperf data from the demands dictionnary

            # now we update the bandwidth edge by edge on the chosen path for iperf

            best_iperf_path = self.find_path(15, 16, g, iperf_size)  # finds the best path
            self.reduce_band(best_iperf_path, g, iperf_size)  # here we actually reduce thr band on the needed links
            print(f'-------CHOSEN PATH FOR IPERF {best_iperf_path} --------------')
            self.get_flow_info_install(g, tuple(['10.0.0.8', '10.0.0.7']), best_iperf_path, 100) # 100 is port nur of tcp for iperf

           # best_paths[tuple(['10.0.0.1','10.0.0.3'])] = []
            best_paths_iperf[tuple(['10.0.0.8', '10.0.0.7'])].append(best_iperf_path)   # best iperf path will be in position 0



        print(f'post iperf demand dict {demand_dict}')

#-----------------------------------------------------------------------------------------------------------------
        # for every demand get best path mapping ip to node index REMEMBER: subtract bandwidth for each installed flow
        print('debugging')
        for key in demand_dict.keys():
            print(key)
            best_path = self.find_path(int(self.credentials['vm_credentials_map'][key[0]]),
                                       int(self.credentials['vm_credentials_map'][key[1]]),
                                       g, demand_dict[key][0])

            print(f'best path for {key} is {best_path} ')
            self.reduce_band(best_path, g, demand_dict[key][0])  # NEW!!
            self.get_flow_info_install(g, key, best_path, 100) # this actually installs the flow
            print(f'installing {best_path, key}')

            if best_path != best_iperf_path:
                best_paths.append(best_path)  # I only add the paths used by the dml
                print('appended '+str(best_path))
            best_paths_iperf[key].append(best_path)


        return best_paths, best_paths_iperf
