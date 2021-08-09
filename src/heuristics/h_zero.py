from .heuristic_base                 import        Heuristic

# This is a really basic blind heuristic, which always returns
# zero. A cleverer version would return zero only for goal states,
# and min action cost for other states.
class H_Zero( Heuristic ) :

        def __init__( self, the_task ) :
                self.name = 'h_{zero}'

        def __call__( self, node ) :
            return 0
