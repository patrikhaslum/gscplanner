#!/usr/bin/python

from __future__ import print_function

import sys
import os
import logging
import time

from model.generic.hybrid.task import HybridTask

from psr.sgt.psr_client import get_network
from psr.sgt.planning import SGTPSRTask, make_initial_state
from psr.sgt.lp import LinearProgram

import solver_support

from run_experiments_sdac import get_task, get_task_ugoal, run_experiment 

#def get_task(infile) :
        #the_network = get_network(infile)
        #print('psr_sgt_solver: network = ' + str(the_network))

        #the_task = SGTPSRTask(the_network)
        #the_task.print_statistics(sys.stdout)
        #the_LP = LinearProgram(the_task)
        #the_hybrid_task = HybridTask(
            #the_task, the_LP, make_initial_state(the_task), [], 
            #the_LP.goal_constraints)

        #the_LP.model.printStats()
        #the_hybrid_task.s0.check_valid()

        #logging.info('Task initial state valid? %s'%the_hybrid_task.s0.valid)

        #if not the_hybrid_task.s0.valid :
            #sys.exit(1)

        #return the_hybrid_task

def main() :
    logging.basicConfig(
        level='INFO',
        #level='DEBUG',
        format='%(asctime)s %(levelname)-8s %(message)s',
        #level='NOTSET',
        #format="LOG [%(filename)s:%(lineno)s %(funcName)0s()] %(message)s",
        stream=sys.stdout)

    infile = os.path.abspath(sys.argv[1])

    if len(sys.argv) < 3 :
        configuration = 'a_star_pdb_haslum_aaai07_sdac'
    else :
        configuration = sys.argv[2]

    if configuration not in solver_support.configs :
        print('Specified configuration name {0} not recognized'.format(configuration))
        print('Available configurations are:')
        for cfg in solver_support.configs :
            print('\t{0}'.format(cfg))
        sys.exit(1)

    print ('Configuration {0} is active'.format(configuration))

    if len(sys.argv) > 3 and sys.argv[3] == "ugoal":
        print("Using get_task_ugoal.")
        task = get_task_ugoal(infile)
    else:
        print("Using get_task.")
        task = get_task(infile)

    if len(sys.argv) > 4:
           task.validate(sys.argv[4:])
           sys.exit(0)            

    solver_support.solve(configuration, task)

if __name__ == '__main__' :
    main()
