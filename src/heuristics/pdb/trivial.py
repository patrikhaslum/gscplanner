from 	__future__		import print_function

import 	logging
import 	random 
	
from 	heuristics.projections	import project_hybrid_over_vars
from	heuristics.pdb.pattern	import Table
from 	heuristics.pdb 		import Canonical_Heuristic_Function 

def trivial_partitioning( in_task ) :
    """
    Implements the trival PDB construction: Every variable that
    is mentioned in a primary goal, or in the trigger of a switched
    constraint if the problem has secondary goals, becomes a singleton
    pattern.
    Returns the canonical PDB heuristic over the resulting set.
    """
    logging.info( 'PDB construction: trival partitioning' )
    goal_vars = set()
    for x, v in in_task.Gp:
        goal_vars.add(x)
    if len(in_task.Gs) > 0:
        for t, c in in_task.lp.constraints:
            for x, v in t:
                goal_vars.add(x)

    pattern_collection = []
    for k, var_num in enumerate(goal_vars):
        sig = [ var_num ]
        logging.info( 'Pattern #{0}: {1}, {2}'.format( k, sig, in_task.task.state_vars[var_num].name ) )
	p_k = Table( sig )
	p_k.build_relevant_action_set( in_task.actions )
	projected_task, vars_maps, actions_maps = project_hybrid_over_vars( in_task, sig )
	p_k.populate( projected_task, vars_maps, actions_maps )
	if p_k.max_value == 0 :
	    logging.info( 'max value is 0, pattern rejected' )
	    continue
	pattern_collection.append( p_k )

    h = Canonical_Heuristic_Function( in_task, pattern_collection )
    return h
