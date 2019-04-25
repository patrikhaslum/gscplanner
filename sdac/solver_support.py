from 	heuristics.h_zero		import 	H_Zero

import  search

import logging
import time

#TIMER_FUN = time.clock
TIMER_FUN = time.time

def     log_plan( the_solution ) : 
        
        the_plan = the_solution[0]
        final_node = the_solution[1]
    
	logging.info( 'Plan Length: {0}'.format( len(the_plan) ) )
        total_cost = 0
	for index, action in enumerate(the_plan) :
		print( '{0}. {1}'.format( index+1, action.name ) )
                total_cost += action.cost
	#logging.info( 'Cost of the sequence of actions: {0}'.format( total_cost ) )
	logging.info( 'Cost of the final state: {0}'.format( final_node.g ) )

def 	solve_blind( task, search_fn, planner_name ) :
	
	start_time = TIMER_FUN()

	the_plan = search_fn( task )
	
	logging.info( 'Wall-clock {0} search time: {1:.4}'.format( planner_name, TIMER_FUN() - start_time ) )
	if the_plan is None :
		print( 'No solution found.' )
		return

        log_plan( the_plan )

def 	solve_heuristic( task, search_fn, h, planner_name, succ_fn = None ) :
	start_time = TIMER_FUN()
	the_plan = search_fn( task, h, succ_fn )
	logging.info( 'Wall-clock {0} search time: {1:.4}'.format( planner_name, TIMER_FUN() - start_time ) )
	if the_plan is None :
		print( 'No solution found.' )
		return

        log_plan( the_plan )
        #task.validate(the_plan)
        return the_plan

configs = [  'blind', 'a_star_h0', 'a_star_pdb_haslum_aaai07_sdac', 'a_star_pdb_naive_sdac', 'a_star_pdb_trivial_sdac']

def solve( configuration, task ) :
	delayed_evaluation = False

	if configuration == 'blind' :
		solve_blind( task, search.breadth_first_search, 'Blind')
	elif configuration == 'a_star_h0' :
		solve_heuristic( task, search.astar_search, H_Zero(task), 'A* (h_0)' )

        elif configuration == 'a_star_pdb_haslum_aaai07_sdac' :  
		from heuristics.pdb.haslum_aaai07 import iPDB
		pdb_h = iPDB( task, 10000, sdac = True )
		solve_heuristic( task, search.astar_search, pdb_h, 'A* (iPDB with SDAC)' )
		
        elif configuration == 'a_star_pdb_naive_sdac' : 
                from heuristics.pdb.randomized import naive_partitioning 
                pdb_h = naive_partitioning( task, 10, 3, sdac = True ) 
		solve_heuristic( task, search.astar_search, pdb_h, 'A* (Naive Partitioning with SDAC PDB)' ) 
            
        elif configuration == 'a_star_pdb_trivial_sdac' :
                from heuristics.pdb.trivial import trivial_partitioning
		pdb_h = trivial_partitioning( task, sdac = True ) 
		solve_heuristic( task, search.astar_search, pdb_h, 'A* (Trivial Partitioning SDAC PDB)' )

	from model.generic.hybrid.state import HybridState
	logging.info( '# Calls to optimize(): {0} Total Time: {1}'.format( HybridState.calls_to_optimize, HybridState.total_time_optimize) )
	logging.info( '# Models created: {0} Total Time: {1}'.format( HybridState.models_created, HybridState.total_time_model_building ) )
