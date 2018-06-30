from    __future__      import print_function
from 	state		import	HybridState
import 	logging
import  sys

# static helper function: 
def get_primary(s):
        try :
                return s.primary
        except AttributeError :
                return s
                

class HybridTask :
	
	def __init__( self, task, lp, s0, primary_G, secondary_G = set() ) :

		self.task = task
		self.lp	= lp
		self.prim_s0 = s0
		self.Gp = primary_G
		self.Gs = secondary_G
		self.inactive_by_default = set()
		self.inactive_by_default |= self.Gs
		self.actions = self.task.actions
		self.no_good_list = []
		self.num_conflicts = 0
		self.pruned_ngl = 0
		self.num_actions_added = 0
		i = 0
		for action in self.actions :
			action.index = i
			self.inactive_by_default |= action.sec_precs
			i+=1
		
		if self.prim_s0 is not None :
			self.s0 = self.initial_state = HybridState( self.prim_s0, self.lp, self.inactive_by_default.copy() )
		#assert self.s0.secondary is not None

	def set_initial_state( self, s ) :
		self.s0 = self.initial_state = HybridState( s, self.lp, self.inactive_by_default.copy() )

        # Check if action secondary preconditions hold in s. This
        # will always use the stronger ("1st weaker") relaxation, i.e.,
        # imposing the actions primary precs on the (relaxed) state.
        # It will always make a call to the external solver, even if
        # the action has no secondary precs (this is to check if the
        # primary precs are consistent with invariant constraints).
        # The switch between 1st and 2nd weaker relaxation is done in
        # RelaxedPlanningGraph, which controls when this method is called.
        # Args: s can be either a HybridState or a (primary) State;
        #       action is a model.generic.planning.Action
	def check_secondary_precondition( self, s, action ) :
                s_p = get_primary(s).copy()
                s_p.set_vec(action.prim_precs)
		return self.check_validity_additional_constraints( s_p, action.sec_precs )

        # Check if actions effects (on real or relaxed state) are
        # consistent with invariant constraints.
        def check_postcondition_validity(self, s, action):
                s_p = get_primary(s).copy()
                s_p.set_vec(action.effect)
                assigned_vars = [var for var, val in action.effect]
                for var, val in action.prim_precs:
                        if var not in assigned_vars:
                                s_p.set(var, val)
                result = self.check_validity_additional_constraints(s_p, set())
                return result

        # Check if secondary goal holds in s. As in check_secondary_prec,
        # this uses the 1st weaker relaxation, and invokes the external
        # solver also if there are no secondary goals.
	def check_secondary_goal( self, s ) :
                if len(self.Gp) > 0:
                        s_p = get_primary(s).copy()
                        s_p.set_vec(self.Gp)
                        s = s_p
                result = self.check_validity_additional_constraints( s, self.Gs )
		return result
	
	def check_validity_additional_constraints( self, s, additional ) :
                if additional is None:
                        inactive = self.inactive_by_default
                else:
                        inactive = self.inactive_by_default - additional
		#logging.debug( 'Checking validity with {0} additional constraints'.format( len(additional)) )
		try :
			tmp = HybridState( s.primary, self.lp, inactive.copy() )
		except AttributeError :
			tmp = HybridState( s, self.lp, inactive.copy() )
		#tmp.write(sys.stdout)
		tmp.check_valid()
		if not tmp.valid :
			return False
		return True

	def is_applicable( self, s, action ) :
		if not s.primary.satisfies( action.prim_precs ) :
			return False # action is not applicable
		if len( action.sec_precs ) != 0 :
			if not self.check_secondary_precondition( s, action ) :
				return False
		return True

	def compute_successor_state( self, s, action ) :
		assert s.valid is not None
		if not s.valid : 
			return None
		if not self.is_applicable( s, action ) : 
			return None
		prim_succ = s.primary.copy()
		prim_succ.set_vec( action.effect )
	
		succ = HybridState( prim_succ, self.lp, self.inactive_by_default.copy() )
		succ.check_valid()

		if not succ.valid :
			return None
	
		return succ	

	def compute_successor_state_ngl_dyn_model( self, s, action ) :
		assert s.valid is not None
		if not s.valid : 
			return None, False
		if not self.is_applicable( s, action ) : 
			return None, False
		prim_succ = s.primary.copy()
		prim_succ.set_vec( action.effect )

		succ = HybridState( prim_succ, self.lp, self.inactive_by_default.copy() )
		# TODO: No Good Learning, needs to be switchable
		succ.check_valid(True)

		if not succ.valid :
			print( 'Action effect:')
			self.task.print_valuation( action.effect, sys.stdout )
			print( 'Conflict:' )
			self.num_conflicts += 1
			no_good = []
			for index in succ.conflict :
				phi = self.lp.constraints[index][0]
				self.task.print_valuation( self.lp.constraints[index][0], sys.stdout ) 
				for val in phi : 
					if val in action.prim_precs : continue
					if val in action.effect : continue
					no_good.append(val)
			import copy
			count = 0
			for val in no_good[1:] :
				new_action = copy.deepcopy(action)
				x, v = val
				new_action.prim_precs.add( (x,  not v) )
				self.task.actions.append( new_action )
				count += 1
			x,v = no_good[0]
			action.prim_precs.add( (x,  not v) )
			print( '|A|: {0}'.format(len(self.task.actions)) )
			self.num_actions_added += count
			return None, True
	
		return ( succ, False )
	
	# Type 0 No Good Learning
	def compute_successor_state_ngl( self, s, action ) :
		assert s.valid is not None
		if not s.valid : 
			return None
		if not self.is_applicable( s, action ) : 
			return None
		prim_succ = s.primary.copy()
	
		for phi in self.no_good_list :
			if prim_succ.satisfies( phi ) : 
				self.pruned_ngl += 1
				return None		

		prim_succ.set_vec( action.effect )
		succ = HybridState( prim_succ, self.lp, self.inactive_by_default.copy() )
		# TODO: No Good Learning, needs to be switchable
		succ.check_valid(True)

		if not succ.valid :
			#print( 'Action effect:')
			#self.task.print_valuation( action.effect, sys.stdout )
			#print( 'Conflict:' )
			self.num_conflicts += 1
			no_good = []
			for index in succ.conflict :
				phi = self.lp.constraints[index][0]
				#self.task.print_valuation( self.lp.constraints[index][0], sys.stdout ) 
				for val in phi : 
					no_good.append(val)
			self.no_good_list.append( no_good )
			return None
	
		return succ	
	
	# Type 1 No Good Learning
	def compute_successor_state_ngl2( self, s, action ) :
		assert s.valid is not None
		if not s.valid : 
			return None
		if not self.is_applicable( s, action ) : 
			return None
		prim_succ = s.primary.copy()
	
		for phi, index in self.no_good_list :
			if prim_succ.satisfies( phi ) and action.index == index : 
				self.pruned_ngl += 1
				return None		

		prim_succ.set_vec( action.effect )
		succ = HybridState( prim_succ, self.lp, self.inactive_by_default.copy() )
		# TODO: No Good Learning, needs to be switchable
		succ.check_valid(True)

		if not succ.valid :
			#print( 'Action effect:')
			#self.task.print_valuation( action.effect, sys.stdout )
			#print( 'Conflict:' )
			self.num_conflicts += 1
			no_good = []
			for index in succ.conflict :
				phi = self.lp.constraints[index][0]
				#self.task.print_valuation( self.lp.constraints[index][0], sys.stdout ) 
				for val in phi:
					no_good.append(val)
			
			# MRJ: The idea below didn't quite work out very well
			"""
			count = 0
			for a in self.task.actions :
				rule = a.regress( no_good )
				if len(rule) == 0 : continue
				self.no_good_list.append( ( rule, a.index ) ) 
				count += 1
			print count
			"""
			self.no_good_list.append( ( action.regress( no_good ), action.index ) )

			return None
	
		return succ	

	def goal_reached( self, s ) :
		#print("checking primary goals:", self.Gp)
		#print("checking secondary goals:", self.Gs)
		assert s.valid is not None
		if s.primary.satisfies( self.Gp ) :
			if len(self.Gs) == 0 : return True
			#logging.debug( 'Goal requires secondary constraints' )
			return self.check_secondary_goal( s )
		return False

	def successor_states( self, s ) :
		for a in self.actions :
			succ = self.get_successor_state( s )
			if succ is None : continue
			yield succ

	# for pyperplan search algorithms
	def get_successor_states( self, s ) :	
		for a in self.task.actions :
			succ = self.compute_successor_state( s, a )
			if succ is None : continue
			yield (a, succ)

        def find_action( self, action_name ):
                for act in self.actions:
                        if act.name == action_name:
                                return act
                return None

        # plan is a sequence of action names; assumes initial state is valid
        def validate( self, plan ):
                state = self.s0
                step = 0
                for aname in plan:
                        print( "====  STATE ", step, " ====" )
                        state.write(sys.stdout)
                        if isinstance(aname, str):
                                action = self.find_action(aname)
                                if action is None:
                                        print("\nplan error: no action '" + aname + "'")
                                        for act in self.actions:
                                                print(" " + act.name)
                                assert action is not None
                        else:
                                action = aname
                        print( "\nnext action:", action.name, "\n" )
                        if not self.is_applicable( state, action ):
                                print( "action is not applicable!" )
                                print( "primary preconditions: ", action.prim_precs, ", ok?",
                                       state.primary.satisfies( action.prim_precs ) )
                                print( "secondary preconditions:", action.sec_precs )
                                return False

	                prim_succ = state.primary.copy()
	                prim_succ.set_vec( action.effect )
	                succ = HybridState( prim_succ, self.lp, self.inactive_by_default.copy() )
	                succ.check_valid()
                        if not succ.valid:
                                print( "successor state is not valid!" )
                                succ.write(sys.stdout)
                                return False

                        state = succ
                        step += 1

                print( "====  STATE ", step, ": FINAL ====" )
                state.write(sys.stdout)
                print( "\nchecking primary goal:", self.Gp )
                if state.primary.satisfies(self.Gp):
                        print( "- primary goal achieved" )
                else:
                        print( "- primary goal NOT achieved!" )
                        return False
                if len(self.Gs) > 0:
                        print( "\nchecking secondary goal:", self.Gs )
                        if self.check_secondary_goal( state ):
                                print( "- secondary goal achieved" )
                        else:
                                print( "- secondary goal NOT achieved!" )
                                return False

                return True

	def write(self, fileobj):
                print("primary task:", self.task)
                print("number of actions:", len(self.actions))
		# self.s0 should be a HybridState
		print("initial state:")
		self.s0.write(fileobj)
		print("primary goals:", self.Gp, file=fileobj)
		print("secondary goals:", self.Gs, file=fileobj)
		print("inactive by default:", self.inactive_by_default, file=fileobj)
