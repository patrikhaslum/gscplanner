#include "PsrParserPlugin.h"

#include <SgtCore/Network.h>

namespace Sgt
{
    template<> void registerParserPlugins<PsrSolver>(Parser<PsrSolver>& p)
    {
        p.registerParserPlugin<PsrParserPlugin>();
    }

    void PsrParserPlugin::parse(const YAML::Node& nd, PsrSolver& solver, const ParserBase& parser) const
    {
        auto ndUseSocp = nd["use_socp"];
        if (ndUseSocp)
        {
            solver.useSocp_ = ndUseSocp.as<bool>();
        }

        auto ndFaults = nd["bus_faults"];
        if (ndFaults)
        {
            for (auto ndFault : ndFaults)
            {
                solver.busInfo(ndFault["id"].as<std::string>()).setFault();
            }
        }
        
        auto ndBreakers = nd["branch_breakers"];
        if (ndBreakers)
        {
            for (auto ndBreaker : ndBreakers)
            {
                auto branch = solver.network().branches()[ndBreaker["id"].as<std::string>()];
                solver.branchInfo(ndBreaker["id"].as<std::string>()).setBreaker(ndBreaker["init_closed"].as<bool>());
            }
        }

        auto ndOptFinalFed = nd["bus_optional_final_fed"];
        if (ndOptFinalFed)
        {
            for (auto n : ndOptFinalFed)
            {
                auto& busInfo = solver.busInfo(n["id"].as<std::string>());
                busInfo.setFinalRequireFed(false);
            }
        }
        
        auto ndDefaultBusFed = nd["bus_default_fed"];
        if (ndDefaultBusFed)
        {
            for (auto n : ndDefaultBusFed)
            {
                auto& busInfo = solver.busInfo(n["id"].as<std::string>());
                Trivalent sc = static_cast<Trivalent>(n["value"].as<int>());
                busInfo.setDefaultFedStateConstr(sc);
            }
        }
        
        auto ndDefaultBranchClosed = nd["branch_default_closed"];
        if (ndDefaultBranchClosed)
        {
            for (auto n : ndDefaultBranchClosed)
            {
                auto& branchInfo = solver.branchInfo(n["id"].as<std::string>());
                Trivalent sc = static_cast<Trivalent>(n["value"].as<int>());
                branchInfo.setDefaultClosedStateConstr(sc);
            }
        }
    }
}
