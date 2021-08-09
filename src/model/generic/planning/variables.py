
class StateVar :
        
        def __init__( self, index, name, domain = [ True, False ], default = 0 ) :
                self.index = index
                self.name = name
                self.domain = domain
                self.default_value = default
                self.value_index = dict( zip( self.domain, range(0,len(self.domain))) )

        def valid_value( self, val ) :
                return val in self.domain

        def domain_size( self ) :
                return len(self.domain)

        def __str__( self ) :
                return self.name

        def __repr__( self ) :
                return 'model.generic.planning.variables.StateVar(' + str(self.index) \
                        + ', ' + self.name + ')'
