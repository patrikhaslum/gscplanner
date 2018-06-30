// Copyright 2015 National ICT Australia Limited (NICTA)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "PsrSolver.h"
#include "utility.h"

#include <SgtCore.h>

#include <cstdio>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <sstream>

using namespace Sgt;

void performSearch(const ComponentPtr<Sgt::Bus>& bus, std::set<std::string>& visitedBuses)
{
    auto (Sgt::Bus::* branchFn0)(void) = &Sgt::Bus::branches0;
    auto (Sgt::Bus::* branchFn1)(void) = &Sgt::Bus::branches1;
    auto (Sgt::BranchAbc::* busFn0)(void) = &Sgt::BranchAbc::bus0;
    auto (Sgt::BranchAbc::* busFn1)(void) = &Sgt::BranchAbc::bus1;

    auto fnsA = std::make_pair(branchFn0, busFn1);
    auto fnsB = std::make_pair(branchFn1, busFn0);

    visitedBuses.insert(bus->id());

    for (auto fns : {fnsA, fnsB})
    {
        for (auto branch : (bus->*fns.first)())
        {
            if (!branch->isInService()) continue;
            auto otherBus = (branch->*fns.second)();
            if (visitedBuses.find(otherBus->id()) != visitedBuses.end()) continue;
            if (otherBus->nInServiceGens() > 0)
            {
                branch->userData()["init_closed"] = false;
                sgtLogMessage() << "Turn off branch " << branch->id() << " to isolate faulty bus." << std::endl;
            }
            else
            {
                performSearch(otherBus, visitedBuses);
            }
        }
    }
}

