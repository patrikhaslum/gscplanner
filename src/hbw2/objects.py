#----------------------------------------

#classes which define elements
# -- Block, Cylinder, Gripper, Fluid

#----------------------------------------

class Block:
	def __init__ (self, index, weight, height, length, breadth):
		self.index = index
		self.weight = weight
		self.height = height
		self.length = length
		self.breadth = breadth
		self.area = self.length * self.breadth
	
	def update_area( self ) :
		self.area = self.length * self.breadth

class Cylinder:
    def __init__ (self, index, area, height):
        self.index = index
        self.area = area
        self.height = height

    
class Gripper:
    def __init__ (self, index):
        self.index = index

class Fluid:
    def __init__ (self, density, total_fluid_in_cylinders):
        self.density = density
        self.total_fluid_in_cylinders = total_fluid_in_cylinders

class InstanceObjects :
	def __init__ (self, num_blocks, num_cylinders):
		self.blocks = []
		self.cylinders = []
		self.grippers = []
		self.fluid = 0
   
	def num_blocks( self ) :
		return len( self.blocks )
	
	def num_cylinders( self ) :
		return len( self.cylinders )
 
	def get_fluid_density (self):
		return self.fluid.density

	def create_block (self, wt, ht, ln, br):
		"""
		@param	wt	weight of the block
		@param 	ht	height of the block
		@param 	ln	length of the block
		@param	br	breadth of the block
		"""
		b = Block (len(self.blocks), wt, ht, ln, br)
		self.blocks.append(b)

	def create_cylinder (self, area, ht):
		"""
		@param	area	area of the cylinder
		@param	ht	height of the cylinder
		"""
		self.cylinders.append (Cylinder (len (self.cylinders), area, ht))

	def create_fluid (self, density, total_fluid_in_cylinders):
		self.fluid = Fluid (density, total_fluid_in_cylinders)

	def create_gripper (self):
		self.grippers.append (Gripper (len (self.grippers)))
	
