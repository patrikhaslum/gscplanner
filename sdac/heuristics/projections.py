# Projects planning tasks over a subset of the state variables
# takes into account the secondary model as well
from __future__				import print_function

import sys

from model.generic.hybrid.task		import HybridTask
from model.generic.planning.task	import Task
from model.generic.planning.variables	import StateVar
from model.generic.planning.actions 	import Action, ConditionalCost

from gurobipy import LinExpr

def 	project_primary_over_vars(  task, G, variable_set ) :
	
	variable_map = { }
	inv_variable_map = { }
	action_map = { }
	inv_action_map = { }
	
	# create projected primary task
	projected_primary = Task( task.domain_name, task.instance_name )

        #print("Projecting primary")

	# re-map primary task variables
	for new_index, old_index in enumerate( variable_set ) :
		variable_map[ old_index ] = new_index
		inv_variable_map[ new_index ] = old_index
		x = task.state_vars[old_index]
		projected_primary.create_state_var( x.name, x.domain, x.default_value )
                #print("Name: ", x.name, " Old index: ",old_index , " New index", new_index) 

        #print("Done with primary. Actions now.")
        
	# re-map planning task actions
	for old_index, action in enumerate( task.actions ) :
		new_index = len( projected_primary.actions )
		new_primary_precs = []
		for x, v in action.prim_precs :
			if x not in variable_map :
				continue
			new_primary_precs.append( ( variable_map[x], v ) )
		new_effect = []
		for x, v in action.effect :
			if x not in variable_map :
				continue
			new_effect.append( ( variable_map[x], v ) )
		if len( new_effect ) == 0 :
			continue 
                new_conditional_costs = [] 
                for cc in action.conditional_costs : 
                    new_primary_condition = []
                    for x,v in cc.primary_conditions : 
                        if x not in variable_map : 
                            print("x not in variable map:", x)
                            continue
                        new_primary_condition.append( (variable_map[x],v) )
                    new_secondary_condition = [] 
                    if len(new_primary_condition)==0 and len(new_secondary_condition)==0 : 
                        print("No primary or secondary conditions")
                        continue
                    new_conditional_costs.append( ConditionalCost ( primary_condition = new_primary_condition, 
                                                                   secondary_condition = new_secondary_condition, 
                                                                   ccost = cc.ccost ) ) 
                #print("variable_map is ", variable_map)
                #print("conditional_costs are ")
                #for cc in action.conditional_costs : 
                    #print("conditions :")
                    #for x,v in cc.primary_conditions : 
                        #print(x,v)
                    #print("cost ", cc.ccost)
                #print("new conditional costs are : ")
                #for ncc in new_conditional_costs : 
                    #print("conditions :")
                    #for x,v in ncc.primary_conditions : 
                    #    print(x,v)
                    #print("cost ", cc.ccost)
		projected_primary.actions.append( Action( action.name, 
                                                          new_primary_precs, 
                                                          action.sec_precs, 
                                                          new_effect, action.cost, 
                                                          conditional_costs = new_conditional_costs,
                                                          objective_function = action.objective_function,
                                                          of_vname = action.of_varname ) )
		#print("Addng action: ", action.name, " New primary precs: ", new_primary_precs, " Effects: ", new_effect)
		action_map[ old_index ] = new_index
		inv_action_map[ new_index ] = old_index
		

        
	projected_G = []
	for x, v in G :
		if x not in variable_map : continue
		projected_G.append( (variable_map[x],v) )	

	return projected_primary, projected_G, ( variable_map, inv_variable_map ), ( action_map, inv_action_map )

def	project_secondary_over_vars( model, variable_set, var_map ) :
	# now, get constraints which are going to be dead because 
	# of variables being projected away
	projected_model = model.copy()
	projected_constraints = []
	new_constraints = []
	for index, constraint in enumerate(projected_model.constraints) :
		condition, c = constraint
		if len(condition) == 0 : # unconditional constraint
			new_constraints.append( (condition, c) )
			continue
		skip = False
		for x, _ in condition :
			if x not in variable_set :
				skip = True
				break
		if skip : 
			new_constraints.append( ([], c) )
			projected_constraints.append( index )
			continue
		for i in range(len(condition)) :
			X, v = condition[i]
			condition[i] = (var_map[X], v)
		new_constraints.append( (condition, c) )

	projected_model.constraints = new_constraints 

	return projected_constraints, projected_model

def	project_hybrid_over_vars( task, variable_set ) :

	projected_primary, projected_G, vars_maps, actions_maps = project_primary_over_vars( task.task, task.Gp, variable_set )
	constraints_projected_away, projected_secondary = project_secondary_over_vars( task.lp, variable_set, vars_maps[0] )

	#print( 'Projected task created' )
	#projected_primary.print_statistics( sys.stdout )
        
        #Check whether there are any conditional costs on secondary variables and whether the conditional costs on secondary 
        #variables are the same for all actions. 
        #all_conditional_costs_same = True
        #conditional_costs_on_secondary = False
        #cc = task.actions[0].conditional_costs
        #if len(cc[0].secondary_conditions)>0 : 
            #conditional_costs_on_secondary = True
        #for a in task.actions : 
            #if a.conditional_costs != cc : 
                #all_conditional_costs_same = False
        #if conditional_costs_on_secondary and all_conditional_costs_same : 
            ##objective_function_expr = task.objective_function                 
            #print(format(projected_secondary))
            #print(format(projected_secondary.model))
            #projected_secondary.model.setObjective(task.objective_function)

	projected_hybrid = HybridTask(  projected_primary, 
                                        projected_secondary, 
                                        None, 
                                        projected_G, projected_secondary.goal_constraints,
                                        sdac_optimization = task.sdac_optimization)

	# kill constraints that have been projected away
	for index in constraints_projected_away :
		projected_hybrid.inactive_by_default.add( index )
	
	return projected_hybrid, vars_maps, actions_maps		
