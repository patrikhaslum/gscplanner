"""
Implements the Preferred Partial A* (a-star) algorithm.
"""

import heapq
import logging

from search import searchspace


def ordered_node_astar(node, h, node_tiebreaker):
    """
    Creates an ordered search node (basically, a tuple containing the node
    itself and an ordering) for A* search.

    @param node The node itself.
    @param heuristic A heuristic function to be applied.
    @param node_tiebreaker An increasing value to prefer the value first
                           inserted if the ordering is the same.
    @returns A tuple to be inserted into priority queues.
    """
    node.f = node.g + h
    return (node.f, h, node_tiebreaker, node)


def tie_breaking_function( node ) :
        if node.preferred_ops_counter < len(node.preferred_ops) : return 0
        return 1

def check_duplicate( s, pending, closed ) :
        n_prima = None
        in_open = False
        in_closed = False
        try :
                n_prima = pending[s]                                
                in_open = True
        except KeyError :
                try :
                        n_prima = closed[s]
                        in_closed = True
                except KeyError :
                        n_prima = None
        return ( in_open, in_closed, n_prima )
        

def new_state( succ_node, heuristic_fn, open_fn, open_list, open_hash, closed_list ) :

        # 1. does exist n' in open \cup closed s.t. state(n') = state
        in_open, in_closed, n_prima = check_duplicate( succ_node.state, open_hash, closed_list )
        
        if n_prima is None :
                h = heuristic_fn( succ_node )
                if h == float('inf' ) :
                        #logging.info( 'PrefPEA*: Successor has infinite heuristic value' ) 
                        return False
                heapq.heappush( open_list, open_fn( succ_node, h, tie_breaking_function(succ_node) ) )
                open_hash[ succ_node.state ] = succ_node
                logging.debug( 'PrefPEA*: Successor f={0}, h={1}, g={2}, s={3} got into OPEN via preferred operator'.format(succ_node.f, h, succ_node.g, str(succ_node.state.primary)) )
                return True

        if succ_node.g < n_prima.g : 
                n_prima.g = succ_node.g
                # update parent pointer
                n_prima.parent = succ_node.parent

                if in_closed : # if in closed, reopen
                        open_hash[ n_prima.state ] = n_prima
                        assert n_prima.state in open_hash
                        closed_list.pop( n_prima.state )
                        #heapq.heappush( open_list, open_fn( n_prima, n_prima.h, tie_breaking_function(n_prima) ) )
                        logging.info( 'Reopening node in closed: {0}'.format( n_prima.state ) )

                # whether in closed or not, the updated node needs to be re-inserted into open
                # to ensure it's in the right position
                heapq.heappush( open_list, open_fn( n_prima, n_prima.h, tie_breaking_function(n_prima) ) )
                return False

        return False


