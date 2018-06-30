from gurobipy		import 	Model, GRB, quicksum

## linear program for a linehaul instance

class LinearProgram :
	
	def __init__( self, task = None ) :

		if task is None:
			return

                self.task = task
	
		self.model = Model( task.instance_name + '.lp' )

		# LP variables
		self.variables = [] # was all_variables
		self.make_model_vars( task )
		self.model.update()

		# LP Constraints
		self.constraints = []
		self.make_model_constraints( task )
		self.model.update()

		self.goal_constraints = set( range(self.first_goal_constraint, len(self.constraints)) )
		#self.model.write( 'tmp.lp' )

 	def copy( self ) :
		from copy import deepcopy

		new_lp = LinearProgram( )
		new_lp.model = self.model.copy()
		new_lp.constraints = []
		for index, ext_constraint in enumerate(self.constraints) :
			new_lp.constraints.append( ( deepcopy(ext_constraint[0]), new_lp.model.getConstrs()[index] ) )
		new_lp.first_goal_constraint = self.first_goal_constraint
		new_lp.goal_constraints = set( range (new_lp.first_goal_constraint, len(new_lp.constraints)) )
		return new_lp

	def make_model_vars( self, task ) :
		# vars are x_{v,l,t} for vehicle v, (non-depot) location l
		# and goods type t in {ambient, chilled}; if the vehicle
		# is non-refridgerated, only t = ambient should be created.
		
		self.varindex = {}
		for (vname, _, cap, chilled) in task.vehicles:
			for loc in task.locations[1:]:
				varname = 'x_{0}_{1}_ambient'.format(vname, loc)
				x = self.model.addVar(vtype = GRB.CONTINUOUS, 
						      name = varname,
						      lb = 0.0,
						      ub = cap)
                                self.variables.append(x)
				self.varindex[(vname, loc, 'ambient')] = x
				if chilled:
					varname = 'x_{0}_{1}_chilled'.format(vname, loc)
					x = self.model.addVar(vtype = GRB.CONTINUOUS, 
							      name = varname,
							      lb = 0.0,
							      ub = cap)
                                        self.variables.append(x)
					self.varindex[(vname, loc, 'chilled')] = x


	def get_all_variables (self):
		return self.variables

	def get_all_constraints (self):
		return self.constraints

	def make_model_constraints (self, task):
		self.constraints = []

		# vehicle capacity constraints: sum of allocations
		# to all locations and goods types must be within
		# vehicle capacity.
		for (vname, _, cap, chilled) in task.vehicles:
			avars = [ self.varindex[(vname, loc, 'ambient')] for loc in task.locations[1:] ]
			if chilled:
				avars += [ self.varindex[(vname, loc, 'chilled')] for loc in task.locations[1:] ]
			c = self.model.addConstr( quicksum( avars ), GRB.LESS_EQUAL, float(cap) )
			constraint = ( [], c )
			self.constraints.append( constraint )

		# switched constraints:
		# visited[v,l] = False -> x_v_l_{a,c} = 0,
		# for all v and l
		for (vname, _, _, chilled) in task.vehicles:
			for loc in task.locations[1:]:
				var = task.visited[(vname, loc)]
				trigger = [ ( var.index, False ) ]
				constraint = ( trigger, self.model.addConstr( self.varindex[(vname, loc, 'ambient')], GRB.EQUAL, 0.0) )
				self.constraints.append(constraint)
				if chilled:
					constraint = ( trigger, self.model.addConstr( self.varindex[(vname, loc, 'chilled')], GRB.EQUAL, 0.0) )
					self.constraints.append(constraint)

		# goal constraints
		self.first_goal_constraint = len(self.constraints)
		for loc in task.locations[1:]:
			(qc, qa) = task.demand[loc]
			avars = []
			cvars = []
			for (vname, _, _, chilled) in task.vehicles:
				avars.append(self.varindex[ (vname, loc, 'ambient') ])
				if chilled:
					cvars.append(self.varindex[ (vname, loc, 'chilled') ])
			c = self.model.addConstr( quicksum( avars ), GRB.EQUAL, float(qa) )
                        #print(loc, c, qa)
			self.constraints.append( ( [], c ) )
			c = self.model.addConstr( quicksum( cvars ), GRB.EQUAL, float(qc) )
                        #print(loc, c, qc)
			self.constraints.append( ( [], c ) )


	def print_constraints (self):
		for index,(phi, gamma) in enumerate(self.constraints):
			if len(phi) == 0 : 
				print( index, ' True -> %s'%gamma )
			else :
				head = ' & '.join( [ '%s = %s'%(self.task.state_vars[x].name,v) for x,v in phi ] )
				print ( index, ' %s -> %s'%( head, gamma ) )
