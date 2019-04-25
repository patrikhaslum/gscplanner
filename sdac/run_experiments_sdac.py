#!/usr/bin/python

from __future__ import print_function

import sys
import os
import logging
import time

from model.generic.hybrid.task import HybridTask

from psr.sgt.psr_client import get_network
from psr.sgt.planning import SGTPSRTask, make_initial_state
from psr.sgt.planning_ugoal import SGTPSRUGTask, make_initial_state
from psr.sgt.lp import LinearProgram

import solver_support

def get_task(infile) :
        the_network = get_network(infile)
        print('psr_sgt_solver: network = ' + str(the_network))

        sdac_type = "Objective"
        sdac_true = True

        the_task = SGTPSRTask(the_network, sdac = sdac_type)
        the_task.print_statistics(sys.stdout)
        the_LP = LinearProgram(the_task)
        the_hybrid_task = HybridTask(
            the_task, the_LP, make_initial_state(the_task), [], 
            the_LP.goal_constraints, sdac_optimization = sdac_true)

        the_LP.model.printStats()
        the_hybrid_task.s0.check_valid()

        logging.info('Task initial state valid? %s'%the_hybrid_task.s0.valid)

        if not the_hybrid_task.s0.valid :
            sys.exit(1)

        return the_hybrid_task

def get_task_ugoal(infile) : 
    
        the_network = get_network(infile)
        for b in the_network.buses : 
            b.final_require_fed = False
        
        print('psr_sgt_solver: network = ' + str(the_network))

        sdac_type = "Objective"
        sdac_true = True

        the_task = SGTPSRUGTask(the_network, sdac = sdac_type)
        the_task.print_statistics(sys.stdout)
        the_LP = LinearProgram(the_task)
        the_LP.goal_constraints = set()
        the_hybrid_task = HybridTask(
            the_task, the_LP, make_initial_state(the_task), [(the_task.plan_end_var.index, True)], 
            #the_LP.goal_constraints)
            set(), sdac_optimization = sdac_true)

        the_LP.model.printStats()
        the_hybrid_task.s0.check_valid()

        logging.info('Task initial state valid? %s'%the_hybrid_task.s0.valid)

        if not the_hybrid_task.s0.valid :
            sys.exit(1)

        return the_hybrid_task


def run_experiment(problem, output, configuration, get_task_function = None): 
    
    logging.basicConfig(
        level='INFO',
        #filename = 'log_all.txt',
        #level='DEBUG',
        format='%(asctime)s %(levelname)-8s %(message)s',
        #level='NOTSET',
        #format="LOG [%(filename)s:%(lineno)s %(funcName)0s()] %(message)s",
        stream= sys.stdout
        )

    infile = os.path.abspath(problem)

    if configuration not in solver_support.configs :
        print('Specified configuration name {0} not recognized'.format(configuration))
        print('Available configurations are:')
        for cfg in solver_support.configs :
            print('\t{0}'.format(cfg))
        sys.exit(1)

    print ('Configuration {0} is active'.format(configuration))
    if get_task_function != None : 
        task = get_task_function(infile)
    else:
        task = get_task(infile) 

    solver_support.solve(configuration, task) 


def run_all_experiments(): 

    #problem = "psr/sgt/PsrSgtServer//data/tests/nesta_case14_ieee/faults_bus_01.yaml" 
    #output = "../experiments/psr_sgt_SDAC/nesta_case14_faults_bus_01.txt"
    configuration = "a_star_h0" 

    problems = ["faults_bus_01", 
                "faults_bus_02", 
                #"faults_bus_03", 
                "faults_bus_04",
                "faults_bus_05", 
                #"faults_bus_06", 
                "faults_bus_07",
                #"faults_bus_08", 
                "faults_bus_11", 
                "faults_bus_12",
                "faults_bus_13", 
                "faults_bus_14"]
    
    for p in problems: 
        problem = "../src/psr/sgt/PsrSgtServer/data/tests/nesta_case14_ieee/"+p+".yaml" 
        output = "../experiments/psr_sgt_SDAC/a_star_h0/nesta_case14_"+p+".txt" 
        run_experiment(problem, output, configuration) 

def run_simple_experiment(): 
    
    #problem = "../src/psr/sgt/PsrSgtServer/data/tests/nesta_case4_gs/faults_bus_4.yaml"
    problem = "../src/psr/sgt/PsrSgtServer/data/tests/nesta_case14_ieee/"+"faults_bus_12"+".yaml"
    output = "../experiments/psr_sgt_SDAC/nesta_case14_faults_bus_12.txt"
    configuration = "a_star_h0"
    #configuration = 'a_star_pdb_haslum_aaai07'
    #configuration = 'psr_pdb_connection' 
    #configuration = 'ppa_star_pdb_naive' 
    #configuration = 'ppa_star_pdb_trivial' 
    
    run_experiment( problem, output, configuration, get_task_function = get_task_ugoal ) 

