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

#include <SgtCore.h>

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>

char* getCmdOption(char** argv, int argc, const std::string & option)
{
    auto begin = argv;
    auto end = argv + argc;
    char ** itr = std::find(begin, end, option);
    if (itr != end && ++itr != end)
    {
        return *itr;
    }
    return 0;
}

bool cmdOptionExists(char** argv, int argc, const std::string& option)
{
    auto begin = argv;
    auto end = argv + argc;
    return std::find(begin, end, option) != end;
}

int main(int argc, char** argv)
{
    using namespace Sgt;

    std::string inFName = argv[argc - 1];

    std::string testType = "ac_rect";
    {
        const char* opt = getCmdOption(argv, argc, "--test_type");
        if (opt != nullptr) testType = opt;
    }
    
    size_t nTime = 2;
    {
        const char* opt = getCmdOption(argv, argc, "--n_time");
        if (opt != nullptr) nTime = static_cast<size_t>(atoi(opt));
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

    Network nw(100.0);
    nw.setUseFlatStart(true);
    NetworkParser netwParser;
    netwParser.parse(inFName, nw);
            
    auto solver = new PsrSolver(nw); 

    Parser<PsrSolver> psrParser;
    psrParser.registerParserPlugin<PsrParserPlugin>();
    psrParser.parse(inFName, *solver);

    if (testType == "pre")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->preCheck();
        std::cout << "Pre status = " << ok << std::endl;
    }
    else if (testType == "ac_rect")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->acRectCheck();
        std::cout << "AC rect status = " << ok << std::endl;
    }
    else if (testType == "ac_rect_switching")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->acRectSwitchingCheck();
        solver->printSwitching<AcRectSwitchingModel>();
        std::cout << "AC rect switching status = " << ok << std::endl;
    }
    else if (testType == "socp")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->socpCheck();
        std::cout << "SOCP status = " << ok << std::endl;
    }
    else if (testType == "socp_switching")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->socpSwitchingCheck();
        solver->printSwitching<SocpSwitchingModel>();
        std::cout << "SOCP switching status = " << ok << std::endl;
    }
    else if (testType == "n_socp_switching")
    {
        solver->reset();
        solver->printStateConstrs();
        solver->lockInProblem();
        bool ok = solver->nSocpSwitchingCheck(nTime);
        std::cout << "N SOCP switching status = " << ok << std::endl;
    }
}
