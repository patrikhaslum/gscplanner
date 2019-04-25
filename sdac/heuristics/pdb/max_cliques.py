"""
	This module implements the algorithm to compute the set of
	maximal cliques for a graph G discussed in this paper
	
	The worst-case time complexity for generating all maximal cliques
	E Tomita, A Tanaka, H Takahashi
	Computing and Combinatorics, 2004
"""

class Graph :
	"""
		A simplistic Graph class
	"""

	def __init__( self, V ) :
		self.V = set(V) # must be a list
		self.adj = { v : set() for v in self.V }

	def add_edge( self, v, w ) :
		assert v in self.V and w in self.V
		self.adj[v].add(w)
		self.adj[w].add(v)

	def adjacent( self, v, w, ) :
		return w in self.adj[v]	

	def edges( self ) :
		for v, w in self.adj.iteritems() :
			yield (v,w) 

class Cliques :

	def __init__( self, G ) :
		self.G = G
		self.Q = set()
		self.max_clique_set = set()

	@staticmethod
	def enumerate_max_cliques( G ) :
		cliques = Cliques( G )
		cliques.expand( G.V, G.V )

		return cliques.max_clique_set

	def expand( self, sub_graph, candidates ) :
		if len(sub_graph) == 0 :
			self.max_clique_set.add( frozenset([ v for v in self.Q]) ) 
			return
		_, u = max( [ (candidates & self.G.adj[u], u) for u in sub_graph ] )
		ext_u = candidates - self.G.adj[u]
		while len( ext_u ) > 0 :
			q = ext_u.pop()
			self.Q.add( q ) 
			new_sub_graph = sub_graph & self.G.adj[q]
			new_candidates = candidates & self.G.adj[q]
			self.expand( new_sub_graph, new_candidates )
			self.Q.remove(q)
		

if __name__ == '__main__' :

	# Example from Tomita et al paper
	V = range(1,10)
	example_graph = Graph(V)
	
	edges = [ (1,9), (1,2), (9,2), (9,3), (2,3), (3,8), (3,4), (8,4), (8,6), (8,7), (4,7), (4,6), (4,5), (5,6), (7,6) ] 

	for edge in edges :
		apply(example_graph.add_edge, edge) 

	for clique in Cliques.enumerate_max_cliques( example_graph ) :
		print clique

