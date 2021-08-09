"""
This module implements the techniques for PDB construction outlined in the paper:

Domain-Independent Construction of Pattern Database Heuristics for Cost-Optimal Planning
P. Haslum, A. Botea, M. Helmert, B. Bonet, S. Koenig
Proceedings of AAAI, 2007
"""
import sys
import logging

import time

#TIMER_FUN = time.clock
TIMER_FUN = time.time


def         select_initial_patterns( in_task ) :
        """
        Selects the initial set of patterns as per AAAI-07, with the twist
        that when the primary goal is empty, we consider all pairs of state
        variables as the set of initial patterns.
        """

        if len( in_task.Gp ) == 0 : 
                from itertools import combinations
                V = in_task.task.state_vars
                signatures = []
                num_entries = []
                k = 0
                increment = 5
                while k < len(V) :
                        signature = range(k, min( len(V), k + increment) )
                        signatures.append( signature )
                        entries = 1
                        for x in signature :
                                entries *= V[x].domain_size()
                        num_entries.append( entries )
                        k += increment
                return signatures, num_entries

        signatures = []
        num_entries = []
        for X, _ in in_task.Gp :
                signatures.append( set([ X ]) )
                num_entries.append( len( in_task.task.state_vars[X].domain ) )
        
        return signatures, num_entries


def         evaluate_over_witnesses( h, witness_collection ) :

        score = 0

        for n, prev_h_value in witness_collection :
                new_h_value = h(n)
                if new_h_value > prev_h_value : score += 1
        return score

def         iPDB( in_task, max_num_entries ) :
        from heuristics.projections        import project_hybrid_over_vars
        from heuristics.pdb.pattern        import Table
        from heuristics.pdb                import Canonical_Heuristic_Function
        from search.a_star                import astar_state_sampling        

        t0 = TIMER_FUN()
        pattern_signatures, pattern_num_entries = select_initial_patterns(in_task)
        
        total_num_entries = sum(pattern_num_entries)

        if total_num_entries > max_num_entries :
                logging.info( 'Num entries ({0}) after initial pattern selection, exceeds the limit ({1})!'.format( total_num_entries, max_num_entries ) )
                sys.exit(1)

        logging.info( 'PDB construction: iPDB (Haslum, 2007)' )

        pattern_collection = []
        new_pattern_signature_list = []
        for k, pattern_signature in enumerate( pattern_signatures ) :
                logging.info( 'Pattern #{0}, signature size: {1}, # entries: {2}'.format( k, len(pattern_signature), pattern_num_entries[k] ) )
                #logging.info( 'Pattern #{0}: {1}'.format( k, pattern_signature ) )
                p_var_names = [ in_task.task.state_vars[i].name for i in pattern_signature ]
                logging.info( 'Pattern #{0}: {1}, {2}'.format( k, pattern_signature, p_var_names ) )
                p_k = Table( pattern_signature )
                p_k.build_relevant_action_set( in_task.actions )
                projected_task, vars_maps, actions_maps = project_hybrid_over_vars( in_task, pattern_signature )
                p_k.populate( projected_task, vars_maps, actions_maps )
                if p_k.max_value == 0 :
                        logging.info( 'Pattern with signature {0} rejected, max h^P() is 0' )
                        #pattern_collection.append(None)
                        continue
                pattern_collection.append( p_k )
                new_pattern_signature_list.append( pattern_signature )
        pattern_signatures = new_pattern_signature_list

        logging.info( 'Number of initial patterns: {0} ({1})'.format( len(pattern_collection), len(pattern_signature) ) )

        h = Canonical_Heuristic_Function( in_task, [p for p in pattern_collection if p is not None] )

        logging.info( '# of additive subsets in heuristic: {0}'.format( len(h.additive_subsets) ) )                

        h_s0, _ = h.evaluate( in_task.prim_s0 )
        logging.info( 'h(s0) = {0}'.format( h_s0 ) )
        witnesses = astar_state_sampling( in_task, h, h_s0 * 2, 100 )
        logging.info( 'Witnesses collected: {0}'.format( len(witnesses) ) )
        
        cutoff_value = h_s0 * 1.1 # minimum improvement is a 10%

        task_variables = set( range(0, len(in_task.task.state_vars)) )

        while True :
                candidates = []
                # for each pattern
                for k, pattern_signature in enumerate(pattern_signatures) :
                        if pattern_collection[k] is None : continue
                        from copy import copy
                        pattern_signature = set(pattern_signature)
                        # initial candidates for pattern extension
                        ext_0 = task_variables - pattern_signature
                        if len(ext_0) == 0 : continue
                        # filter causally disconnected variables
                        ext_1 = ext_0 & pattern_collection[k].relevant_vars
                        if len(ext_1) == 0 : continue
                        logging.info( 'Candidates for pattern extension: {0}'.format( ext_1 ) )
                        for x in ext_1 :
                                # check space limits
                                new_pattern_size = pattern_num_entries[k] * in_task.task.state_vars[x].domain_size()
                                new_database_size = total_num_entries + new_pattern_size - pattern_num_entries[k]
                                if new_database_size > max_num_entries : # pattern becomes too big
                                        logging.info( 'Space requirements surpassed' )
                                        continue
                                new_pattern_signature = copy(pattern_signature)
                                new_pattern_signature.add(x)
                                new_pattern = Table( new_pattern_signature )
                                new_pattern.build_relevant_action_set( in_task.actions )
                                projected_task, vars_maps, actions_maps = project_hybrid_over_vars( in_task, pattern_signature )
                                new_pattern.populate_informed( projected_task, vars_maps, actions_maps, Canonical_Heuristic_Function( in_task, [ pattern_collection[k] ] ) )
                                if new_pattern.max_value == 0 :
                                        logging.info( 'new pattern does not contribute any information to the heuristic' )
                                        # useless pattern
                                        continue
                                new_pattern_collection = [ pattern for l, pattern in enumerate( pattern_collection ) if l != k ]
                                new_pattern_collection.append( new_pattern )
                                
                                new_h = Canonical_Heuristic_Function( in_task, new_pattern_collection )
                                new_h_s0, _ = new_h.evaluate( in_task.prim_s0 )
                                score = evaluate_over_witnesses( new_h, witnesses )
                                logging.info( 'Score: {0}'.format(score) ) 
                                if  score > 0 :
                                        candidates.append( ( score, new_h_s0, k, new_pattern_signature, new_pattern_size, new_pattern, new_pattern_collection, new_h ) )
                if len(candidates) == 0 :
                        logging.info( 'PDB construction finished!')
                        break
                logging.info( 'New pattern added, prev. value of h(s0) = {0}'.format( h_s0) )
                score, h_s0, index,  new_pattern_signature, new_pattern_size, new_pattern, new_pattern_collection, new_h = max(candidates)
                cutoff_value = h_s0 * 1.1
                logging.info( 'Pattern score: {0}, new value for h(s0) ={1}, cutoff = {2}'.format( score, h_s0, cutoff_value ) )
                pattern_signatures[index] = new_pattern_signature
                pattern_num_entries[index] = new_pattern_size
                pattern_collection = new_pattern_collection
                h = new_h
                witnesses = astar_state_sample( in_task, h, h_s0 * 2, 100 )
                logging.info( 'Witnesses collected: {0}'.format( len(witnesses) ) )

        t1 = TIMER_FUN()
        logging.info( 'iPDB construction time: {0}'.format( t1 - t0 ) )
        return h
