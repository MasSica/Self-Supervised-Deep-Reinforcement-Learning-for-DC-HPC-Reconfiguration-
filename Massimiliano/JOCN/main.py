"""This file brings all the components of the program together and 
allows the user to run the simulation"""

from Workload import Workload
from topology import TopologyGenerator
import time 


if __name__ == "__main__":

    # store all the currently running workloads 
    workloads = []

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

        # Ask user what they want to do 
        print("1- Check status of workload")
        print("2- Deploy new workload")
        choice = input()

        if choice == "1":
            while len(workloads) != 0:
                #For every old workload we need to check if they have expired 
                for workload in workloads:
                    cur_time = time.time()
                    if cur_time - workload.start_time >= workload.time_to_finish_s:
                        workload.terminate(G)
                        workloads.remove(workload)
                    else:
                        print("--------------")
                        print(f"Workload {workload.name} started at {workload.start_time}")
                        print(f"Time remaining {workload.time_to_finish_s-(cur_time-workload.start_time)}")
                        print("--------------")
                        time.sleep(1)

        if choice == "2":
            # Ask user to deploy a workload 
            print("Please provide workload information on each line: Name, Gigabit/s, Time to finish (seconds), ToRs involved ")
            inputs = []
            while True:
                inp = input()
                if inp == "":
                    break
                inputs.append(inp)
            
            ttf = float(inputs[2])
            gbs = float(inputs[1])
            name = inputs[0]
            tors_involved = inputs[3:]

            workload = Workload(name, num_tors_h, num_tors_v, ttf, gbs, *tors_involved)
            tm = workload.fill_tm()
            print(f"tm {tm}")
            
            # Now that we have our traffic matrix, we can route the workload the user requested
            workload.route(G)
            workload.start(G)
            workloads.append(workload)

        
