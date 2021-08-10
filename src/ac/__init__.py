from ac.planning import SASTask, make_initial_state, make_goal
from ac.lp import Mirror, AvoidConditionModel
from model.generic.planning.task import State
from model.generic.hybrid.task import HybridTask

def create_task( domain_file, problem_file ):
    the_task = SASTask( domain_file, problem_file )
    s0 = make_initial_state( the_task )
    G = make_goal( the_task )
    the_LP = Mirror( the_task, AvoidConditionModel )
    return HybridTask( the_task, the_LP, s0, G )
