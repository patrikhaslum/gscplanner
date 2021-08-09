from model.generic.planning.task        import        State

import logging
import time

#TIMER_FUN = time.clock
TIMER_FUN = time.time

xrange = range

# Simple RPG - does not require to check satisfiability of the
# (projected) secondary model
class RelaxedPlanningGraph :
        # This is an option flag which controls whether the
        # rpg is built using the 1st (when True) or 2nd (False)
        # weaker relaxation. It is defined as a class variable
        # because h+ creates a new RPG builder on every call.
        meticulous = False
        
        def __init__( self, the_task ) :
                self.task = the_task
                self.all_actions = frozenset( [ i for i in xrange( len( self.task.actions ) ) ] ) # actions available 
                self.available = [ True for idx in self.all_actions ]
                self.reset()
                self.goal_reached_time = 0
                self.add_next_layer_time = 0

        def reset( self ) :
                self.a_layers = []
                self.f_layers = []
                self.h_a = {}  # dictionary mapping action preconditions to h-values
                self.h_f = {}  # dictionary mapping valuations (X = v) to h-values
                for idx in self.all_actions :
                        self.available[idx] = True
                self.changed = False

        def layer_saturated( self ) :
                return not self.changed 

        def goal_reached( self ) :
                t0 = TIMER_FUN()
                if len(self.f_layers) == 0 : 
                        self.goal_reached_time += TIMER_FUN() - t0
                        return False
                # check if last layer satisfies goal
                #print("Gp = {}".format(self.task.Gp))
                if not self.f_layers[-1].possible( self.task.Gp ) :
                        self.goal_reached_time += TIMER_FUN() - t0 
                        return False
                #print("Gs = {}".format(self.task.Gs))

                # In 1st weaker relaxation, check consistency of
                # invariant constraints with primary goal even if there
                # are no secondary goals:
                if self.task.Gs is not None or self.meticulous:
                        result = self.task.check_secondary_goal( self.f_layers[-1] )
                        self.goal_reached_time += TIMER_FUN() - t0
                        return result

                return True

        def set_available_actions( self, A=set() ) :
                for idx in self.all_actions :
                        self.available[idx] = False
                for idx in A :
                        self.available[idx] = True

        def build_graph( self, state ) :
                #logging.debug( 'Available actions: {0}'.format( len(self.available) ) )
                self.add_initial_layer( state )
                while  self.changed :
                        if self.goal_reached() : return True
                        self.add_next_layer()
                return self.goal_reached() 

        def add_initial_layer( self, state ) :
                t0 = TIMER_FUN()
                self.a_layers = [ set() ]
                self.f_layers = [ state.primary.copy() ]
                self.f_layers[0].relaxed = True
                for X, v in state.primary.iter_values() :
                        self.h_f[ (X,v) ] = 0
                #logging.debug( "h_max: initial layer, true facts: %d, reachable actions: %d"%(len(self.h_f.items()), len(self.h_a.items()) ) )
                self.changed = True
                self.add_next_layer_time += TIMER_FUN() - t0

        def add_initial_layer2( self, state ) :
                self.a_layers = [ set() ]
                self.f_layers = [ state.copy() ]
                for X, v in state.iter_values() :
                        self.h_f[ (X,v) ] = 0
                #logging.debug( "h_max: initial layer, true facts: %d, reachable actions: %d"%(len(self.h_f.items()), len(self.h_a.items()) ) )
                self.changed = True

        def add_next_layer( self ) :
                t0 = TIMER_FUN()
                self.changed = False
                applied_actions = set()
                for idx in self.all_actions :
                        if not self.available[idx] : continue
                        action = self.task.actions[idx]
                        if not self.f_layers[-1].possible( action.prim_precs ) :
                                continue
                        # In 1st weaker relaxation, check consistency of
                        # invariant constraints with primary prec even if
                        # there are no secondary precs:
                        if (len( action.sec_precs ) != 0) or self.meticulous:
                                if not self.task.check_secondary_precondition( self.f_layers[-1], action ) :
                                        continue
                        # and also check consistency with post-conditions
                        if self.meticulous:
                                if not self.task.check_postcondition_validity(self.f_layers[-1], action):
                                        continue
                        skip = False
                        for ng in self.task.no_good_list :
                                try :
                                        phi, j = ng
                                        if idx == j and self.f_layers[-1].satisfies( phi ) :
                                                skip = True
                                                break
                                except ValueError :
                                        tmp = self.f_layers[-1].copy()
                                        for X, v in self.task.actions[idx].effect :
                                                tmp.relaxed_set(X,v)
                                        if tmp.satisfies(ng) :
                                                skip = True
                                                break
                        if skip : continue
        
                        applied_actions.add( idx )
                        self.h_a[ idx ] = len(self.f_layers ) - 1
                self.a_layers.append( applied_actions )
                self.f_layers.append( self.f_layers[-1].copy() )
                self.f_layers[-1].relaxed = True
                self.last_values = []
                for idx in applied_actions :
                        self.available[idx] = False
                        for X, v in self.task.actions[idx].effect :
                                try :
                                        foo = self.h_f[ (X, v) ]
                                except KeyError :
                                        self.f_layers[-1].relaxed_set( X, v )
                                        self.h_f[ (X, v) ] = len(self.f_layers)-1
                                        self.last_values.append( (X,v) )
                                        self.changed = True
                self.add_next_layer_time += TIMER_FUN() - t0
                #logging.debug( "h_max: layer #%d, true facts: %d, reachable actions: %d"%(len(self.f_layers)-1,len(self.h_f.items()), len(self.h_a.items()) ) )
                        
        def print_graph(self):
                for lnum in range(len(self.f_layers)):
                        print("action layer {}:".format(lnum))
                        for idx in self.a_layers[lnum]:
                                print("  {}".format(self.task.actions[idx].name))
                        print("fact layer {}:".format(lnum))
                        #self.f_layers[lnum].print_relaxed()
                        for lit,val in self.h_f.items():
                                if val == lnum:
                                        X, v = lit
                                        print("  {} = {}".format(self.f_layers[lnum].task.state_vars[X].name, v))
