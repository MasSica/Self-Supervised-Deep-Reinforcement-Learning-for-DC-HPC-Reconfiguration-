# Self-Supervised Reversibility- Aware Deep Reinforcement Learning for DC/HPC Optical Network Reconfiguration (RA-DRL)

## Introduction

This work has been carried out at the University of California Davis for my master's thesis and it is the starting point for the paper "Experimental Assessment of Reversibility-Aware Deep Reinforcement Learning for Optical Data Center Network Reconfiguration" that is currently under review for the ONDM 2023 conference. This repository contains only the code associated with the offline training of both the deep reinforcemnt learning (DRL) and reversibility aware deep reinforcemnt learning (RA-DRL) agents since the code used to deploy the agent to the testbed cannot be shared. Hence here you will find the code for the routing module, traffic monitoring module and the agents.

## Goals

The goal of this work is to prove experimentally that a reinforcement learning driven approach to optical switch reconfiguration in datacenter networks can lead to improving the performance of critical workloads(like distributed machine learning training). 


## Results

The DRL agent was able to obtain a improvemnt in training time for a test distributed computer vision application of a factor 5, while the RA-DRL was able to get to the same result with up to 64% improvement in convergence time.  


## How to run
- Download the code 
- Install the required packages in requirements.txt 
- Choose which scenario you want to simulate: pure DRL or RA-DRL
- Run the assciated main file 
