#!/usr/bin/python
from __future__ import        print_function
import sys
import os
import logging
import time
# NOTE: uncommenting the line below may help Python to locate modules
#sys.path.append( os.getcwd() ) 

from model.generic.planning.task        import         State
from model.generic.hybrid.task                import        HybridTask

import hbw3

import solver_support

from gurobipy                                import         GRB, setParam


def main() :

        if len(sys.argv) < 2 :
                print( 'No instance specified!', file=sys.stderr )
                sys.exit(1)

        input_file = sys.argv[1]

        
        if len(sys.argv) < 3 :
                configuration = 'ppa_star_hplus'
        else :
                configuration = sys.argv[2]

        constrained = True
        if len(sys.argv) < 4 :
                total_amount_of_fluid = 10
        elif sys.argv[3] == 'unconstrained':
                constrained = False
                total_amount_of_fluid = 0
        else :
                total_amount_of_fluid = int(sys.argv[3])

        if configuration not in solver_support.configs :
                print( 'Specified configuration name {0} not recognized'.format( configuration ) )
                print( 'Available configurations are:' )
                for cfg in configs :
                        print( '\t{0}'.format( cfg ) )
                sys.exit(1)
        print ( 'Configuration {0} is active'.format( configuration ) )

        #if len(sys.argv) < 4 :
        #        output_redirect = sys.stdout
        #else :
        #        output_redirect = open( sys.argv[3], 'w' )

        # set Gurobi parameters
        setParam( 'LogFile', '' )
        setParam( 'LogToConsole', 0 )
        setParam( 'OutputFlag', 0 )
        logging.basicConfig(        level='INFO',
                                #level='DEBUG',
                                format='%(asctime)s %(levelname)-8s %(message)s',
                                stream=sys.stdout)

        task = hbw3.create_prob_from_file( input_file, total_amount_of_fluid, constrained )
        task.s0.check_valid()
        logging.info( 'Task initial state valid? %s'%task.s0.valid )        

        if len(sys.argv) > 4:
                task.validate(sys.argv[4:])
                sys.exit(0)

        solver_support.solve( configuration, task )

if __name__ == '__main__' :
        main()
