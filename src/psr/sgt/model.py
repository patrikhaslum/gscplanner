import psr_client
import copy
import network

import json

# Model class should obey certain elements of the Gurobi Model interface.
# It should have the following:
#     status (1 = loaded (but not solved, 2 = optimal, 3+ = bad...
#     copy(self)
#     reset(self) -> Set status to 1, reset any variables necessary
#     remove(self, constraint)
#     getConstrs(self) -> list of constraints
#     getVars(self) -> list of variables 
#     numvars(self) -> number of variables 
#     update(self)
#     optimize(self) -> Optimize the problem, setting any variables
#         as necessary
class Model:
    def __init__(self):
        self.status = 1
        self.constraints = []
        self.variables = []

    # Needed for interface purposes - need to imitate the Gurobi interface.
    # Deep copy of constraints list, as we will be required to mutate the list
    # without affecting the original model.
    # Safest: make a full deep copy.
    def copy(self):
        result = Model()
        result.constraints = copy.deepcopy(self.constraints)
        result.variables = copy.deepcopy(self.variables)
        return result

    # Needed for interface purposes - need to imitate the Gurobi interface.
    def reset(self):
        self.status = 1
        self.variables = []
    
    # Needed for interface purposes - need to imitate the Gurobi interface.
    def getConstrs(self):
        return self.constraints
    
    # Needed for interface purposes - need to imitate the Gurobi interface.
    # constraint: an object of the element type of list returned by getConstrs.
    def remove(self, constraint):
        found = False
        for (i, c) in enumerate(self.constraints):
            if c == constraint:
                self.constraints[i] = None
                found = True
        assert(found)
        return
   
    # Needed for interface purposes - need to imitate the Gurobi interface.
    def getVars(self):
        return self.variables
   
    @property
    def numvars(self):
        return len(self.variables)
    
    # Needed for interface purposes - need to imitate the Gurobi interface.
    # Validate/update the model after having made changes.
    def update(self):
        self.constraints = [c for c in self.constraints if c is not None]
        return

    # Needed for interface purposes - need to imitate the Gurobi interface.
    def optimize(self):
        branch_constrs = []
        bus_constrs = []
        for constr in self.constraints:
            if isinstance(constr[0], network.Branch):
                branch_constrs.append((constr[0].name, constr[1]))
            elif isinstance(constr[0], network.Bus):
                bus_constrs.append((constr[0].name, constr[1]))

        msg = {
            'branch_closed_constraints': branch_constrs,
            'bus_fed_constraints': bus_constrs}
        # print '--------------------------------------------------------------------------------'
        # print 'psr.sgt.model.optimize'
        # print
        # print 'Bus fed:'
        # print json.dumps(bus_constrs)
        # print
        # print 'Breaker closed:'
        # print json.dumps(branch_constrs)
        # print
        resp = psr_client.optimize_network(msg)
        # print 'Status response = ' + str(resp[u'solver_status'])
        self.status = 2 if resp[u'solver_status'] else 3 # Imitate GUROBI returns
        # print '--------------------------------------------------------------------------------'

    # Needed for interface purposes - need to imitate the Gurobi interface.
    def printStats(self):
        return
