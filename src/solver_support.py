from         heuristics.h_max                import         H_Max
from         heuristics.h_plus                import         H_Plus
from         heuristics.h_zero                import         H_Zero

import  search

import logging
import time

#TIMER_FUN = time.clock
TIMER_FUN = time.time

def     log_plan( the_plan ) :
        logging.info( 'Plan Length: {0}'.format( len(the_plan) ) )
        total_cost = 0
        for index, action in enumerate(the_plan) :
                print( '{0}. {1} ({2})'.format( index+1, action.name, action.cost ) )
                total_cost += action.cost
        logging.info( 'Plan Cost: {0}'.format( total_cost ) )

def         solve_blind( task, search_fn, planner_name ) :
        
        start_time = TIMER_FUN()

        the_plan = search_fn( task )
        
        logging.info( 'Wall-clock {0} search time: {1:.4}'.format( planner_name, TIMER_FUN() - start_time ) )
        if the_plan is None :
                print( 'No solution found.' )
                return

        # logging.info( 'Plan Length: {0}'.format( len(the_plan) ) )        
        # for index, action in enumerate(the_plan) :
        #         print( '{0}. {1}'.format( index+1, action.name ) )
        log_plan( the_plan )

def         solve_restarting( task, search_fn, h, planner_name ) :

        start_time = TIMER_FUN()

        while True :
                the_plan, needs_restart = search_fn( task, h )
                if the_plan is None : break
                if needs_restart is False : break
        
        logging.info( 'Wall-clock {0} search time: {1:.4}'.format( planner_name, TIMER_FUN() - start_time ) )
        
        if the_plan is None :
                print( 'No solution found.' )
                return

        # logging.info( 'Plan Length: {0}'.format( len(the_plan) ) )        
        # for index, action in enumerate(the_plan) :
        #         print( '{0}. {1}'.format( index+1, action.name ) )
        log_plan( the_plan )
        return the_plan

def         solve_heuristic( task, search_fn, h, planner_name, succ_fn = None ) :
        start_time = TIMER_FUN()
        the_plan = search_fn( task, h, succ_fn )
        logging.info( 'Wall-clock {0} search time: {1:.4}'.format( planner_name, TIMER_FUN() - start_time ) )
        if the_plan is None :
                print( 'No solution found.' )
                return

        # logging.info( 'Plan Length: {0}'.format( len(the_plan) ) )        
        # for index, action in enumerate(the_plan) :
        #         print( '{0}. {1}'.format( index+1, action.name ) )
        log_plan( the_plan )
        #task.validate(the_plan)
        return the_plan

configs = [  'blind', 'iw_1', 'iw_2', 'bfs_f_1', 'bfs_f_2', 'a_star_h0', 'a_star_hmax', 'a_star_hmax_r1', 'a_star_hplus', 'a_star_hplus_r1', 'ppa_star_hplus', 'ppa_star_hplus_r1', 'ppa_star_hmax', 'ppa_star_hplus_ngl','ppa_star_hplus_ngl2', 'restarting_ppa_star_hplus',
                'delayed_eval_ppa_star_hplus', 'delayed_eval_ppa_star_hplus_ngl2', 'ppa_star_pdb_trivial', 'ppa_star_pdb_naive', 'ppa_star_pdb_haslum_aaai07', 'a_star_pdb_haslum_aaai07', 'ppa_star_pdb_haslum_aaai07_ngl',
                'ppa_star_pdb_haslum_aaai07_ngl2'   ]


