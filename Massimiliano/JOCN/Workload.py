# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : massica

"""
This class will implement a workload simulator for our topology:
- *args represents the arbitrary number of tors involved in the workload's processing
- tm_matrix_size_h and _w are the rows and columns of the traffic matrix that we return to the main program
- time_to_finish is the amount of seconds that the workload has to run at full speed to complete
- gigabit_s is the amount of gigabit per second that the workload needs to finish in time_to_finish seconds
- all_paths will be used to record where each workload is flowing
- to_be_allocated: amount of traffic in Gb/s to be allocated into the network   
- initial_time is used to record when the workload has begun
- start_time is used to keep track of the gigabits served at every time instant 
- new_gigabit_s is used to record the new velocity after slowing down the workload 
"""


import networkx as nx 
import time as time 
import itertools

class Workload:
    
    def __init__(self,name:str, tm_matrix_size_h:int, tm_matrix_size_w:int, time_to_finish_s:float, gigabit_s:float, *args) -> None:
        
        self.name = name
        self.tors = []
        self.tm_matrix_size_h = tm_matrix_size_h  # defines how big the traffic matrix is 
        self.tm_matrix_size_w = tm_matrix_size_w
        self.tm_size = self.tm_matrix_size_h * self.tm_matrix_size_w
        self.tm = [[0 for i in range(self.tm_size)] for j in range(self.tm_size)]
        self.time_to_finish_s = time_to_finish_s
        self.new_gigabit_s = gigabit_s
        self.gigabit_s = gigabit_s
        self.all_paths = {}
        self.to_be_allocated = self.gigabit_s 
        self.start_time = None
        self.initial_time = None

        for arg in args:
            self.tors.append(arg)
    
    def fill_tm(self)-> list:
        
        # here I get all the ToR pairs between which traffic flows 
        pairs = []
        l= 0
        r = 1
        while r < len(self.tors):
            pairs.append(tuple((self.tors[l], self.tors[r])))
            l+=1
            r+=1

        #print(f"Tor pairs {pairs}")
        # here I need to add the traffic amount to the tm
        for i in range(self.tm_size):
            for j in range(self.tm_size):
                # ToRs are passed in order where the first one is where the workload starts and the last one where it ends
                if (str(i),str(j)) in pairs:
                    self.tm[i][j] = self.gigabit_s
        
        return self.tm

    def route(self, G:nx.DiGraph) -> None:
        """
        - max_cumulative bandwidth represents the maximum bandwidth recorded 
        - cur_cumulative_bandwidth represents the current cumulative bandwidth for a path
        - all_paths stores the chosen paths to serve a workload (may need more than one path)

        NB: a workload can be made up if many demands, we have to take care of all of them!
        NB :a demand is a non-zero entry in the traffic matrix 
        """

        max_cumulative_band = 0
        band_avail = nx.get_edge_attributes(G, "weight")


        for i in range(len(self.tm[0])):
            for j in range(len(self.tm[0])):                
                if self.tm[i][j] != 0:  
                    
                    # step 1 - get all possible paths for the demand FIX! TOO computationally intensive
                    paths = list(nx.all_simple_paths(G, source=i, target=j))

                    # step 2 - pick the one with the most available bandwidth 
                    chosen_path = paths[0]
                    max_cumulative_band = 0 # reset before processing new demand
                    
                    for path in paths:
                        cur_cumulative_band = 0
                        l = 0; r = 1
                        
                        while r < len(path):
                            cur_cumulative_band += band_avail[tuple([path[l],path[r]])]
                            l+=1
                            r+=1
                        
                        if cur_cumulative_band > max_cumulative_band:
                            max_cumulative_band = cur_cumulative_band
                            chosen_path = path
                            self.all_paths[(i,j)] = chosen_path 
        return 

    def start(self, G:nx.DiGraph)->None:
        """
        This function will take care of updating the graph band and tracking the amount of traffic
        being served at every timestep
        """
        self.start_time = time.time()
        self.initial_time = time.time()
        most_bottlnecked_edge_cap = 100  # the value set in the topology class 
        most_bottlnecked_edge = None
        slowed = False  # This flag tells us if the workload has been slowed or not 

        for _, chosen_path in self.all_paths.items():
            # step 3 - update graph bandwidth 
            l = 0; r = 1
            to_reduce = []
            
            while r < len(chosen_path):

                band_avail = G.edges[tuple([chosen_path[l],chosen_path[r]])]['weight']

                # I rememeber which edges need subtraction to reduce later
                if self.gigabit_s <= band_avail:
                    to_reduce.append(tuple([chosen_path[l],chosen_path[r]])) 

                # Find the edge creating the strongest bottleneck and use it for the computation

                elif self.gigabit_s > band_avail:
                    if band_avail <= most_bottlnecked_edge_cap: 
                        most_bottlnecked_edge_cap = band_avail
                        most_bottlnecked_edge = tuple([chosen_path[l],chosen_path[r]])
                     
                else:
                    pass

                l+=1
                r+=1
            
        # for the all the paths involved in the workload, decrease band and calculate new time if 
        # some traffic could not be allocated
        
        paths = [x for _,x in self.all_paths.items()] # I need to break this into edges and deal with all of them for band reduction
        path_combined = list(itertools.chain.from_iterable(paths)) # combine paths together for processing
        edges = set()
        
        l=0; r=1

        while r < len(path_combined):
            if path_combined[l] != path_combined[r]:
                edges.update([tuple([path_combined[l], path_combined[r]])]) # duplicates will be ignored
            r+=1
            l+=1

        # if the workload is slowed
        # process edge by edge and subtract bandwidth (here I should add back the original band to avoid subtracting twice!)
        if most_bottlnecked_edge != None:
            
            self.to_be_allocated -= most_bottlnecked_edge_cap # I still need to allocate the rest of the band 
            
            for edge in edges: 
                band_avail = G.edges[edge]['weight']
                
                if G.edges[edge]['weight'] > self.gigabit_s:
                    G.edges[edge]['weight']-= most_bottlnecked_edge_cap
                else:
                    G.edges[edge]['weight']=0

            # ------------------
            print(f"time to finish before {self.time_to_finish_s}")
            # here i calculate how much time is needed with the new speed
            total_gigs = self.time_to_finish_s*self.gigabit_s
            new_time_to_finish = total_gigs * (1/most_bottlnecked_edge_cap) # I use the most bottlenecked link as reference
    
            if new_time_to_finish == 0:
                raise Exception("Network too busy, workload on hold!")
            
            self.time_to_finish_s = new_time_to_finish
            self.new_gigabit_s = most_bottlnecked_edge_cap # data is sent at the lowest rate
            print(f"Time to finish after {self.time_to_finish_s}")
            print(f"New speed {self.new_gigabit_s}")
            slowed = True
            #-------------------

        # if the workload is not slowed, subtract original gigabit_s value
        else: 
            self.to_be_allocated -= self.gigabit_s
            for edge in to_reduce:
                G.edges[edge]['weight'] -= self.gigabit_s


        print(f"All_Paths {self.all_paths}")
        print("edge weights")
        print(nx.get_edge_attributes(G, "weight"))
        
        return slowed

    def terminate(self,G):
        # terminate workload
        paths = [x for _,x in self.all_paths.items()] # I need to break this into edges and deal with all of them for band reduction
        path_combined = list(itertools.chain.from_iterable(paths)) # combine paths together for processing
        edges = set()
        l=0; r=1

        while r < len(path_combined):
            if path_combined[l] != path_combined[r]:
                edges.update([tuple([path_combined[l], path_combined[r]])]) # duplicates will be ignored
            r+=1
            l+=1

        for edge in edges:
            G.edges[edge]['weight']+= self.new_gigabit_s 
                

        print(f"Workload {self.name} has terminated! Workload duration = {time.time()-self.initial_time} ") 
        status = nx.get_edge_attributes(G, "weight")
        print(f"Current network status: {status}")

    def update_ttf_slowed(self,G):
        """
        This function takes care of updating the time to finish of a workload which was slowed down 
        before 
        """
        # edge analysis 

        paths = [x for _,x in self.all_paths.items()] # I need to break this into edges and deal with all of them for band reduction
        path_combined = list(itertools.chain.from_iterable(paths)) # combine paths together for processing
        edges = set()
        
        l=0; r=1

        while r < len(path_combined):
            if path_combined[l] != path_combined[r]:
                edges.update([tuple([path_combined[l], path_combined[r]])]) # duplicates will be ignored
            r+=1
            l+=1
        
        most_bottlenecked_edge_band = 100  #default value for ToR links

        # check for the bottleneck link in the current path and use it to calculate new ttf

        for edge in edges:
            if G.edges[edge]['weight'] <= most_bottlenecked_edge_band:
                most_bottlenecked_edge_band = G.edges[edge]['weight']


        # check if congestion status has worsened wrt intitial setup due to other workloads
        if most_bottlenecked_edge_band == 0:
            return False 
        
        # perform new calculations

        new_time = time.time()
        total_gigs = self.to_be_allocated*(new_time-self.start_time) 
        self.time_to_finish_s = total_gigs * (1/most_bottlenecked_edge_band) # Gb * s/Gb
        self.start_time = new_time # I will have to wait x seconds from this time
        print("--------------------")
        print(f"Workload {self.name} has been sped up. New ttf {self.time_to_finish_s}")
        print("--------------------")

        # check if workload is running at full speed 
        if most_bottlenecked_edge_band == self.gigabit_s:
            return True

         














        







