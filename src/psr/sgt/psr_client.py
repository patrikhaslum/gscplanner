import logging
import requests
import json
from network import Network, Bus, Branch

logging.getLogger("requests").setLevel(logging.WARNING)

def get_network(infile):
    netw = Network()

    resp = requests.put('http://localhost:12345/network?config=' + infile)
    netw_json = resp.json()

    # print(str(netw_json))

    for bus_json in netw_json[u'buses']:
        netw.buses.append(Bus(bus_json[u'name'], bus_json[u'final_require_fed']))
    
    for branch_json in netw_json[u'branches']:
        netw.branches.append(Branch(branch_json[u'name'],
                                    branch_json[u'init_closed']))

    return netw

def optimize_network(msg):
    print("-> " + json.dumps(msg))
    resp = requests.put('http://localhost:12345/network/state',
                        data=json.dumps(msg)).json()
    print("<- " + json.dumps(resp))
    return resp
