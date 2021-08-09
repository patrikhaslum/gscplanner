from model.generic.planning.task         import         Task, State
from model.generic.planning.actions        import        Action

xrange = range
 
class HydraulicBlocksWorldTask( Task ) :
        
        def __init__( self, object_set ) :
                print( object_set.num_blocks() )
                instance_name = 'hbw-num-blocks-%s-num-cyls-%s'%( object_set.num_blocks(),  object_set.num_cylinders() )
                Task.__init__(self, 'Hydraulic-BlocksWorld', instance_name )
                self.objects = object_set
                self.create_vars( self.objects.num_blocks(), self.objects.num_cylinders() )        

        def create_vars( self, num_blocks, num_cylinders ) :
                
                # Is block i in gripper?
                self.block_in_gripper = [ self.create_bool_state_var( 'block_%d_in_gripper'%i ) for i in xrange( num_blocks ) ]
                
                # Is gripper empty?
                self.gripper_empty = self.create_bool_state_var( 'gripper_empty' )

                # Is block i in cylinder j?
                self.block_in_cylinder = {}
                
                for x in xrange(num_blocks) :
                        for y in xrange( num_cylinders ) :
                                self.block_in_cylinder[ (x,y) ] = self.create_bool_state_var( 'block_%d_in_cylinder_%d'%(x,y) )

                # Is cylinder j empty?
                self.cylinder_empty = [ self.create_bool_state_var( 'cylinder_%d_empty'%x ) for x in xrange( num_cylinders ) ]
        
                # Is block i on block j?
                self.block_on_block = {}
                
                for x in xrange( num_blocks ) :
                        for y in xrange( num_blocks ) :
                                if y == x : continue
                                self.block_on_block[ (y, x) ] = self.create_bool_state_var( 'block_%d_on_block_%d'%(y,x) )
                
                # Is block i clear?
                self.block_clear = [ self.create_bool_state_var( 'block_%d_clear'%x ) for x in xrange(num_blocks) ]

                # Is block at bottom of stack?
                self.block_on_piston = [ self.create_bool_state_var( 'block_%d_on_piston'%x ) for x in xrange(num_blocks) ] 

        def        __make_pickup_action_4( self, block, cylinder ) :
                name = 'pickup_block_%d_from_cylinder_%d'%( block, cylinder )
                prec = [        ( self.block_clear[block].index, True ),
                                ( self.block_on_piston[block].index, True ),
                                ( self.block_in_cylinder[(block,cylinder)].index, True ),
                                ( self.gripper_empty.index, True ) ]

                eff = [                ( self.block_clear[block].index, False ),
                                ( self.block_on_piston[block].index, False),
                                ( self.block_in_cylinder[ (block,cylinder) ].index, False ),
                                ( self.gripper_empty.index, False ),
                                ( self.cylinder_empty[ cylinder ].index, True ),
                                ( self.block_in_gripper[ block ].index, True ) ]

                return Action( name, prec, [], eff )
        
        def        __make_putdown_action_4( self, block, cylinder ) :
                name = 'putdown_block_%d_onto_cylinder_%d'%(block,cylinder)
                
                prec = [        ( self.cylinder_empty[ cylinder ].index, True ),
                                ( self.block_in_gripper[ block ].index, True ) ]
                
                eff = [                ( self.block_clear[ block ].index, True ),
                                ( self.block_on_piston[ block ].index, True ),
                                ( self.block_in_cylinder[ (block, cylinder) ].index, True ),
                                ( self.gripper_empty.index, True ),
                                ( self.cylinder_empty[cylinder].index, False ),
                                ( self.block_in_gripper[ block ].index, False ) ]
                
                return Action( name, prec, [], eff )

        def        __make_unstack_action_4( self, top_block, bot_block, cylinder ) :
                name = 'unstack_block_%d_from_block_%d_in_cylinder_%d'%(top_block, bot_block, cylinder)

                prec = [        ( self.block_clear[ top_block ].index, True ),
                                ( self.block_in_cylinder[ ( top_block, cylinder ) ].index, True ),
                                ( self.block_in_cylinder[ ( bot_block, cylinder ) ].index, True ),
                                ( self.gripper_empty.index, True ),
                                ( self.block_on_block[ (top_block, bot_block ) ].index, True ) ]

                eff = [                ( self.block_clear[ top_block ].index, False ),
                                ( self.block_in_cylinder[ (top_block, cylinder) ].index, False ),
                                ( self.gripper_empty.index, False ),
                                ( self.block_on_block[ ( top_block, bot_block ) ].index, False ),
                                ( self.block_in_gripper[ top_block ].index, True ),
                                ( self.block_clear[ bot_block ].index, True ) ]

                return Action( name, prec, [], eff )

        def         __make_stack_action_4( self, top_block, bot_block, cylinder ) :
                
                name = 'stack_block_%d_onto_block_%d_in_cylinder_%d'%(top_block, bot_block, cylinder )
                
                prec = [        ( self.block_in_gripper[ top_block ].index, True ),
                                ( self.block_clear[ bot_block ].index, True ),
                                ( self.block_in_cylinder[ (bot_block, cylinder ) ].index, True ) ]

                eff = [                ( self.block_clear[ top_block ].index, True ),
                                ( self.block_in_cylinder[ (top_block, cylinder) ].index, True ),
                                ( self.gripper_empty.index, True ),
                                ( self.block_on_block[ ( top_block, bot_block ) ].index, True ),
                                ( self.block_in_gripper[ top_block ].index, False ),
                                ( self.block_clear[ bot_block ].index, False ) ]


                return Action( name, prec, [], eff )

        def         create_actions_4ops( self ) :
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

        def __make_unstack_putdown_action (self, top_block, bot_block, from_cylinder, cylinder):

                name = "move_block_" + format (top_block) + "_from_block_" + format (bot_block) + "_in_cylinder_"+ format (from_cylinder) + "_to_piston_in_cylinder_{0}".format (cylinder)

                pre = [        (self.cylinder_empty [cylinder].index, True),
                        (self.block_clear [top_block].index, True),
                        (self.block_in_cylinder [(top_block,from_cylinder)].index, True),
                        (self.block_in_cylinder [(bot_block,from_cylinder)].index, True),
                        (self.block_on_block [(top_block,bot_block)].index, True) ]
 
                # now effects
                eff = [ (self.block_on_piston [top_block].index, True),
                        (self.block_in_cylinder [(top_block,cylinder)].index, True),
                        (self.cylinder_empty [cylinder].index, False),
                        (self.block_clear [bot_block].index, True),
                        (self.block_in_cylinder [(top_block,from_cylinder)].index, False),
                        (self.block_on_block [(top_block,bot_block)].index, False) ]

                return Action ( name, pre, [], eff )


        def __make_unstack_stack_action (self, top_block, bot_block, dest_block, cylinder, dest_cylinder):

                name = "move_block_" + format (top_block) + "_from_block_" + format (bot_block) + "_in_cylinder_"+ format (cylinder) + "_to_block_{0}_in_cylinder_{1}".format (dest_block, dest_cylinder)

                pre = [        (self.block_clear [top_block].index, True),
                        (self.block_clear [dest_block].index, True),
                        (self.block_in_cylinder [(top_block,cylinder)].index, True),
                        (self.block_in_cylinder [(bot_block,cylinder)].index, True),
                        (self.block_in_cylinder [(dest_block,dest_cylinder)].index, True),
                        (self.block_on_block [(top_block,bot_block)].index, True) ]

                eff = [ (self.block_in_cylinder [(top_block,cylinder)].index, False),
                        (self.block_in_cylinder [(top_block,dest_cylinder)].index, True),
                        (self.block_on_block [(top_block,bot_block)].index, False),
                        (self.block_on_block [(top_block,dest_block)].index, True), 
                        (self.block_clear [bot_block].index, True), 
                        (self.block_clear [dest_block].index, False) ]

                return Action (name, pre, [], eff )

        def __make_pickup_putdown_action (self, block, from_cylinder, cylinder):

                name = "move_block_" + format (block) + "_from_piston" + "_in_cylinder_"+ format (from_cylinder) + "_to_piston_in_cylinder_{0}".format (cylinder)

                pre = [ (self.cylinder_empty [cylinder].index, True),
                        (self.block_clear [block].index, True), 
                        (self.block_in_cylinder [(block,from_cylinder)].index, True),
                        (self.block_on_piston [block].index, True) ]
 
                eff = [        (self.block_in_cylinder [(block,cylinder)].index, True),
                        (self.block_in_cylinder [(block,from_cylinder)].index, False),
                        (self.cylinder_empty [cylinder].index, False),
                        (self.cylinder_empty [from_cylinder].index, True) ]

                return Action ( name, pre, [], eff )

        def __make_pickup_stack_action (self, top_block, dest_block, cylinder, dest_cylinder):
                name = "move_block_" + format (top_block) + "_from_piston" + "_in_cylinder_"+ format (cylinder) + "_to_block_{0}_in_cylinder_{1}".format (dest_block, dest_cylinder)

                pre = [        (self.block_clear [top_block].index, True),
                        (self.block_clear [dest_block].index, True),
                        (self.block_in_cylinder [top_block,cylinder].index, True),
                        (self.block_in_cylinder [(dest_block,dest_cylinder)].index, True),
                        (self.block_on_piston [top_block].index, True) ]

                eff = [        (self.block_in_cylinder [(top_block,cylinder)].index, False),
                        (self.block_in_cylinder [(top_block,dest_cylinder)].index, True),
                        (self.block_on_piston [top_block].index, False),
                        (self.cylinder_empty [cylinder].index, True),
                        (self.block_on_block [(top_block,dest_block)].index, True),
                        (self.block_clear [dest_block].index, False) ]

                return Action ( name, pre, [], eff)

        def        create_actions_3ops( self ) :
                self.actions = []

                for b in xrange (self.objects.num_blocks()):
                        for c in xrange (self.objects.num_cylinders()):
                                for c1 in xrange (self.objects.num_cylinders()):
                                        if c != c1:
                                                self.actions.append (self.__make_pickup_putdown_action (b, c, c1))

                for b in xrange (self.objects.num_blocks()):
                        for b1 in xrange (self.objects.num_blocks()):
                                if b != b1:
                                        for c in xrange (self.objects.num_cylinders()):
                                                for c1 in xrange (self.objects.num_cylinders()):
                                                        if c != c1:
                                                                self.actions.append (self.__make_pickup_stack_action (b, b1, c, c1))

                for b in xrange (self.objects.num_blocks()):
                        for b1 in xrange (self.objects.num_blocks()):
                                if b != b1:
                                        for c in xrange (self.objects.num_cylinders()):
                                                for c1 in xrange (self.objects.num_cylinders()):
                                                        if c != c1:
                                                                self.actions.append (self.__make_unstack_putdown_action (b, b1, c, c1))

                for b in xrange (self.objects.num_blocks()):
                        for b1 in xrange (self.objects.num_blocks()):
                                if b != b1:
                                        for b2 in xrange (self.objects.num_blocks()):
                                                if b2 != b1 and b2 != b:
                                                        for c in xrange (self.objects.num_cylinders()):
                                                                for c1 in xrange (self.objects.num_cylinders()):
                                                                        if c != c1:
                                                                                self.actions.append( self.__make_unstack_stack_action (b, b1, b2, c, c1))

                
        
        def         make_state( self, valuation ) :
                
                return State( self, valuation ) 
                
