from	model.generic.planning.task	import	Task, State
from	model.generic.planning.actions	import	Action

class	CountersTask( Task ) :

	def __init__( self, counters, max_value ) :
		Task.__init__( self, 'Counters', 'Num-Counters-{0}-Max-Value-{1}'.format( len(counters), max_value ) )
		self.counters = counters
		self.max_value = int(max_value)
		self.counter_values = []
		self.create_vars()
		self.create_actions()

	def create_vars( self ) :
	
		for c in self.counters :
			x_c = self.create_state_var( 'X_{0}'.format( c ), range( 0, self.max_value + 1), 0 )
			self.counter_values.append( x_c )

	def create_actions( self ) :
		
		self.inc_actions_by_counter_and_value = {}
		self.dec_actions_by_counter_and_value = {}		

		for x in self.counter_values :
			for v in range( 0, self.max_value  ) :
				precondition = [ ( x.index, v ) ]
				effects	= [ (x.index, v+1) ]
				a = Action( 'inc-{0}-{1}'.format( x.name, v ), precondition, [], effects )
				self.actions.append( a )
				self.inc_actions_by_counter_and_value[ ( x.name, v ) ] = a
								

			for v in range( 1, self.max_value + 1 ) :
				precondition = [ ( x.index, v ) ]
				effects = [ ( x.index, v-1) ]
				a = Action( 'dec-{0}-{1}'.format( x.name, v ), precondition, [], effects )
				self.actions.append( a ) 
				self.dec_actions_by_counter_and_value[ ( x.name, v ) ] = a
	
def make_initial_state( task, initial_values ) :
	valuation = dict( task.default_valuation() )
	for c, v in initial_values :
		x = None
		for y in task.state_vars :
			if c in y.name :
				x = y
				break
		valuation[ x.index ] = v
	return State( task, [ (x,v) for x,v in valuation.iteritems() ] )	
