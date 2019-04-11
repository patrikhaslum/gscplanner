from __future__		import	print_function
import itertools
import logging

class Entry :

	def __init__( self, h, a ) :
		self.h_value = h
		self.action = a

class Table :

	def __init__(self, signature ) :
		# signature: list of variable indices
		self.signature = signature
		self.table = {}
		self.relevant_actions = set()
		self.relevant_vars = set()

	def build_relevant_action_set( self, actions ) :
		for action in actions :
			# Check if effects affect any variable in the signature
			for x, _ in action.effect :
				if x in self.signature : 
					self.relevant_actions.add( action.index )
					self.relevant_vars |= set( [ x for x, _ in action.prim_precs ])
					self.relevant_vars |= set( [ x for x, _ in action.effect ] )


	def populate_informed( self, projected_task, vars_maps, actions_maps, h ) :
		from itertools				import product
		from model.generic.planning.task 	import State

		def optimal_search( task, h ) :
			from search				import astar_search
			from search.a_star			import ordered_node_astar

			h.enable_preferred_ops = False
			
			def heuristic_adapter( node ) :
				_, inv_var_map = vars_maps
				node.state.primary.unprojected = [ (inv_var_map[X],v) for X,v in node.state.primary.iter_values() ]
				return h(node)

			
			return astar_search( task, heuristic_adapter, make_open_entry=ordered_node_astar, use_relaxed_plan=False, mute=True )

		var_map, inv_var_map = vars_maps
		action_map, inv_action_map =  actions_maps

		domains = [ x.domain for x in projected_task.task.state_vars ]
	
		value_index = 0

		self.unsolvable_count = 0
		self.num_non_zero_entries = 0
		self.max_value = 0
		for valuation in apply(product, map(tuple,domains) ) :
			value_index += 1
			# indexed with the original vars
			entry_index = tuple([ ( inv_var_map[x], v) for x, v in enumerate(valuation) ])
			s0 = State( projected_task.task, [ (x,v) for x,v in enumerate(valuation) ] )
			projected_task.set_initial_state( s0 )
			projected_task.initial_state.check_valid()
			if not projected_task.initial_state.valid :
				self.table[ entry_index ] = Entry( float('inf'), None )
				self.unsolvable_count += 1
				continue				
			plan = optimal_search( projected_task, h )
			if plan is None :
				self.table[ entry_index ] = Entry( float('inf'), None )
				self.unsolvable_count += 1
				continue
			first_action_in_plan = None
			if len(plan) > 0 :
				self.num_non_zero_entries += 1
				first_action_in_plan =  inv_action_map[plan[0].index]
                        plan_cost = sum([ action.cost for action in plan ])
			self.table[ entry_index ] = Entry( plan_cost, first_action_in_plan )	
			self.max_value = max( self.max_value, plan_cost )


	def populate( self, projected_task, vars_maps, actions_maps ) :
                from heuristics.h_zero import H_Zero
                self.populate_informed(projected_task, vars_maps, actions_maps, H_Zero(projected_task))


	def evaluate( self, state ) :
		try :
			projected_state = tuple([ (X, state.value(X)) for X in self.signature ])
		except IndexError :
			projected_state = tuple([ (X, v) for X, v in state.unprojected if X in self.signature])

		try : 
			entry = self.table[ projected_state ]
			return entry.h_value, entry.action
		except KeyError :
 			pass
		return 0, None
