
class ConditionalCost : 
    
        def __init__(self, primary_condition=[], secondary_condition=[], ccost=1) : 
            
                self.primary_conditions = primary_condition#a variable value pair 
                self.secondary_conditions = secondary_condition
                self.ccost = ccost 
                
        def evaluate( self, state ):
        
                #should look similar as evaluating the goal 
                if state.primary.satisfies( self.primary_conditions ):
                    #if there is no secondary, return True
                    if len(self.secondary_conditions) == 0 : return True
                
                    #else, evaluate secondary conditions 
                    for var,value in self.secondary_conditions :
                        for i,v in state.secondary_valuation : 
                            #print "variable,value in condition: ",var,value," i,v in secondary_valuation: ", i,v
                            if var == i : 
                                if value != v : return False 
                    
                    return True
        
                return False
            
class Action :

	def __init__( self, name, prim_prec = [], sec_prec = [], eff = [], cost = 1, conditional_costs = [] , objective_function = None, of_vname = None, of_i = None, ep_constant = 1 ) :
		self.name = name
		self.cost = cost #for min_cost_hitting_set
		self.var = None #the variable used for minimum hitting set problem 
		self.inset = None #whether it is within the minimum cost hitting set
		self.sec_precs = set(sec_prec) #a list of constraints??
		self.prim_precs = set(prim_prec) #a list of (variable, value) pairs
		self.effect = set(eff) #also a list of (variable, value) pairs
                self.conditional_costs = conditional_costs #a list of conditional costs 
                self.objective_function = objective_function #for state-depndent action costs
                self.of_varname = of_vname
                self.of_i = of_i #index of the variable in gurobi 
                
                self.end_plan_constant = ep_constant
	
	def effect_consistent( self, valuation ) :
		table_val = dict(valuation)
		for X, v in self.effect :
			try :
				if table_val[X] != v : return False
			except KeyError :
				return False
		return True

	def regress( self, valuation ) :
		table_val = dict(valuation)
		for X, v in self.effect :
			try :
				del table_val[X]
			except KeyError :
				return []
		for X, v in self.prim_precs :
			try :
				if table_val[X] != v : return [] # regression contains false
			except KeyError :
				table_val[X] = v
		return [ (X,v) for X,v in table_val.iteritems() ]
