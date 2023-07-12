"""This file brings all the components of the program together and 
allows the user to run the simulation"""

from Workload import Workload
from topology import TopologyGenerator


if __name__ == "__main__":

    while True:
        print("""
        --------------------------------
        Welcome to the RA-DRL Simulator
        --------------------------------
        """)

        num_tors_v = 2
        num_tors_h = num_tors_v
        num_tors = num_tors_h*num_tors_v

        # Initilize traffic matrix 
        tm = [[0 for i in range(num_tors_v)] for j in range(num_tors_h)] 

        # get flat multi-POD topology
        topology_gen = TopologyGenerator(num_tors_v, num_tors_h)
        G, connectivity_h, connetivity_v = topology_gen.get_graph()
        topology_gen.write_to_file()

        # Ask user to deploy a workload 
        print("Please provide workload information on each line: Gigabit/s, Time to finish (seconds), ToRs involved ")
        inputs = []
        while True:
            inp = input()
            if inp == "":
                break
            inputs.append(float(inp))
        
        ttf = inputs[1]
        gbs = inputs[0]
        tors_involved = inputs[2:]

        workload = Workload(num_tors_h, num_tors_v, ttf, gbs, *tors_involved)
        tm = workload.fill_tm()

        # Now that we have our traffic matrix, we can route the workload the user requested