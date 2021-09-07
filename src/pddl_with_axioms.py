#!/usr/bin/python3
import sys
import os
import logging
import time

from model.generic.planning.task import State
from model.generic.hybrid.task import HybridTask, HybridState

## ac task class imports the FD translator, which parses the
## commandline on import; to allow us to read args that it does
## not recognise, we have have to strip them from sys.argv
## before the import
argv = sys.argv[:]
sys.argv = sys.argv[:3]

import ac
import solver_support

from gurobipy import GRB, setParam

def main() :
        domain_file = argv[1]
        problem_file = argv[2]
        
        if len(argv) < 4 :
                configuration = 'ppa_star_hplus'
        else :
                configuration = argv[3]

        if configuration not in solver_support.configs :
                print( 'Specified configuration name {0} not recognized'.format( configuration ) )
                print( 'Available configurations are:' )
                for cfg in configs :
                        print( '\t{0}'.format( cfg ) )
                sys.exit(1)
        print ( 'Configuration {0} is active'.format( configuration ) )

        # set Gurobi parameters
        setParam( 'LogFile', '' )
        setParam( 'LogToConsole', 0 )
        setParam( 'OutputFlag', 0 )
        logging.basicConfig( level='INFO',
                             #level='DEBUG',
                             format='%(asctime)s %(levelname)-8s %(message)s',
                             stream=sys.stdout)

        HybridState.strong_relaxation = True
        task = ac.create_task( domain_file, problem_file )
        logging.info( str(len(task.task.vars)) + " primary and " + str(len(task.task.derived)) + " derived variables; " + str(len(task.lp.rules) if task.lp is not None else 0) + " axioms")

        ## print the whole task (in somewhat human-readable form)
        # print("primary state variables:")
        # for i in range(len(task.task.vars)):
        #         print(str(i) + ". " + task.task.vars[i].name + " : ", end='')
        #         for j in task.task.vars[i].domain:
        #                 print(' ' + task.task.primary_literal_name[(i,j)], end='')
        #         print()
        # print("secondary (derived) variables:")
        # for i in range(len(task.task.derived)):
        #         print(str(i) + ". " + task.task.derived[i][0] + " : ", end='')
        #         v0 = task.task.derived[i][1]
        #         print(' ' + task.task.derived_literal_name[(i,v0)], end='')
        #         print(' ' + task.task.derived_literal_name[(i,1-v0)])
        # print("actions:")
        # for i in range(len(task.task.actions)):
        #         print(str(i) + ". " + task.task.actions[i].name)
        #         print(" primary prec: " + task.task.str_primary_condition(task.task.actions[i].prim_precs))
        #         if task.lp is not None:
        #                 print(" secondary prec: " + task.lp.str_secondary_condition(task.task.actions[i].sec_precs))
        #         print(" effect: " + task.task.str_primary_condition(task.task.actions[i].effect))
        #         print(" cost: " + str(task.task.actions[i].cost))
        # print("axioms:")
        # for i in range(len(task.lp.rules)):
        #         head, pos_body, neg_body = task.lp.rules[i]
        #         print(" " + str(task.lp.rules[i]) + " = " + task.lp.str_rule(head, pos_body, neg_body))
        
        task.s0.check_valid()
        logging.info( 'Task initial state valid? %s'%task.s0.valid )

        # from heuristics.h_max import H_Max
        # from search.searchspace import make_root_node
        # n = make_root_node(task.s0)
        # logging.info("evaluating heuristic...")
        # H_Max.meticulous = True
        # h = H_Max(task, verbose = True)
        # v = h(n)
        # logging.info("heuristic value: " + str(v))
        # sys.exit(0)

        if len(argv) > 4:
                task.validate(argv[4:])
                sys.exit(0)

        solver_support.solve( configuration, task )

if __name__ == '__main__' :
        main()
