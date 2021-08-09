#!/usr/bin/python

from __future__ import print_function

import sys
import os
import logging
import time

from         gurobipy                        import        setParam

from        counters.planning_v2                import         CountersTask, make_initial_state
from        counters.lp_v2                        import        LinearProgram

import        counters.parsing

from         model.generic.hybrid.task        import        HybridTask

from         heuristics.h_max                import         H_Max
from         heuristics.h_plus                import         H_Plus

import  search

import        counters.parsing
import solver_support

def parse_instance( inst_file ) :
        
        count_vars, max_value, initial_values, goal_condition = counters.parsing.parse_instance( inst_file )
        planning_task = CountersTask( count_vars, max_value ) 
        planning_task.print_statistics( sys.stdout )
        the_LP = LinearProgram( planning_task )
        the_hybrid_task = HybridTask( planning_task, the_LP, make_initial_state( planning_task, initial_values ), [], the_LP.make_goal_constraints( goal_condition ) )
                
        the_LP.model.printStats() # Includes goal constraints
        the_hybrid_task.s0.check_valid()

        logging.info( 'Task initial state valid? %s'%the_hybrid_task.s0.valid )        

        if not the_hybrid_task.s0.valid :
                sys.exit(1)        
        

        return the_hybrid_task

def main() :
        
        if len( sys.argv ) < 2 :
                print( 'Missing argument: input problem!', file=sys.stderr )
                sys.exit(1)

        instance = sys.argv[1]

        if not os.path.exists( instance ) :
                print( 'Could not find {0}'.format( instance ), file=sys.stderr )
                sys.exit(1)


        if len(sys.argv) < 3 :
                configuration = 'ppa_star_hplus'
        else :
                configuration = sys.argv[2]


        if configuration not in solver_support.configs :
                print( 'Specified configuration name {0} not recognized'.format( configuration ) )
                print( 'Available configurations are:' )
                for cfg in solver_support.configs :
                        print( '\t{0}'.format( cfg ) )
                sys.exit(1)
        print ( 'Configuration {0} is active'.format( configuration ) )

        if len(sys.argv) < 4 :
                output_redirect = sys.stdout
        else :
                output_redirect = open( sys.argv[3], 'w' )
        
        # set Gurobi parameters
        setParam( 'LogFile', '' )
        setParam( 'LogToConsole', 0 )
        setParam( 'OutputFlag', 0 )
        logging.basicConfig(        level='INFO',
                                #level='DEBUG',
                                format='%(asctime)s %(levelname)-8s %(message)s',
                                stream=output_redirect)

        task = parse_instance( instance ) 
        solver_support.solve( configuration, task )

if __name__ == '__main__' :
        main()
