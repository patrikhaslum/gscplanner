#
# This file is part of pyperplan.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

"""
Implements the A* (a-star) and weighted A* search algorithm.
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
    f = node.g + h
    return (f, h, node_tiebreaker, node)


def ordered_node_weighted_astar(weight):
    """
    Creates an ordered search node (basically, a tuple containing the node
    itself and an ordering) for weighted A* search (order: g+weight*h).

    @param weight The weight to be used for h
    @param node The node itself
    @param h The heuristic value
    @param node_tiebreaker An increasing value to prefer the value first
                           inserted if the ordering is the same
    @returns A tuple to be inserted into priority queues
    """
    """
    Calling ordered_node_weighted_astar(42) actually returns a function (a
    lambda expression) which is the *actual* generator for ordered nodes.
    Thus, a call like
        ordered_node_weighted_astar(42)(node, heuristic, tiebreaker)
    creates an ordered node with weighted A* ordering and a weight of 42.
    """
    return lambda node, h, node_tiebreaker: \
        (node.g + weight * h, h, node_tiebreaker, node)


def ordered_node_greedy_best_first(node, h, node_tiebreaker):
    """
    Creates an ordered search node (basically, a tuple containing the node
    itself and an ordering) for greedy best first search (the value with lowest
    heuristic value is used).

    @param node The node itself.
    @param h The heuristic value.
    @param node_tiebreaker An increasing value to prefer the value first
                           inserted if the ordering is the same.
    @returns A tuple to be inserted into priority queues.
    """
    f = h
    return (f, h, node_tiebreaker, node)

def ordered_node_greedy_best_first_g_tie_breaking(node, h, node_tiebreaker):
    """
    Creates an ordered search node (basically, a tuple containing the node
    itself and an ordering) for greedy best first search (the value with lowest
    heuristic value is used).

    @param node The node itself.
    @param h The heuristic value.
    @param node_tiebreaker An increasing value to prefer the value first
                           inserted if the ordering is the same.
    @returns A tuple to be inserted into priority queues.
    """
    f = h
    return (node.h, node.g, node_tiebreaker, node)


def greedy_best_first_search(task, heuristic, use_relaxed_plan=False):
    """
    Searches for a plan in the given task using greedy best first search.

    @param task The task to be solved.
    @param heuristic A heuristic callable which computes the estimated steps
                     from a search node to reach the goal.
    """
    return astar_search(task, heuristic, ordered_node_greedy_best_first_g_tie_breaking,
                        use_relaxed_plan)


def greedy_best_first_search_g_tie_breaking(task, heuristic, use_relaxed_plan=False):
    """
    Searches for a plan in the given task using greedy best first search.

    @param task The task to be solved.
    @param heuristic A heuristic callable which computes the estimated steps
                     from a search node to reach the goal.
    """
    return astar_search(task, heuristic, task.compute_successor_state, ordered_node_greedy_best_first_g_tie_breaking,
                        use_relaxed_plan)

def weighted_astar_search(task, heuristic, weight=5, use_relaxed_plan=False):
    """
    Searches for a plan in the given task using A* search.

    @param task The task to be solved.
    @param heuristic  A heuristic callable which computes the estimated steps.
                      from a search node to reach the goal.
    @param weight A weight to be applied to the heuristics value for each node.
    """
    return astar_search(task, heuristic, ordered_node_weighted_astar(weight),
                        use_relaxed_plan)


def astar_state_sampling( task, heuristic, max_fn, sample_size ) :
	"""
	Samples states in the heuristic search cone
	
	@param task 		The task defining the state model
	@param heuristic 	The heuristic to be used
	"""
	import random

	open = []
	state_cost = {task.initial_state: 0}
	node_tiebreaker = 0
	
	root = searchspace.make_root_node(task.initial_state)
	root.g = 0
	root.tie = node_tiebreaker
	init_h = heuristic(root)
	root.h = init_h
	heapq.heappush(open, ordered_node_astar(root, init_h, node_tiebreaker))
	
	besth = float('inf')
	counter = 0
	expansions = 0

	witnesses = []
	
	while open:
		(f, h, _tie, pop_node) = heapq.heappop(open)
		if pop_node.g > max_fn : continue
		pop_state = pop_node.state
		# Only expand the node if its associated cost (g value) is the lowest
		# cost known for this state. Otherwise we already found a cheaper
		# path after creating this node and hence can disregard it.
		if state_cost[pop_state] == pop_node.g:
			expansions += 1

			if random.randint(0,  max_fn ) > pop_node.g :
				witnesses.append( ( pop_node, h ) )
				sample_size -= 1
				if sample_size == 0 : return witnesses # we're done

			if task.goal_reached(pop_state):
				continue

			for op, succ_state in task.get_successor_states(pop_state):
				succ_node = searchspace.make_child_node(pop_node, op,
								succ_state)
				h = heuristic(succ_node)
				if h == float('inf'):
					# don't bother with states that can't reach the goal anyway
					continue
				old_succ_g = state_cost.get(succ_state, float("inf"))
				if succ_node.g < old_succ_g:
					# We either never saw succ_state before, or we found a
					# cheaper path to succ_state than previously.
					node_tiebreaker += 1
					succ_node.tie = node_tiebreaker
					succ_node.h = h
					heapq.heappush(open, ordered_node_astar(succ_node, h, node_tiebreaker))
					state_cost[succ_state] = succ_node.g
					

		counter += 1

	return witnesses

def astar_search(task, heuristic, succ_fn = None, make_open_entry=ordered_node_astar,
                 use_relaxed_plan=False, mute=False):
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
	state_cost = {task.initial_state: 0}
	node_tiebreaker = 0
	
	root = searchspace.make_root_node(task.initial_state)
	root.g = 0
	root.tie = node_tiebreaker
	init_h = heuristic(root)
	root.h = init_h
	heapq.heappush(open, make_open_entry(root, init_h, node_tiebreaker))
	
	if not mute :
		logging.info("Initial h value: %f" % init_h)
	
	besth = float('inf')
        maxf = root.g + root.h
	counter = 0
	expansions = 0
	heuristic.num_calls = 1
	
	while open:
		(f, h, _tie, pop_node) = heapq.heappop(open)
                if f > maxf:
                    maxf = f
                    logging.info("f = %f, nodes = %d" % (maxf, expansions))
		if pop_node.h < besth:
			besth = pop_node.h
			logging.debug("Found new best h: %d after %d expansions" %
				(besth, counter))
		pop_state = pop_node.state
		# Only expand the node if its associated cost (g value) is the lowest
		# cost known for this state. Otherwise we already found a cheaper
		# path after creating this node and hence can disregard it.
		if state_cost[pop_state] == pop_node.g:
			expansions += 1

			if task.goal_reached(pop_state):
				if not mute :
					logging.info("Goal reached. Start extraction of solution.")
                                        logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, heuristic.num_calls))
					# logging.info("%d Nodes expanded" % expansions)
				return pop_node.extract_solution()
			rplan = None
			if use_relaxed_plan:
				(rh, rplan) = heuristic.calc_h_with_plan(
							searchspace.make_root_node(pop_state))
				if not mute :
					logging.debug("relaxed plan %s " % rplan)

			for op, succ_state in task.get_successor_states(pop_state):
				if use_relaxed_plan:
					if rplan and not op.name in rplan:
						# ignore this operator if we use the relaxed plan
						# criterion
						if not mute :
							logging.debug('removing operator %s << not a '
							'preferred operator' % op.name)
						continue
					else:
						if not mute :
							logging.debug('keeping operator %s' % op.name)

				succ_node = searchspace.make_child_node(pop_node, op,
								succ_state)
				h = heuristic(succ_node)
                                heuristic.num_calls += 1

				if h == float('inf'):
					# don't bother with states that can't reach the goal anyway
					continue
				old_succ_g = state_cost.get(succ_state, float("inf"))
				if succ_node.g < old_succ_g:
					# We either never saw succ_state before, or we found a
					# cheaper path to succ_state than previously.
					node_tiebreaker += 1
					succ_node.tie = node_tiebreaker
					succ_node.h = h
					heapq.heappush(open, make_open_entry(succ_node, h,
										node_tiebreaker))
					state_cost[succ_state] = succ_node.g

		counter += 1

	if not mute :
		logging.info("No operators left. Task unsolvable.")
                logging.info("{0} Nodes expanded, {1} Nodes evaluated".format (expansions, heuristic.num_calls))
	return None