def pref_partial_astar_search(task, heuristic, succ_fn = None, make_open_entry=ordered_node_astar ):
        """
        Searches for a plan in the given task using A* search.
        
        @param task The task to be solved
        @param heuristic  A heuristic callable which computes the estimated steps
                          from a search node to reach the goal.
        @param make_open_entry An optional parameter to change the bahavior of the
                                   astar search. The callable should return a search
                                node, possible values are ordered_node_astar,
                                ordered_node_weighted_astar and
                                ordered_node_greedy_best_first with obvious
                                meanings.
        """
        if succ_fn is None :
                succ_fn = task.compute_successor_state
        open = []
        node_tiebreaker = 0
        
        root = searchspace.make_root_node(task.initial_state)
        init_h = heuristic(root)
        heapq.heappush(open, make_open_entry(root, init_h, tie_breaking_function(root)))
        logging.info("Initial h value: %f" % init_h)
        # try:
        #     heuristic.print_relaxed_plan()
        # except:
        #     pass
        pending = {task.initial_state: root}
        closed = {}

        if init_h == float('inf') :
                logging.info( 'Problem has no solution, h(s0) = infty' )
                return None

        besth = float('inf')
        maxf = root.g + root.h
        counter = 0
        expansions = 0

        while open:
                entry = heapq.heappop(open) # this is the best node in Open
                f, h, _tie, pop_node = entry
                check_f = pop_node.g + h
                if check_f < f:
                    # this node was re-inserted with a lower f-value, so it has already
                    # been expanded.
                    continue
                elif check_f > f:
                    logging.info( 'PrefPEA*: ASSERT FAIL! f={0}, h={1}, g={2}, po(n)={3}, s={4}, n={5}'.format( f, h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter, str(pop_node.state.primary), [act.name for act in pop_node.extract_solution() ] ) )
                assert check_f <= f
                #assert pop_node.state in pending        
                pending.pop( pop_node.state ) 
                if f > maxf:
                    maxf = f
                    logging.info("f = %d, nodes = %d" % (maxf, expansions))
                if h < besth:
                        besth = h
                        logging.debug("Found new best h: %d after %d evaluations" %
                                        (besth, counter))

                pop_state = pop_node.state
                if h == float('inf') :
                        # Remove from open
                        closed[ pop_state ] = pop_node        
                        continue        

                if task.goal_reached(pop_state):
                        logging.info("Goal reached. Start extraction of solution.")
                        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, counter))
                        return pop_node.extract_solution()
                
                logging.debug( 'PrefPEA*: Expanding f={0}, h={1}, g={2}, po(n)={3}, s={4}, n={5}'.format( f, h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter, str(pop_node.state.primary), [act.name for act in pop_node.extract_solution() ] ) )
                
                if pop_node.preferred_ops_counter < len( pop_node.preferred_ops ) :
                        # get next preferred operator, and increase the counter
                        action = pop_node.preferred_ops[ pop_node.preferred_ops_counter ]
                        pop_node.preferred_ops_counter += 1
                        
                        # generate successor (expensive!)
                        succ_state = succ_fn( pop_state, action )
                        if succ_state is None :
                                heapq.heappush( open, (f, h, _tie, pop_node) )
                                pending[ pop_state ] = pop_node
                                continue
                        logging.debug( 'Applying helpful action: {0} with cost: {1}'.format( action.name, action.cost ) ) 
                        succ_node = searchspace.make_child_node( pop_node, action, succ_state )
                        if new_state( succ_node, heuristic, make_open_entry, open, pending, closed ) :
                                counter += 1
                                #assert succ_node.state in pending
                        heapq.heappush( open, (f, h, _tie, pop_node) )
                        pending[ pop_state ] = pop_node
                        continue
                        
                for a in task.actions :
                        if a in pop_node.preferred_ops : continue
                        #logging.info( 'PrefPEA*: Generating successor through non-preferred op...' ) 
                        succ_state = succ_fn( pop_state, a )
                        if succ_state is None : 
                                continue
                        succ_node = searchspace.make_child_node( pop_node, a, succ_state )
                        if new_state( succ_node, heuristic, make_open_entry, open, pending, closed ) :
                                counter += 1
                                #assert succ_node.state in pending
                        
                # Remove from open
                logging.debug( 'PrefPEA*: closing f={0}, h={1}, g={2}, po(n)={3}, s={4}, n={5}'.format( pop_node.f, pop_node.h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter, str(pop_node.state.primary), [act.name for act in pop_node.extract_solution() ] ) )
                closed[ pop_state ] = pop_node        
                expansions += 1

        logging.info("No operators left. Task unsolvable.")
        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, counter))
        return None


###
# Delayed evaluation algorithm - don't know if this is correct
##

