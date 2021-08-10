
# This class implements the "secondary" constraints; it is required
# to have a model, and constraints.
# constraints: a list of (trigger, constr) pairs; trigger is a
# partial valuation over the primary vars (simple condition);
# constr is interpreted only by the model
# model: an object that supports the relevant subset of the
# Gurobi model interface.

# The Mirror object has one switched constraint of each literal of
# the task, whose rhs is simply the same literal.

class Mirror(object):

    def __init__(self, task, model_factory ):
        self.task = task
        # self.variables = [] # do we need this?
        self.constraints = []
        for var in self.task.state_vars:
            for val in range(var.domain_size()):
                self.constraints.append(([(var.index, val)], (var, val)))
        # self.goal_constraints = set() # do we need this?
        self.model = model_factory([lit for (_, lit) in self.constraints])

    def copy(self) :
        assert False
        the_copy = Mirror(self.task, lambda x : None)
        the_copy.model = self.model.copy()
        the_copy.constraints = self.constraints[:]
        return the_copy

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

# General avoid condition model; this model does not implement any
# actual condition, but provides infrastructure for subclasses.
class AvoidConditionModel:

    def __init__(self, literals ):
        self.status = 1
        self.literals = literals
        self.active = [True for i in range(len(self.literals))]

    # Needed to imitate the Gurobi interface.
    def copy(self):
        result = AvoidConditionModel( self.literals )
        result.active = self.active[:]
        return result

    # Needed to imitate the Gurobi interface.
    def reset(self):
        self.status = 1
        self.active = [True for i in range(len(self.literals))]

    # Needed to imitate the Gurobi interface.
    def getConstrs(self):
        return self.literals

    # Needed to imitate the Gurobi interface.
    # constraint: an object of the element type of list returned by getConstrs.
    def remove(self, constraint):
        i = self.literals.index(constraint)
        self.active[i] = False

    # Needed to imitate the Gurobi interface.
    def getVars(self):
        return []

    @property
    def numvars(self):
        return 0

    # Needed to imitate the Gurobi interface.
    # Validate/update the model after having made changes.
    def update(self):
        return

    # Needed to imitate the Gurobi interface.
    def optimize(self):
        # Collect the currently active literals; at the end we should
        # have a partial (but consistent) valuation
        valuation = dict()
        for i in range(len(self.literals)):
            if self.active[i]:
                var, val = self.literals[i]
                assert var not in valuation
                valuation[var] = val
        # Call evaluate on this valuation
        cond_is_true = self.evaluate(valuation)
        # If the condition is (necessarily) true, the state is bad
        # (violates the avoid condition), else it's ok
        if cond_is_true:
            self.status = 3
        else:
            self.status = 2

    # This is the method that performs the actual condition checking
    # valuation is var->val dictionary representing a partial but
    # consistent primary state.
    def evaluate(self, valuation):
        return False

    # Needed to imitate the Gurobi interface.
    def printStats(self):
        return

class AvoidConditionModel_Openstacks (AvoidConditionModel):
    '''

    '''

    def evaluate(self, valuation):
        
