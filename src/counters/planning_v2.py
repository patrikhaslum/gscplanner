from        model.generic.planning.task        import        Task, State
from        model.generic.planning.actions        import        Action

xrange = range

class        CountersTask( Task ) :

        def __init__( self, counters, max_value ) :
                Task.__init__( self, 'Counters', 'Num-Counters-{0}-Max-Value-{1}'.format( len(counters), max_value ) )
                self.counters = counters
                self.max_value = int(max_value)
                self.counter_values = { c : { k : None for k in xrange(0,self.max_value) } for c in self.counters }
                self.create_vars()
                self.create_actions()

        def create_vars( self ) :
                
                for c in self.counters :
                        for k in xrange(0,self.max_value) :
                                p_c_k = self.create_bool_state_var( 'p_{0}_{1}'.format( c, k ) )        
                                self.counter_values[c][k] = p_c_k

        def create_actions( self ) :
                for c in self.counters :
                        # counter actions
                        # inc(c,1)
                        precondition = [ (self.counter_values[c][0].index, True), ( self.counter_values[c][1].index, False ) ]
                        effect = [ (self.counter_values[c][1].index, True ) ]
                        a = Action( 'inc-{0}-{1}'.format( c, 1), precondition, [], effect )
                        self.actions.append( a )
                        #inc(c,k)
                        for k in xrange(2,self.max_value) :
                                precondition = [ (self.counter_values[c][k-1].index, True), (self.counter_values[c][k].index, False) ]
                                effect = [ (self.counter_values[c][k].index, True) ]
                                a = Action( 'inc-{0}-{1}'.format( c, k), precondition, [], effect )
                                self.actions.append( a )
                        #dec(c,max)
                        precondition = [ (self.counter_values[c][self.max_value-1].index, True) ]
                        effect = [ (self.counter_values[c][self.max_value-1].index, False ) ]
                        a = Action( 'dec-{0}-{1}'.format( c, self.max_value ), precondition, [], effect )
                        self.actions.append(a)
                        #dec(c,k)
                        for k in xrange( self.max_value-2, 0, -1) :
                                precondition = [ (self.counter_values[c][k+1].index, False), (self.counter_values[c][k].index, True) ]
                                effect = [ (self.counter_values[c][k].index, False ) ]
                                a = Action( 'dec-{0}-{1}'.format( c, k ), precondition, [], effect )
                                self.actions.append(a)
                                 
                
        
def make_initial_state( task, initial_values ) :
        valuation = dict( task.default_valuation() )
        for c, v in initial_values :
                for k in xrange( v, -1, -1) :
                        valuation[ task.counter_values[c][k].index ] = True
                for k in xrange( v+1, task.max_value ) :
                        valuation[ task.counter_values[c][k].index ] = False
        return State( task, [ (x,v) for x,v in valuation.items() ] )                                        
