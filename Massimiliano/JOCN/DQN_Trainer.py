"""Here the DQN agent is implemented"""

import torch
import torch.nn as nn
from DQN_Agent import DQN_Net
from torch.optim import Adam
import random


class DQN:

    def __init__(self, buffer, state):

        # the sizes are fixed
        self.buffer = buffer
        self.state_size = len(state)
        self.action_size = 1#6 

        # we define hyperparameters

        self.lr_c = 0.001

        self.batch = 4
        self.gamma = 0.99 #0.99
        self.tau = 1e-3
        self.epsilon = 0.8  #0.8 # ACT VERY RANDOMLY AT THE BEGINNING 0.8 dec 0.01 min 0.1
        self.eps_dec = 0.01
        self.eps_min = 0.001

        # We define DQN_Net, DQN_Net target and optimizer
        self.net = DQN_Net(self.state_size, self.action_size)
        self.target_net = DQN_Net(self.state_size, self.action_size)
        self.net_optimizer = Adam(self.net.parameters(), lr=self.lr_c)

        # we need to make sure that the neural net and its corresponding target have the same weights

        self.target_net.load_state_dict(self.net.state_dict())

        # I need to define the action space( ocs cnnectivity mtrix arrayof arrays)


        # these are the availble reconfigurations we can choose from 
        # template [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
        # check notability for pics 

        self.action_space = [
            #[[0,1,1,0],[1,0,0,1],[1,0,0,1],[0,1,1,0]],
            #[[0,1,0,1],[1,0,1,0],[0,1,0,1],[1,1,0,0]],
            #[[0,1,0,0],[0,0,0,1],[0,0,0,0],[0,0,0,0]],
            #[[0,1,0,1],[1,0,1,0],[0,1,0,0],[1,0,0,0]],
            [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
            #[[0,1,0,1],[1,0,0,0],[0,0,0,1],[1,0,1,0]]
        ]



    def take_action(self, state): # take action and generate new state
        # convert state to tensor
        state = torch.tensor(state, dtype=torch.float, requires_grad=True)

        if random.random() > self.epsilon:
            scores = self.net(state)
            print(f'----scores {scores}-----')
            action_index = torch.argmax(scores)

        else:
            print('----------EXPLORING-----------')
            action_index = random.randint(0, len(self.action_space)-1)  # randomly choose success or failure

        print(f'CHOSEN ACTION {self.action_space[action_index]} CHOSEN INDEX {action_index}')
        return action_index, self.action_space[action_index]

    # Target Update (https://github.com/ghliu/pytorch-ddpg/blob/master/util.py)
    def soft_update(self):

        for target_param, param in zip(self.target_net.parameters(), self.net.parameters()):
            target_param.data.copy_(target_param.data * (1.0 - self.tau) + param.data * self.tau)


    def update_parameters(self, episode):

        # actor loss vector
        # sample minibatch of transitions
        s, a, r, s2 = self.buffer.sample_buffer(self.batch)

        criterion = nn.SmoothL1Loss()

        for i in range(len(s)):
            self.net_optimizer.zero_grad()

            y = self.net(s[i])[a[i]]
            y_t = r[i] + self.gamma * torch.max(self.target_net(s2[i]))

            net_loss = criterion(y, y_t)
            net_loss.backward()

            for param in self.net.parameters():
                param.grad.data.clamp_(-1, 1)
                #print(param.grad.data)

            self.net_optimizer.step()

        print('-----------UPDATED NET------------')

        self.epsilon = self.epsilon - self.eps_dec if self.epsilon > self.eps_min else self.eps_min
        print('------------------------REDUCING EPSILON----------------------')

        print(f'RETURNING {net_loss} ')
        print(f'EPSILON {self.epsilon}')

        return net_loss

    def save_parameters(self):
        path = 'model.pt'
        torch.save(self.net.state_dict(), path)

    def reset_weights(self):
        self.target_net.load_state_dict(self.net.state_dict())



































