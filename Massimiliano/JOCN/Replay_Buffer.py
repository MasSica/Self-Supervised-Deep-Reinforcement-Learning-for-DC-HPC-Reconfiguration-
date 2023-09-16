"""This class implements the replay buffer """

import random

class ReplayBuffer:

    def __init__(self, buffer_size):

        self.buffer_size = buffer_size
        self.buffer_s = []
        self.buffer_a = []
        self.buffer_r = []
        self.buffer_s2 = []
        self.used_indexes =[]

    # here i create a function for adding a trajectory s a r s' to the replay buffer
    def add_trajectory(self, s, a, r, s2):

        # first I need to check if the buffer is full (checking one is enough since they are all the same size)

        if len(self.buffer_s) >= self.buffer_size:
            self.buffer_s.remove(self.buffer_s[0])     # remove the oldest element
            self.buffer_a.remove(self.buffer_a[0])
            self.buffer_r.remove(self.buffer_r[0])
            self.buffer_s2.remove(self.buffer_s2[0])

        else:

            self.buffer_s.append(s)
            self.buffer_a.append(a)
            self.buffer_r.append(r)
            self.buffer_s2.append(s2)


        return

    def sample_buffer(self, batch):

        # now we get batch samples at random from the buffer; generate batch random numbers

        indexes = [random.randint(0, len(self.buffer_s)-1) for i in range(0, batch)]

        s_samples = [self.buffer_s[x] for x in range(len(self.buffer_s)) if x in indexes]  # take only the buffer values at the indexes we want
        a_samples = [self.buffer_a[x] for x in range(len(self.buffer_a)) if x in indexes]
        r_samples = [self.buffer_r[x] for x in range(len(self.buffer_r)) if x in indexes]
        s2_samples = [self.buffer_s2[x] for x in range(len(self.buffer_s2)) if x in indexes]

        return s_samples, a_samples, r_samples, s2_samples

    def sample_buffer_ss(self, batch):

        # now we get batch samples at random from the buffer; generate batch random numbers


        indexes = []


        for i in range(0, batch):

            random_num = random.randint(0, len(self.buffer_s)-1)

            while random_num in indexes and random_num in self.used_indexes: # make sure you don't pick the same trajectory twice
                random_num = random.randint(0, len(self.buffer_s)-1)
                print(random_num)

            indexes.append(random_num)
            self.used_indexes.append(random_num)  # remember which indexes you used so that you don't pick teh same trajectory twice


        print(indexes)
        s_samples = [self.buffer_s[x] for x in range(len(self.buffer_s)) if x in indexes]  # take only the buffer values at the indexes we want
        a_samples = [self.buffer_a[x] for x in range(len(self.buffer_a)) if x in indexes]
        r_samples = [self.buffer_r[x] for x in range(len(self.buffer_r)) if x in indexes]
        #s2_samples = [self.buffer_s2[x] for x in range(len(self.buffer_s2)) if x in indexes]


        return s_samples, a_samples, r_samples, indexes

    def get_lenght(self):
        return len(self.buffer_s)











