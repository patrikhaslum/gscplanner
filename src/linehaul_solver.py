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

import linehaul

import solver_support

from gurobipy                                import         GRB, setParam


try:
    val = int(os.environ['PYTHONHASHSEED'])
except Exception as e:
    val = None

if val != 1:
    print('\n' + "*"*80)
    print("- WARNING -\n Automatically setting PYTHONHASHSEED to 1 to obtain more reliable results")
    print("*"*80 + '\n')
    # We simply set the environment variable and re-call ourselves.
    from subprocess import call
    os.environ["PYTHONHASHSEED"] = '1'
    call(["python", "-OO"] + sys.argv)
    sys.exit(1)

def main() :
        if len(sys.argv) < 3 :
                #print( 'No instance specified!', file=sys.stderr )
                print( 'No instance specified!' )
                sys.exit(1)

        vrx_file = sys.argv[1]
        dm_file = sys.argv[2]
        
        if len(sys.argv) < 4 :
                configuration = 'ppa_star_hplus'
        else :
                configuration = sys.argv[3]

        if len(sys.argv) < 5 :
            fleet = [4,3,2,2,1]
        else :
            fleet_str = sys.argv[4]
            try:
                fleet = [ int(num) for num in fleet_str.split(',') ]
            except:
                print("Invalid fleet spec " + fleet_str)
                sys.exit(1)
            if len(fleet) != 5:
                print("Invalid fleet spec " + str(fleet) + " (length is not 5)")
                sys.exit(1)

        if configuration not in solver_support.configs :
                print( 'Specified configuration name {0} not recognized'.format( configuration ) )
                print( 'Available configurations are:' )
                for cfg in solver_support.configs :
                        print( '\t{0}'.format( cfg ) )
                sys.exit(1)

        ## redirect output to a log file; this is necessary when
        ## running on the cluster, since normal output redirection
        ## (through shell pipelining) doesn't seem to work.
        #import redirection
        #lname = redirection.mk_log_name(vrx_file)
        #redirection.redirect_to_logfile(lname)

        print ( 'Configuration {0} is active'.format( configuration ) )

        # set Gurobi parameters
        setParam( 'LogFile', '' )
        setParam( 'LogToConsole', 0 )
        setParam( 'OutputFlag', 0 )
        # ensure Gurobi is single-threaded
        setParam( 'Threads', 1 )
        logging.basicConfig(level='INFO',
                            #level='DEBUG',
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            stream=sys.stdout)

        logging.info( 'args = ' + str(sys.argv) )

        # Set to False to disable symmetry breaking (True is default):
        # linehaul.LinehaulTask.SYMMETRY_BREAKING = True

        # Optional last arg specifies the number of vehicles
        # of each type; eg., [0,0,1,1,0] means 1 B-double reefer,
        # 1 B-double, and zero of the other types. The count can
        # also be given as a single number, which then applied to
        # all vehicle types. If not provided, the default is
        # [4,3,2,2,1] (what was given in Phil's problem spec).
        # task = linehaul.create_problem( vrx_file, dm_file, [0,0,1,1,0] )
        # task = linehaul.create_problem( vrx_file, dm_file )
        task = linehaul.create_problem( vrx_file, dm_file, fleet )
        ## debug stuff
        ##task.lp.print_constraints()
        ##task.lp.model.write("test.lp")
        ##print(task.Gs)
        task.s0.check_valid()
        logging.info( 'Task initial state valid? %s'%task.s0.valid )

        solver_support.solve( configuration, task )

if __name__ == '__main__' :
        main()
