#!/usr/bin/python3
import sys
import os
import logging
import time

from model.generic.planning.task import State
from model.generic.hybrid.task import HybridTask

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

        task = ac.create_task( domain_file, problem_file )
        task.s0.check_valid()
        logging.info( 'Task initial state valid? %s'%task.s0.valid )        

        # if len(argv) > 5:
        #         task.validate(argv[4:])
        #         sys.exit(0)

        solver_support.solve( configuration, task )

if __name__ == '__main__' :
        main()
