from __future__ import absolute_import
from model.generic.planning.task import Task, State
from model.generic.planning.actions import Action, ConditionalCost

class SGTPSRUGTask(Task):

    def __init__(self, network, sdac = None):
        Task.__init__(self, 'SGT_PSR_UG', 'SGT_PSR_UG_NETWORK')
        self.network = network 
        self.network.find_total_load()
        self.plan_end_var = None
        self.create_vars()
        self.conditional_costs = [] 
        self.sdac_type = sdac
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
        self.plan_end_var = self.create_bool_state_var("EndActionUsed") 
        for branch in self.network.branches:
            branch.closed = self.create_bool_state_var(branch.name) 

    def create_open_action(self, branch):
        name = 'Open_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, True),(self.plan_end_var.index, False)]
        effects = [(branch.closed.index, False)]
        #print name, " conditional costs: ", self.conditional_costs
        self.actions.append(Action(name, preconditions, [], effects, cost = 0.1, conditional_costs = self.conditional_costs, 
                                   of_vname = self.objective_function ))

    def create_close_action(self, branch):
        name = 'Close_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, False),(self.plan_end_var.index, False)]
        effects = [(branch.closed.index, True)]
        #print name, " conditional costs: ", self.conditional_costs 
        self.actions.append(Action(name, preconditions, [], effects, cost = 0.1,  conditional_costs = self.conditional_costs, 
                                   of_vname = self.objective_function ))

    def create_actions(self):
        self.actions = []
        for branch in self.network.branches:
            self.create_open_action(branch)
            self.create_close_action(branch)
            # TODO: See ../README - Settle on what is right.
            # if branch.start_closed and not branch.final_closed:
            #     self.create_open_action(branch)
            # elif not branch.start_closed and branch.final_closed:
            #     self.create_close_action(branch) 
            
        #Eend action here. 
        end_preconditions = [ (self.plan_end_var.index, False) ]
        end_effects = [ (self.plan_end_var.index, True) ] 
        
        action_constant = 1
        end_conditional_costs = []
        constant = 2 ** len(self.network.branches)
        for bus in self.network.buses: 
            if self.sdac_type=="Objective": 
                action_constant = constant
            elif sdac=="Valuation": 
                end_conditional_costs.append( ConditionalCost ( secondary_condition=[(bus.secondary_variable_i,False)],  
                                                             ccost= constant * bus.p) ) 
        
        self.actions.append( Action( "End_plan", end_preconditions, [], end_effects, conditional_costs = end_conditional_costs,
                                     of_vname = self.objective_function, ep_constant = action_constant ) )

def make_initial_state(task):
    valuation = dict(task.default_valuation()) # needs to be a full one!

    for branch in task.network.branches:
        valuation[branch.closed.index] = branch.init_closed

    return State(task, [(x,v) for x,v in valuation.iteritems()])
