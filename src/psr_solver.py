#!/usr/bin/python

from __future__ import print_function

import sys
import os
import logging
import time

from 	gurobipy			import	setParam

from 	model.generic.hybrid.task	import	HybridTask

from 	psr.two_end_line.parsing	import	load_network_description
from 	psr.two_end_line.planning	import	TwoEndLinePSRTask, make_initial_state
from 	psr.two_end_line.lp		import	LinearProgram

import	solver_support

def parse_instance( instance_filename ) :

	the_network = load_network_description( instance_filename )

	#print(the_network)

	logging.info( 'Loaded network {0}'.format( the_network.name ) )
	logging.info( '\tCircuit breakers: {0}'.format( len(the_network.TECircuitbreakerLines) ) )
	logging.info( '\tLines with Remote Switch: {0}'.format( len(the_network.TERDeviceLines) ) )
	logging.info( '\tLines with Manual Switch: {0}'.format( len(the_network.TEMDeviceLines) ) )
	logging.info( '\tBuses: {0} Faults: {1}'.format( len( the_network.TEBuses ), the_network.num_faults() ) )

	the_task = TwoEndLinePSRTask( the_network )
	the_task.print_statistics( sys.stdout )	
	the_LP = LinearProgram( the_task )
	the_hybrid_task = HybridTask( the_task, the_LP, make_initial_state(the_task), [], the_LP.make_bus_feeding_constraints_2( the_task ) )

	the_LP.model.printStats()
	#the_hybrid_task.write(sys.stdout)
	the_hybrid_task.s0.check_valid()

	logging.info( 'Task initial state valid? %s'%the_hybrid_task.s0.valid )	

	if not the_hybrid_task.s0.valid :
		sys.exit(1)

	return the_hybrid_task	

def main() :
	setParam( 'LogFile', '' )
	setParam( 'LogToConsole', 0 )
	setParam( 'OutputFlag', 0 )
	logging.basicConfig(	level='INFO',
				#level='DEBUG',
				format='%(asctime)s %(levelname)-8s %(message)s',
				stream=sys.stdout)
	
	if len( sys.argv ) < 2 :
		print( 'Missing argument: input problem!', file=sys.stderr )
		sys.exit(1)

	if len( sys.argv ) < 3 :
		configuration = 'ppa_star_hplus'
	else :
		configuration = sys.argv[2]

	instance = sys.argv[1]

	if not os.path.exists( instance ) :
		print( 'Could not find {0}'.format( instance ), file=sys.stderr )
		sys.exit(1)
	if configuration not in solver_support.configs :
		print( 'Specified configuration name {0} not recognized'.format( configuration ) )
		print( 'Available configurations are:' )
		for cfg in solver_support.configs :
			print( '\t{0}'.format( cfg ) )
		sys.exit(1)
	print ( 'Configuration {0} is active'.format( configuration ) )

	task = parse_instance( instance ) 

	solver_support.solve( configuration, task )


if __name__ == '__main__' :
	main()
