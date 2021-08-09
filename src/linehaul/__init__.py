from linehaul.planning                        import         LinehaulTask
from linehaul.lp                        import         LinearProgram
from model.generic.planning.task        import         State
from model.generic.hybrid.task                import        HybridTask

import sys
import os
import math

### create linehaul task from vrx file; also needs distance matrix file.

def create_problem( vrxfile, dmfile, vehicle_limit = None):
    # read distance matrix: dm is a map from pairs of location names
    # to distances; that is, dm[('A', 'B')] is the distance from A to B.
    dm = read_distance_matrix(dmfile)

    # read requests: reqs is a list of tuples (orig, dest, qc, qa),
    # where orig/dest = location names, qc = quantity (demand) chilled,
    # qa = quantity ambient.
    reqs = read_requests(vrxfile)
    locs = set()
    pickups = set()
    for (orig, dest, qchi, qamb) in reqs:
        pickups.add(orig)
        locs.add(orig)
        locs.add(dest)

    # check that there is only one depot:
    assert len(pickups) == 1
    depot = list(pickups)[0]

    # check that all locations mentioned in requests are defined
    # in the distance matrix.
    for el1 in locs:
        for el2 in locs:
            if el1 != el2:
                if (el1, el2) not in dm:
                    print("error: pair {} missing from DM".format((el1, el2)))
                    assert False

    # make a list of (relevant) locations, ensure that depot is
    # first in the list:
    llist = list(locs)
    i = llist.index(depot)
    if i != 0:
        llist[i] = llist[0]
        llist[0] = depot

    # collect aggregate demands for each location (in case there are
    # multiple requests for the same good type for some location):
    # demand[l] = (qc, qa) means the total demand for chilled (ambient)
    # goods at location l is qc (qa).
    demand = dict()
    for (orig, dest, qchi, qamb) in reqs:
        if dest not in demand:
            demand[dest] = (qchi, qamb)
        else:
            (qc1, qa1) = demand[dest]
            demand[dest] = (qc1 + qchi, qa1 + qamb)

    # vehicle type data: list of tuples (name, count, pkc, cap, chilled),
    # where: pkc = per-kilometer cost, cap = capactiy, chilled = True/False
    vcount = [4, 3, 2, 2, 1]
    if isinstance(vehicle_limit, int):
        for i in range(5):
            vcount[i] = vehicle_limit
    elif isinstance(vehicle_limit, list):
        assert(len(vehicle_limit) == 5)
        vcount = vehicle_limit

    vehicle = [ ('ADouble', vcount[0], 2.67, 40, False),
                ('ADoubleReefer', vcount[1], 3.04, 40, True),
                ('BDouble', vcount[2], 2.59, 34, False),
                ('BDoubleReefer', vcount[3], 2.99, 34, True),
                ('BTriple', vcount[4], 2.86, 48, False) ]

    (pname, _) = os.path.splitext(os.path.basename(vrxfile))
    the_task = LinehaulTask( pname, dm, llist, demand, vehicle )
    the_LP = LinearProgram( the_task )
    the_LP.model.printStats()

    # load initial state
    s0 = the_task.make_initial_state()
    pG = the_task.make_primary_goal()
    #the_task.print_valuation( pG, sys.stdout )

    return HybridTask( the_task, the_LP, s0, pG, the_LP.goal_constraints )

## end create_problem

def read_distance_matrix(filename):
    dm = dict()
    dfile = open(filename)
    for line in dfile:
        bits = line.strip().split()
        if len(bits) > 0:
            assert len(bits) == 3
            dm[(bits[0], bits[1])] = int(bits[2])
    dfile.close()
    return dm

def read_requests(filename):
    reqs = []
    in_section = False
    prev = []
    rfile = open(filename)
    for line in rfile:
        if in_section:
            if line.strip() == '*END*':
                rfile.close()
                assert len(prev) == 0
                return reqs
            else:
                bits = line.strip().split()
                # print(bits, prev)
                assert(len(bits) == 5)
                if len(prev) == 0:
                    assert bits[0][-2:] == '-P'
                    prev = bits[1:5]
                else:
                    assert bits[0][-2:] == '-D'
                    assert len(prev) == 4
                    orig = prev[0]
                    dest = bits[1]
                    q_chilled = int(prev[2])
                    q_ambient = int(prev[3])
                    reqs.append((orig, dest, q_chilled, q_ambient))
                    prev = []
        elif line.strip() == 'REQUESTS':
            in_section = True
    rfile.close()
    assert False # this shall never occur
