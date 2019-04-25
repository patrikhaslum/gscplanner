import json

class Bus:
    def __init__(self, name, final_require_fed, sVar = None, p = 0):
        self.name = name
        self.final_require_fed = final_require_fed
        self.p = p
        #Every bus gets a secondary_variable_i when it is created. This value is used when creating variables Model and 
        #when creating conditional costs. 
        self.secondary_variable_i = sVar  

    def __str__(self):
        return 'name: ' + self.name + ', final_require_fed: ' + str(self.final_require_fed)

class Branch:
    def __init__(self, name, init_closed):
        self.name = name
        self.init_closed = init_closed
    
    def __str__(self):
        return 'name: ' + self.name + ', init_closed: ' + str(self.init_closed)

class Network:
    def __init__(self):
        self.buses = list()
        self.branches = list()
        self.total_load = None
    
    def __str__(self):
        result = '\n'
        result += '    buses:\n'
        result += '\n'.join(['        ' + str(x) for x in self.buses])
        result += '\n'
        result += '    branches:\n'
        result += '\n'.join(['        ' + str(x) for x in self.branches])
        return result
    
    def find_total_load(self): 
        l = 0 
        for b in self.buses: 
            #print(b.name, b.p)
            l += b.p
        self.total_load = l
