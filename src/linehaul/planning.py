from model.generic.planning.task         import         Task, State
from model.generic.planning.actions        import        Action

import math

class LinehaulTask( Task ):
        SYMMETRY_BREAKING = True

        def __init__( self, name, dm, locations, demand, vehicles ):
                instance_name = name
                Task.__init__(self, 'Linehaul', instance_name )
                # list of location names, depot is locations[0]:
                self.locations = locations
                self.distance_matrix = dm
                # demand[l] = (qc, qa) means the total demand for
                # chilled (ambient) goods at location l is qc (qa).
                self.demand = demand
                # vehicles: list of tuples (type, pkc, cap, chilled),
                # where: pkc = per-kilometer cost, cap = capactiy,
                # chilled = True/False
                self.vehicles = []
                self.vehicle_type = dict()
                for (vtype, count, pkc, cap, chilled) in vehicles:
                        for i in range(count):
                                vname = "{0}{1}".format(vtype, i)
                                self.vehicles.append((vname, pkc, cap, chilled))
                                self.vehicle_type[vname] = vtype
                self.create_vars()
                self.create_actions()

        def create_vars( self ):
                # there is one primary variable per vehicle, which
                # is its current location
                depot = self.locations[0]
                home = depot + "*"
                self.at = {}
                for (vname, _, _, _) in self.vehicles:
                        self.at[vname] = self.create_state_var( '{0}_at'.format(vname), self.locations + [home], depot )

                # there is a boolean variable for every vehicle, location
                # pair, where location != depot, which indicates if the
                # vehicle has visited the location.
                self.visited = {}
                for (vname, _, _, _) in self.vehicles:
                        for loc in self.locations[1:]:
                                self.visited[ (vname, loc) ] = self.create_bool_state_var( '{0}_visited_{1}'.format(vname, loc) )

                # for symmetry breaking, we need an additional boolean
                # variable for each vehicle type, which indicates if any
                # vehicle of this type has been used:
                if LinehaulTask.SYMMETRY_BREAKING:
                        self.vehicle_type_used = {}
                        for vtype in set(self.vehicle_type.values()):
                                self.vehicle_type_used[ vtype ] = self.create_bool_state_var( '{0}_used'.format(vtype) )


        def create_actions( self ):
                # there is only one type of action: drive(veh, from, to).
                # if to != depot, the action has the additional effect
                # visited[(vname, to)] = True.
                self.actions = []
                depot = self.locations[0]
                home = depot + "*"

                for (vname, pkc, _, _) in self.vehicles:
                        for lfrom in self.locations:
                                for lto in self.locations[1:] + [home]:
                                        if lto != lfrom:
                                                self.actions.append(self.__make_drive_action(vname, pkc, lfrom, lto))


        def __make_drive_action( self, vname, pkc, lfrom, lto ):
                name = 'drive_{0}_{1}_to_{2}'.format(vname, lfrom, lto)
                prec = [ ( self.at[vname].index, lfrom ) ]
                if LinehaulTask.SYMMETRY_BREAKING:
                        prev = None
                        for (vn, _, _, _) in self.vehicles:
                                if vn == vname:
                                        break
                                else:
                                        prev = vn
                        depot = self.locations[0]
                        home = depot + "*"
                        if prev != None and lfrom == depot:
                                sb_prec = [ ( self.at[prev].index, home ) ]
                                prec += sb_prec
                        if lfrom == depot and lto == home:
                                vtype = self.vehicle_type[vname]
                                sb_prec = [ ( self.vehicle_type_used[vtype].index, False ) ]
                                prec += sb_prec
                eff = [        ( self.at[vname].index, lto ) ]
                if lto not in self.locations:
                        lto = self.locations[0]
                if lto != self.locations[0]:
                        eff += [ (self.visited[(vname,lto)].index, True) ]
                if LinehaulTask.SYMMETRY_BREAKING:
                        if lfrom == self.locations[0] and lto != lfrom:
                                vtype = self.vehicle_type[vname]
                                sb_eff = [ ( self.vehicle_type_used[vtype].index, True ) ]
                                eff += sb_eff
                dist = self.distance_matrix[(lfrom, lto)]
                cost = math.trunc((dist / 100.0) * pkc)
                #print( 'action: {0} cost: {1}'.format( name, cost ) ) 
                return Action( name, prec, [], eff, cost )


        def make_initial_state( self ):
                valuation = []
                depot = self.locations[0]
                for (vname, _, _, _) in self.vehicles:
                        var = self.at[vname]
                        valuation.append( (var.index, depot) )
                        for loc in self.locations[1:]:
                                var = self.visited[(vname, loc)]
                                valuation.append( (var.index, False) )
                if LinehaulTask.SYMMETRY_BREAKING:
                        for vtype in self.vehicle_type.values():
                                var = self.vehicle_type_used[ vtype ]
                                valuation.append( (var.index, False) )
                return State( self, valuation )

        def make_primary_goal( self ):
                valuation = []
                depot = self.locations[0]
                home = depot + '*'
                for (vname, _, _, _) in self.vehicles:
                        var = self.at[vname]
                        valuation.append( (var.index, home) )
                return valuation

        def make_state( self, valuation ):
                return State( self, valuation ) 
