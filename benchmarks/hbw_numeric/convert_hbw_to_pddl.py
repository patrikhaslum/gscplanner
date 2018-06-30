#!/usr/bin/python

from __future__ import	print_function
import sys
import os

#import hbw3

FOR_VAL=False

def decode_vars( input_line, block_names, block_wts, cyl_names, facts, ne_cyl, cyl_wts ) :
    tokens = input_line.split ()
    if tokens [0] == "gripper_empty":
	facts.append('(handempty)')
	return

    elif tokens [0] == "block_on_piston":
	blockId = int (tokens [1])
	facts.append('(on_piston ' + block_names[blockId] + ')')
	return

    elif tokens [0] == "block_in_cylinder":
	blockId = int (tokens [1])
	cylId = int (tokens [2])
	facts.append( '(in ' + block_names[blockId] + ' ' + cyl_names[cylId] + ')' )
        ne_cyl.add(cylId)
        cyl_wts[cylId] += block_wts[blockId]
	return

    elif tokens [0] == "block_clear":
	blockId = int (tokens [1])
	facts.append( '(clear ' + block_names[blockId] + ')' )
	return

    elif tokens [0] == "block_on_block":
	tblockId = int (tokens [1])
        bblockId = int (tokens [2])
        facts.append( '(on ' + block_names[tblockId] + ' ' +  block_names[bblockId] + ')' )
        return

    # fact name not recognised
    print(input_line)
    assert False

def height_for_cylinder(cname, cylinder_names):
    s = "(- (* (/ 1 (total_area)) (volume)) (* (/ (- (total_area) (area " + cname + ")) (* (total_area) (area " + cname + "))) (/ (weight_on " + cname + ") (density))))"
    for ocn in cylinder_names:
        if ocn != cname:
            s = "(+ " + s + " (* (/ 1 (total_area)) (/ (weight_on " + ocn + ") (density))))"
    return s

if __name__ == '__main__':

    if len(sys.argv) < 2 :
	print( 'No instance specified!', file=sys.stderr )
	sys.exit(1)

    hbw_file_name = sys.argv[1]
    if not os.path.exists( hbw_file_name ) :
	raise RuntimeError( "file {0} does not exist".format( hbw_file_name ) )

    problem_name, _ = os.path.splitext(os.path.basename(hbw_file_name))

    # get volume
    if len(sys.argv) < 3 :
	total_amount_of_fluid = 10
    else :
	total_amount_of_fluid = int(sys.argv[2])

    # get exp # of cyls
    if len(sys.argv) < 4 :
	expected_num_cylinders = 3
    else :
	expected_num_cylinders = int(sys.argv[3])

    f = open( hbw_file_name, 'r' )

    num_blocks = int( f.readline() )
    num_cylinders = int( f.readline() )

    if num_cylinders == 2 :
	num_cylinders = 3

    if num_cylinders != expected_num_cylinders:
        print( 'wrong number of cylinders: ', num_cylinders )
        sys.exit(0)

    # magic numbers
    block_weights = [ 5, 9, 7, 2, 4, 7, 1, 6, 4, 8 ]
    cylinder_areas = [ 2, 2, 1, 4, 1 ]
    cylinder_heights = [ 10, 10, 10, 15, 15 ]
    fluid_density = 5

    block_names = [ 'b{0}'.format(i) for i in xrange(num_blocks) ]
    cylinder_names = [ 'c{0}'.format(i) for i in xrange(num_cylinders) ]

    init_facts = []
    init_non_empty = set()
    init_cyl_wts = [0 for i in xrange(num_cylinders)]

    line = f.readline() # skip header line
    line = f.readline()
    while 'goal' not in line :
	decode_vars( line, block_names, block_weights, cylinder_names,
                     init_facts, init_non_empty, init_cyl_wts )
	line = f.readline()

    goal_facts = []
    goal_non_empty = set()
    goal_cyl_wts = [0 for i in xrange(num_cylinders)]

    line = f.readline()
    while 'end' not in line :
	decode_vars( line, block_names, block_weights, cylinder_names,
                     goal_facts, goal_non_empty, goal_cyl_wts )
	line = f.readline()

    # done reading input
    f.close()

    if FOR_VAL:
        of_name = problem_name + '_v' + str(total_amount_of_fluid) + '_for_val'
    else:
        of_name = problem_name + '_v' + str(total_amount_of_fluid)
    of = open(of_name + '.pddl', 'w')
    print("(define (problem {0}_v{1})".format(problem_name, total_amount_of_fluid), file=of)
    print("  (:domain hydraulic_blocks_world)", file=of)
    print("  (:objects " + " ".join(block_names) + " - block)", file=of)
    print("  (:init", file=of)
    for fact in init_facts:
        print("    " + fact, file=of)
    for i in xrange(num_cylinders):
        if i not in init_non_empty:
            print("    (clear_piston " + cylinder_names[i] + ")", file=of)
    for i in xrange(num_blocks):
        print("    (= (weight " + block_names[i] + ") " + str(block_weights[i]) + ")", file=of)
    for i in xrange(num_cylinders):
        print("    (= (area " + cylinder_names[i] + ") " + str(cylinder_areas[i]) + ")", file=of)
    print("    (= (total_area) " + str(sum(cylinder_areas[:num_cylinders])) + ")", file=of)
    for i in xrange(num_cylinders):
        print("    (= (height " + cylinder_names[i] + ") " + str(cylinder_heights[i]) + ")", file=of)
    for i in xrange(num_cylinders):
        print("    (= (weight_on " + cylinder_names[i] + ") " + str(init_cyl_wts[i]) + ")", file=of)
    print("    (= (volume) " + str(total_amount_of_fluid) + ")", file=of)
    print("    (= (density) " + str(fluid_density) + ")", file=of)
    print("   )", file=of)
    print("  (:goal (and " + " ".join(goal_facts) + "))", file=of)
    if FOR_VAL:
        print("  (:constraints (and", file=of)
        for cname in cylinder_names:
            print("    (always (>= " + height_for_cylinder(cname, cylinder_names) + " 0))", file=of)
            print("    (always (<= " + height_for_cylinder(cname, cylinder_names) + " (height " + cname + ")))", file=of)
        print("   ))", file=of)
    print(" )", file=of)
    of.close()
