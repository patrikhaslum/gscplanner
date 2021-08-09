from .heuristic_base                 import        Heuristic
from .simple_rpg                        import  RelaxedPlanningGraph 

xrange = range

class H_Max( Heuristic ) :

        def __init__( self, the_task ) :
                self.name = 'h_{max}'
                self.task = the_task
                # self.all_actions is an enumerable set of indices
                # into self.task.actions[]
                self.all_actions = frozenset( [ i for i in xrange( len( self.task.actions ) ) ] )


        def goal_reached( self, s ) :
                if not s.possible( self.task.Gp ) :
                        return False
                if self.task.Gs is not None:
                        result = self.task.check_secondary_goal( s )
                        return result
                return True


        def enqueue( self, action, acc_cost ):
                p = 0
                while p < len(self.queue):
                        (a, c) = self.queue[p]
                        if c <= acc_cost:
                                p += 1
                        else:
                                self.queue.insert( p, (action, acc_cost) )
                                return
                self.queue.append( (action, acc_cost) )


        def check_and_enqueue( self, pre_cost ):
                for idx in self.all_actions :
                        if not self.available[idx] :
                                continue
                        action = self.task.actions[idx]
                        if not self.rp_state.possible( action.prim_precs ) :
                                continue
                        if (len( action.sec_precs ) != 0):
                                if not self.task.check_secondary_precondition( self.rp_state, action ) :
                                        continue
                        self.available[idx] = False
                        self.enqueue( idx, pre_cost + action.cost )


        def dequeue_to_cost( self, cost ):
                changed = False
                while len(self.queue) > 0 :
                        (act_idx, act_cost) = self.queue[0]
                        if act_cost > cost:
                                return changed
                        for X, v in self.task.actions[act_idx].effect :
                                if not self.rp_state.possible( [ (X, v) ] ) :
                                        self.rp_state.relaxed_set( X, v )
                                        changed = True
                        self.queue.pop(0)
                return changed


        def __call__( self, node ) :
                node.preferred_ops = [ ]
                node.preferred_ops_counter = 0
                try:
                        self.rp_state = node.state.primary.copy()
                except AttributeError:
                        self.rp_state = node.state.copy()
                # from here on, rp_state is a relaxed, primary state.
                if self.goal_reached( self.rp_state ):
                        node.h = 0
                        return 0
                self.queue = []
                self.available = [ True for idx in self.all_actions ]
                if True in self.available:
                        self.check_and_enqueue( 0 )
                h_value = 0
                while len(self.queue) > 0:
                        changed = self.dequeue_to_cost( h_value )
                        if changed :
                                if self.goal_reached( self.rp_state ):
                                        node.h = h_value                
                                        return h_value
                                if True in self.available:
                                        self.check_and_enqueue( h_value )
                        if len(self.queue) > 0:
                                (act, cost) = self.queue[0]
                                h_value = cost
                node.h = float('inf')
                return float('inf')
