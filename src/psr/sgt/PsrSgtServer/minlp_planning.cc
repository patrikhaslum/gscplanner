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
#include <csignal>

using namespace std;
using namespace Sgt;

enum class Method
{
    AC_RECT,
    SOCP
};

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

bool attempt(PsrSolver& solver, size_t n, Method method)
{
    solver.reset();
    solver.lockInProblem();

    bool ok = method == Method::AC_RECT ? solver.nAcRectSwitchingCheck(n) : solver.nSocpSwitchingCheck(n) ;
    std::cout << "N-switching-check status = " << ok << std::endl;

    return ok;
}

unsigned int getInitNClosed(PsrSolver& solver)
{
    unsigned int result = 0;
    for (auto& branchInf : solver.branchInfos())
    {
        if (branchInf.second.hasBreaker() && branchInf.second.breakerIsInitClosed()) ++result;
    }
    return result;
}

unsigned int getFinalNClosed(PsrSolver& solver, Method method)
{
    sgtLogMessage() << "Solving for final state." << std::endl;
    LogIndent _;
    solver.reset();
    solver.lockInProblem();
    if (method == Method::AC_RECT)
    {
        assert(solver.acRectSwitchingCheck());
    }
    else if (method == Method::SOCP)
    {
        assert(solver.socpSwitchingCheck());
    }
    unsigned int result = 0;
    for (auto& branchInf : solver.branchInfos())
    {
        if (method == Method::AC_RECT)
        {
            const auto& mod = branchInf.second.modelBranch<AcRectSwitchingModel>();
            if (mod.closed.get_value()) ++result;
        }
        else if (method == Method::SOCP)
        {
            const auto& mod = branchInf.second.modelBranch<SocpSwitchingModel>();
            if (mod.closed.get_value()) ++result;
        }
    }
    return result;
}

namespace
{
    Stopwatch sw;
    json planJson;
}

int main(int argc, char** argv)
{
    std::string inFName = argv[argc - 1];

    Method method = Method::AC_RECT;
    {
        const char* opt = getCmdOption(argv, argc, "--method");
        if (opt != nullptr)
        {
            std::string optStr(opt);
            if (optStr == "ac_rect")
            {
                method = Method::AC_RECT;
            }
            else if (optStr == "socp")
            {
                method = Method::SOCP;
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
    
    sw.start();

    Network nw(100.0);
    nw.setUseFlatStart(true);
    NetworkParser netwParser;
    netwParser.parse(inFName, nw);
            
    PsrSolver solver(nw); 
    Parser<PsrSolver> psrParser;
    psrParser.registerParserPlugin<PsrParserPlugin>();
    psrParser.parse(inFName, solver);

    std::signal(SIGTERM, [](int){
            std::cout << "FINAL" << "\t" << false << "\t" << false << "\t"
            << -1 << "\t" << sw.wallSeconds() 
            << "\t" << sw.cpuSeconds() << "\t" << planJson.dump() << std::endl; exit(1);});
        
    int initNClosed = getInitNClosed(solver);
    int finalNClosed = getFinalNClosed(solver, method);
    int minPlanLength = abs(finalNClosed - initNClosed);
    const unsigned int maxPlanLength = 10;
    sgtLogMessage() << "Initial n closed: " << initNClosed << std::endl;
    sgtLogMessage() << "Final n closed: " << finalNClosed << std::endl;
    sgtLogMessage() << "Minimum plan length: " << minPlanLength << std::endl;
    sgtLogMessage() << "Maximum plan length: " << maxPlanLength << std::endl;

    bool ok = false;

    for (unsigned int planLength = minPlanLength; planLength <= maxPlanLength; planLength += 2)
    {
        LogIndent a;
        sgtLogMessage() << "Trying max plan length " << planLength << std::endl;
        LogIndent b;
        ok = attempt(solver, planLength + 1, method);
        if (ok)
        {
            if (method == Method::AC_RECT)
                planJson = solver.getMinlpPlanJson<NAcRectSwitchingModel>();
            else if (method == Method::SOCP)
                planJson = solver.getMinlpPlanJson<NSocpSwitchingModel>();
            sgtLogMessage() << "Success for plan length = " << planJson.size() << std::endl;
            if (method == Method::AC_RECT)
                solver.printNSwitching<NAcRectSwitchingModel>();
            else if (method == Method::SOCP)
                solver.printNSwitching<NSocpSwitchingModel>();
            sgtLogMessage(LogLevel::NORMAL) << "--------" << endl;
            sgtLogMessage(LogLevel::NORMAL) << "Plan JSON:" << endl;
            sgtLogMessage(LogLevel::NORMAL) << planJson.dump() << endl;
            sgtLogMessage(LogLevel::NORMAL) << "--------" << endl;
            break;
        }
        else
        {
            sgtLogMessage() << "Failed for plan length " << planLength << std::endl;
        }
    }
    sw.stop();
    int finalPlanLength = ok ? planJson.size() : -1;
    std::cout << "FINAL" << "\t" << ok << "\t" << true << "\t" << finalPlanLength << "\t" << sw.wallSeconds() << "\t" << sw.cpuSeconds() << "\t" << planJson.dump() << std::endl;
}
