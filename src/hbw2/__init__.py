from hbw2.objects                        import         InstanceObjects
from hbw2.planning                        import         HydraulicBlocksWorldTask
from hbw2.lp                                import         LinearProgram
from model.generic.planning.task        import         State
from model.generic.hybrid.task                import        HybridTask

import sys
import os

def make_blocks_and_cylinders() :
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
        obj_collection.create_fluid( 5, 10 )

        return obj_collection

def         make_instance_objects( num_blocks, num_cylinders ) :
        object_collection = make_blocks_and_cylinders()
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

def        decode_var( task, input_line ) :
        tokens = input_line.split ()
        if tokens [0] == "gripper_empty":
                return task.gripper_empty.index
    
        elif tokens [0] == "block_on_piston":
                blockId = int (tokens [1])
                return task.block_on_piston [blockId].index

        elif tokens [0] == "block_in_cylinder":
                blockId = int (tokens [1])
                cylId = int (tokens [2])
                return task.block_in_cylinder [(blockId,cylId)].index

        elif tokens [0] == "block_clear":
                blockId = int (tokens [1])
                return task.block_clear [blockId].index

        elif tokens [0] == "block_on_block":
                tblockId = int (tokens [1])
                bblockId = int (tokens [2])
                return task.block_on_block [(tblockId,bblockId)].index


def        make_initial_state( instream, task, orig_num_cylinders ) :
        # 1. initialize all to False
        valuation = dict( task.default_valuation() ) # needs to be a full one!

        # 2. initialize actual values
        input_line = instream.readline()
        while 'goal' not in input_line :
                valuation[ decode_var( task, input_line ) ] = True        
                input_line = instream.readline()

        if orig_num_cylinders == 2 :
                valuation[ task.cylinder_empty[2].index ] = True
        print( [ (task.state_vars[x].name, v) for x, v in valuation.items() ] )
        return State( task, [ (x,v) for x,v in valuation.items() ] )

def        make_goal( instream, task ) :
        valuation = {}

        input_line = instream.readline()

        while 'end' not in input_line :
                valuation[ decode_var( task, input_line ) ] = True
                input_line = instream.readline()
        return [ (x,v) for x,v in valuation.items() ]

def         create_prob_from_file( filename ) :

        if not os.path.exists( filename ) :
                raise RuntimeError( "Could not open problem file {0}".format( filename ) )

        f = open( filename, 'r' )

        num_blocks = int( f.readline() )
        num_cylinders = orig_num_cylinders = int( f.readline() )

        if orig_num_cylinders == 2 :
                num_cylinders = 3
        
        task_objs = make_instance_objects( num_blocks, num_cylinders )
        the_task = HydraulicBlocksWorldTask( task_objs )
        the_LP = LinearProgram( the_task )
        the_LP.model.printStats()

        # load initial state
        l = f.readline()        # consume header of section
        s0 = make_initial_state( f, the_task, orig_num_cylinders )
        G = make_goal( f, the_task )        

        the_task.create_actions_4ops()

        the_task.print_valuation( G, sys.stdout )

        print( "|A| = %d"%len(the_task.actions) )

        return HybridTask( the_task, the_LP, s0, G )        
