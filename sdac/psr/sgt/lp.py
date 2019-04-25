from model import Model
import copy

import sys

# This class is required to have a model, and constraints.
class LinearProgram(object):
    def __init__(self, psr_task = None):
        if psr_task is None :
            return

        self.total_load = psr_task.network.total_load
        self.model = Model(total_load = psr_task.network.total_load)
        self.variables = []
        self.constraints = []
        self.goal_constraints = set()

        self._add_variables(psr_task.network)
        self._add_constraints(psr_task.network)

    def copy(self) :
        # print 'psr.sgt.lp.copy is assumed not to be called.'
        # sys.exit()
        the_copy = LinearProgram()
        the_copy.model = self.model.copy()
        the_copy.variables = copy.deepcopy(self.variables)
        the_copy.constraints = copy.deepcopy(self.constraints)
        the_copy.goal_constraints = copy.deepcopy(self.goal_constraints)
        the_copy.total_load = self.total_load
        return the_copy

    def _add_variables(self, network):
        
        for bus in network.buses:  
            #print "Bus. Name ", bus.name, "final_require_fed:", bus.final_require_fed, "sVar_i", bus.secondary_variable_i, " p = ", bus.p 
            modelvar_i = self.model.addVar( bus.name, bus.secondary_variable_i )
            self.variables.append( modelvar_i ) 
                
    def _add_constraints(self, network):
        for branch in network.branches:
            # The "breaker" constraints are switched: that is, they are turned
            # on and off by a condition of the primary variables
            # 
            # Switched constraints: 
            # ([(primary_idx, trigger), ...], secondary constraint)
            # the list [(primary_idx, trigger), ...] is a conjunction of
            # primary conditions that need to hold. The constraint is a
            # model constraint that should hold if the trigger conditions apply.
            #
            # Add both "closed" and "open" constraints - corresponding to
            # switched constraints. At each iteration, one of these will be
            # removed by the hybrid solver.
            self._add_constraint([(branch.closed.index, True)], 
                                 (branch, True))
            self._add_constraint([(branch.closed.index, False)],
                                 (branch, False))

        # The goal constraints are only checked during goal evaluation.
        bus_feeding_constraints = []
        for bus in network.buses:
            if bus.final_require_fed == 1:
                self._add_constraint([], (bus, True))
                bus_feeding_constraints.append(len(self.constraints)-1)

        self.goal_constraints = set(bus_feeding_constraints)

    def _add_constraint(self, triggers, constr):
        self.constraints.append((triggers, constr))
        self.model.constraints.append(constr)