def solve( configuration, task ) :
        delayed_evaluation = False
        if configuration == 'delayed_eval_ppa_star_hplus' :
                configuration = 'ppa_star_hplus'
                delayed_evaluation = True
        elif configuration == 'delayed_eval_ppa_star_hplus_ngl2' :
                configuration = 'ppa_star_hplus_ngl2'
                delayed_evaluation = True


        if configuration == 'blind' :
                solve_blind( task, search.breadth_first_search, 'Blind')
        elif 'iw_' in configuration :
                if configuration == 'iw_1' :
                        def IW1( task ) : return search.IW(task,1)
                        solve_blind( task, IW1, 'IW(1)' )
                elif configuration == 'iw_2' :
                        def IW2( task ) : return search.IW(task,2)
                        solve_blind( task, IW2, 'IW(2)' )
        elif 'bfs_f_' in configuration :
                from heuristics.novelty import Novelty_Table

                novelty_evaluator = Novelty_Table()
                if '1' in configuration:
                        novelty_evaluator.set_novelty_bound(1)        
                elif '2' in configuration :
                        novelty_evaluator.set_novelty_bound(2)

                def h_adapter( n ) :                
                        return novelty_evaluator.evaluate_novelty(n.state.primary)
                solve_heuristic( task, search.greedy_best_first_search_g_tie_breaking, h_adapter, 'BFS(f), novelty={0}'.format( novelty_evaluator.max_novelty ) )

        elif configuration == 'a_star_h0' :
                solve_heuristic( task, search.astar_search, H_Zero(task), 'A* (h_0)' )
        elif configuration == 'a_star_hmax' :
                solve_heuristic( task, search.astar_search, H_Max(task), 'A* (h_max)' )
        elif configuration == 'a_star_hmax_r1' :
                H_Max.meticulous = True
                solve_heuristic( task, search.astar_search, H_Max(task), 'A* (h_max)' )
        elif configuration == 'a_star_hplus' :
                hplus = H_Plus(task)
                hplus.compute_pref_ops = False
                solve_heuristic( task, search.astar_search, hplus, 'A* (h+)')
                hplus.print_statistics()
        elif configuration == 'a_star_hplus_r1' :
                from heuristics.simple_rpg import RelaxedPlanningGraph
                RelaxedPlanningGraph.meticulous = True
                hplus = H_Plus(task)
                hplus.compute_pref_ops = False
                solve_heuristic( task, search.astar_search, hplus, 'A* (h+)')
                hplus.print_statistics()

        elif configuration == 'ppa_star_hmax' :
                h = H_Max( task ) 
                solve_heuristic( task, search.pref_partial_astar_search, h, 'Pref. Partial A* (h_max)' )

        elif configuration == 'ppa_star_pdb_trivial' :
                from heuristics.pdb.trivial import trivial_partitioning
                pdb_h = trivial_partitioning( task ) 
                solve_heuristic( task, search.pref_partial_astar_search, pdb_h, 'Pref. Partial A* (Trivial Partitioning PDB)' )

        elif configuration == 'ppa_star_pdb_naive' :
                from heuristics.pdb.randomized import naive_partitioning                
                pdb_h = naive_partitioning( task, 10, 1024 )
                solve_heuristic( task, search.pref_partial_astar_search, pdb_h, 'Pref. Partial A* (Naive Partitioning PDB)' )

        elif configuration == 'ppa_star_pdb_haslum_aaai07' :
                from heuristics.pdb.haslum_aaai07 import iPDB
                pdb_h = iPDB( task, 10000 )
                #pdb_h.evaluate( task.s0.primary, True )
                solve_heuristic( task, search.pref_partial_astar_search, pdb_h, 'Pref. Partial A* (Haslum, 2007)' )
        elif configuration == 'a_star_pdb_haslum_aaai07' :
                from heuristics.pdb.haslum_aaai07 import iPDB
                pdb_h = iPDB( task, 10000 )
                solve_heuristic( task, search.astar_search, pdb_h, 'A* (Haslum, 2007)' )
        elif configuration == 'ppa_star_hplus' :
                hplus = H_Plus(task)
                hplus.compute_pref_ops = True
                if delayed_evaluation :
                        solve_heuristic( task, search.pref_partial_astar_search_with_delayed_evaluation, hplus,  'Pref. Partial A* (h+, delayed evaluation)')
                else :
                        solve_heuristic( task, search.pref_partial_astar_search, hplus, 'Pref. Partial A* (h+)')        
                hplus.print_statistics()
                #logging.info( '# Calls to optimize(): {0} Total Time: {1}'.format( HybridState.calls_to_optimize, HybridState.total_time_optimize) )
                #logging.info( '# Models created: {0} Total Time: {1}'.format( HybridState.models_created, HybridState.total_time_model_building ) )

        elif configuration == 'ppa_star_hplus_r1' :
                from model.generic.hybrid.state import HybridState
                from heuristics.simple_rpg import RelaxedPlanningGraph
                RelaxedPlanningGraph.meticulous = True
                hplus = H_Plus(task)
                hplus.compute_pref_ops = True
                solve_heuristic( task, search.pref_partial_astar_search, hplus, 'Pref. Partial A* (h+)')        
                hplus.print_statistics()
                #logging.info( '# Calls to optimize(): {0} Total Time: {1}'.format( HybridState.calls_to_optimize, HybridState.total_time_optimize) )
                #logging.info( '# Models created: {0} Total Time: {1}'.format( HybridState.models_created, HybridState.total_time_model_building ) )
        #
        elif configuration == 'ppa_star_pdb_haslum_aaai07_ngl' :
                from heuristics.pdb.haslum_aaai07 import iPDB
                pdb_h = iPDB( task, 10000 )
                solve_heuristic( task, search.pref_partial_astar_search, pdb_h, 'Pref. Partial A* (Haslum, 2007)', task.compute_successor_state_ngl )
                logging.info( 'No Good Learning: # Conflicts: {0}'.format( task.num_conflicts ) ) 
                logging.info( 'No Good Learning: # Pruned: {0}'.format( task.pruned_ngl ) )
                ng_lens = [ len(ng) for ng in task.no_good_list ]
                if len(ng_lens) == 0 :
                        biggest_no_good = smallest_no_good = 0
                else :
                        biggest_no_good = max( ng_lens )
                        smallest_no_good = min( ng_lens )
                logging.info( 'No Good Learning: # Lits in Biggest No Good {0} # Lits in Smallest No Good {1}'.format( biggest_no_good, smallest_no_good ) ) 
        elif configuration == 'ppa_star_pdb_haslum_aaai07_ngl2' :
                from heuristics.pdb.haslum_aaai07 import iPDB
                pdb_h = iPDB( task, 10000 )
                solve_heuristic( task, search.pref_partial_astar_search, pdb_h, 'Pref. Partial A* (Haslum, 2007)', task.compute_successor_state_ngl2 )

                logging.info( 'No Good Learning: # Conflicts: {0}'.format( task.num_conflicts ) ) 
                logging.info( 'No Good Learning: # Pruned: {0}'.format( task.pruned_ngl ) )
                ng_lens = [ len(ng[0]) for ng in task.no_good_list ]
                if len(ng_lens) == 0 :
                        biggest_no_good = smallest_no_good = 0
                else :
                        biggest_no_good = max( ng_lens )
                        smallest_no_good = min( ng_lens )
                logging.info( 'No Good Learning: # Lits in Biggest No Good {0} # Lits in Smallest No Good {1}'.format( biggest_no_good, smallest_no_good ) ) 

        elif configuration == 'ppa_star_hplus_ngl' :
                hplus = H_Plus(task)
                hplus.compute_pref_ops = True
                solve_heuristic( task, search.pref_partial_astar_search, hplus, 'Pref. Partial A* (h+)', task.compute_successor_state_ngl )
                hplus.print_statistics()        
                logging.info( 'No Good Learning: # Conflicts: {0}'.format( task.num_conflicts ) ) 
                logging.info( 'No Good Learning: # Pruned: {0}'.format( task.pruned_ngl ) )
                ng_lens = [ len(ng) for ng in task.no_good_list ]
                if len(ng_lens) == 0 :
                        biggest_no_good = smallest_no_good = 0
                else :
                        biggest_no_good = max( ng_lens )
                        smallest_no_good = min( ng_lens )
                logging.info( 'No Good Learning: # Lits in Biggest No Good {0} # Lits in Smallest No Good {1}'.format( biggest_no_good, smallest_no_good ) ) 
        elif configuration == 'ppa_star_hplus_ngl2' :
                hplus = H_Plus(task)
                hplus.compute_pref_ops = True
                if delayed_evaluation :
                        solve_heuristic( task, search.pref_partial_astar_search_with_delayed_evaluation, hplus,  'Pref. Partial A* (h+, delayed evaluation)', task.compute_successor_state_ngl2 )
                else :
                        solve_heuristic( task, search.pref_partial_astar_search, hplus, 'Pref. Partial A* (h+)', task.compute_successor_state_ngl2 )        
                hplus.print_statistics()
                logging.info( 'No Good Learning: # Conflicts: {0}'.format( task.num_conflicts ) ) 
                logging.info( 'No Good Learning: # Pruned: {0}'.format( task.pruned_ngl ) )
                ng_lens = [ len(ng[0]) for ng in task.no_good_list ]
                if len(ng_lens) == 0 :
                        biggest_no_good = smallest_no_good = 0
                else :
                        biggest_no_good = max( ng_lens )
                        smallest_no_good = min( ng_lens )
                logging.info( 'No Good Learning: # Lits in Biggest No Good {0} # Lits in Smallest No Good {1}'.format( biggest_no_good, smallest_no_good ) ) 
        elif configuration == 'restarting_ppa_star_hplus' :
                hplus = H_Plus(task)
                hplus.compute_pref_ops = True
                solve_restarting( task, search.restarting_pref_partial_astar_search, hplus, 'Restarting Pref. Partial A* (h+)' )
                hplus.print_statistics()        
                logging.info( 'No Good Learning: # Conflicts: {0}'.format( task.num_conflicts ) ) 
                logging.info( 'No Good Learning: # Actions Added: {0}'.format( task.num_actions_added ) )
        from model.generic.hybrid.state import HybridState
        logging.info( '# Calls to optimize(): {0} Total Time: {1}'.format( HybridState.calls_to_optimize, HybridState.total_time_optimize) )
        logging.info( '# Models created: {0} Total Time: {1}'.format( HybridState.models_created, HybridState.total_time_model_building ) )

