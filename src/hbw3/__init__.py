from hbw3.objects                        import         InstanceObjects
from hbw3.planning                        import         HydraulicBlocksWorldTask, on_block, on_cylinder_piston, in_cylinder
from hbw3.lp                                import         LinearProgram
from model.generic.planning.task        import         State
from model.generic.hybrid.task                import        HybridTask

import sys
import os

xrange = range

def make_blocks_and_cylinders(total_amount_of_fluid) :
        num_blocks = 10
        num_cylinders = 10

        # initialize objects

        obj_collection = InstanceObjects( num_blocks, num_cylinders )
        
        block_weights = [ 5, 9, 7, 2, 4, 7, 1, 6, 4, 8 ]
        block_dimensions = [ (1,1,1) ] * 10 # creates a list containing 10 instances of (1,1,1)

        cylinder_areas = [ 2, 2, 1, 4, 1 ]
        cylinder_heights = [ 10, 10, 10, 15, 15 ]

        for i in range( 0, num_blocks ) :
                w_i = block_weights[i]
                h_i, l_i, b_i = block_dimensions[i]
                obj_collection.create_block( w_i, h_i, l_i, b_i )
                
        for i in range( 0, len(cylinder_areas) ) :
                obj_collection.create_cylinder( cylinder_areas[i], cylinder_heights[i] )

        obj_collection.create_gripper( )
        obj_collection.create_fluid( 5, total_amount_of_fluid )

        return obj_collection

def         make_instance_objects( num_blocks, num_cylinders, total_amount_of_fluid ) :
        object_collection = make_blocks_and_cylinders( total_amount_of_fluid )
        obj_set = InstanceObjects( num_blocks, num_cylinders )
        for i in range(0, num_blocks ) :
                obj_set.blocks.append( object_collection.blocks[i] )
        for i in range(0, num_cylinders ) :
                obj_set.cylinders.append( object_collection.cylinders[i] )

        print ( 'Number of blocks: %d'%num_blocks )
        print ( 'Number of cylinders: %d'%num_cylinders )
        
        obj_set.grippers.append( object_collection.grippers[0] )
        obj_set.fluid = object_collection.fluid

        return obj_set

def block_on_piston( b ) :
        return  'on_piston_{0}'.format(b)

def block_in_cylinder( b, c ) :
        return 'block_{0}_in_cylinder_{1}'.format(b,c)

def block_clear( b ) :
        return 'clear_{0}'.format(b)

def block_on_block( b1, b2 ) :
        return '{0}_on_{1}'.format(b1,b2)

def        decode_vars( task, input_line, facts ) :
        tokens = input_line.split ()
        if tokens [0] == "gripper_empty":
                facts.add('gripper_empty')
                return
    
        elif tokens [0] == "block_on_piston":
                blockId = int (tokens [1])
                facts.add( block_on_piston(blockId) )
                return

        elif tokens [0] == "block_in_cylinder":
                blockId = int (tokens [1])
                cylId = int (tokens [2])
                facts.add( block_in_cylinder(blockId,cylId) )
                return

        elif tokens [0] == "block_clear":
                blockId = int (tokens [1])
                facts.add( block_clear(blockId) )
                return

        elif tokens [0] == "block_on_block":
                tblockId = int (tokens [1])
                bblockId = int (tokens [2])
                facts.add( block_on_block( tblockId, bblockId ) )
                return


