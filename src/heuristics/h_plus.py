from .heuristic_base                                import        Heuristic
from .simple_rpg                                        import        RelaxedPlanningGraph

import sys

# Try importing gurobi: if it doesn't work, set flag and fall back on pulp.
# This doesn't work with fake gurobi, so when using that set flag to True.
_tmp_use_pulp = False
try:
        from gurobipy                                import         Model, GRB, quicksum
        if GRB.VERSION == 'Fake':
                _tmp_use_pulp = True
except ImportError:
        _tmp_use_pulp = True
except AttributeError:
        pass

if _tmp_use_pulp:
        import pulp

import logging
import time
import sys
import heapq

#TIMER_FUN = time.clock
TIMER_FUN = time.time

xrange = range

class H_Plus( Heuristic ) :
        _use_pulp = _tmp_use_pulp

        def __init__( self, the_task ) :
                self.task = the_task
                
                self.L = [] # landmark collection
                self.A = set() # minimum-cost hitting set <- that's the relaxed plan
                self.zero_cost_actions = set()
                for i in range(len(self.task.actions)):
                        if self.task.actions[i].cost == 0:
                                self.zero_cost_actions.add(i)
                self.name = 'h+'
                self.reachability_time = 0
                self.goal_reached_time = 0
                self.add_next_layer_time = 0
                self.hitting_set_time = 0
                self.total_time = 0
                ## extra stats (basic alg. only):
                self.n_calls = 0
                self.n_landmarks = 0
                self.n_rpg_tests = 0
                self.sum_rpg_size = 0
                ## following variables control how the function behaves
                self.compute_pref_ops = False
                self.emulate_lm_cut = False
                self.no_change_threshold = None

        def print_statistics( self ) :
                logging.info( 'h+ heuristic: Total time: {0}'.format( self.total_time ) )
                logging.info( 'h+ heuristic: Reachability time: {0}'.format( self.reachability_time ) )
                logging.info( 'h+ heuristic: Reachability: Goal reached testing time: {0}'.format( self.goal_reached_time ) )
                logging.info( 'h+ heuristic: Reachability: Add layer to planning graph time: {0}'.format( self.add_next_layer_time ) )
                logging.info( 'h+ heuristic: Hitting Set time: {0}'.format( self.hitting_set_time ) )
                logging.info( '{0} calls to h+'.format( self.n_calls ) )
                logging.info( '# of landmarks: {0}'.format( self.n_landmarks ) )
                logging.info( '# of RPG calls: {0}'.format( self.n_rpg_tests ) )
                if self.n_rpg_tests > 0:
                        logging.info( 'avg. RPG depth: {0}'.format( float(self.sum_rpg_size) / float(self.n_rpg_tests) ) )


        def reset( self ) :
                self.rpg_builder.reset()
                self.L = []
                self.A = set()
                self.lb = 0
                if self.curr_model is not None :
                        del self.curr_model
                self.curr_model = self.base_model.copy()

        def __build_base_model_for_hitting_set( self ) :
                if self._use_pulp:
                        self.base_model = pulp.LpProblem( "min-cost-hitting-set", pulp.LpMinimize )
                else:
                        self.base_model = Model( "min-cost-hitting-set" )
                        self.base_model.setParam( "OutputFlag", 0 )
                
                # variables -> one per action
                self.hs_vars = []
                self.hs_coeffs = {}
                for idx in xrange( len(self.task.actions) ) :
                        var_name = 'a_%d'%idx
                        if self._use_pulp:
                                self.hs_vars.append( pulp.LpVariable( var_name, 0, 1, cat = 'Integer' ) )
                        else:
                                self.hs_vars.append( self.base_model.addVar( name=var_name, vtype=GRB.BINARY ) )
                        self.hs_coeffs[ var_name ] = self.task.actions[idx].cost
                if not self._use_pulp:
                        self.base_model.update()

                # objective functions
                if self._use_pulp:
                        obj = 0
                        for var in self.hs_vars:
                                obj = (self.hs_coeffs[var.getName()] * var) + obj
                        self.base_model.setObjective(obj)
                else:
                        # MRJ: Support for non-unit costs, makes heuristic admissible if there are action costs
                        self.base_model.setObjective( quicksum( self.hs_coeffs[a.getAttr('VarName')] * a for a in self.hs_vars ), GRB.MINIMIZE )
                        # MRJ: Assumes action have unit costs, makes heuristic inadmissible if there are action costs
                        #self.base_model.setObjective( quicksum( a for a in self.hs_vars ), GRB.MINIMIZE )
                        self.base_model.update()

        def __update_hitting_set_model( self, disj_landmark ) :
                #logging.debug( 'New constraint {0}'.format( disj_landmark ) )
                if self._use_pulp:
                        constr = (sum([self.hs_vars[index] for index in disj_landmark]) >= 1)
                        self.curr_model.addConstraint( constr )
                else:
                        self.curr_model.addConstr( quicksum( self.curr_model.getVars()[index] for index in disj_landmark ) >= 1 )


        def __new_landmark( self, s, A ) :
                self.n_landmarks += 1
                candidates = self.all_actions - A
                passed = A.copy()
                goal_reached = self.__is_goal_reachable( s, passed )
                assert goal_reached is False
                prev_last_layer = self.rpg_builder.f_layers[-1].copy()        
                #print( '# Candidates:  {0} Passed: {1}'.format( len(candidates), len(passed) ) )        
                for idx in candidates :
                        if prev_last_layer.possible( self.task.actions[idx].prim_precs ) :
                                passed.add(idx)
                                goal_reached = self.__is_goal_reachable( s, passed )
                                if goal_reached :
                                        passed.remove(idx)
                                        continue
                                prev_last_layer = self.rpg_builder.f_layers[-1].copy()
                        else :
                                passed.add(idx)

                n = self.all_actions - passed
                return n

        def __min_cost_hitting_set( self ) :
                t0 = TIMER_FUN()
                if self._use_pulp:
                        #print(self.curr_model)
                        status = self.curr_model.solve()
                        assert status == 1
                else:
                        self.curr_model.update()
                        #logging.debug( 'Min-Cost Hitting Set: |X|={0}, |C|={1}'.format( len(self.curr_model.getVars()), len(self.curr_model.getConstrs())) )
                        self.curr_model.optimize()
                        assert self.curr_model.status == 2
                self.A = set()
                self.lb = 0
                if self._use_pulp:
                        for index, var in enumerate(self.hs_vars) :
                                if pulp.value(var) == 1.0 :
                                        self.A.add( index )
                                        self.lb += self.task.actions[index].cost
                                else:
                                        assert pulp.value(var) is None or pulp.value(var) == 0.0, str(pulp.value(var))
                else:
                        curr_vars = self.curr_model.getVars()
                        for index in xrange( len(curr_vars) ) :
                                if curr_vars[index].x :
                                        self.A.add( index )
                                        self.lb += self.task.actions[index].cost
                #logging.debug( 'Length of relaxed plan: {0}'.format( len(self.A) ) )
                assert len(self.A) > 0
                if not self._use_pulp:
                        self.curr_model.reset()
                tf = TIMER_FUN()
                self.hitting_set_time += (tf - t0 )

        def __extend_current_hitting_set( self ) :
                best_action = None
                best_cost = float('inf')
                for a_index in self.L[-1] :
                        a_i_cost = self.task.actions[ a_index ].cost
                        if a_i_cost < best_cost :
                                best_action = a_index
                                best_cost = a_i_cost
                return self.A | set( [ best_action ] ) # all actions assumed to have the same cost

        def __chvatal_weighted_degree_heuristic_algorithm( self ) :
                H = set()
                unhit = set( [ i for i in xrange(len(self.L)) ] )
                while len(unhit) != 0 :
                        heap = []
                        for j in unhit :
                                landmark = self.L[j]
                                for a_idx in landmark :
                                        hits = set( [ i for i in unhit if a_idx in self.L[i]  ] )
                                        heapq.heappush( heap, ( len(unhit) - len(hits), ( hits, a_idx ) ) )
                        _, best = heapq.heappop( heap )
                        assert len(best[0]) > 0
                        unhit -= best[0]
                        H.add( best[1] )
                return H

        def __compute_cost( self, action_set ) :
                cost = 0
                for a_idx in action_set :
                        cost += self.task.actions[ a_idx ].cost
                return cost

        def __approximate_hitting_set( self ) :

                H_a = self.__extend_current_hitting_set()
                cost_H_a = self.__compute_cost( H_a )
                #logging.debug( 'Greedy Hitting Set extension: {0}, cost={1}'.format( H_a, cost_H_a ) )
                H_b = self.__chvatal_weighted_degree_heuristic_algorithm()
                cost_H_b = self.__compute_cost( H_b )
                #logging.debug( 'Chvatal Hitting Set : {0}, cost={1}'.format( H_b, cost_H_b ) )
                if cost_H_a > cost_H_b :
                        return H_b
                return H_a

        def __improved_algorithm( self, node ) :
                t0 = TIMER_FUN()
                L_union = self.zero_cost_actions.copy()
                while not self.__is_goal_reachable( node.state, L_union ) :
                        new_disjunctive_landmark = self.__new_landmark( node.state, L_union )
                        L_union |= new_disjunctive_landmark
                        self.L.append( new_disjunctive_landmark )
                        self.__update_hitting_set_model( self.L[-1] )

                self.__min_cost_hitting_set( ) 
                self.A |= self.zero_cost_actions
                i = 1
                #logging.debug( 'Improved Iterative Landmark Algorithm: 1st pass: , |L|={1}, |A|={2}, lb = {3}'.format(i, len(self.L), len(self.A), self.lb) )
                if self.emulate_lm_cut : return False
                while not self.__is_goal_reachable( node.state, self.A ) :
                        #self.lb = self.__compute_cost(self.A)
                        #logging.debug( 'Improved Iterative Landmark Algorithm: iteration #{0}: , |L|={1}, |A|={2}, lb = {3}'.format(i, len(self.L), len(self.A), self.lb) )
                        self.L.append( self.__new_landmark( node.state, self.A ) )
                        self.__update_hitting_set_model( self.L[-1] )
                        H = self.__approximate_hitting_set()
                        if self.__is_goal_reachable( node.state, self.A | H ) :
                                self.A = H | self.zero_cost_actions
                        else :
                                self.A |= H
                        if self.__is_goal_reachable( node.state, self.A ) :
                                self.__min_cost_hitting_set()
                                self.A |= self.zero_cost_actions
                        #logging.debug( 'Relaxed Plan' )
                        #for idx in self.A :
                        #        logging.debug( '\t{0}'.format( self.task.actions[idx].name ) )
                        i += 1
                tf = TIMER_FUN()
                self.total_time += tf - t0
                #logging.debug( 'Improved Iterative Landmark Algorithm: Finished after {0} iterations, |L|={1}, |A|={2}'.format(i, len(self.L), len(self.A)) )
                #logging.debug( 'Improved Iterative Landmark Algorithm: {0} secs'.format( tf - t0 ) )
                #logging.debug( 'Improved Iterative Landmark Algorithm: Reachability Time {0} secs'.format( self.reachability_time ) )
                #logging.debug( 'Improved Iterative Landmark Algorithm: Hitting Set Time {0} secs'.format( self.hitting_set_time ) )
                return False

        def __basic_algorithm( self, node ) :
                t0 = TIMER_FUN()
                i = 1
                last_rp_cost = 0
                its_with_no_change = 0
                self.A |= self.zero_cost_actions
                while not self.__is_goal_reachable( node.state, self.A ) :
                        #logging.debug( 'Basic Iterative Landmark Algorithm: iteration #{0}: , |L|={1}, |A|={2}, lb = {3}'.format(i, len(self.L), len(self.A), self.lb) )
                        new_landmark = self.__new_landmark( node.state, self.A )
                        if len(new_landmark) == 0 : return True 
                        self.L.append( new_landmark )
                        #logging.debug( 'Basic Iterative Landmark Algorithm: iteration #{0}: , #actions in new landmark: {1}'.format( i, len(self.L[-1]) ) )
                        self.__update_hitting_set_model( self.L[-1] )
                        self.__min_cost_hitting_set()
                        rp_cost = self.__compute_cost( self.A )
                        if rp_cost > last_rp_cost:
                                last_rp_cost = rp_cost
                                its_with_no_change = 0
                        else:
                                its_with_no_change += 1
                        if self.no_change_threshold != None:
                                if its_with_no_change >= self.no_change_threshold:
                                        break
                        self.A |= self.zero_cost_actions
                        #logging.debug( 'Relaxed Plan' )
                        #for idx in self.A :
                        #        logging.debug( '\t{0}'.format( self.task.actions[idx].name ) )
                        #logging.debug( 'Basic Iterative Landmark Algorithm: iteration #{0}: '.format( i ) )
                        i += 1
                        #if i > 1 : sys.exit(0)
                tf = TIMER_FUN()
                self.total_time += tf - t0
                #logging.debug( 'Basic Iterative Landmark Algorithm: Finished after {0} iterations, |L|={1}, |A|={2}'.format(i, len(self.L), len(self.A)) )
                #logging.debug( 'Basic Iterative Landmark Algorithm: Total {0} secs'.format( tf-t0 ) )
                #logging.debug( 'Basic Iterative Landmark Algorithm: Reachability Time {0} secs'.format( self.reachability_time ) )
                #logging.debug( 'Basic Iterative Landmark Algorithm: Hitting Set Time {0} secs'.format( self.hitting_set_time ) )
                return False

        def __is_goal_reachable( self, s, A ) :
                t0 = TIMER_FUN()
                self.rpg_builder.reset()
                self.rpg_builder.set_available_actions( A )
                res = self.rpg_builder.build_graph( s )
                tf = TIMER_FUN()
                self.reachability_time += tf - t0
                self.n_rpg_tests += 1;
                self.sum_rpg_size += len(self.rpg_builder.f_layers);
                return res

        def evaluate( self, node ) :
                self.n_calls += 1
                self.all_actions = frozenset( [ i for i in xrange( len(self.task.actions) ) ] )
                self.rpg_builder = RelaxedPlanningGraph( self.task )
                self.base_model = None
                self.curr_model = None
                self.__build_base_model_for_hitting_set()

                self.reset()
                try :
                        L_parent = node.parent.landmarks
                        self.L = [ l for l in L_parent if node.action.index not in l ]
                except AttributeError :
                        pass
                dead_end = self.__basic_algorithm( node )
                #dead_end = self.__improved_algorithm( node )
                #self.__improved_algorithm( node )
                if dead_end :
                        h = float('inf')
                        node.h = h
                        node.preferred_ops = []
                        node.preferred_ops_counter = 0
                        self.goal_reached_time += self.rpg_builder.goal_reached_time
                        self.add_next_layer_time += self.rpg_builder.add_next_layer_time
                        return h

                h = 0
                for idx in self.A :
                        h += self.task.actions[idx].cost
                node.landmarks = [ l for l in self.L ]
                node.h = h                

                if self.compute_pref_ops : 
                        node.preferred_ops = [ self.task.actions[idx] for idx in self.A if self.task.is_applicable( node.state, self.task.actions[idx] ) ]
                        node.preferred_ops_counter = 0
                self.goal_reached_time += self.rpg_builder.goal_reached_time
                self.add_next_layer_time += self.rpg_builder.add_next_layer_time

                return h

        def __call__( self, node ) :
                return self.evaluate(node)

        # def __call__( self, node ) :
        #         v2 = self.evaluate(node)
        #         RelaxedPlanningGraph.meticulous = True
        #         v1 = self.evaluate(node)
        #         RelaxedPlanningGraph.meticulous = False
        #         print "v1 =", v1, ", v2 =", v2, str(node.state.primary), [act.name for act in node.extract_solution() ]
        #         if v2 > v1:
        #                 print "ERROR: ", v2, ">", v1
        #                 node.state.write(self, sys.stdout)
        #                 sys.exit(0)
        #         return v1


        def calc_h_with_plan( self, node ) :
                h = self.__call__(node)
                return h, [ self.task.actions[idx].name for idx in self.A ]

        def print_relaxed_plan( self ):
                for idx in self.A :
                        print( self.task.actions[idx].name )
