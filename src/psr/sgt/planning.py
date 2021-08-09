from __future__ import absolute_import
from model.generic.planning.task import Task, State
from model.generic.planning.actions import Action

class SGTPSRTask(Task):

    def __init__(self, network):
        Task.__init__(self, 'SGT_PSR', 'SGT_PSR_NETWORK')
        self.network = network
        self.create_vars()
        self.create_actions()

    def create_vars(self):
        # Primary variables only here: just the breakers.
        for branch in self.network.branches:
            branch.closed = self.create_bool_state_var(branch.name)

    def create_open_action(self, branch):
        name = 'Open_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, True)]
        effects = [(branch.closed.index, False)]
        self.actions.append(Action(name, preconditions, [], effects))

    def create_close_action(self, branch):
        name = 'Close_{0}'.format(branch.name)
        preconditions = [(branch.closed.index, False)]
        effects = [(branch.closed.index, True)]
        self.actions.append(Action(name, preconditions, [], effects))

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

def make_initial_state(task):
    valuation = dict(task.default_valuation()) # needs to be a full one!

    for branch in task.network.branches:
        valuation[branch.closed.index] = branch.init_closed

    return State(task, [(x,v) for x,v in valuation.items()])