def        make_initial_state( instream, task, orig_num_cylinders ) :
        # 1. initialize all to False

        # 2. initialize actual values
        input_line = instream.readline()
        facts = set()
        while 'goal' not in input_line :
                decode_vars( task, input_line, facts )
                input_line = instream.readline()

        # determine values for task variables        
        valuation = dict()

        if 'gripper_empty' in facts :
                valuation[ task.gripper_empty.index ] = True
        
        for k in xrange( task.objects.num_blocks() ) :
                if block_clear(k) in facts :
                        valuation[task.block_clear[k].index] = True

        for l in xrange( task.objects.num_cylinders() ) :
                valuation[task.cylinder_empty[l].index] = True

        for k in xrange( task.objects.num_blocks() ) :
                for l in xrange( task.objects.num_cylinders() ) :
                        if block_in_cylinder(k,l) in facts :
                                valuation[task.block_container[k].index] = task.block_container_values[ in_cylinder(l) ]
                                valuation[task.cylinder_empty[l].index] = False
                                break
        
        for k in xrange( task.objects.num_blocks() ) :
                is_on_block = False
                for l in xrange( task.objects.num_blocks() ) :
                        if block_on_block(k,l) in facts :
                                valuation[task.block_position[k].index] = task.block_position_values[ on_block(l) ]
                                valuation[task.block_clear[l].index] = False
                                is_on_block = True
                                break
                if is_on_block : continue
                is_on_piston = False
                for l in xrange( task.objects.num_cylinders() ) :
                        if  block_on_piston(k) in facts :
                                valuation[ task.block_position[k].index ] = task.block_position_values[ 'on_piston' ]
                                is_on_piston = True
                                break
                if is_on_piston : continue
                assert False                        

        print( [ (task.state_vars[x].name, v) for x, v in valuation.items() ] )
        return State( task, [ (x,v) for x,v in valuation.items() ] )

def        make_goal( instream, task ) :
        valuation = {}

        input_line = instream.readline()

        facts = set()
        while 'end' not in input_line :
                decode_vars( task, input_line, facts )
                input_line = instream.readline()
        # determine values for task variables        
        valuation = dict()

        if 'gripper_empty' in facts :
                valuation[ task.gripper_empty.index ] = True
        
        for k in xrange( task.objects.num_blocks() ) :
                if block_clear(k) in facts :
                        valuation[task.block_clear[k].index] = True

        for k in xrange( task.objects.num_blocks() ) :
                for l in xrange( task.objects.num_cylinders() ) :
                        if block_in_cylinder(k,l) in facts :
                                valuation[task.block_container[k].index] = task.block_container_values[ in_cylinder(l) ]
                                break
        
        for k in xrange( task.objects.num_blocks() ) :
                is_on_block = False
                for l in xrange( task.objects.num_blocks() ) :
                        if block_on_block(k,l) in facts :
                                valuation[task.block_position[k].index] = task.block_position_values[ on_block(l) ]
                                is_on_block = True
                                break
                if is_on_block : continue
                is_on_piston = False
                for l in xrange( task.objects.num_cylinders() ) :
                        if  block_on_piston(k) in facts :
                                valuation[ task.block_position[k].index ] = task.block_position_values[ 'on_piston' ]
                                is_on_piston = True
                                break
                if is_on_piston : continue

        return [ (x,v) for x,v in valuation.items() ]

def         create_prob_from_file( filename, total_amount_of_fluid, constrained = True ) :

        if not os.path.exists( filename ) :
                raise RuntimeError( "Could not open problem file {0}".format( filename ) )

        f = open( filename, 'r' )

        num_blocks = int( f.readline() )
        num_cylinders = orig_num_cylinders = int( f.readline() )

        if orig_num_cylinders == 2 :
                num_cylinders = 3
        
        task_objs = make_instance_objects( num_blocks, num_cylinders, total_amount_of_fluid )
        the_task = HydraulicBlocksWorldTask( task_objs )
        if constrained:
                the_LP = LinearProgram( the_task )
                the_LP.model.printStats()
        else:
                the_LP = None

        # load initial state
        l = f.readline()        # consume header of section
        s0 = make_initial_state( f, the_task, orig_num_cylinders )
        G = make_goal( f, the_task )        

        the_task.create_actions_4ops()

        the_task.print_valuation( G, sys.stdout )

        print( "|A| = %d"%len(the_task.actions) )

        # the_LP.print_constraints()

        return HybridTask( the_task, the_LP, s0, G )        
