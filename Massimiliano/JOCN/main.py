# -*- coding: utf-8 -*-
# @Time    : 22.09.21
# @Author  : massica

"""This file brings all the components of the program together and 
allows the user to run the simulation"""

from Workload import Workload
from topology import TopologyGenerator
import time 


if __name__ == "__main__":

    # store all the currently running workloads 
    workloads_deployed = []
    workloads_on_hold = []
    workloads_slowed = []

    num_tors_v = 2
    num_tors_h = num_tors_v
    num_tors = num_tors_h*num_tors_v

    # Initilize traffic matrix 
    tm = [[0 for i in range(num_tors_v)] for j in range(num_tors_h)] 

    # get flat multi-POD topology
    topology_gen = TopologyGenerator(num_tors_v, num_tors_h)
    G, connectivity_h, connetivity_v = topology_gen.get_graph()
    topology_gen.write_to_file()

    while True:
        print("""
        --------------------------------
        Welcome to the RA-DRL Simulator
        --------------------------------
        """)

        print(f""" 
        Number of workloads on hold: {len(workloads_on_hold)}
        Workloads on hold: {[workload.name for workload in workloads_on_hold]}
        """)
        print(f""" 
        Number of workloads slowed: {len(workloads_slowed)}
        Workloads on hold: {[workload.name for workload in workloads_slowed]}
        """)
        

        # Ask user what they want to do 
        print("1- Check status of workload")
        print("2- Deploy new workload")
        choice = input()

        if choice == "1":
            #For every old workload we need to check if they have expired 
            cur_time = time.time()
            for workload in workloads_deployed:
                if cur_time - workload.start_time >= workload.time_to_finish_s:
                    workload.terminate(G)  # if the workload has terminated, end it
                    workloads_deployed.remove(workload)

                    # check if other workloads can be sped up
                    for slow_workload in workloads_slowed:
                        slow_workload.update_ttf_slowed()

                else:
                    print("--------------")
                    print(f"Workload {workload.name}")
                    print(f"Time remaining {'%.3f'%(workload.time_to_finish_s-(cur_time-workload.start_time))}")
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

            # If the network is too busy catch the exception and restore band 
            try:
                slowed = workload.start(G)  # start the workload and get if slowed or not
                workloads_deployed.append(workload)

                if slowed:
                    workloads_slowed.append(workload)
            
            except Exception:
                workload.terminate(G)
                workloads_on_hold.append(workload)
            
            

        
