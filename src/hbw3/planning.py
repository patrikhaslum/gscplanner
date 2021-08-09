from model.generic.planning.task         import         Task, State
from model.generic.planning.actions        import        Action

xrange = range

def on_block( b ) :
        return 'on_block_{0}'.format(b)

def on_cylinder_piston( c ) :
        return 'on_cylinder{0}_piston'.format(c)

def in_cylinder( c ) :
        return 'in_cylinder_{0}'.format(c)

class HydraulicBlocksWorldTask( Task ) :

        def __init__( self, object_set ) :
                print(object_set.num_blocks())
                instance_name = 'hbw-num-blocks-%s-num-cyls-%s'%( object_set.num_blocks(),  object_set.num_cylinders() )
                Task.__init__(self, 'Hydraulic-BlocksWorld', instance_name )
                self.objects = object_set

                self.block_position_value_names = [ on_block(k) for k in xrange(0,self.objects.num_blocks()) ]
                self.block_position_value_names += [ 'on_piston' ]#on_cylinder_piston(k) for k in xrange(0, self.objects.num_cylinders()) ]
                self.block_position_value_names += [ 'hand' ]
                self.block_position_values = { name : k for k, name in enumerate( self.block_position_value_names ) }

                self.block_container_value_names = [ in_cylinder(k) for k in xrange( 0, self.objects.num_cylinders()) ] + [ 'none' ]
                self.block_container_values = { name : k for k, name in enumerate( self.block_container_value_names ) }

                self.create_vars( self.objects.num_blocks(), self.objects.num_cylinders() )

        def create_vars( self, num_blocks, num_cylinders ) :

                # block i position
                num_values = len(self.block_position_values)
                self.block_position = [ self.create_state_var( 'block_{0}_position'.format(i), range(num_values) ) for i in xrange(num_blocks) ]
                for sv in self.block_position:
                        sv.domain_print_names = self.block_position_value_names

                # Is gripper empty?
                self.gripper_empty = self.create_bool_state_var( 'gripper_empty' )

                # Is block i in cylinder j?
                num_values = len( self.block_container_values )
                self.block_container = [ self.create_state_var( 'block_{0}_container'.format(i), range(num_values) ) for i in xrange(num_blocks) ]
                for sv in self.block_container:
                        sv.domain_print_names = self.block_container_value_names

                # Is cylinder j empty?
                self.cylinder_empty = [ self.create_bool_state_var( 'cylinder_%d_empty'%x ) for x in xrange( num_cylinders ) ]

                # Is block i clear?
                self.block_clear = [ self.create_bool_state_var( 'block_%d_clear'%x ) for x in xrange(num_blocks) ]

        def __make_pickup_action_4( self, block, cylinder ) :
                name = 'pickup_block_%d_from_cylinder_%d'%( block, cylinder )
                prec = [ ( self.block_clear[block].index, True ),
                         ( self.block_position[block].index, self.block_position_values[ 'on_piston' ] ),
                         ( self.block_container[block].index, self.block_container_values[ in_cylinder(cylinder) ] ),
                         ( self.gripper_empty.index, True ) ]

                eff = [ ( self.block_clear[block].index, False ),
                        ( self.gripper_empty.index, False ),
                        ( self.cylinder_empty[cylinder].index, True ),
                        ( self.block_position[block].index, self.block_position_values[ 'hand' ] ),
                        ( self.block_container[block].index, self.block_container_values[ 'none' ] ) ]

                return Action( name, prec, [], eff )

        def __make_putdown_action_4( self, block, cylinder ) :
                name = 'putdown_block_%d_onto_cylinder_%d'%(block,cylinder)

                prec = [ ( self.cylinder_empty[ cylinder ].index, True ),
                         ( self.block_position[ block ].index, self.block_position_values[ 'hand' ] ) ]

                eff = [ ( self.block_clear[ block ].index, True ),
                        ( self.gripper_empty.index, True ),
                        ( self.cylinder_empty[ cylinder ].index, False ),
                        ( self.block_position[ block ].index, self.block_position_values[ 'on_piston' ] ),
                        ( self.block_container[ block ].index, self.block_container_values[in_cylinder(cylinder)] ) ]

                return Action( name, prec, [], eff )

        def __make_unstack_action_4( self, top_block, bot_block, cylinder ) :
                name = 'unstack_block_%d_from_block_%d_in_cylinder_%d'%(top_block, bot_block, cylinder)

                prec = [ ( self.block_clear[ top_block ].index, True ),
                         ( self.gripper_empty.index, True ),
                         ( self.block_position[ top_block ].index, self.block_position_values[ on_block(bot_block) ] ),
                         ( self.block_container[ bot_block ].index, self.block_container_values[in_cylinder(cylinder)] ) ]

                eff = [ ( self.block_clear[ top_block ].index, False ),
                        ( self.block_container[ top_block ].index, self.block_container_values[ 'none' ] ),
                        ( self.gripper_empty.index, False ),
                        ( self.block_position[ top_block ].index, self.block_position_values[ 'hand' ] ),
                        ( self.block_clear[ bot_block ].index, True ) ]

                return Action( name, prec, [], eff )

        def __make_stack_action_4( self, top_block, bot_block, cylinder ) :

                name = 'stack_block_%d_onto_block_%d_in_cylinder_%d'%(top_block, bot_block, cylinder )

                prec = [ ( self.block_position[ top_block ].index, self.block_position_values[ 'hand' ] ),
                         ( self.block_container[ bot_block ].index, self.block_container_values[in_cylinder(cylinder)] ),
                         ( self.block_clear[ bot_block ].index, True ) ]

                eff = [ ( self.block_clear[ top_block ].index, True ),
                        ( self.gripper_empty.index, True ),
                        ( self.block_position[ top_block ].index, self.block_position_values[ on_block(bot_block) ] ),
                        ( self.block_container[ top_block ].index, self.block_container_values[ in_cylinder(cylinder) ] ),
                        ( self.block_clear[ bot_block ].index, False ) ]

                return Action( name, prec, [], eff )

        def create_actions_4ops( self ) :
                self.actions = []

                self.pickup_actions = []
                for b in xrange (self.objects.num_blocks()):
                        for c in xrange (self.objects.num_cylinders()):
                                self.pickup_actions.append(self.__make_pickup_action_4(b, c))

                self.actions += self.pickup_actions

                self.putdown_actions = []
                for b in xrange (self.objects.num_blocks()):
                        for c in xrange (self.objects.num_cylinders()):
                                self.putdown_actions.append(self.__make_putdown_action_4(b, c))

                self.actions += self.putdown_actions

                self.unstack_actions =[]
                for b1 in xrange (self.objects.num_blocks()):
                        for b2 in xrange (self.objects.num_blocks()):
                                if b1 != b2:
                                        for c in xrange (self.objects.num_cylinders()):
                                                self.unstack_actions.append ( self.__make_unstack_action_4(b1, b2, c))

                self.actions += self.unstack_actions

                self.stack_actions = []
                for b1 in xrange (self.objects.num_blocks()):
                        for b2 in xrange (self.objects.num_blocks()):
                                if b1 != b2:
                                        for c in xrange (self.objects.num_cylinders()):
                                                self.stack_actions.append ( self.__make_stack_action_4(b1, b2, c))

                self.actions += self.stack_actions

        def make_state( self, valuation ) :
                return State( self, valuation )
