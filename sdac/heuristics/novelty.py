from heuristic_base				import	Heuristic

import logging
import time
import sys
import heapq
import itertools

class Novelty_Table :

	def __init__(self) :
		self.novelty_table = []
		self.max_novelty = None
	
	def 	set_novelty_bound( self, value ) :
		self.max_novelty = value
		self.novelty_table = [ set() for i in xrange(0,value) ]

	def 	get_tuples( self, s, size ) :
		seen = set()
		seen_add = seen.add
		for t in itertools.permutations( s.iter_values(), size ) :
			l = list(t)
			l.sort()
			t = tuple(l)
			if t in seen : continue
			yield t
		

	def 	evaluate_novelty( self, s ) :
		i = 1
		novelty = 0
		while i <= self.max_novelty  :
			for t in self.get_tuples( s, i ) :
				if t in self.novelty_table[i-1] : continue
				if novelty == 0 : novelty = i
				self.novelty_table[i-1].add( t )
			i += 1
		if novelty == 0 : novelty = s.num_literals() + 1 
		return novelty	

