from __future__ import absolute_import
from model.generic.planning.task import Task, State
from model.generic.planning.actions import Action, ConditionalCost

class SGTPSRTask(Task):

    def __init__( self, network, sdac = None ):
        Task.__init__(self, 'SGT_PSR', 'SGT_PSR_NETWORK')
        self.network = network 
        self.network.find_total_load()
        print("Total load:", self.network.total_load)
        self.create_vars()
        self.objective_function = None
        self.conditional_costs = []
        if sdac=="Valuation": 
            self.create_conditional_costs() 
        elif sdac=="Objective": 
            self.objective_function = "PSRObjective"
        self.create_actions() 
        
    def create_conditional_costs(self): #a conditional cost associated with every bus  
        for bus in self.network.buses: 
            self.conditional_costs.append( ConditionalCost ( secondary_condition=[(bus.secondary_variable_i,False)],  
                                                             ccost=bus.p) ) 

    def create_vars(self):
        # Primary variables only here: just the breakers.
        for branch in self.network.branches:
            branch.closed = self.create_bool_state_var(branch.name)

    def create_open_action(self, branch):
        name = 'Open_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, True)]
        effects = [(branch.closed.index, False)]
        #print name, " conditional costs: ", self.conditional_costs
        self.actions.append(Action(name, preconditions, [], effects, cost = 0.1, conditional_costs = self.conditional_costs, of_vname = self.objective_function ))

    def create_close_action(self, branch):
        name = 'Close_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, False)]
        effects = [(branch.closed.index, True)]
        #print name, " conditional costs: ", self.conditional_costs 
        self.actions.append(Action(name, preconditions, [], effects, cost = 0.1, conditional_costs = self.conditional_costs, of_vname = self.objective_function ))

    def create_actions(self):
        self.actions = []
        for branch in self.network.branches:
            self.create_open_action(branch)
            self.create_close_action(branch)

def make_initial_state(task):
    valuation = dict(task.default_valuation()) # needs to be a full one!

    for branch in task.network.branches:
        valuation[branch.closed.index] = branch.init_closed

    return State(task, [(x,v) for x,v in valuation.iteritems()])
