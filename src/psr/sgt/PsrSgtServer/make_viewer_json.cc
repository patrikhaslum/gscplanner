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

#include "PsrParserPlugin.h"
#include "PsrSolver.h"
#include "ViewerJson.h"

#include <SgtCore.h>

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>

char* getCmdOption(char** argv, int argc, const string & option)
{
    auto begin = argv;
    auto end = argv + argc;
    char ** itr = find(begin, end, option);
    if (itr != end && ++itr != end)
    {
        return *itr;
    }
    return 0;
}

bool cmdOptionExists(char** argv, int argc, const string& option)
{
    auto begin = argv;
    auto end = argv + argc;
    return find(begin, end, option) != end;
}

int main(int argc, char** argv)
{
    using namespace Sgt;

    string outFName = "";
    {
        const char* opt = getCmdOption(argv, argc, "--out_file");
        assert(opt != nullptr);
        outFName = opt;
    }
    ofstream outFile(outFName);

    json planJson;
    {
        const char* opt = getCmdOption(argv, argc, "--plan");
        if(opt != nullptr)
        {
            std::stringstream ss(opt);
            ss >> planJson;
        }
    }

    string inFName = argv[argc - 1];

    Network nw(100.0);
    nw.setUseFlatStart(true);
    NetworkParser netwParser;
    netwParser.parse(inFName, nw);
            
    auto solver = new PsrSolver(nw); 

    Parser<PsrSolver> psrParser;
    psrParser.registerParserPlugin<PsrParserPlugin>();
    psrParser.parse(inFName, *solver);

    solver->reset();

    for (auto& b : solver->branchInfos())
    {
        b.second.setClosedStateConstr(static_cast<Trivalent>(b.second.breakerIsInitClosed() ? 1 : 0));
    }
    solver->lockInProblem();

    json j = makeViewerJson(*solver);
    addFrame(j, *solver);

    if (!planJson.is_null())
    {
        for (const auto& branchStr : planJson)
        {
            auto& branchInf = solver->branchInfo(branchStr);
            switch (branchInf.closedStateConstr())
            {
                case Trivalent::NO:
                    branchInf.setClosedStateConstr(Trivalent::YES);
                    break;
                case Trivalent::YES:
                    branchInf.setClosedStateConstr(Trivalent::NO);
                    break;
                case Trivalent::MAYBE:
                    branchInf.setClosedStateConstr(Trivalent::NO);
                    sgtError("Unexpected closedStateConstr when applying plan.");
            }
            solver->lockInProblem();
            addFrame(j, *solver);
        }
    }

    outFile << j.dump(4) << endl;
}
