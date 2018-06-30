from	gurobipy	import Var, Constr, Model, GRB, quicksum

class 	LinearProgram :

	def __init__( self, counters_task ) :
		
		self.model = Model( counters_task.instance_name + '.lp' )

		# LP Vars
		self.variables = []
		self.make_model_vars( counters_task )
		self.model.update()

		# LP Constraints
		self.constraints = []
		self.make_model_constraints( counters_task )
		self.model.update()
		
		self.goal_constraints = set()

	def copy( self ) :
		from copy 	import deepcopy

		new_lp = LinearProgram()
		new_lp.variables = deepcopy(self.variables)
		new_lp.goal_constraints = deepcopy(self.goal_constraints)
		new_lp.model = self.model.copy()
		new_lp.constraints = []
		for index, ext_constraint in enumerate(self.constraints) :
			 new_lp.constraints.append( ( deepcopy(ext_constraint[0]), new_lp.model.getConstrs()[index] ) )
		return new_lp

	def	make_model_vars( self, task ) :
		for x_c in task.counter_values :
			x_c_2 = self.model.addVar( name = x_c.name, lb=min(x_c.domain), ub=max(x_c.domain), vtype = GRB.INTEGER )
			self.variables.append( x_c_2 )

	def 	make_model_constraints( self, task ) :
		
		for i in range( 0, len( self.variables ) ) :
			x = task.counter_values[i]
			x2 = self.variables[i]

			# Equivalence constraints
			for v in x.domain :
				c = self.model.addConstr( x2 == v )
				self.constraints.append( ( [ (x.index, v) ], c ) )

			# Bounds constraints
			gt_zero = self.model.addConstr( x2 >= 0 )
			lt_max = self.model.addConstr( x2, GRB.LESS_EQUAL, task.max_value )
			
			self.constraints.append( ( [], gt_zero ) )
			self.constraints.append( ( [], lt_max ) )
		
	def	make_goal_constraints( self, goal_condition ) :
		goal_constraints = []
		for cond, lhs, rhs in goal_condition :
			x_lhs = None
			x_rhs = None
			for x in self.model.getVars() :
				if lhs in x.getAttr('VarName') : 
					x_lhs = x 
				if rhs in x.getAttr('VarName') :
					x_rhs = x
			assert x_lhs is not None
			assert x_rhs is not None
			c = None
			if cond == '<' :
				c = ( [], self.model.addConstr( x_lhs <= x_rhs ) )
				self.constraints.append(c)
				goal_constraints.append( len(self.constraints)-1 )
				
				c = ( [], self.model.addConstr( x_lhs <= x_rhs - 1 ) )
				self.constraints.append(c)
				goal_constraints.append( len(self.constraints)-1 )
			elif cond == '>' :
				c = ( [], self.model.addConstr( x_lhs >= x_rhs ) )
				self.constraints.append(c)
				goal_constraints.append( len(self.constraints)-1 )

				c = ( [], self.model.addConstr( x_lhs - 1 >= x_rhs ) )
				self.constraints.append(c)
				goal_constraints.append( len(self.constraints)-1 )

			elif cond == '=' :
				c = ( [], self.model.addConstr( x_lhs == x_rhs ) )
				self.constraints.append(c)
				goal_constraints.append( len(self.constraints)-1 )

			else :
				assert False

		self.model.update()
		self.goal_constraints = set(goal_constraints)
		return self.goal_constraints
