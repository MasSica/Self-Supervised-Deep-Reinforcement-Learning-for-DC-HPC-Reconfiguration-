"""This file contains all the necessary methods for performing prediction and training for the self-supervised reversibility-aware agent"""

import torch
from SelfSupervised import *
from Replay_Buffer import *
from torch.optim import *


class SSTrain:
    def __init__(self):

        self.net = SS_Net()  # this is the feature extractor for the observation
        self.net_optimizer = Adam(self.net.parameters(), lr=0.1)
        self.criterion = torch.nn.MSELoss()  # this is the loss function used for precedence estimator 

    def flatten(self, x):
        flat_list = []
        # Iterate through the outer list
        for element in x:
            if isinstance(element, list):
                # If the element is of type list, iterate through the sublist
                for item in element:
                    flat_list.append(item)
            else:
                flat_list.append(element)
        return flat_list

    def tensor_to_list(self, tensor):
        new_list =[]

        for elem in tensor:
            new_list.append(elem.tolist())

        new_list = self.flatten(new_list)
        return new_list

    # returns precendence score 
    def pred(self, s, buffer):

        s_sampl, _, _, _ = buffer.sample_buffer_ss(1)  # sample one observation
        s_sampl = torch.tensor(s_sampl[0], dtype=torch.float)
        prev = self.net(s, s_sampl)

        return prev


    # trains the network 
    def train(self, buffer):

        # I have to combine two observations

        torch.autograd.set_detect_anomaly(True)


        s, _, _, indexes = buffer.sample_buffer_ss(4)  # batch is 4

        s = torch.stack(s)  # these are all long the same


        obs = []  # this is needed to process the tensor

        for i in range(len(s)):
            obs.append([s[i]])

        # now I have to pick one pair

        obs1 = torch.tensor(self.tensor_to_list(obs[0]), requires_grad=True)
        obs2 = torch.tensor(self.tensor_to_list(obs[1]), requires_grad=True)
        obs3 = torch.tensor(self.tensor_to_list(obs[2]), requires_grad=True)
        obs4 = torch.tensor(self.tensor_to_list(obs[3]), requires_grad=True)

        # here the self-labeling procedure begins

        if random.random() >= 0.5:
            
            # we swap order
            prev1 = self.net(obs2, obs1)
            prev2 = self.net(obs3, obs4)
            prev3 = self.net(obs1, obs4)
            prev4 = self.net(obs2, obs4)

            if indexes[0] > indexes[1]:
                label1 = 1
            else:
                label1 = 0

            if indexes[3] > indexes[2]:
                label2 = 1
            else:
                label2 = 0

            if indexes[3] > indexes[0]:
                label3 = 1
            else:
                label3 = 0

            if indexes[3] > indexes[1]:
                label4 = 1
            else:
                label4 = 0


        else:

            prev1 = self.net(obs1, obs2)
            prev2 = self.net(obs4, obs3)
            prev3 = self.net(obs4, obs1)
            prev4 = self.net(obs4, obs2)

            if indexes[0] > indexes[1]:
                label1 = 0
            else:
                label1 = 1

            if indexes[3] > indexes[2]:
                label2 = 0
            else:
                label2 = 1

            if indexes[3] > indexes[0]:
                label3 = 0
            else:
                label3 = 1

            if indexes[3] > indexes[1]:
                label4 = 0
            else:
                label4 = 1

        # now we compute the loss
        prevs = torch.cat((prev1, prev2, prev3, prev4))
        labels = torch.tensor((label1, label2, label3, label4), dtype=torch.float, requires_grad=True)
        loss = self.criterion(prevs, labels)
        self.net_optimizer.zero_grad()
        loss.backward()
        self.net_optimizer.step()
        print('------SS UPDATED-------')
        return float(loss)

    def save_model(self):

        path = 'ssonly.pt'
        torch.save(self.net.state_dict(), path)















