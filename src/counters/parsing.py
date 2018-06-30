from __future__ import print_function

import os
import sys
import re

def parse_instance( instfile ) :

	with open(instfile) as instream :
		text = instream.read()

	#print( 'Chars read {0}\n{1}'.format( len(text), text ) )

	objects = re.compile( r'\(:objects(\s|[^:])+\)' )
	init = re.compile( r'\(:init(\s|[^:])+\)' )
	goal = re.compile( r'\(:goal(\s|[^:])+\)' )

	objects_match = objects.search( text )

	if objects_match is None :
		print( 'Could not find instance objects!', file=sys.stderr )
		sys.exit(1)

	objects_text = objects_match.group()
	#print( 'Objects:\n{0}'.format( objects_text ) )


	counter_names = re.compile( r'.+ - counter' )
	counter_names_match = counter_names.search( objects_text )
	if counter_names_match is None :
		print( 'Could not find any counter variables!', file=sys.stderr )
		sys.exit(1)

	counter_names_text = counter_names_match.group()
	counters = [ tok for tok in counter_names_text.split('-')[0].strip().split(' ') ]
	print('Counters: {0}'.format( counters ) )

	init_match = init.search( text )
	
	if init_match is None :
		print( 'Could not find instance init!', file=sys.stderr )
		sys.exit(1)

	init_text = init_match.group()
	#print( 'Init:\n{0}'.format( init_text ) )

	max_value = re.compile( r'\(max_int\) \d+' )
	max_value_match = max_value.search( init_text )
	if max_value_match is None :
		print( 'Could not find max value!', file=sys.stderr )
	max_value = int( max_value_match.group().split(' ')[1] )
	print( 'Max value: {0}'.format( max_value ) )

	init_values = []
	assignment = re.compile( r'\(= \(value ([\w\d]+)\) (\d+)\)' )
	for x, v in assignment.findall( init_text ) :
		init_values.append( (x, int(v)) )
	#print( 'Init: {0}'.format(init_values))

	goal_match = goal.search( text )
	
	if goal_match is None :
		print( 'Could not find instance goal!', file=sys.stderr )
		sys.exit(1)

	goal_text = goal_match.group()
	#print( 'Goal:\n{0}'.format( goal_text ) )
	relation = re.compile( r'\(([<>=]) \(value ([\w\d]+)\) \(value ([\w\d]+)\)\)' )	
	goal_condition = relation.findall( goal_text )
	print( 'Goal: {0}'.format( goal_condition ) )
	
	return  counters, max_value, init_values, goal_condition
