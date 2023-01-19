"""
Here I am going to implement the traffic monitoring system that consists in collecting statistics from all the servers

"""
import time

from Switch_communication import *
import json
import networkx as nx


class TrafficMonitor():

    def __init__(self):
        self.credentials = json.load(open('credentials.json'))

    def get_traffic_matrix(self):

        # here i test the sflow rest api to build the traffic matrix
        r = requests.get(url="XXXXX") # get flow information from sflow
        r = json.loads(r.text) # json file format


        # here i scan the dictionary knowing that the first entries are the most recent

        vm1_demands = {}
        vm2_demands = {}
        vm3_demands = {}
        vm4_demands = {}
        vm7_demands = {}
        vm8_demands = {}

        # we need to make sure we don't get some pairs twice since the records are long in the past
        met_pairs = []

        for element in r:
            if element['name'] == "tcp" and element['flowKeys'] not in met_pairs:

                if element['flowKeys'].split(',')[0] == '10.0.0.1':
                    vm1_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])

                elif element['flowKeys'].split(',')[0] == '10.0.0.2':
                    vm2_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])

                elif element['flowKeys'].split(',')[0] == '10.0.0.3':
                    vm3_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])

                elif element['flowKeys'].split(',')[0] == '10.0.0.4':
                    vm4_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])

                elif element['flowKeys'].split(',')[0] == '10.0.0.7':
                    vm7_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])

                else:
                    vm8_demands[element['flowKeys'].split(',')[1]] = element['value']  # destination : value
                    met_pairs.append(element['flowKeys'])




        traffic_matrix = []

        vm1 = [0, 0, 0, 0, 0, 0]
        vm2 = [0, 0, 0, 0, 0, 0]
        vm3 = [0, 0, 0, 0, 0, 0]
        vm4 = [0, 0, 0, 0, 0, 0]
        vm7 = [0, 0, 0, 0, 0, 0]
        vm8 = [0, 0, 0, 0, 0, 0]

        # I am aware this part could be done more efficiently 

        for key in list(vm1_demands.keys()):
            if key == '10.0.0.2':
                vm1[1] = vm1_demands[key]
            elif key == '10.0.0.3':
                vm1[2] = vm1_demands[key]
            elif key == '10.0.0.4':
                vm1[3] = vm1_demands[key]
            elif key == '10.0.0.7':
                vm1[4] = vm1_demands[key]
            elif key == '10.0.0.8':
                vm1[5] = vm1_demands[key]


        for key in list(vm2_demands.keys()):
            if key == '10.0.0.1':
                vm2[0] = vm2_demands[key]
            elif key == '10.0.0.3':
                vm2[2] = vm2_demands[key]
            elif key == '10.0.0.4':
                vm2[3] = vm2_demands[key]
            elif key == '10.0.0.7':
                vm2[4] = vm2_demands[key]
            elif key == '10.0.0.8':
                vm2[5] = vm2_demands[key]

        for key in list(vm3_demands.keys()):
            if key == '10.0.0.1':
                vm3[0] = vm3_demands[key]
            elif key == '10.0.0.2':
                vm3[1] = vm3_demands[key]
            elif key == '10.0.0.4':
                vm3[3] = vm3_demands[key]
            elif key == '10.0.0.7':
                vm3[4] = vm3_demands[key]
            elif key == '10.0.0.8':
                vm3[5] = vm3_demands[key]

        for key in list(vm4_demands.keys()):
            if key == '10.0.0.1':
                vm4[0] = vm4_demands[key]
            elif key == '10.0.0.2':
                vm4[1] = vm4_demands[key]
            elif key == '10.0.0.3':
                vm4[2] = vm4_demands[key]
            elif key == '10.0.0.7':
                vm1[4] = vm4_demands[key]
            elif key == '10.0.0.8':
                vm1[5] = vm4_demands[key]

        for key in list(vm7_demands.keys()):
            if key == '10.0.0.1':
                vm7[0] = vm7_demands[key]
            elif key == '10.0.0.2':
                vm7[1] = vm7_demands[key]
            elif key == '10.0.0.3':
                vm7[2] = vm7_demands[key]
            elif key == '10.0.0.4':
                vm7[3] = vm7_demands[key]
            elif key == '10.0.0.8':
                vm7[5] = vm7_demands[key]

        for key in list(vm8_demands.keys()):
            if key == '10.0.0.1':
                vm8[0] = vm8_demands[key]
            elif key == '10.0.0.2':
                vm8[1] = vm8_demands[key]
            elif key == '10.0.0.3':
                vm8[2] = vm8_demands[key]
            elif key == '10.0.0.7':
                vm8[4] = vm8_demands[key]
            elif key == '10.0.0.4':
                vm8[3] = vm8_demands[key]


        traffic_matrix.append(vm1)
        traffic_matrix.append(vm2)
        traffic_matrix.append(vm3)
        traffic_matrix.append(vm4)
        traffic_matrix.append(vm7)
        traffic_matrix.append(vm8)

        return traffic_matrix

    # gets a list of all the edges that belong to the DML

    def break_into_edges(self, current_paths):

        edge_list = []
        path_not_found = False
        counter = 0
        for path in current_paths:
            if len(path) == 0:
                path_not_found = True
                counter += 1

            for i in range(len(path)-1):

                edge_list.append(tuple([path[i], path[i+1]]))

        return edge_list, path_not_found, counter, len(current_paths)

    def normalize(self, value):

        lower = 0.208
        upper = 0.125
        l_norm = lower + (upper - lower) * value

        return l_norm


    # this function will check if the given action will produce a collapse

    def will_collapse(self, r, g_tb):

        metric = None
        # I get the dictionnary of demands
        demand_dict = r.get_demand_dict()

        best_paths =[]

        # now i build the set of paths
        for key in demand_dict.keys():
            best_path = r.find_path(int(self.credentials['vm_credentials_map'][key[0]]),
                                       int(self.credentials['vm_credentials_map'][key[1]]),
                                       g_tb, demand_dict[key][0])

            best_paths.append(best_path)  # I only add the paths used by the dml



        # with this functio I check weteher a path was not found (ie a collapse)
        _, collapse, counter_nulls, counter =self.break_into_edges(best_paths)

        print(counter)

        if collapse or counter <= 10 :
            metric = 2 * self.normalize(counter_nulls / 12)

            return True, metric
        else:
            return False, metric


    # TO COLLECT THE METRIC FOR NUMBER OF LINKS CONGESTED
    def monitor(self, g, traffic_matrix, check_collapse, current_paths):
        reconfigure_flag = False
        max_band = 10000000000
        collapse_flag = False

        dml_edges, path_not_found, counter_nulls, counter = self.break_into_edges(current_paths) # edges not traversed by iperf,

        bandwidth_data = nx.get_edge_attributes(g, "bandwidth") # gets the remaining band available on a link

        if tuple([1, 15]) in dml_edges:
            dml_edges.remove(tuple([1, 15]))

        if tuple([16, 3]) in dml_edges:
            dml_edges.remove(tuple([16, 3]))

        # number of bottlenecked links (usage above 20 percent) as metric

        edges_non_conforming = 0
        for edge in bandwidth_data:
            if bandwidth_data[edge] <= 0.20 * max_band and edge in dml_edges:     # if for the specific link the band available is above 80 percent and belongs to dml  keep track
                #sum_band_non_conforming += bandwidth_data[edge]
                edges_non_conforming += 1
                print(f'non conforming {edge}')


        number_edges = 24 #g.number_of_edges() 12x2 since bidirectional and considering vm to tor links

        # condition for reconfiguration
        if edges_non_conforming/number_edges >=0.010:  # if the percentage of non conforming links of the dml is above 10%
            reconfigure_flag = True
            metric = edges_non_conforming / number_edges

        else:

            metric = edges_non_conforming / number_edges



        return reconfigure_flag, collapse_flag, metric, edges_non_conforming


