from         __future__         import         print_function

import sys
import logging
import time

#TIMER_FUN = time.clock
TIMER_FUN = time.time

xrange = range

class HybridState :

        calls_to_optimize = 0
        total_time_optimize = 0
        total_time_model_building = 0
        models_created = 0

        def __init__(self, ps, lp, inactive ) :

                self.primary = ps
                self.valid = None
                self.active = []
                self.conflict = []
                self.secondary = self.project_inactive_constraints( lp, inactive )
                self.inactive = inactive
                self.secondary_valuation = []
                # hold a pointer to the lp only to be able to print variable names
                self.lp = lp

        def project_inactive_constraints( self, lp, inactive ) :
                #print("project inactive: lp =", lp, ", inactive =", inactive)
                if lp is None : return None
        
                for i in xrange( len(lp.constraints) ) :
                        phi_i, _ = lp.constraints[i]
                        # Check whether phi is true under current primary state
                        if self.primary.satisfies( phi_i ) : 
                                self.active.append(i)
                                continue
                        inactive.add( i )
                t0 = TIMER_FUN()
                model = lp.model.copy()
                for index in inactive :
                        try :
                                model.remove( model.getConstrs()[index] )
                        except IndexError :
                                print( 'index {0} # constraints in LP object: {1} # constraints in Gurobi obj: {2}'.format( index, len(lp.constraints), len(model.getConstrs()) ) )
                                raise
                                #sys.exit(1)
                model.update()
                HybridState.total_time_model_building += TIMER_FUN() - t0
                HybridState.models_created += 1
                #print("project inactive: model =", model)
                return model

        def check_valid( self, extract_no_good = False ) :
                # If self.secondary and self.value are both None, that means the
                # hybrid state was created with lp = None, i.e., that there is no
                # secondary model; in this case, set valid to true. If, on the
                # other hand, self.secondary is None but self.valid is not, that
                # means the state's validity has already been checked, so we don't
                # modify it. In either case, return without further checking.
                if self.secondary is None:
                        if self.valid is None:
                                self.valid = True
                        return
                # this is the case when we need to run a consistency check
                if self.secondary.status != 1 :
                        self.secondary.reset()
                t0 = TIMER_FUN()
                self.secondary.optimize()
                HybridState.calls_to_optimize += 1
                HybridState.total_time_optimize += TIMER_FUN() - t0
                #self.secondary.write( 'last_projected.lp' )
                if self.secondary.status == 2 : 
                        self.valid = True
                        # extract assignment to secondary variables
                        self.secondary_valuation = [ ( i, self.secondary.getVars()[i].x ) for i in xrange( self.secondary.numvars ) ]
                elif self.secondary.status in ( 3, 4 ) :
                        self.valid = False
                        if extract_no_good :
                                self.conflict = []
                                self.secondary.computeIIS()
                                for i, C in enumerate( self.secondary.getConstrs() ) :
                                        if C.getAttr('IISConstr') :                        
                                                self.conflict.append( self.active[i] )
                                logging.info( 'Conflict constraints: {0}'.format(len(self.conflict) ) )
                del self.secondary
                self.secondary = None

        
        def __eq__( self, other ) :
                return self.primary.__eq__(other.primary)
                
        def __ne__( self, other ) :
                return not self.__eq__(other)

        def __hash__( self ) :
                return hash( self.primary ) 

        def write(self, fileobj):
                self.primary.write(fileobj)
                print("valid?:", self.valid)
                if self.secondary is not None:
                        print("constraints:")
                        for i, C in enumerate( self.secondary.getConstrs() ) :
                                print(i, ": ", C, file=fileobj)
                        print("inactive:", self.inactive, file=fileobj)
                print("secondary valuation:")
                for (i,v) in self.secondary_valuation:
                        assert i >= 0 and i < len(self.lp.variables)
                        print(self.lp.variables[i].name, "=", v, file=fileobj)