def new_state_delayed_evaluation( succ_node, heuristic_fn, open_fn, open_list, open_hash, closed_list ) :

        # 1. does exist n' in open \cup closed s.t. state(n') = state
        in_open, in_closed, n_prima = check_duplicate( succ_node.state, open_hash, closed_list )
        
        if n_prima is None :
                h = min( succ_node.parent.h - succ_node.action.cost, 0 )
                heapq.heappush( open_list, open_fn( succ_node, h, succ_node.g ) )
                open_hash[ succ_node.state ] = succ_node
                logging.debug( 'PrefPEA*: Successor f={0}, h={1} got into OPEN via preferred operator'.format(succ_node.f, h) )
                return True

        if succ_node.g < n_prima.g : 
                n_prima.g = succ_node.g
                # update parent pointer
                n_prima.parent = succ_node.parent
                        
                if in_closed : # if in closed, reopen
                        open_hash[ n_prima.state ] = n_prima
                        assert n_prima.state in open_hash
                        closed_list.pop( n_prima.state )
                        heapq.heappush( open_list, make_open_entry( n_prima, n_prima.h, n_prima.g ) )
                        logging.info( 'Reopening node in closed: {0}'.format( n_prima.state ) )
                return False

        return False

def pref_partial_astar_search_with_delayed_evaluation(task, heuristic, succ_fn = None, make_open_entry=ordered_node_astar ):
        """
        Searches for a plan in the given task using A* search.
        
        @param task The task to be solved
        @param heuristic  A heuristic callable which computes the estimated steps
                          from a search node to reach the goal.
        @param make_open_entry An optional parameter to change the bahavior of the
                                   astar search. The callable should return a search
                                node, possible values are ordered_node_astar,
                                ordered_node_weighted_astar and
                                ordered_node_greedy_best_first with obvious
                                meanings.
        """
        if succ_fn is None :
                succ_fn = task.compute_successor_state
        open = []
        node_tiebreaker = 0

        heuristic.num_calls = 0        
        root = searchspace.make_root_node(task.initial_state)
        root.evaluated = False
        heapq.heappush(open, make_open_entry(root, 0, 0))
        pending = {task.initial_state: root}
        closed = {}

        besth = float('inf')
        counter = 0
        expansions = 0

        while open:
                entry = heapq.heappop(open) # this is the best node in Open
                f, h, _tie, pop_node = entry
                #assert pop_node.state in pending        
                pending.pop( pop_node.state )

                if not pop_node.evaluated :
                        pop_node.evaluated = True
                        heuristic.num_calls += 1
                        h = heuristic( pop_node )        

                if h < besth:
                        besth = h
                        logging.debug("Found new best h: %d after %d evaluations" %
                                        (besth, counter))

                pop_state = pop_node.state
                if h == float('inf') :
                        # Remove from open
                        closed[ pop_state ] = pop_node        
                        continue        

                if task.goal_reached(pop_state):
                        logging.info("Goal reached. Start extraction of solution.")
                        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, heuristic.num_calls))
                        return pop_node.extract_solution()
                
                logging.debug( 'PrefPEA*: Expanding f={0}, h={1}, g={2}, po(n)={3}'.format( f, h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter ) )
                
                if pop_node.preferred_ops_counter < len( pop_node.preferred_ops ) :
                        # get next preferred operator, and increase the counter
                        action = pop_node.preferred_ops[ pop_node.preferred_ops_counter ]
                        pop_node.preferred_ops_counter += 1
                        
                        # generate successor (expensive!)
                        succ_state = succ_fn( pop_state, action )
                        if succ_state is None :
                                heapq.heappush( open, (f, h, _tie, pop_node) )
                                pending[ pop_state ] = pop_node
                                continue

                        succ_node = searchspace.make_child_node( pop_node, action, succ_state )
                        succ_node.evaluated = False
                        new_state_delayed_evaluation( succ_node, heuristic, make_open_entry, open, pending, closed )
                        heapq.heappush( open, (f, h, _tie, pop_node) )
                        pending[ pop_state ] = pop_node
                        continue
                        
                for a in task.actions :
                        if a in pop_node.preferred_ops : continue
                        #logging.info( 'PrefPEA*: Generating successor through non-preferred op...' ) 
                        succ_state = succ_fn( pop_state, a )
                        if succ_state is None : 
                                continue
                        succ_node = searchspace.make_child_node( pop_node, a, succ_state )
                        succ_node.evaluated = False
                        new_state_delayed_evaluation( succ_node, heuristic, make_open_entry, open, pending, closed )
                        
                # Remove from open
                logging.debug( 'PrefPEA*: closing f={0}, h={1}, g={2}, po(n)={3}'.format( pop_node.h, pop_node.h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter ) )
                closed[ pop_state ] = pop_node        
                expansions += 1

        logging.info("No operators left. Task unsolvable.")
        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, heuristic.num_calls))
        return None


