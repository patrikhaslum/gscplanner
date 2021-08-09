
class Action :

        def __init__( self, name, prim_prec = [], sec_prec = [], eff = [], cost = 1 ) :
                self.name = name
                self.cost = cost #for min_cost_hitting_set
                self.var = None #the variable used for minimum hitting set problem 
                self.inset = None #whether it is within the minimum cost hitting set
                self.sec_precs = set(sec_prec) #a list of constraints??
                self.prim_precs = set(prim_prec) #a list of (variable, value) pairs
                self.effect = set(eff) #also a list of (variable, value) pairs
                self.conditional_costs = None #a list of conditional costs 
        
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
