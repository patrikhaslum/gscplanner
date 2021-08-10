from __future__ import absolute_import
from model.generic.planning.task import Task, State
from model.generic.planning.actions import Action

## import from FD translator
import pddl_parser
import normalize
import translate

class SASTask(Task):

    def __init__(self, domain_file, problem_file):
        Task.__init__(self, 'PDDL_domain', 'PDDL_problem')
        task = pddl_parser.open(domain_filename=domain_file,
                                task_filename=problem_file)
        normalize.normalize(task)
        self.sas_task = translate.pddl_to_sas(task)
        self.create_vars()
        self.create_actions()

    def create_vars(self):
        # create primary state variables mirroring the SAS task
        self.vars = [None for i in range(len(self.sas_task.variables.ranges))]
        for i in range(len(self.sas_task.variables.ranges)):
            if self.sas_task.variables.axiom_layers[i] != -1:
                print("axioms in translated SAS task not supported")
                self.sas_task.variables.dump()
                raise RuntimeError("axioms in translated SAS task not supported")
            var_name = 'v' + str(i)
            #var_domain = self.sas_task.variables.value_names[i]
            var_domain = list(range(self.sas_task.variables.ranges[i]))
            self.vars[i] = self.create_state_var( var_name, var_domain )

    def create_actions(self):
        self.actions = [None for i in range(len(self.sas_task.operators))]
        for i in range(len(self.sas_task.operators)):
            o = self.sas_task.operators[i]
            if max([len(cond) for (_, _, _, cond) in o.pre_post]) > 0:
                print("conditional effects in translated SAS task not supported")
                o.dump()
                raise RuntimeError("conditional effects in translated SAS task not supported")
            name = o.name
            pre = [(var, pre) for (var, pre, _, _) in o.pre_post] + [(var, pre) for (var, pre) in o.prevail]
            eff = [(var, post) for (var, _, post, _) in o.pre_post]
            self.actions[i] = Action(name, pre, [], eff)

def make_initial_state(task):
    pairs = [(i, task.sas_task.init.values[i]) for i in range(len(task.vars))]
    # print(pairs)
    # for var in task.vars:
    #     print(var.index, var.name, var.domain)
    return State(task, pairs)

def make_goal(task):
    pairs = [(var, val) for (var, val) in task.sas_task.goal.pairs]
    return pairs
