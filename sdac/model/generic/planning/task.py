from 	__future__ 	import 	print_function

from 	array		import	array
from 	variables 	import 	StateVar

import sys

class Task :

	def __init__( self, domain_name, instance_name ) :
		self.domain_name = domain_name
		self.instance_name = instance_name
		self.state_vars = []
		self.state_var_last_idx = 0
		self.last_lit_idx = 0
		self.lit_offsets = []
		self.actions = []

	def create_state_var( self, var_name, var_domain, default = None ) :
		if default is None :
			default = var_domain[0]
		x = StateVar( self.state_var_last_idx, var_name, var_domain, default )
		self.state_vars.append( x )
		self.state_var_last_idx += 1
		start = self.last_lit_idx
		end = self.last_lit_idx + x.domain_size()
		self.lit_offsets.append( ( start, end ) )
		self.last_lit_idx = end 
		return x

	def print_statistics( self, fileobj ) :
		print('Domain: {0}'.format( self.domain_name ), file=fileobj )
		print('Instance: {0}'.format( self.instance_name ), file=fileobj )
		print('|V| = {0}, |A| = {1}'.format( len(self.state_vars), len(self.actions) ), file = fileobj )

	def print_valuation( self, assignment, file_obj ) : 

		for x_idx, v in assignment :
                        try:
                                v_name = self.state_vars[x_idx].domain_print_names[v]
                        except:
                                v_name = v
			print( '{0}={1}'.format(self.state_vars[x_idx].name,v_name), file=file_obj )

	def create_bool_state_var( self, var_name ) :
		return self.create_state_var( var_name, [ False, True ], False )


	def default_valuation( self ) :
		return [ ( x.index, x.domain[ x.default_value ] ) for x in self.state_vars ]

class State :

	bTrue = chr(0xff)
	bFalse = chr(0x00)

	def __init__( self, task, valuation, check_domain = False ) :
		#print(task.state_vars)
                #print(valuation)
                
		self.task = task
		self.literals = array('c',[ State.bFalse ] * self.task.last_lit_idx )
		self.relaxed = False
		
		if check_domain :
			for x, v in valuation :
				if not task.state_vars[x].valid_value(v) :
					domain_string = ','.join( [ str(v) for v in self.task.state_vars[x].domain ] )
					params = ( v, self.task.state_vars[x].name, domain_string )
					raise ValueError( 'Value "%s" does not belong to domain of variable "%s": { %s }'%params )

		for x,v in valuation :
			start, _ = self.task.lit_offsets[ x ]
			offset = start + self.task.state_vars[x].value_index[ v ]
			self.literals[ offset ] = State.bTrue 


	def __eq__( self, other ) :
		for i in xrange( len(self.literals) ) :
			if other.literals[i] != self.literals[i] : return False
		return True

	def __ne__( self, other ) :
		return not self.__eq__(other)

	def __hash__(self ) :
		h = 0
		for c in self.literals :
			h = 101 * h + ord( c )
		return h	

	def num_literals( self ) :
		return len(self.literals)

        def __str__( self ):
                return ''.join(['1' if lit == self.bTrue else '0' for lit in self.literals])

	def copy( self ) :
		s = State( self.task, [] )
		s.literals = array( 'c', self.literals )
                s.relaxed = self.relaxed
		return s

	def possible( self, valuation ) :
		for x, v in valuation :
			start, end =  self.task.lit_offsets[ x ]
			offset = start + self.task.state_vars[x].value_index[ v ]
			if self.literals[offset] == State.bFalse  : return False

		return True
	
	def satisfies( self, valuation ) :

		if self.relaxed :
			for x, v in valuation :
				start, end =  self.task.lit_offsets[ x ]
				offset = start + self.task.state_vars[x].value_index[ v ]
				if self.literals[offset] == State.bFalse  : return False
				other_values = [ self.literals[ k ] for k in range( start, end ) if k != offset ]
				if State.bTrue in other_values : return False # X != v is possibly true

			return True

		for x, v in valuation :
			start, end =  self.task.lit_offsets[ x ]
			offset = start + self.task.state_vars[x].value_index[ v ]
			if self.literals[offset] == State.bFalse  : return False

		return True

	def relaxed_set_vec( self, valuation ) :
		"""
		Here we don't need to flip the truth value of multi-valued variables
		literals
		"""
		self.relaxed = True
		for x,v in valuation :
			start, end = self.task.lit_offsets[ x ]
			offset = start + self.task.state_vars[x].value_index[ v ]
			self.literals[ offset ] = State.bTrue
		
	def relaxed_set( self, x, v ) :
		"""
		Here we don't need to flip the truth value of multi-valued variables
		literals
		"""
		self.relaxed = True		
		try :
			var_index = x.index
			start, end = self.task.lit_offsets[var_index]
			self.literals[ start + x.value_index[ v ] ] = State.bTrue
		except AttributeError :
			var = self.task.state_vars[x]
			start, end = self.task.lit_offsets[x]
			self.literals[ start + var.value_index[ v ] ] = State.bTrue
	


	def set_vec( self, valuation ) :
		for x,v in valuation :
			start, end = self.task.lit_offsets[ x ]
			for offset in range( start, end ) :
				self.literals[offset] = State.bFalse
			offset = start + self.task.state_vars[x].value_index[ v ]
			self.literals[ offset ] = State.bTrue
		

	def set( self, x, v ) :
		try :
			var_index = x.index
			start, end = self.task.lit_offsets[var_index]
			for offset in range( start, end ) :
				self.literals[offset] = State.bFalse
			self.literals[ start + x.value_index[ v ] ] = State.bTrue
		except AttributeError :
			var = self.task.state_vars[x]
			start, end = self.task.lit_offsets[x]
			for offset in range( start, end ) :
				self.literals[offset] = State.bFalse
			self.literals[ start + var.value_index[ v ] ] = State.bTrue

	def iter_values( self ) :
		for i in xrange( len(self.task.state_vars) ) :
			start, end = self.task.lit_offsets[i]
			for offset in range( start, end ) :
				if self.literals[offset] == State.bTrue :
					yield ( i, self.task.state_vars[i].domain[offset-start] )

	def get_valuation( self ) :
		return [ assignment for assignment in self.iter_values() ]

	def value( self, x ) :
		try :
			var_index = x.index
			start, end = self.task.lit_offsets[var_index]
			for offset in range( start, end ) :
				if self.literals[offset] == State.bTrue :
					return x.domain[ offset - start ]
			raise ValueError( 'Variable %s has no value set!'%x.name )
		except AttributeError :
			var = self.task.state_vars[x]
			start, end = self.task.lit_offsets[x]
			for offset in range( start, end ) :
				if self.literals[offset] == State.bTrue :
					return var.domain[ offset - start ]
			raise ValueError( 'Variable %s has no value set!'%var.name )

	def write( self, file_obj ) :
		for x in self.task.state_vars :
                        try:
			        print( '%s=%s'%(x.name, self.value(x)), file = file_obj )
                        except ValueError:
                                print( ' %s has no value!' % (x.name), file=file_obj)

        def print_relaxed(self):
		for idx in xrange( len(self.task.state_vars) ) :
                        print(self.task.state_vars[idx].name + " = {", end='')
			start, end = self.task.lit_offsets[idx]
                        first = True
			for offset in range( start, end ) :
				if self.literals[offset] == State.bTrue :
                                        if not first:
                                                print(", ", end='')
                                        print(self.task.state_vars[idx].domain[offset-start], end='')
                                        first = False
                        print("}")

	def dump(self) :
		self.write( sys.stdout )

	def dump_true_facts( self ) :
		self.write( sys.stdout ) 
