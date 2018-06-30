from model.generic.planning.task	import	Task, State
from model.generic.planning.actions	import	Action

class TwoEndLinePSRTask( Task ) :

	def __init__(self, power_network):
		Task.__init__( self, 'Two-End Line PSR', power_network.name )
		self.network = power_network	
		self.create_vars()
		self.create_actions()

	def create_vars( self ) :

		for circuit_breaker in self.network.TECircuitbreakerLines :
			circuit_breaker.closed = self.create_bool_state_var( '{0}_switch'.format( circuit_breaker.name ) )

		for r_dev in self.network.TERDeviceLines :
			r_dev.closed = self.create_bool_state_var( '{0}_switch'.format( r_dev.name ) )

		for m_dev in self.network.TEMDeviceLines :
			m_dev.closed = self.create_bool_state_var( '{0}_switch'.format( m_dev.name ) )

	def create_open_action( self, device ) :
		# Open action
		name = 'Open_{0}'.format( device.name )
		preconditions = [ (device.closed.index, True ) ]
		effects = [ (device.closed.index, False ) ]
		self.actions.append( Action( name, preconditions, [], effects ) )
	
	def create_close_action( self, device ) :
		name = 'Close_{0}'.format( device.name )	
		precondition = [ ( device.closed.index, False ) ]
		effects = [ ( device.closed.index, True ) ]
		self.actions.append( Action( name, precondition, [], effects ) )

	def create_actions( self ) :
		self.actions = []
		for r_dev in self.network.TECircuitbreakerLines + self.network.TERDeviceLines :
			#if r_dev.start_closed and not r_dev.final_closed :
			self.create_open_action( r_dev )
			#elif not r_dev.start_closed and r_dev.final_closed :
			self.create_close_action( r_dev )

		#for m_dev in self.network.TEMDeviceLines :
		#	self.create_open_action( m_dev )
		#	self.create_close_action( m_dev )

def make_initial_state( task ) :
	valuation = dict( task.default_valuation() ) # needs to be a full one!

	for switch in task.network.TECircuitbreakerLines + task.network.TERDeviceLines + task.network.TEMDeviceLines :
		valuation[ switch.closed.index ] = switch.start_closed

	return State( task, [ (x,v) for x,v in valuation.iteritems() ] )	
