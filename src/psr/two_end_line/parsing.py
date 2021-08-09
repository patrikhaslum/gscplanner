from .network                import *

def load_network_description(input_file_name):
        
        buses_list=[]
        rdevice_list=[]
        mdevice_list=[]
        cb_list=[]

        input_file=open(input_file_name)
        all_lines=input_file.readlines()
        
        #finding the devices
        for line in all_lines:
                split_line=line.split()
                #for word in split_line:
                 # print word
                if len(split_line)==0: continue

                if split_line[0]=="line": #if the first word is val, it's a device
                        #print "Found line"
                        if split_line[4]=="circuit_breaker": #it is a circuit breaker line
                                new_cb_name=split_line[1]
                                new_cb_connection=split_line[2]
                                new_cb_capacity=float(split_line[3])
                                if split_line[5]=="closed":
                                        new_cb_start_closed=True
                                else:
                                        new_cb_start_closed=False
                                if split_line[-1]=="to-open":
                                        new_cb_final_closed=False
                                elif split_line[-1]=="to-close":
                                        new_cb_final_closed=True
                                else:
                                        new_cb_final_closed=new_cb_start_closed
                                new_cb=TECircuitBreakerLine(new_cb_name,[new_cb_connection],new_cb_capacity,new_cb_start_closed,new_cb_final_closed)
                                cb_list.append(new_cb)
                        elif split_line[5]=="mdevice":
                                new_m_name=split_line[1]
                                new_m_connection1=split_line[2]
                                new_m_connection2=split_line[3]
                                new_m_capacity=float(split_line[4])
                                if split_line[6]=="closed":
                                        new_m_start_closed=True
                                else:
                                        new_m_start_closed=False
                                if split_line[-1]=="to-open":
                                        new_m_final_closed=False
                                elif split_line[-1]=="to-close":
                                        new_m_final_closed=True
                                else:
                                        new_m_final_closed=new_cb_start_closed
                                new_m=TEMDeviceLine(new_m_name,[new_m_connection1,new_m_connection2],new_m_capacity,new_m_start_closed)
                                mdevice_list.append(new_m)
                        elif split_line[5]=="rdevice":
                                new_r_name=split_line[1]
                                new_r_connection1=split_line[2]
                                new_r_connection2=split_line[3]
                                new_r_capacity=float(split_line[4])
                                if split_line[6]=="closed":
                                        new_r_start_closed=True
                                else:
                                        new_r_start_closed=False
                                if split_line[-1]=="to-open":
                                        new_r_final_closed=False
                                elif split_line[-1]=="to-close":
                                        new_r_final_closed=True
                                else:
                                        new_r_final_closed=new_cb_start_closed
                                new_r=TERDeviceLine(new_r_name,[new_r_connection1,new_r_connection2],new_r_capacity,new_r_start_closed,new_r_final_closed)
                                rdevice_list.append(new_r)
                elif split_line[0]=="bus":
                        new_bus_name=split_line[1]
                        new_bus_fault=string_to_boolean(split_line[2])
                        new_bus_load=float(split_line[3])
                        try:
                                new_bus_generation=float(split_line[4])
                        except (IndexError,ValueError):
                                #        print "exception: 0.0"
                                new_bus_generation=0.0
                        if split_line[-1]=="feed":
                                new_bus_feed=True
                        else:
                                new_bus_feed=False
                        new_bus=TEBus(new_bus_name,new_bus_fault,new_bus_load,new_bus_generation,new_bus_feed)
                        buses_list.append(new_bus)

        #converting the connections string to actual connections
        for device in cb_list+rdevice_list+mdevice_list:
                device.connections=string_to_connections(device,buses_list)
        """
        print "The network elements are:"
        print "Number of cbs: ",len(cb_list)
        print "Number of rdevices:",len(rdevice_list)
        print "Number of mdevices:",len(mdevice_list)
        print "Number of buses:", len(buses_list)
        """
        powernetwork=TEPowerNetwork(name="{0}_network".format(input_file_name),TECircuitbreakerLines=cb_list,TERDeviceLines=rdevice_list,TEMDeviceLines=mdevice_list,TEBuses=buses_list)
        
        return powernetwork


def string_to_boolean(s):
        if(s in ["True","true"]):
                return True
        return False 


#function which converts the string representing the connections to connections
def string_to_connections(device,list_of_buses):
        list_of_connections=[]
        for c in device.connections:
                for b in list_of_buses:
                        if b.name==c:
                                list_of_connections.append(b)
        return list_of_connections