def validate_one(p, plan): 
    problem = "../src/psr/sgt/PsrSgtServer/data/tests/nesta_case14_ieee/"+p+".yaml"

    logging.basicConfig(
        level='INFO',
        #filename = 'log_all.txt',
        #level='DEBUG',
        format='%(asctime)s %(levelname)-8s %(message)s',
        #level='NOTSET',
        #format="LOG [%(filename)s:%(lineno)s %(funcName)0s()] %(message)s",
        stream= sys.stdout
        )

    infile = os.path.abspath(problem)
    task_1 = get_task(infile)
    task_1.validate(plan)


def validate_all(): 
    
    p_1 = "faults_bus_01"
    plan_1 = [ 
        "Close_branch_02_bus_02_bus_03", 
        "Open_branch_06_bus_04_bus_05" , 
        "Close_branch_04_bus_02_bus_05" , 
        "Close_branch_09_bus_05_bus_06" , 
        "Open_branch_16_bus_09_bus_14" , 
        "Close_branch_12_bus_06_bus_13" , 
        "Close_branch_11_bus_06_bus_12" , 
        "Open_branch_17_bus_10_bus_11" , 
        "Close_branch_10_bus_06_bus_11"  
        ] 
    
    p_2 =  "faults_bus_02"
    plan_2 = [ 
        "Open_branch_15_bus_09_bus_10", 
        "Open_branch_16_bus_09_bus_14", 
        "Close_branch_01_bus_01_bus_05", 
        "Close_branch_05_bus_03_bus_04", 
        "Close_branch_09_bus_05_bus_06", 
        "Close_branch_10_bus_06_bus_11", 
        "Open_branch_17_bus_10_bus_11", 
        "Close_branch_12_bus_06_bus_13" 
        ]

    p_4 =  "faults_bus_04"
    plan_4 = [ 
        "Open_branch_06_bus_04_bus_05",
        "Close_branch_01_bus_01_bus_05" ,
        "Close_branch_04_bus_02_bus_05" ,
        "Open_branch_07_bus_04_bus_07" ,
        "Open_branch_08_bus_04_bus_09" ,
        "Close_branch_09_bus_05_bus_06" ,
        "Open_branch_16_bus_09_bus_14" ,
        "Close_branch_10_bus_06_bus_11" ,
        "Close_branch_12_bus_06_bus_13" 
        ]
    
    p_5 =  "faults_bus_05"  
    plan_5 = [  "Open_branch_06_bus_04_bus_05",  
                "Open_branch_16_bus_09_bus_14",  
                "Close_branch_03_bus_02_bus_04",  
                "Close_branch_05_bus_03_bus_04",  
                "Close_branch_10_bus_06_bus_11",  
                "Close_branch_16_bus_09_bus_14" ] 
    
    p_7 =  "faults_bus_07"
    plan_7 = [ "Open_branch_07_bus_04_bus_07", 
                "Open_branch_14_bus_07_bus_09" ,
                "Open_branch_16_bus_09_bus_14" ,
                "Close_branch_03_bus_02_bus_04" ,
                "Close_branch_01_bus_01_bus_05" ,
                "Close_branch_09_bus_05_bus_06" ,
                "Close_branch_11_bus_06_bus_12" ]
    
    p_11 = "faults_bus_11" 
    plan_11 = [ "Open_branch_16_bus_09_bus_14" ,
                "Open_branch_17_bus_10_bus_11" ,
                "Close_branch_03_bus_02_bus_04" ,
                "Close_branch_09_bus_05_bus_06" ,
                "Close_branch_12_bus_06_bus_13" ]

    p_12 = "faults_bus_12"
    plan_12 = [ "Open_branch_16_bus_09_bus_14" ,
                "Close_branch_01_bus_01_bus_05" ,
                "Close_branch_03_bus_02_bus_04" ,
                "Open_branch_18_bus_12_bus_13" ,
                "Close_branch_16_bus_09_bus_14" ]

    p_13 = "faults_bus_13" 
    plan_13 = [ ]

    p_14 = "faults_bus_14"
    plan_14 = [ ]
    
    validate_one(p_12, plan_12) 


if __name__ == '__main__' :
    #run_all_experiments()
    #validate_all()
    run_simple_experiment() 
