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
        self.sas_task = translate.pddl_to_sas(task, cna = False)
        self.create_vars()
        self.create_actions()

    def create_vars(self):
        # create primary state variables mirroring the SAS task
        self.vars = []
        self.derived = []
        self.primary_var_map = dict()
        self.secondary_var_map = dict()
        self.primary_literal_name = dict()
        self.derived_literal_name = dict()
        for i in range(len(self.sas_task.variables.ranges)):
            if self.sas_task.variables.axiom_layers[i] == -1:
                var_name = 'v' + str(i)
                #var_domain = self.sas_task.variables.value_names[i]
                var_domain = list(range(self.sas_task.variables.ranges[i]))
                self.vars.append(self.create_state_var( var_name, var_domain ))
                # sas_task var#i maps to a primary
                self.primary_var_map[i] = len(self.vars) - 1
                for j in var_domain:
                    self.primary_literal_name[(len(self.vars) - 1,j)] = self.sas_task.variables.value_names[i][j]
            else:
                # print("axioms in translated SAS task not supported")
                # self.sas_task.variables.dump()
                # raise RuntimeError("axioms in translated SAS task not supported")
                # this is a derived variable
                assert self.sas_task.variables.ranges[i] == 2, "non-binary derived variable: " + str(i) + " (" + str(self.sas_task.variables.dump()) + ")"
                default_value = self.sas_task.init.values[i]
                non_default_value = 1 - default_value
                var_name = 'v' + str(i)
                self.derived.append((var_name, default_value))
                self.secondary_var_map[i] = len(self.derived) - 1
                self.derived_literal_name[(len(self.derived) - 1, default_value)] = self.sas_task.variables.value_names[i][default_value]
                self.derived_literal_name[(len(self.derived) - 1, non_default_value)] = self.sas_task.variables.value_names[i][non_default_value]

    def create_actions(self):
        self.actions = [None for i in range(len(self.sas_task.operators))]
        for i in range(len(self.sas_task.operators)):
            o = self.sas_task.operators[i]
            if max([len(cond) for (_, _, _, cond) in o.pre_post]) > 0:
                print("conditional effects in translated SAS task not supported")
                o.dump()
                raise RuntimeError("conditional effects in translated SAS task not supported")
            name = o.name.replace(' ', '_')
            ppre = [(self.primary_var_map[var], pre)
                    for (var, pre, _, _) in o.pre_post
                    if (var in self.primary_var_map) and (pre != -1)] + \
                [(self.primary_var_map[var], pre)
                 for (var, pre) in o.prevail
                 if var in self.primary_var_map]
            spre = [(self.secondary_var_map[var], pre)
                    for (var, pre) in o.prevail
                    if var in self.secondary_var_map]
            eff = [(self.primary_var_map[var], post)
                   for (var, _, post, _) in o.pre_post]
            self.actions[i] = Action(name, ppre, spre, eff)

    # some convenience methods
    def str_primary_condition(self, conds):
        '''
        conds is an iterable of (var, val) pairs; vars are all primary.
        '''
        return ', '.join([ self.primary_literal_name[c] for c in conds ])
            
    
def make_initial_state(task):
    pairs = []
    for i in range(len(task.sas_task.variables.ranges)):
        if i in task.primary_var_map:
            pairs.append((task.primary_var_map[i], task.sas_task.init.values[i]))
    # print(pairs)
    # for var in task.vars:
    #     print(var.index, var.name, var.domain)
    return State(task, pairs)

def make_primary_goal(task):
    pairs = [(task.primary_var_map[var], val)
             for (var, val) in task.sas_task.goal.pairs
             if var in task.primary_var_map]
    return pairs

def make_secondary_goal(task):
    pairs = [([], (task.secondary_var_map[var], val))
             for (var, val) in task.sas_task.goal.pairs
             if var in task.secondary_var_map]
    return pairs
