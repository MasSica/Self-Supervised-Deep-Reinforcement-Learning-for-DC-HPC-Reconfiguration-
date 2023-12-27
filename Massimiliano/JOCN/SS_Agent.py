"""This file contains the structure and forward method for the self-supervise reversibility-aware module"""

import torch.nn as nn
import torch
import torch.nn.functional as F  #for the activation functions
import numpy as np


def fanin_init(size, fanin=None):
    fanin = fanin or size[0]
    v = 1. / np.sqrt(fanin)
    return torch.Tensor(size).uniform_(v)


class SS_Net(nn.Module):

    def __init__(self, states, init_w=3e-3):
        super(SS_Net, self).__init__()

        # define the network for the state input

        self.SS_Net_input_state = nn.Linear(len(states), 5)
        self.SS_Net_layer_state = nn.Linear(10, 1)
        torch.manual_seed(42727638232)
        self.init_weights(init_w)

    def init_weights(self, init_w):
        self.SS_Net_input_state.weight.data = fanin_init(self.SS_Net_input_state.weight.data.size())
        self.SS_Net_layer_state.weight.data = fanin_init(self.SS_Net_layer_state.weight.data.size())

    def forward(self, old_obs, obs):

        obs = F.relu(self.SS_Net_input_state(obs))
        old_obs = F.relu(self.SS_Net_input_state(old_obs))

        concat = torch.cat((old_obs, obs), dim=-1)

        concat = F.normalize(concat, p=2.0, dim=0, eps=1e-12, out=None)

        p_rev = F.sigmoid(self.SS_Net_layer_state(concat))

        print(f'p_rev = {p_rev}')

        return p_rev






