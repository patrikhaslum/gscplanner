#This should create a planning graph given the description of a network.
#Things that should be specified are the network elements (generators, powerlines and nodes).
#This should generate the constraints (Kirchoff's laws, capacity constraints, both sides fed) and 
#opening and closing switches actions. The state on switches at the time when the switches are created
#are the start state s_0. Variables (primary and secondary) are also created here. 

#To get the planning problem, the only thing missing is the goal (which can be defined as all buses fed).

#powernetworks that allow only two end lines
#lines don't have consumption, only buses do (and some buses also have generation)

import math

#line attached to a circuitbreaker
class TECircuitBreakerLine: 
        def __init__(self,name,connections,capacity,start_closed,final_closed,susceptance=None):
                self.name=name
                self.connections=connections #only one connection, to the circuitbreaker bus
                self.capacity=capacity
                if susceptance is not None:
                        self.susceptance = susceptance
                else:
                        self.susceptance=-capacity*(math.pi/12.0)
                self.start_closed=start_closed
                self.final_closed=final_closed

        def __str__(self):
                s="CircuitbreakerLine {0}, start_closed? {1}, final_closed?: {2}, capacity: {3}, susc: {4} connection: {5}".format(self.name,self.start_closed,self.final_closed,self.capacity,self.susceptance,self.connections[0].name)
                return s

        def __repr__( self ) :
                return 'CB Line {0}'.format( self.name )

#line with a corresponding RDevice
class TERDeviceLine:
        def __init__(self,name,connections,capacity,start_closed,final_closed,susceptance=None):
                self.name=name
                self.connections=connections #a list of buses (two buses)
                self.capacity=capacity
                if susceptance is not None:
                        self.susceptance = susceptance
                else:
                        self.susceptance=-capacity*(math.pi/12.0)
                self.start_closed=start_closed
                self.final_closed=final_closed

        def __str__(self):
                s="TE R-Device Line {0}, start_closed?: {1}, final_closed?: {2}, capacity: {3}, connections: {4},{5}, susc: {6}".format(self.name,self.start_closed,self.final_closed,self.capacity,self.connections[0].name,self.connections[1].name,self.susceptance)
                return s

        def __repr__( self ) :
                return 'TE R-Device Line {0}'.format(self.name)

#like TERDevice, except it has no opening and closing actions
class TEMDeviceLine:
        def __init__(self,name,connections,capacity,start_closed,susceptance=None):
                self.name=name
                self.connections=connections
                self.capacity=capacity
                if susceptance is not None:
                        self.susceptance = susceptance
                else:
                        self.susceptance=-capacity*(math.pi/12.0)
                self.start_closed=start_closed
                self.final_closed=start_closed #always same as the start state?

        def __str__(self):
                s="TE M-Device Line {0}, start_closed?: {1}, final_closed?: {2}, capacity: {3}, connections: {4},{5}".format(self.name,self.start_closed,self.final_closed,self.capacity,self.connections[0].name,self.connections[1].name)
                return s

        def __repr__( self ) :
                return 'TE M-Device Line {0}'.format( self.name )


#bus
class TEBus: 
        def __init__(self,name,fault,load_max,generation_max,feed):
                self.name=name
                self.fault=fault
                self.load_max=load_max #maximum load
                self.generation_max=generation_max #power generated
                self.feed=feed #whether fed in the final state
                self.connections_in=[]
                self.connections_out=[]

        def __str__(self):
                connections_in_string=""
                for c_in in self.connections_in:
                        connections_in_string=connections_in_string+c_in.name+" "
                connections_out_string=""
                for c_out in self.connections_out:
                        connections_out_string=connections_out_string+c_out.name+" "
                s="Bus {0}, fault?: {1}, load_max: {2}, generation_max: {3}, feed? {6}, connection_in: {4}, connection_out: {5}".format(self.name,self.fault,self.load_max,self.generation_max,connections_in_string,connections_out_string,self.feed)
                return s

        def __repr__( self ) :
                return 'Bus {0}, has fault? {1}, in conn: {2}, out conn: {3}'.format( self.name, self.fault, len(self.connections_in), len(self.connections_out) )


#powernetwork should contain all the loads, powerlines and generators
class TEPowerNetwork:

        def __init__(self,name="",TECircuitbreakerLines=[],TERDeviceLines=[],TEMDeviceLines=[],TEBuses=[]):
                self.name=name
                self.TECircuitbreakerLines=TECircuitbreakerLines
                self.TERDeviceLines=TERDeviceLines
                self.TEMDeviceLines=TEMDeviceLines
                self.TEBuses=TEBuses
                #updating the the connection_in and connection_out for circuit breakers and rdevices

                #NOTE: As cb lines draw no power, this is simply not needed.
                #        for line in self.TECircuitbreakerLines:
                #          for bus in line.connections: #powerflow out of circuitbreaker is positive?
                #            bus.connection_out=line #NOTE: Not sure about this??

                for device in self.TERDeviceLines+self.TEMDeviceLines: #first line is line out, second line is line in?
                        device.connections[0].connections_out.append(device) #WHAT?? #It's ok I think...
                        device.connections[1].connections_in.append(device) #Are you sure about this?? I am not... #I think I am now
                self.final_supplied_load=self.find_final_supplied_load()

        def __str__(self):
                s="Powernetwork {0}\n".format(self.name)
                s=s+"\nTECircuitbreakerLines:\n"
                for cbl in self.TECircuitbreakerLines:
                        s=s+str(cbl)+"\n"
                s=s+"\nRDevicesLines:\n"
                for terdl in self.TERDeviceLines:
                        s=s+str(terdl)+"\n"
                s=s+"\nMDevicesLines:\n"
                for temdl in self.TEMDeviceLines:
                        s=s+str(temdl)+"\n"
                s=s+"\nBuses:\n"
                for teb in self.TEBuses:
                        s=s+str(teb)+"\n"
                return s

        def num_faults( self ) :
                count = 0
                for teb in self.TEBuses :
                        if teb.fault : count +=1
                return count

        def add_fault(self,name): #adds fault to a powerline with a given name
                for teb in self.TEBuses:
                        if teb.name==name:
                                teb.fault=True
                                break

        def open_all_cbs(self):
                for cb in self.TECircuitbreakerLines:
                        cb.start_closed=False

        def open_cbs_list(self,cbs_list):
                for cb_label in cbs_list:
                        for powernetwork_cb in self.TECircuitbreakerLines:
                                if powernetwork_cb.name==cb_label:
                                        powernetwork_cb.state_closed=False

        def find_final_supplied_load(self):
                supplied_load=0.0
                for b in self.TEBuses:
                        if b.feed:
                                supplied_load=supplied_load+b.load_max
                return supplied_load
