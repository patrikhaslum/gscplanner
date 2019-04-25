from gurobipy import Model, GRB, quicksum

class LinearProgram :

        def __init__( self, hbw_task = None ) :

                if hbw_task is None :
                        return

                self.model = Model( hbw_task.instance_name + '.lp' )

                # LP variables
                self.variables = [] # was all_variables
                self.make_model_vars( hbw_task )
                self.model.update()

                # LP Constraints
                self.constraints = []
                self.make_model_constraints( hbw_task )
                self.model.update()

                self.goal_constraints = set()
                #self.model.write( 'tmp.lp' )

        def copy( self ) :
                from copy import deepcopy

                new_lp = LinearProgram( )
                new_lp.model = self.model.copy()
                new_lp.constraints = []
                new_lp.goal_constraints = set()
                for index, ext_constraint in enumerate(self.constraints) :
                         new_lp.constraints.append( ( deepcopy(ext_constraint[0]), new_lp.model.getConstrs()[index] ) )
                return new_lp

        def make_model_vars( self, hbw_task ) :
                # each cylinder contains a piston of negl. weight and cross
                # section area equal to the cylinder's. In general, there will
                # be a fluid column below it

                self.fluid_column_heights = [] # the k-th element of this list corresponds with d_k
                for x in xrange( hbw_task.objects.num_cylinders() ) :
                        varname = 'd_{0}'.format(x)
                        fch_i = self.model.addVar( vtype = GRB.CONTINUOUS,
						   name = varname,
						   lb = 0.0,
						   ub = hbw_task.objects.cylinders[x].height )
                        self.fluid_column_heights.append( fch_i )

                self.variables += self.fluid_column_heights

                # modeling the partial wts of blocks on the piston as a list of
                # LP variables -- pw_i = partial wt of blocks in the range [0,i-1] that are in the cylinder
                # base case -- pw_0 = 0
                self.partial_wts = {} # this contains vars w_i,k

                for i in xrange( hbw_task.objects.num_blocks() ) :
                        for j in xrange( hbw_task.objects.num_cylinders() ) :
                                varname = 'w_{0},{1}'.format(i,j)
                                pw_ij = self.model.addVar( vtype = GRB.CONTINUOUS,
							   name = varname,
							   lb = 0.0,
							   ub = hbw_task.objects.blocks[i].weight )
                                self.partial_wts[ (i, j ) ] = pw_ij
                                self.variables.append( pw_ij )
                # wt of columns (fluid + blocks) in each cylinder

                self.column_wts = []
                for x in xrange( hbw_task.objects.num_cylinders() ) :
                        varname = 'f_{0}'.format(x)
                        cw_x = self.model.addVar( vtype = GRB.CONTINUOUS,
						  name = varname )
                        self.column_wts.append( cw_x )
                self.variables += self.column_wts

                #adding the column heights 
                self.partial_heights = {} # this contains vars h_i,k

                for i in xrange( hbw_task.objects.num_blocks() ) :
                        for j in xrange( hbw_task.objects.num_cylinders() ) :
                                varname = 'h_{0},{1}'.format(i,j)
                                ph_ij = self.model.addVar( vtype = GRB.CONTINUOUS,
							   name = varname,
							   lb = 0.0,
							   ub = hbw_task.objects.blocks[i].height )
                                self.partial_heights[ (i, j ) ] = ph_ij
                                self.variables.append( ph_ij )
                # wt of columns (fluid + blocks) in each cylinder

                self.column_heights = []
                for x in xrange( hbw_task.objects.num_cylinders() ) :
                        varname = 'height_{0}'.format(x)
                        ch_x = self.model.addVar( vtype = GRB.CONTINUOUS,
						  name = varname )
                        self.column_heights.append( ch_x )
                self.variables += self.column_heights

        def get_all_variables (self):
                return self.variables

        def get_all_constraints (self):
                return self.constraints

        def make_model_constraints (self, hbw_task):
                self.constraints = self.make_partial_wt_constraints (hbw_task)
                self.constraints += self.make_column_wt_constraints (hbw_task)
                self.constraints += self.make_pressure_balancing_constraints (hbw_task)
                self.constraints += self.make_fluid_balancing_constraint (hbw_task)

                self.constraints += self.make_partial_height_constraints (hbw_task)
                self.constraints += self.make_column_height_constraints (hbw_task)

        def make_partial_wt_constraints (self, hbw_task):
                wt_constraints = []
                for cylId in xrange( hbw_task.objects.num_cylinders() ) :
                        wt_constraints += self.make_wt_constraints_for_cylinder( cylId, hbw_task )
                return wt_constraints

        def make_wt_constraints_for_cylinder (self, cylId, hbw_task ) : #hbw_obj, vars):
                from hbw3.planning import in_cylinder
                wt_constraints = []
                cylinder = hbw_task.objects.cylinders[cylId]

                for i in xrange(0,hbw_task.objects.num_blocks()) :
                        var = hbw_task.block_container[i]
                        var_valuation = [ ( var.index, hbw_task.block_container_values[ in_cylinder(cylId) ] ) ]

                        constraint = ( var_valuation, self.model.addConstr( self.partial_wts[(i,cylId)] - hbw_task.objects.blocks[i].weight  == 0 ) )
                        wt_constraints.append( constraint )

                        for name, v in hbw_task.block_container_values.iteritems() :
                                if name == in_cylinder(cylId) : continue
                                var_valuation = [ ( var.index, v ) ]

                                constraint = ( var_valuation, self.model.addConstr( self.partial_wts[(i,cylId)]   == 0 ) )
                                wt_constraints.append( constraint )

                return wt_constraints

        #partial height constraints
        def make_partial_height_constraints (self, hbw_task):
                height_constraints = []
                for cylId in xrange( hbw_task.objects.num_cylinders() ) :
                        height_constraints += self.make_height_constraints_for_cylinder( cylId, hbw_task )
                return height_constraints
        
        #make height constraint -- used in the objective function for the action. 
        def make_height_constraints_for_cylinder (self, cylId, hbw_task ) : #hbw_obj, vars):
                from hbw3.planning import in_cylinder
                height_constraints = []
                cylinder = hbw_task.objects.cylinders[cylId]

                for i in xrange(0,hbw_task.objects.num_blocks()) :
                        var = hbw_task.block_container[i]
                        var_valuation = [ ( var.index, hbw_task.block_container_values[ in_cylinder(cylId) ] ) ]

                        constraint = ( var_valuation, self.model.addConstr( self.partial_heights[(i,cylId)] - hbw_task.objects.blocks[i].height  == 0 ) )
                        height_constraints.append( constraint )

                        for name, v in hbw_task.block_container_values.iteritems() :
                                if name == in_cylinder(cylId) : continue
                                var_valuation = [ ( var.index, v ) ]

                                constraint = ( var_valuation, self.model.addConstr( self.partial_heights[(i,cylId)]   == 0 ) )
                                height_constraints.append( constraint )

                return height_constraints

        # this function adds equality constraints to calculate the total downward force
        # at the bottom of the cylinder (column_wt = total weight of all blocks + wt of fluid column)
        def make_column_wt_constraints_for_cylinder (self, cylId, hbw_task):
                density = hbw_task.objects.get_fluid_density ()
                cross_section_area_of_cyl = hbw_task.objects.cylinders[cylId].area

                constr = ( [], # unconditional
			   self.model.addConstr( self.column_wts [cylId]
						 - density*cross_section_area_of_cyl*self.fluid_column_heights [cylId]
						 - quicksum( self.partial_wts[(i,cylId)] for i in xrange(hbw_task.objects.num_blocks() )) == 0  ) )
                return constr



        def make_column_wt_constraints (self, hbw_task):
                return [ self.make_column_wt_constraints_for_cylinder (cylId, hbw_task)  for cylId in xrange( hbw_task.objects.num_cylinders() ) ]

        def make_column_height_constraints_for_cylinder (self, cylId, hbw_task): 
            
                #density = hbw_task.objects.get_fluid_density ()
                #cross_section_area_of_cyl = hbw_task.objects.cylinders[cylId].area

                constr = ( [], # unconditional
			   self.model.addConstr( self.column_heights [cylId]
						 - self.fluid_column_heights [cylId]
						 - quicksum( self.partial_heights[(i,cylId)] for i in xrange(hbw_task.objects.num_blocks() )) == 0  ) )
                return constr
            
        
        def make_column_height_constraints (self, hbw_task): 
                return [ self.make_column_height_constraints_for_cylinder (cylId, hbw_task)  for cylId in xrange( hbw_task.objects.num_cylinders() ) ]

        def make_pressure_balancing_constraints (self, hbw_task ):
                pb_constraints = []
                # we have 'numCylinders -1' constraints - one for each consecutive pair
                for cylId in xrange (hbw_task.objects.num_cylinders() - 1):
                        # constr for cylId & cylId + 1
                        reciprocal_area_1 = 1.0 / hbw_task.objects.cylinders[cylId].area
                        reciprocal_area_2 = 1.0 / hbw_task.objects.cylinders[cylId + 1].area

                        lpconstr = ( [], # unconditional
				     self.model.addConstr( reciprocal_area_1 * self.column_wts[cylId]
							   - reciprocal_area_2 * self.column_wts[cylId+1] == 0 ) )
                        pb_constraints.append( lpconstr )

                return pb_constraints

        def make_fluid_balancing_constraint (self, hbw_task):
                constr = ( [], # unconditional
			   self.model.addConstr(
				quicksum( hbw_task.objects.cylinders[cylId].area * self.fluid_column_heights[cylId] for cylId in xrange(hbw_task.objects.num_cylinders()) )
				== hbw_task.objects.fluid.total_fluid_in_cylinders ) )
                return [ constr ]

        def print_constraints (self):
                for phi, gamma in self.constraints:
                        if len(phi) == 0 :
                                print( ' True -> %s'%gamma )
                        else :
                                head = ' & '.join( [ '%s = %s'%(x,v) for x,v in phi ] )
                                print ( ' %s -> %s'%( head, gamma ) )
