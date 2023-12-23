# -*- coding: utf-8 -*-
# @Time    : 22.09.23
# @Author  : massica

"""This file brings all the components of the program together and 
allows the user to run the simulation"""

from Workload import Workload
from topology import TopologyGenerator
from DQN_Trainer import DQN
from Replay_Buffer import ReplayBuffer
import networkx as nx 
import time 
import torch
import pandas as pd
import matplotlib.pyplot as plt


# helper function to sum matrices of same shape 
def sum_matrices(tm1, tm2):
    tm_sum=[[0 for i in range(len(tm1[0]))] for j in range(len(tm1))]
    for i in range(len(tm1)):
        for j in range(len(tm1[0])):
            tm_sum[i][j]= tm1[i][j]+tm2[i][j]
    return tm_sum


if __name__ == "__main__":

    ## DRL specific variables 
    # reconfiguration threshold defined in terms of workloads oh hold and slowed
    RECONF_THR = {
        'on hold': 1,
        'slowed': 1
    }

    NUM_WORLOADS = 3 # this is the number of workloads that will be deployed in the network 

    BUF_SIZE = 250 # DQN buffer size

    K = 5 # number of reconfiguratios before training session 
    C = 100 # control traget reset 

    EPISODES = 2000 # total number of episodes to run 
    episode_number = 0 # keep track of the episode we are at 

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

    # store rewards for plotting 
    rewards_plot = []

    # values used to compute the reward 
    after = 0
    before = 0

    # initialize number of reconfigurations to know when to train
    number_of_reconfig = 0

    # buffer 
    buffer = ReplayBuffer(BUF_SIZE)

    # topology configuration 
    num_tors_v = 2
    num_tors_h = num_tors_v
    num_tors = num_tors_h*num_tors_v

    # Initilize traffic matrix 
    tm = [[0 for i in range(num_tors_v*num_tors_h)] for j in range(num_tors_v*num_tors_h)] 
    TM = [[0 for i in range(num_tors_v*num_tors_h)] for j in range(num_tors_v*num_tors_h)] # the total traffic matrix for all the workloads 

    # keep track of workloads
    all_workloads =[]
    # create DQN trainer
    DQN_model = DQN(buffer, STATE_SPACE, num_tors_h, num_tors_v, TM)

    while episode_number <= EPISODES:
        episode_number+=1
        print(f"---------STARTING EP NUM {episode_number}----------")

        # reset iterations 
        # number of program iterations to keep track of the steps and define episode end
        program_iterations = 0

        # get flat multi-POD topology
        topology_gen = TopologyGenerator(num_tors_v, num_tors_h)
        initial_topo_failed = [[0]*(num_tors_h*num_tors_v)]*(num_tors_h*num_tors_v) 
        G = topology_gen.get_reconfig_graph(initial_topo_failed)
        #topology_gen.write_to_file()

        # ------------------------------------------
        # clear memeories and start workloads 
        workloads_on_hold.clear()
        workloads_deployed.clear()
        workloads_slowed.clear()

        workloads = pd.read_csv(r"/Users/massimilianosica/Desktop/Research Work/Self-Supervised-Deep-Reinforcement-Learning-for-DC-HPC-Reconfiguration-/Massimiliano/JOCN/workloads.csv")
        #print(workloads.head(5))
        for i in range(len(workloads)):

            tg = float(workloads.loc[i, "total_gigs"])
            gbs = float(workloads.loc[i, "gigabit"])
            name = workloads.loc[i, "name"]
            tors_involved = workloads.loc[i, "tors"].strip('][')
            tors_involved = tors_involved.split(',')
            workload = Workload(name, num_tors_h, num_tors_v, tg, gbs, *tors_involved)
            tm = workload.fill_tm()
            TM = sum_matrices(tm,TM)

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

        # DQN Model was here

        #-------------------------------------------
        # START EPISODE ITERATION
        #-------------------------------------------

        # run for a maximum of 10 iterations before moving to next episode  
        while program_iterations <= 10:
            print(f"---------STARTING ITER NUM {program_iterations}----------")
            program_iterations +=1

            # current MC state 
            print(STATE_SPACE)
            print(len(workloads_slowed)+len(workloads_on_hold))
            cur_state = STATE_SPACE[(len(workloads_slowed)+len(workloads_on_hold))-1]

            # used to compute reward later
            before = len(workloads_slowed)+len(workloads_on_hold)

            # check if reconfiguration is needed 
            if len(workloads_on_hold) >= RECONF_THR['on hold'] or len(workloads_slowed) >= RECONF_THR['slowed']:
                # reconfigure
                print("RECONFIGURING!")
                # initial state tensor
                state_tensor = torch.tensor(cur_state,dtype=torch.float) #, requires_grad=True
                # get action index
               
                action_index, action = DQN_model.take_action(state_tensor)
                
                all_workloads.clear()
                all_workloads.extend(workloads_deployed)
                all_workloads.extend(workloads_on_hold)
                workloads_on_hold.clear()
                workloads_deployed.clear()
                workloads_slowed.clear()

                # reset G
                G = topology_gen.get_reconfig_graph(action)

                # reroute everything
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
        
                    except Exception as e:
                        print(str(e))
                        workload.terminate(G)
                        workloads_on_hold.append(workload)
                
                # here I will need to compute the reward and add to buffer
                state2 = STATE_SPACE[(len(workloads_slowed)+len(workloads_on_hold))-1]
                state2_tensor = torch.tensor(state2, dtype=torch.float) #, requires_grad=True
                after = len(workloads_slowed)+len(workloads_on_hold)
                reward = before - after
                buffer.add_trajectory(state_tensor, torch.tensor(action_index), torch.tensor(reward), state2_tensor) 
                number_of_reconfig += 1
                rewards_plot.append(reward)
                print(f"-------REWARD {reward}-----------")
                
                # setup for next iteration
                cur_state = state2
                before = state2
                after = 0
                reward = 0

                # I need to check if it is time to update the weights 
                if number_of_reconfig == K:
                    print('-------------UPDATING-------------------------------')
                    net_loss = DQN_model.update_parameters()
                    number_of_reconfig = 0
                    
                if episode_number % C == 0 and episode_number != 0:
                    print('--------------------TARGET RESET--------------------------')
                    DQN_model.reset_weights()
                
                # if best state has been reached stop 
                if len(workloads_slowed)+len(workloads_on_hold) == 0:
                    print("optimal state reached, ending episode")
                    break 

            else:
                #For every old workload we need to check if they have expired 
                cur_time = time.time()
                for workload in workloads_deployed:
                    if workload.time_to_finish -(cur_time-workload.start_time) <= 0:
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
                                    workload_on_hold.remove(workload_on_hold)
                            except Exception:
                                workload_on_hold.terminate(G)
                    else:
                        print("--------------")
                        print(f"Workload {workload.name}")
                        print(f"Time remaining {'%.3f'%(workload.time_to_finish -(cur_time-workload.start_time))}")
                        print("--------------")
                        time.sleep(1)

    x = list(range(0, EPISODES))
    y = rewards_plot
    plt.plot(list(range(len(y))),y)
    plt.show() 
            
            
            
        

            
            
            

        
