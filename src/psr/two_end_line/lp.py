from gurobipy		import 	Model, GRB, quicksum

class LinearProgram :
	
	def __init__( self, psr_task = None ) :
		if psr_task is None :
			return
		self.model = Model( psr_task.instance_name + '.lp' )

		# LP variables
		self.variables = [] # was all_variables
		self.make_model_vars( psr_task )
		self.model.update()

		# LP Constraints
		self.constraints = []
		self.make_model_constraints( psr_task )
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
		

	def __make_power_vars( self, task ) :
		for cb in task.network.TECircuitbreakerLines :
			# it is always zero
			# NOTE: if it always zero, this should simplify some constraints - and this variable should
			# not be in the model
			cb.power = self.model.addVar( name='p_{0}'.format( cb.name ), lb=0.0, ub=0.0, vtype=GRB.CONTINUOUS ) 

		for r_line in task.network.TERDeviceLines :
			r_line.power = self.model.addVar( name='p_{0}'.format( r_line.name ), lb=-r_line.capacity, ub=r_line.capacity, vtype = GRB.CONTINUOUS )
		
		for m_line in task.network.TEMDeviceLines :
			m_line.power = self.model.addVar( name='p_{0}'.format( m_line.name ), lb=-m_line.capacity, ub=m_line.capacity, vtype=GRB.CONTINUOUS )

		for bus in task.network.TEBuses :
                        lb_fed = 1.0 if ((bus.generation_max > 0) and not bus.fault) else 0.0
			bus.fed = self.model.addVar( name='b_{0}_fed'.format( bus.name ), lb = lb_fed, ub = 1.0, vtype = GRB.CONTINUOUS )
			bus.generation = self.model.addVar( name='b_{0}_gen'.format( bus.name ), lb = 0.0, ub = bus.generation_max, vtype = GRB.CONTINUOUS )
                        # theta is an angle, so it should be bounded by a full circle
                        # assuming unit is degrees, that is, between -180 and +180
			bus.theta = self.model.addVar( name='b_{0}_theta'.format( bus.name ), lb = -180.0, ub = 180.0, vtype = GRB.CONTINUOUS )
                #self.model.setObjective(quicksum([bus.generation for bus in task.network.TEBuses]), GRB.MAXIMIZE)

	def make_model_vars( self, task ) :
		self.__make_power_vars( task )	

	def __make_kirchoff_constraints( self, task ) :
		
		for bus in task.network.TEBuses :
			c = self.model.addConstr( 	bus.generation + quicksum( [ l.power for l in bus.connections_in ] ),
							GRB.EQUAL,
							bus.load_max * bus.fed + quicksum( [ l.power for l in bus.connections_out ] ) )
			#c = self.model.addConstr( 	bus.generation + quicksum( [ l.power for l in bus.connections_in ] )
			#				- bus.load_max * bus.fed + quicksum( [ -l.power for l in bus.connections_out ] )
			#				== 0.0 ) 
			self.constraints.append( ( [], c ) )

	# Corresponds with TEcreate_default_goal
	def make_bus_feeding_constraints( self, task ) :
		bus_feeding_constraints = []
		for bus in task.network.TEBuses :
			if bus.fault :
				c = self.model.addConstr( bus.fed, GRB.EQUAL, 0.0 )
				self.constraints.append( ( [], c ) )
				bus_feeding_constraints.append( len(self.constraints)-1 )
			else :
				if bus.generation_max > 0.0 : # is a generator
					c = self.model.addConstr( bus.fed, GRB.EQUAL, 1.0 )
					self.constraints.append( ( [], c ) )
					bus_feeding_constraints.append( len(self.constraints)-1 )
		self.model.update()
		print( 'Constraints in goal: {0}'.format( len(bus_feeding_constraints ) ) )
		self.goal_constraints = set(bus_feeding_constraints)
		return self.goal_constraints

	# Corresponds with TEpowerlines_create_goal
	def  make_bus_feeding_constraints_2( self, task ) :
		bus_feeding_constraints = []
		for bus in task.network.TEBuses :
			if bus.fault :
				c = self.model.addConstr( bus.fed, GRB.EQUAL, 0.0 )
				self.constraints.append( ( [], c ) )
				#bus_feeding_constraints.append( len(self.constraints)-1 )
				continue
			if not bus.feed : continue
			c = self.model.addConstr( bus.fed, GRB.EQUAL, 1.0 )
			self.constraints.append( ( [], c ) )
			bus_feeding_constraints.append( len(self.constraints)-1 )
		self.model.update()
		print( 'Constraints in goal: {0}'.format( len(bus_feeding_constraints ) ) )
		#print( 'Constraints in self {0}, constraints in Gurobi obj {1}'.format( len(self.constraints), len(self.model.getConstrs()) ) ) 
		self.goal_constraints = set(bus_feeding_constraints)
		return self.goal_constraints

	def __make_line_constraints( self, task ) :
		
		for line in task.network.TERDeviceLines + task.network.TEMDeviceLines :
			c_dc_flow_model_closed = self.model.addConstr( line.power, GRB.EQUAL, -line.susceptance*( line.connections[0].theta - line.connections[1].theta ) )
			self.constraints.append( ( [ (line.closed.index, True) ], c_dc_flow_model_closed ) )
			c_dc_flow_model_open = self.model.addConstr( line.power, GRB.EQUAL, 0.0 )
			self.constraints.append( ( [ (line.closed.index, False ) ], c_dc_flow_model_open ) )
			c_bus_feeding_state = self.model.addConstr( line.connections[0].fed, GRB.EQUAL, line.connections[1].fed )
			#c_bus_feeding_state = self.model.addConstr( line.connections[0].fed - line.connections[1].fed == 0.0 )
			self.constraints.append( ( [ (line.closed.index, True ) ], c_bus_feeding_state ) )

	def __make_circuit_breaker_constraints( self, task ) :
		
		for breaker in task.network.TECircuitbreakerLines :
			c_if_closed_always_fed = self.model.addConstr( breaker.connections[0].fed, GRB.EQUAL, 1.0 )
			self.constraints.append( ( [ (breaker.closed.index, True) ], c_if_closed_always_fed ) )
			c_if_open_not_fed = self.model.addConstr( breaker.connections[0].fed, GRB.EQUAL, 0.0 )
			self.constraints.append( ( [ (breaker.closed.index, False) ], c_if_open_not_fed ) )
			# March 2015: This follows from Sylvie's IJCAI-13 paper on PSR
			# see constraints on circuit breakers			
			if_open_kill_gen_in_connected_bus = self.model.addConstr( breaker.connections[0].generation, GRB.EQUAL, 0.0 )
			self.constraints.append( ( [ (breaker.closed.index, False) ], if_open_kill_gen_in_connected_bus ) )

	def make_model_constraints( self, task ) :
		self.__make_kirchoff_constraints( task )
		self.__make_line_constraints( task )
		self.__make_circuit_breaker_constraints( task )
		#self.make_bus_feeding_constraints( task )
		
	def print_constraints (self):
		for phi, gamma in self.constraints:
			if len(phi) == 0 : 
				print( ' True -> %s'%gamma )
			else :
				head = ' & '.join( [ '%s = %s'%(x,v) for x,v in phi ] )
				print ( ' %s -> %s'%( head, gamma ) )
