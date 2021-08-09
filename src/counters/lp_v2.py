from        gurobipy        import Model, GRB, quicksum

xrange = range

class         LinearProgram :

        def __init__( self, counters_task  = None ) :
                
                if counters_task is None :
                        return

                self.model = Model( counters_task.instance_name + '.lp' )

                self.var_map = {}

                # LP Vars
                self.variables = []
                self.make_model_vars( counters_task )
                self.model.update()

                # LP Constraints
                self.constraints = []
                self.make_model_constraints( counters_task )
                self.model.update()
                
                self.goal_constraints = set()

        def copy( self ) :
                from copy         import deepcopy

                new_lp = LinearProgram()
                new_lp.goal_constraints = deepcopy(self.goal_constraints)
                new_lp.model = self.model.copy()
                new_lp.constraints = []
                for index, ext_constraint in enumerate(self.constraints) :
                         new_lp.constraints.append( ( deepcopy(ext_constraint[0]), new_lp.model.getConstrs()[index] ) )
                return new_lp

        def        make_model_vars( self, task ) :
                for x_c in task.counter_values :
                        x_c_2 = self.model.addVar( name = x_c, lb=0, ub=task.max_value-1 ) ## , vtype = GRB.INTEGER
                        self.variables.append( x_c_2 )
                        self.var_map[ x_c ] = x_c_2

        def         make_model_constraints( self, task ) :
        
                for counter in task.counter_values :
                        for k in xrange(0, task.max_value ) :
                                x = self.var_map[ counter ]
                                c = self.model.addConstr( k <= x )
                                self.constraints.append( ( [ (task.counter_values[counter][k].index, True) ], c ) )
                                c = self.model.addConstr( x <= k-1 )
                                self.constraints.append( ( [ (task.counter_values[counter][k].index, False) ], c ) )
                
        def        make_goal_constraints( self, goal_condition ) :
                goal_constraints = []
                # print(goal_condition)
                # print(self.model.variables)
                # print(self.var_map)
                for cond, lhs, rhs in goal_condition :
                        # x_lhs = None
                        # x_rhs = None
                        # for x in self.model.getVars() :
                        #         if lhs in x.getAttr('VarName') : 
                        #                 x_lhs = x 
                        #         if rhs in x.getAttr('VarName') :
                        #                 x_rhs = x
                        # assert x_lhs is not None
                        # assert x_rhs is not None
                        x_lhs = self.var_map[ lhs ]
                        x_rhs = self.var_map[ rhs ]
                        c = None
                        if cond == '<' :
                                c = ( [], self.model.addConstr( x_lhs <= x_rhs - 1 ) )
                                self.constraints.append(c)
                                goal_constraints.append( len(self.constraints)-1 )
                                
                        elif cond == '>' :
                                c = ( [], self.model.addConstr( x_lhs - 1 >= x_rhs ) )
                                self.constraints.append(c)
                                goal_constraints.append( len(self.constraints)-1 )

                        elif cond == '=' :
                                c = ( [], self.model.addConstr( x_lhs == x_rhs ) )
                                self.constraints.append(c)
                                goal_constraints.append( len(self.constraints)-1 )

                        else :
                                assert False

                self.model.update()
                self.goal_constraints = set(goal_constraints)
                return self.goal_constraints
