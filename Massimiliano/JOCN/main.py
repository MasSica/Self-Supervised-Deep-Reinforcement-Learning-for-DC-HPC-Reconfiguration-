# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : massica

"""This file brings all the components of the program together and 
allows the user to run the simulation"""

from Workload import Workload
from topology import TopologyGenerator
from DQN_Trainer import DQN
import networkx as nx 
import time 
import torch
import pandas as pd

"""
notes:
- need to define the concept of network crash for radrl 
- create a workload generator to automatize the procedure 
"""

if __name__ == "__main__":

    ## DRL specific variables 
    # reconfiguration threshold defined in terms of workloads oh hold and slowed
    RECONF_THR = {
        'on hold': 1,
        'slowed': 1
    }

    NUM_WORLOADS = 5 # this is the number of workloads that will be deployed in the network 

    # My state space is dynamic and will depend on the number of workloads on hold and slowed
    STATE_SPACE = [[0 for _ in range(NUM_WORLOADS)] for _ in range(NUM_WORLOADS)] 
    
    # Now I need to ohe the state space 
    for i in range(len(STATE_SPACE[0])):
        for j in range(len(STATE_SPACE[1])):
            if i == j:
                STATE_SPACE[i][j] = 1

    # store all the currently running workloads 
    workloads_deployed = []
    workloads_on_hold = []
    workloads_slowed = []

    # create DQN trainer
    DQN_model = DQN(10,STATE_SPACE )

    num_tors_v = 2 #2 
    num_tors_h = num_tors_v
    num_tors = num_tors_h*num_tors_v

    # Initilize traffic matrix 
    tm = [[0 for i in range(num_tors_v)] for j in range(num_tors_h)] 

    # get flat multi-POD topology
    topology_gen = TopologyGenerator(num_tors_v, num_tors_h)
    G, connectivity_h, connetivity_v = topology_gen.get_graph()
    topology_gen.write_to_file()

    while True:
        print("""
        --------------------------------
        Welcome to the RA-DRL Simulator
        --------------------------------
        """)

        print(f""" 
        Number of workloads on hold: {len(workloads_on_hold)}
        Workloads on hold: {[workload.name for workload in workloads_on_hold]}
        """)
        print(f""" 
        Number of workloads slowed: {len(workloads_slowed)}
        Workloads slowed: {[workload.name for workload in workloads_slowed]}
        """)
        
        # Ask user what they want to do 
        print("1- Check status of workload")
        print("2- Deploy new workload")
        choice = input()

        if choice == "1":

            cur_state = STATE_SPACE[(len(workloads_slowed)+len(workloads_on_hold))]

            while True:
                # check if reconfiguration is needed 
                if len(workloads_on_hold) >= RECONF_THR['on hold'] or len(workloads_slowed) >= RECONF_THR['slowed']:
                    # reconfigure
                    print("RECONFIGURING!")
                    state_tensor = torch.tensor(cur_state,dtype=torch.float, requires_grad=True)
                    _, action = DQN_model.take_action(state_tensor)
                    # reroute everything
                    all_workloads = []
                    all_workloads.extend(workloads_deployed)
                    all_workloads.extend(workloads_on_hold)
                    workloads_on_hold.clear()
                    workloads_deployed.clear()
                    workloads_slowed.clear()

                    G = topology_gen.get_reconfig_graph(action) # reset G

                    for workload in all_workloads:
                        print(workload.name)
                        workload.reset_paths()
                        workload.route(G)
                        try:
                            status = workload.start(G)  # start the workload and get if slowed or not

                            if status == "slowed":
                                workloads_slowed.append(workload)
                                workloads_deployed.append(workload)
                            elif status == "on hold":
                                workloads_on_hold.append(workload)
                            else:
                                workloads_deployed.append(workload)
            
                        except Exception:
                            workload.terminate(G)
                            workloads_on_hold.append(workload)
                    
                    # here I will need to compute the reward

                else:
                    #For every old workload we need to check if they have expired 
                    cur_time = time.time()
                    for workload in workloads_deployed:
                        if workload.time_to_finish == 0:
                            workload.terminate(G)  # if the workload has terminated, end it
                            workloads_deployed.remove(workload)
                            workloads_slowed.remove(workload) if workload in workloads_slowed else workloads_slowed
                            print(nx.get_edge_attributes(G, "weight"))

                            # check if other workloads can be sped up
                            for slow_workload in workloads_slowed:
                                full_speed = slow_workload.update_ttf_slowed(G)
                                # add check if workload is going at full speed
                                if full_speed:
                                    workloads_slowed.remove(slow_workload)
                            
                            # deal with workloads on hold
                            for workload_on_hold in workloads_on_hold:
                                try:
                                    slowed = workload_on_hold.start(G)  # start the workload and get if slowed or not
                                    if slowed:
                                        workloads_slowed.append(workload_on_hold)
                                except Exception:
                                    workload_on_hold.terminate(G)
                        else:
                            print("--------------")
                            print(f"Workload {workload.name}")
                            print(f"Time remaining {'%.3f'%(workload.time_to_finish -(cur_time-workload.start_time))}")
                            print("--------------")
                            time.sleep(1)

        if choice == "2":
            # Ask user to deploy a workload 
            workloads = pd.read_csv(r"/Users/massimilianosica/Desktop/Research Work/Self-Supervised-Deep-Reinforcement-Learning-for-DC-HPC-Reconfiguration-/Massimiliano/JOCN/workloads.csv")
            print(workloads.head(5))
            for i in range(len(workloads)):

                tg = float(workloads.loc[i, "total_gigs"])
                gbs = float(workloads.loc[i, "gigabit"])
                name = workloads.loc[i, "name"]
                tors_involved = workloads.loc[i, "tors"].strip('][')
                tors_involved = tors_involved.split(',')
                workload = Workload(name, num_tors_h, num_tors_v, tg, gbs, *tors_involved)
                tm = workload.fill_tm()
                print(f"tm {tm}")
                # Now that we have our traffic matrix, we can route the workload the user requested
                workload.route(G)
                # If the network is too busy catch the exception and restore band 
                try:
                    status = workload.start(G)  # start the workload and get if slowed or not
                    if status == "slowed":
                        workloads_slowed.append(workload)
                        workloads_deployed.append(workload)
                    elif status == "on hold":
                        workloads_on_hold.append(workload)
                    else:
                        workloads_deployed.append(workload)


                except Exception as e:
                    print(str(e))
                    workload.terminate(G)
                    workloads_on_hold.append(workload)
            
        

            
            
            

        