###
# restarting algorithm - don't know if this is correct
##

def restarting_pref_partial_astar_search(task, heuristic, make_open_entry=ordered_node_astar ):
        """
        Searches for a plan in the given task using A* search.
        
        @param task The task to be solved
        @param heuristic  A heuristic callable which computes the estimated steps
                          from a search node to reach the goal.
        @param make_open_entry An optional parameter to change the bahavior of the
                                   astar search. The callable should return a search
                                node, possible values are ordered_node_astar,
                                ordered_node_weighted_astar and
                                ordered_node_greedy_best_first with obvious
                                meanings.
        """
        succ_fn = task.compute_successor_state_ngl_dyn_model
        open = []
        node_tiebreaker = 0
        
        root = searchspace.make_root_node(task.initial_state)
        init_h = heuristic(root)
        heapq.heappush(open, make_open_entry(root, init_h, tie_breaking_function(root)))
        logging.info("Initial h value: %f" % init_h)
        pending = {task.initial_state: root}
        closed = {}

        besth = float('inf')
        counter = 0
        expansions = 0

        while open:
                entry = open[0] # this is the best node in Open
                (f, h, _tie, pop_node) = entry                
                if h < besth:
                        besth = h
                        logging.debug("Found new best h: %d after %d evaluations" %
                                        (besth, counter))

                pop_state = pop_node.state
                if h == float('inf') :
                        # Remove from open
                        heapq.heappop( open )
                        pending.pop( pop_state )
                        closed[ pop_state ] = pop_node        
                        continue        

                if task.goal_reached(pop_state):
                        logging.info("Goal reached. Start extraction of solution.")
                        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, counter))
                        return pop_node.extract_solution(), False
                
                logging.debug( 'PrefPEA*: Expanding f={0}, h={1}, g={2}, po(n)={3}'.format( f, h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter ) )
                
                if pop_node.preferred_ops_counter < len( pop_node.preferred_ops ) :
                        # get next preferred operator, and increase the counter
                        action = pop_node.preferred_ops[ pop_node.preferred_ops_counter ]
                        pop_node.preferred_ops_counter += 1
                        
                        # generate successor (expensive!)
                        succ_state, needs_restart = succ_fn( pop_state, action )
                        if succ_state is None :
                                if needs_restart : return [], True
                                continue

                        succ_node = searchspace.make_child_node( pop_node, action, succ_state )
                        if new_state( succ_node, heuristic, make_open_entry, open, pending, closed ) :
                                counter += 1
                        continue
                        
                for a in task.actions :
                        if a in pop_node.preferred_ops : continue
                        #logging.info( 'PrefPEA*: Generating successor through non-preferred op...' ) 
                        succ_state, needs_restart = succ_fn( pop_state, a )
                        if succ_state is None : 
                                if needs_restart : return [], True
                                continue
                        succ_node = searchspace.make_child_node( pop_node, a, succ_state )
                        if new_state( succ_node, heuristic, make_open_entry, open, pending, closed ) :
                                counter += 1
                        
                # Remove from open
                logging.debug( 'PrefPEA*: closing f={0}, h={1}, g={2}, po(n)={3}'.format( pop_node.h, pop_node.h, pop_node.g, len(pop_node.preferred_ops)-pop_node.preferred_ops_counter ) )
                heapq.heappop( open )
                pending.pop( pop_state )
                closed[ pop_state ] = pop_node        
                expansions += 1

        logging.info("No operators left. Task unsolvable.")
        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, counter))
        return None, False

