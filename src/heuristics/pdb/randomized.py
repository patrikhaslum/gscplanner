# This module contains several randomized pattern selection 
# strategies, meant to be used as a baseline for more principled
# approaches
from 	__future__		import print_function

import 	logging
import 	random 
	
from 	heuristics.projections	import project_hybrid_over_vars
from	heuristics.pdb.pattern	import Table
from 	heuristics.pdb 		import Canonical_Heuristic_Function 

def naive_partitioning( in_task, max_num_patterns, max_num_entries ) :
	"""
		Partitions in_task variables into as many patterns
		as possible given max_num_entries. Variables are
		assigned to patterns on a random basis

		in_task - Input hybrid task see HybridTask class in model/generic/hybrid/task.py
		max_num_patterns - Maximum number of patterns
		max_num_entries - Maximum number of entries per pattern

		returns a list of pattern databases, already populated
	"""
	logging.info( 'PDB construction: Naive partitioning' )
	variables = {}
	for index, x in enumerate(in_task.task.state_vars) :
		variables[index] = x.domain_size()	

	# such a PDB doesn't make sense
	assert max_num_patterns < len(in_task.task.state_vars)

	pattern_signatures = [ [] for i in xrange(max_num_patterns) ]
	pattern_num_entries = [ 0 for i in xrange(max_num_patterns) ]

	# add one variable to each pattern
	for k, pattern_signature in enumerate( pattern_signatures ) :
		# Choose one variable randomly from the set of variables
		x = random.choice( variables.keys() )
		domain_size = variables[x]
		variables.pop( x ) # remove x
		pattern_signature.append( x )
		pattern_num_entries[ k ] = domain_size

	logging.info( '# Variables after initial allocation to patterns: {0}'.format( len( variables ) ) )
	
	# keep doing this until we don't have any variables left
	while len(variables) > 0 :
		logging.info( '# Remaining variables {0}'.format( len(variables) ) )
		x = random.choice( variables.keys() )
		domain_size = variables[ x ]
		variables.pop( x ) # remove x
		
		# Find a pattern that can accomodate this variable
		allocated = None
		for k, pattern_signature in enumerate( pattern_signatures ) :
			if pattern_num_entries[ k ] * domain_size > max_num_entries :
				logging.info( 'Variable {0} does not fit in pattern {1}, current # entries is {2}, after adding {0} # entries would be {3}'.format( x, k, pattern_num_entries[k], pattern_num_entries[ k ] * domain_size ) )
				continue
			allocated = k
			pattern_signature.append( x )
			pattern_num_entries[k] *= domain_size
			break
 		
		# there was no room to allocate this variable without violating the
		# constraint on the maximum number of entries
		if allocated is None : 			
			logging.info( 'Variable {0} did not fit in any existing pattern, creating new pattern'.format( x ) )
			pattern_signatures.append( [ x ] )
			pattern_num_entries.append( domain_size )

	logging.info( 'All variables allocated to patterns' )
	for k, pattern_signature in enumerate( pattern_signatures ) :
		logging.info( 'Pattern #{0}, signature size: {1}, # entries: {2}'.format( k, len(pattern_signature), pattern_num_entries[k] ) )
	if len( pattern_signatures) > max_num_patterns :
		logging.info( '# of patterns {0}, requested was {1}'.format( len(pattern_signatures), max_num_patterns ) )

	logging.info( 'Projecting task over pattern variables' )
	projected_tasks = []
	for k, signature in enumerate( pattern_signatures ) :
		logging.info( 'Pattern {0}, size {1}:'.format( k, len(signature) ) )
		projected_tasks.append( project_hybrid_over_vars( in_task, signature ) )
	logging.info( 'Projection complete' )

	logging.info( 'Populating pattern databses' )
	database = []
	for k, projection_data in enumerate( projected_tasks ) :
		logging.info( 'Computing values for Pattern {0}, size {1}:'.format( k, len(pattern_signatures[k]) ) )
		p_k = Table( pattern_signatures[k] )
		p_k.build_relevant_action_set( in_task.actions )
		projected_task, vars_maps, actions_maps = projection_data
		p_k.populate( projected_task, vars_maps, actions_maps ) 
	logging.info( 'Pattern databases have been populated' )
	
	return 	Canonical_Heuristic_Function( in_task, database )	
