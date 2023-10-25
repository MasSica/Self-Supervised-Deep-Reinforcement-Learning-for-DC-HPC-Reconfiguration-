"""Here the DQN agent structure is defined"""

import torch.nn as nn
import torch
import torch.nn.functional as F  #for the activation functions
import numpy as np



def fanin_init(size, fanin=None):
    fanin = fanin or size[0]
    v = 1. / np.sqrt(fanin)
    return torch.Tensor(size).uniform_(v)

class DQN_Net(nn.Module):

    def __init__(self, state_size, action_size,  init_w=1e-3):
        super(DQN_Net, self).__init__()

        # define the variables

        self.state = state_size
        self.action = action_size

        # define the network (currently very simple) for the state input

        self.DQN_Net_input_state = nn.Linear(self.state, 30) #30
        self.DQN_Net_layer_state = nn.Linear(30, 64) #64
        self.DQN_Net_layer_state2 = nn.Linear(64, self.action)

        self.init_weights(init_w)

    def init_weights(self, init_w):
        self.DQN_Net_input_state.weight.data = fanin_init(self.DQN_Net_input_state.weight.data.size())
        self.DQN_Net_layer_state.weight.data = fanin_init(self.DQN_Net_layer_state.weight.data.size())
        self.DQN_Net_layer_state2.weight.data = fanin_init(self.DQN_Net_layer_state2.weight.data.size())

    # here is where the computation happens

    def forward(self, state):

        state = F.relu(self.DQN_Net_input_state(state))
        state = F.normalize(state, p=2.0, dim=0, eps=1e-12, out=None)
        state = F.relu(self.DQN_Net_layer_state(state))
        state = F.normalize(state, p=2.0, dim=0, eps=1e-12, out=None)
        state = F.relu(self.DQN_Net_layer_state2(state))

        return state