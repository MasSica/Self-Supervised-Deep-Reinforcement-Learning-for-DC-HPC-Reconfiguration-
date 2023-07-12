"""
This class will implement a workload simulator for our topology:
- *args represents the arbitrary number of tors involved in training
- tm_matrix_size_h and _w are the rows and columns of the traffic matrix that we return to the main program
- time_to_finish is the amount of seconds that the workload has to run at full speed to complete
- gigabit_s is the amount of gigabit per second that the workload needs to finish in time_to_finish seconds
- path_taken will be used to record where each workload is flowing 
"""

class Workload:
    
    def __init__(self,tm_matrix_size_h:int, tm_matrix_size_w:int, time_to_finish_s:float, gigabit_s:float, *args) -> None:
        
        self.tors = []
        self.tm_matrix_size_h = tm_matrix_size_h  # defines how big the traffic matrix is 
        self.tm_matrix_size_w = tm_matrix_size_w
        self.tm = [[0 for i in range(tm_matrix_size_w)] for j in range(tm_matrix_size_h)]
        self.time_to_finish_s = time_to_finish_s
        self.gigabit_s = gigabit_s
        self.path_taken = []

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

        # here I need to add the traffic amount to the tm
        for i in range(self.tm_matrix_size_w):
            for j in range(self.tm_matrix_size_h):
                # ToRs are passed in order where the first one is where the workload starts and the last one where it ends
                if (i,j) in pairs:
                    self.tm[i][j] = self.gigabit_s
        
        return self.tm







