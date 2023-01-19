"""This code runs offline without the need to interface with the testbed hardware as a simulation of the markov process. 
The code which allows to run this algorithm over the physiscal testbed cannot be shared """

from DQN import DQN
from Traffic_Monitor import TrafficMonitor
import numpy as np
import torch
from Replay_Buffer import ReplayBuffer
import time
from SSTrain import *
import torch.nn.functional as F  #for the activation functions



episodes = 2000
buffer_size = 250
K = 5  # tune
C = 100


failure_state_counter = 0

SelfS = SSTrain()

with open('logs.txt', "w"):  # delete file contents
    pass

f = open('logs.txt', 'a')



# here I initialize the buffer and DQN object

buffer = ReplayBuffer(buffer_size)
DQN = DQN(buffer)

net_loss_print =[]
ss_loss_print =[]
state2 = 0

number_of_reconfig = 0

# given by the number of non conforming edges increasing row by row (row1 is one non conforming edge)


state_space = [[1, 0, 0, 0],  # state 0
               [0, 0, 1, 0],  # state 2
               [0, 0, 0, 1],  # state 3
               [0, 0, 0, 0]]  # failed state

non_conforming_per_state ={0: 0,
                           1: 2,
                           2: 3,
                           3: 6}


print('------- Algorithm Starting-------')

rewards_for_plotting = []
rewards_for_episode = []
ss = 0

number_of_reconfig_ep = 0

for episode in range(episodes):

    action_index = 2  # Initialize 


    print(f'-------- episode: {episode}-----------')

    # initialize network to make it work at the beginning
    # as an initial step I need to guarantee connectivity between all nodes otherwise the DRL doesnt start
    tm_initial = [[0, 100000000, 100000000, 100000000, 0, 0],
                  [100000000, 0, 100000000, 100000000, 0, 0],
                  [100000000, 100000000, 0, 1000000000, 0, 0],
                  [100000000, 100000000, 100000000, 0, 0, 0],
                  [0, 0, 0, 0, 0, 10000],
                  [0, 0, 0, 0, 10000, 0]]

    ocs_initial = np.array([[0, 0, 0, 1, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0, 0, 0],
                            [1, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 1],
                            [0, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 1, 0, 0]])

    print('----------Initializing connectivity between peers-----')

    # set step
    current_step = 0

    # initialize flags

    collapse_flag = False
    ocs = ocs_initial


    edges_non_conforming = 3  # starting point

    reconfigure_flag, _, metric = True, False, 0.125

    while not collapse_flag:

        print(f'-------- step: {current_step}-----------')

        # monitor the current network situation -- # of congested links

        state = state_space[action_index]
        state_tensor = torch.tensor(np.array(state).flatten(), dtype=torch.float, requires_grad=True)

        if reconfigure_flag:

            action_index, new_ocs_matrix = DQN.take_action(state_tensor)

            w_collapse = False  # tells if the chosen action will lead to a collapse 

            if not w_collapse:
                print('----------RECONFIGURING-----------')
                number_of_reconfig += 1
                number_of_reconfig_ep += 1

                # 2 gather new data
                print('-------WAITING FOR GATHERING NEW DATA--------')

                edges_non_conforming = non_conforming_per_state[int(action_index)]
                metric2 = edges_non_conforming / 24

                # 3 Collect new state

                state2 = state_space[action_index]

                # 4 Collect reward

                print(f'----------COLLECTING REWARD {metric}-{metric2}----------')
                if int(action_index) == 3:
                    w_collapse = True
                    re = -0.125
                    failure_state_counter += 1


                else:
                    re = metric - metric2

                print('--------- REWARD  ' + str(re) + '-------------')

                state_tensor2 = torch.tensor(np.array(state2).flatten(), dtype=torch.float, requires_grad=True)

                ##################################################
                # self-supervised part
                if number_of_reconfig_ep > 1:

                    print(f'passing{torch.tensor(state, dtype=torch.float)} ')
                    precedence = SelfS.pred(torch.tensor(state, dtype=torch.float), buffer)
                    precedence = precedence.tolist()
                    print(f'--------------------PURE PRECEDENCE {precedence}----------------------------------')
                    ss = precedence[0]
                    print(f'------PRECEDENCE {ss}--------')
                    re = 0.125 + (0.125 - -0.125) * (re - ss)  # normalize to fit our range
                    print(f'--------REWARD SS {re}----ss {ss}-----')
                #########################################

                if action_index == 0:
                    rewards_for_plotting.append(0.125)  #  for plotting
                else:
                    rewards_for_plotting.append(re)

                # 5 update replay buffer (get only the half matrix of the needed action)

                # add trajectory to buffer for self-supervised
                if action_index == 0:  # the best action
                    buffer.add_trajectory(state_tensor, torch.tensor(action_index), torch.tensor(0.125), state_tensor2) # do not include ss penalty
                else:
                    buffer.add_trajectory(state_tensor, torch.tensor(action_index), torch.tensor(re), state_tensor2)
                    print(f'--------ADDED TO BUFFER SS {[state_tensor, torch.tensor(action_index, dtype=torch.float, requires_grad=True), torch.tensor(re, dtype=torch.float, requires_grad=True), state_tensor2]}--------')





            # update actor critic and targets if K steps have passed CAREFUL HERE!
            if number_of_reconfig == K:
                print('-------------UPDATING-------------------------------')
                net_loss = DQN.update_parameters(episode)
                net_loss_print.append(float(net_loss))

                # update ss network
                ss_loss = SelfS.train(buffer)
                ss_loss_print.append(ss_loss)

                print('-------------UPDATING-------------------------------')
                number_of_reconfig = 0

            if episode % C == 0 and episode != 0:
                print('--------------------resetting target --------------------------')
                DQN.reset_weights()

        current_step += 1
        if (action_index == 0) or (action_index == 3) or current_step == 10:  # 0 1terminate the episode once you reach the best configuration or the failure state (0 and 2)
            print('--------MAX STEPS REACHED ENDING EPISODE--------')
            break
        print(f'------------------------------------{rewards_for_plotting}--------------------------------------------------------------')

    print(f'-------- ENDING EPISODE : {episode}-----------')
    rewards_for_episode.append(rewards_for_plotting)
    rewards_for_plotting = []
    print('---------------------------------------------')
    print(f'Rewards per episode {rewards_for_episode}')
    print(f'ss loss evolution {ss_loss_print}\n')
    print(f'net loss evolution {net_loss_print}\n')
    print('---------------------------------------------')
    f.write('----------------------')
    f.write(f'EPISODE: {episode}\n')
    f.write(f'Rewards per episode {rewards_for_episode}\n')
    f.write(f'agent loss evolution {net_loss_print}\n')
    f.write(f'ss loss evolution {ss_loss_print}\n')
    f.write('----------------------')

DQN.save_parameters()  # save the training parameters
SelfS.save_model()
print('------PARAMETERS SAVED ---------')
print(f'failures {failure_state_counter}')























