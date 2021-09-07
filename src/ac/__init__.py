from ac.planning import SASTask, make_initial_state, make_primary_goal, make_secondary_goal
from ac.lp import Axioms
from model.generic.planning.task import State
from model.generic.hybrid.task import HybridTask

import logging

def create_task( domain_file, problem_file ):
    the_task = SASTask( domain_file, problem_file )
    s0 = make_initial_state( the_task )
    Gp = make_primary_goal( the_task )
    if len(the_task.derived) > 0:
        the_LP = Axioms( the_task )
        Gs = the_LP.goal_constraints
    else:
        logging.info('task has no derived variables - omitting secondary model')
        the_LP = None
        Gs = set()
    return HybridTask( the_task, the_LP, s0, Gp, Gs )
