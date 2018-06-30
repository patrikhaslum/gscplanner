from heuristic_base 		import	Heuristic
from simple_rpg			import  RelaxedPlanningGraph 

class H_Max( Heuristic ) :

	def __init__( self, the_task ) :
		self.name = 'h_{max}'
		self.rpg_builder = RelaxedPlanningGraph( the_task )

	def __call__( self, node ) :
		self.rpg_builder.reset()
		goal_reached = self.rpg_builder.build_graph( node.state )
		if not goal_reached : return float('inf') 
		return len(self.rpg_builder.f_layers)-1	
