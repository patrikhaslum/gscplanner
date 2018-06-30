import json

class Bus:
    def __init__(self, name, final_require_fed):
        self.name = name
        self.final_require_fed = final_require_fed

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
    
    def __str__(self):
        result = '\n'
        result += '    buses:\n'
        result += '\n'.join(['        ' + str(x) for x in self.buses])
        result += '\n'
        result += '    branches:\n'
        result += '\n'.join(['        ' + str(x) for x in self.branches])
        return result
