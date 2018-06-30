from 	__future__ 	import 	print_function

import pulp

## define GRB.XXX constants:
class GRB:
    # objective types
    MINIMIZE = pulp.constants.LpMinimize
    MAXIMIZE = pulp.constants.LpMaximize
    # constraint types
    EQUAL = pulp.LpConstraintEQ
    LESS_EQUAL = pulp.LpConstraintLE
    # variable types
    CONTINUOUS = 'Continuous'
    INTEGER = 'Integer'
    BINARY = 'Binary'

    VERSION = 'Fake'

    ## end class GRB

class Model:

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
    #     addVar ( name, lb, ub, type )
    #     addConstr ( expr, op, expr ), where op is one of GRB.EQUAL, ...

    def __init__(self, name):
        self.status = 1
        self.name = name
        self.constraints = []
        self.inactive = []
        self.variables = []
        self.numvars = 0
        self.objective = None
        self.sense = pulp.constants.LpMinimize

    def addVar(self, name, lb = None, ub = None, vtype = 'Continuous'):
        the_var = pulp.LpVariable(name, lb, ub, vtype)
        self.variables.append(the_var)
        self.numvars = len(self.variables)
        return the_var

    def addConstr(self, exp1, op = None, exp2 = None ):
        if op is None:
            assert isinstance(exp1, pulp.LpConstraint)
            the_constr = exp1
        elif isinstance(exp2, float):
            #print("addC/3: exp1 =", exp1, ", op =", op, ", exp2 =", exp2)
            the_constr = pulp.LpConstraint(exp1, op, rhs = exp2)
            #print("constr =", the_constr)
        else:
            #print("addC/3: exp1 =", exp1, ", op =", op, ", exp2 =", exp2)
            #new_exp = exp1 - exp2
            #print(new_exp, type(new_exp))
            the_constr = pulp.LpConstraint(exp1 - exp2, op, rhs = 0)
            #print("constr =", the_constr)
        self.constraints.append(the_constr)
        return the_constr

    def setObjective(self, expr, sense):
        self.objective = expr
        self.sense = sense

    def copy(self):
        new_model = Model(self.name)
        new_model.status = self.status
        new_model.constraints = self.constraints[:]
        new_model.inactive = self.inactive[:]
        new_model.variables = self.variables[:]
        new_model.numvars = len(new_model.variables)
        new_model.objective = self.objective
        new_model.sense = self.sense
        return new_model

    def reset(self):
        # Set status to 1, reset any variables necessary
        self.status = 1
    
    def remove(self, constraint):
        # print("removing {0} from {1}".format(constraint, self.constraints))
        self.inactive.append(constraint)

    def getConstrs(self):
        return self.constraints

    def getVars(self):
        return self.variables
    
    def update(self):
        return None # this is a no-op

    def optimize(self):
        #print("optimise:")
        #print("constraints: ", self.constraints)
        #print("inactive: ", self.inactive)
        inactive_set = set()
        for inaccon in self.inactive:
            inactive_set.add(id(inaccon))
        #print("inactive set:", inactive_set)
        the_lp = pulp.LpProblem( self.name, self.sense )
        for con in self.constraints:
            if id(con) not in inactive_set:
                #print("active constraint: ", con)
                the_lp.addConstraint(con)
        if self.objective is not None:
            the_lp.setObjective(self.objective)
        #the_lp.solve(pulp.CPLEX_PY(msg = False))
        #the_lp.solve(pulp.COINMP_DLL(msg = False))
        the_lp.solve()
        if the_lp.status == pulp.LpStatusOptimal:
            self.status = 2
            for var in self.variables:
                #print("solution:", var.name, '=', pulp.value(var))
                var.x = pulp.value(var)
        elif the_lp.status == pulp.LpStatusInfeasible:
            self.status = 3
        else:
            print( "bad status", the_lp.status )
            assert False
        del the_lp

    def printStats(self):
        print( "stats (GRB model): {0} vars (numvars = {1}), {2} constraints".format(len(self.variables), self.numvars, len(self.constraints)) )

    def setParam(self, option, value):
        return None # a no-op

    ## end class Model

def quicksum(exp_list):
    return sum(exp_list)

def setParam(option, value):
    return None # a no-op