int main(int argc, char** argv)
{
    using namespace Sgt;

    // -------------------------------------------------------------------------
    // Command line options, etc.
    sgtAssert(argc > 1,
            "Usage: setup_problem [--outfile filename] [--faults fault[, fault...]] [--method ac_rect|socp] [--debug level] infile");
        
    std::string inFName = argv[argc - 1];

    std::string outFName = "out";
    {
        const char* opt = getCmdOption(argv, argc, "--outfile");
        if (opt != nullptr) outFName = opt;
    }
    
    std::list<std::string> faults;
    {
        const char* opt = getCmdOption(argv, argc, "--faults");
        if (opt != nullptr)
        {
            std::istringstream ss(opt);
            std::string token;
            while(std::getline(ss, token, ',')) 
            {
                faults.push_back(token);
            }
        }
    }
   
    bool useAcRect = true;
    {
        const char* opt = getCmdOption(argv, argc, "--method");
        if (opt != nullptr)
        {
            std::string method(opt);
            if (method == "socp")
            {
                useAcRect = false;
            }
            else
            {
                assert(method == "ac_rect");
            }
        }
    }
    
    std::string debugLevel = "none";
    {
        const char* opt = getCmdOption(argv, argc, "--debug");
        if (opt != nullptr)
        {
            debugLevel = opt;
        }
    }

    debugLogLevel() = LogLevel::NONE;
    if (debugLevel == "normal")
    {
        debugLogLevel() = LogLevel::NORMAL;
    }
    else if (debugLevel == "verbose")
    {
        debugLogLevel() = LogLevel::VERBOSE;
    }
    
    // -------------------------------------------------------------------------
    // Setup:

    // Parse in the network:
    Network nw(100.0);
    {
        nw.setUseFlatStart(true);
        std::string yamlStr = std::string("--- [{matpower : {input_file : ") + inFName + ", default_kV_base : 11}}]";
        YAML::Node n = YAML::Load(yamlStr);
        NetworkParser netwParser;
        netwParser.parse(n, nw);
    }

    // Set a solver:
    auto solver = new PsrSolver(nw); 
    solver->useSocp_ = true;
    
    // Every in-service branch is a breaker.
    for (auto branch : nw.branches())
    {
        if (branch->isInService()) solver->branchInfo(branch->id()).setBreaker(true);
    }

    // All closed unless branch was out of service to start with.
    for (auto branch : nw.branches())
    {
        branch->userData()["init_closed"] = branch->isInService();
    }

    // Faults:
    for (auto fault : faults)
    {
        const ComponentPtr<Sgt::Bus> faultBus = nw.buses()[fault];
        
        if (faultBus->nInServiceGens() > 0)
        {
            // For a faulty generator bus, turn off all connected branches.
            sgtLogMessage() << "Faulty generator bus." << std::endl;
            for (auto branch : faultBus->branches0())
            {
                branch->userData()["init_closed"] = false;
                sgtLogMessage() << "Turn off branch " << branch->id() << " to isolate faulty bus." << std::endl;
            }
            for (auto branch : faultBus->branches1())
            {
                branch->userData()["init_closed"] = false;
                sgtLogMessage() << "Turn off branch " << branch->id() << " to isolate faulty bus." << std::endl;
            }
        }
        else
        {
            // For a faulty non-generator bus, search back & turn off branches incident on a generator.
            sgtLogMessage() << "Faulty non-generator bus." << std::endl;
            std::set<std::string> visitedBuses;
            performSearch(faultBus, visitedBuses); // Does not need lockInProblem as islanding info not used.
        }

        // Mark the bus as faulty.
        solver->busInfo(fault).setFault();
    }

    auto check = [&] () -> bool {
        LogIndent _;
        solver->reset();
        for (auto b : nw.branches())
        {
            solver->branchInfo(b->id()).setClosedStateConstr(
                    b->userData()["init_closed"].get<bool>() ? Trivalent::YES : Trivalent::NO);
        }
        bool result = solver->solve(); // Includes lockInProblem.
        sgtLogMessage() << "valid = " << result << std::endl;
        return result;
    };

    bool isOk = true;

    sgtLogMessage() << "Checking initial state" << std::endl;
    isOk = check();

    if (!isOk)
    {
        // Fallback: just turn off all the generators.
        sgtLogMessage() << "Fallback: disable all generators" << std::endl;
        for (auto g : nw.gens())
        {
            for (auto b : g->bus()->branches0())
            {
                b->userData()["init_closed"] = false;
            }
            for (auto b : g->bus()->branches1())
            {
                b->userData()["init_closed"] = false;
            }
        }

        sgtLogMessage() << "Checking fallback state" << std::endl;
        isOk = check();
        if (!isOk)
        {
            sgtLogMessage() << "Exit: can't find valid initial state." << std::endl;
            exit(0);
        }
    }
        
    sgtLogMessage() << "Valid initial state generated." << std::endl;

    // Set initFed information:
    for (auto& busInf : solver->busInfos())
    {
        busInf.second.bus().userData()["init_fed"] = static_cast<int>(busInf.second.tightenedFedStateConstr());
    }

    // Solve the switching problem:
    sgtLogMessage() << "Finding final state" << std::endl;
    {
        LogIndent _;
        solver->reset();
        // When we reset, closed state constraint gets reset to default. This is MAYBE for a breaker, NO for out of
        // service non-breaker, YES for in service non-breaker.
        solver->lockInProblem();
        if (useAcRect)
        {
            isOk = solver->acRectSwitchingCheck();
            sgtLogMessage() << "AC Rect status = " << isOk << std::endl;
            solver->applySwitchingResults<AcRectSwitchingModel>();
            solver->lockInProblem();
        }
        else
        {
            isOk = solver->socpSwitchingCheck();
            sgtLogMessage() << "SOCP status = " << isOk << std::endl;
            if (isOk)
            {
                solver->applySwitchingResults<SocpSwitchingModel>();
                solver->lockInProblem();
                isOk = solver->acRectCheck();
                sgtLogMessage() << "AC Rect post check status = " << isOk << std::endl;
                if (!isOk)
                {
                    sgtLogMessage() << "Note: SOCP switching solution found, but fails AC Rect post check." << std::endl;
                }
            }
        }
        sgtLogMessage() << "Switching-check status = " << isOk << std::endl;

        if (!isOk)
        {
            sgtLogMessage() << "Exit: can't find valid final state." << std::endl;
            exit(0);
        }

        // Is the final state different to the initial state? If not, don't abandon the problem as not interesting.
        bool isImproved = false;
        for (const auto& branchInf : solver->branchInfos())
        {
            bool initClosed = branchInf.second.branch().userData()["init_closed"].get<bool>();
            bool finalClosed = branchInf.second.closedStateConstr() == Trivalent::YES;
            if (initClosed != finalClosed)
            {
                sgtLogMessage() << "Final state " << finalClosed << " differs from initial state " << initClosed 
                    << " at branch " << branchInf.second.branch().id() << std::endl;
                isImproved = true;
                break;
            }
        }
        // Furthermore, check that we have managed to improve the fed state of the buses.
        if (isImproved)
        {
            isImproved = false;
            for (const auto& busInf : solver->busInfos())
            {
                int initFed = busInf.second.bus().userData()["init_fed"].get<int>();
                assert(initFed != 2); // Because it comes from a definite starting state.
                bool finalFed = busInf.second.fedStateConstr() == Trivalent::YES;
                if (initFed == 0 && finalFed)
                {
                    sgtLogMessage() << "Final state " << finalFed << " differs from initial state " << initFed 
                        << " at bus " << busInf.second.bus().id() << std::endl;
                    isImproved = true;
                    break;
                }
            }
        }
        if (!isImproved)
        {
            sgtLogMessage() << "Exit: final state no better than initial state." << std::endl;
            exit(0);
        }
    }
        
    sgtLogMessage() << "Outputting valid problem." << std::endl;

    auto outFile = std::ofstream(outFName.c_str());

    YAML::Emitter emitter;
    emitter << YAML::BeginDoc;
    {
        emitter << YAML::BeginSeq;
        {
            emitter << YAML::BeginMap;
            {
                emitter << YAML::Key << "matpower" << YAML::Value << YAML::BeginMap;
                {
                    emitter << YAML::Key << "input_file" << YAML::Value << inFName;
                    emitter << YAML::Key << "default_kV_base" << YAML::Value << 11;
                }
                emitter << YAML::EndMap;
            }
            emitter << YAML::EndMap;
            emitter << YAML::BeginMap;
            {
                emitter << YAML::Key << "psr" << YAML::Value << YAML::BeginMap;
                {
                    emitter << YAML::Key << "use_socp" << YAML::Value << true;
                    emitter << YAML::Key << "bus_faults" << YAML::Value << YAML::BeginSeq;
                    {
                        for (auto bus : nw.buses())
                        {
                            const auto& busInfo = solver->busInfo(bus->id());
                            if (busInfo.hasFault())
                            {
                                emitter << YAML::BeginMap;
                                {
                                    emitter << YAML::Key << "id" << YAML::Value << bus->id();
                                }
                                emitter << YAML::EndMap;
                            }
                        }
                    }
                    emitter << YAML::EndSeq;
                    emitter << YAML::Key << "bus_optional_final_fed" << YAML::Value << YAML::BeginSeq;
                    {
                        for (auto bus : nw.buses())
                        {
                            const auto& busInfo = solver->busInfo(bus->id());
                            bool isFed = busInfo.isFed() == Trivalent::YES;
                            if (!isFed)
                            {
                                emitter << YAML::BeginMap;
                                {
                                    emitter << YAML::Key << "id" << YAML::Value << bus->id();
                                }
                                emitter << YAML::EndMap;
                            }
                        }
                    }
                    emitter << YAML::EndSeq;
                    emitter << YAML::Key << "branch_breakers" << YAML::Value << YAML::BeginSeq;
                    {
                        for (auto branch : nw.branches())
                        {
                            emitter << YAML::Flow << YAML::BeginMap;
                            {
                                emitter << YAML::Key << "id" << YAML::Value << branch->id();
                                emitter << YAML::Key << "init_closed" 
                                    << YAML::Value << branch->userData()["init_closed"].get<bool>();
                            }
                            emitter << YAML::EndMap;
                        }
                    }
                    emitter << YAML::EndSeq;
                }
                emitter << YAML::EndMap;
            }
            emitter << YAML::EndMap;
        }
        emitter << YAML::EndSeq;
    }
    emitter << YAML::EndDoc;
    outFile << emitter.c_str();
}
