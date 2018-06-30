# Evaluation functions for PDB heuristics

from 	heuristics.heuristic_base	import	Heuristic
from	heuristics.pdb.pattern		import  Table
from 	heuristics.pdb.max_cliques	import 	Graph, Cliques 

import logging

class Canonical_Heuristic_Function ( Heuristic ) :

	def __init__( self, in_task, pattern_database ) :
		self.task = in_task
		self.db = pattern_database
		self.determine_additive_subsets()
		self.enable_preferred_ops = True

	def determine_additive_subsets( self ) :
		from max_cliques import *		
		from itertools import combinations

		if len(self.db) == 1 :
			self.additive_subsets = [ frozenset( [0] ) ]
			return

		#logging.info( 'Computing additive subsets' )
		V = range(0, len(self.db) )
		self.dependency_graph = Graph( V )
		#logging.info( 'Graph: V={0} E={1}'.format( self.dependency_graph.V, self.dependency_graph.adj ) )
		for i, j in combinations( range(len(self.db)), 2 ) :
			if len( self.db[i].relevant_actions & self.db[j].relevant_actions ) == 0 :	
				self.dependency_graph.add_edge( i, j )
		#logging.info( 'BUILT pattern dependency graph' )
		self.additive_subsets = Cliques.enumerate_max_cliques( self.dependency_graph )

	def evaluate( self, state, verbose = False ) :	
		import logging	
		components = []

		for A in self.additive_subsets :
			if verbose:
				print "additive set: ", A
			h = 0
			actions = []
			for k in A :
				h_k, action_index = self.db[k].evaluate( state )
				if h_k == float('inf') :
					h = float('inf')
					break
				if verbose:
					print "  pattern: ", self.db[k].signature, ", value = ", h_k
				h += h_k
				if self.enable_preferred_ops :
					a_k = None
					if action_index is not None :
						a_k = self.task.actions[action_index]
						if  state.satisfies(a_k.prim_precs ) :
							actions.append( a_k )
			if h == float('inf') :
				return float('inf'), []
			components.append( ( h, actions ) )
		
		return  max( components )

	def __call__( self, node ) :
		node.h = 0
		node.preferred_ops = []
		node.preferred_ops_counter = 0	
		max_h, best_actions = self.evaluate( node.state.primary )
		node.h = max_h
		node.preferred_ops = best_actions

		return node.h
