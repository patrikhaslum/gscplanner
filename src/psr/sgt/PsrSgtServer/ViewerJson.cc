#include "ViewerJson.h"

#include "PsrSolver.h"
#include "utility.h"

#include <SgtCore/Branch.h>
#include <SgtCore/Bus.h>

namespace Sgt
{
    json makeViewerJson(const PsrSolver& solver)
    {
        json j;

        auto& nodesJson = j["nodes"] = json::array();
        for (auto& busInfo : solver.busInfos())
        {
            json ndJson = json::object();
            ndJson["id"] = busInfo.second.id();
            ndJson["hasGen"] = busInfo.second.bus().gens().size() != 0;
            ndJson["hasLoad"] = busInfo.second.bus().zips().size() != 0;
            ndJson["hasFault"] = busInfo.second.hasFault();
            ndJson["finalRequireFed"] = busInfo.second.finalRequireFed();
            ndJson["isFed"] = json::array();
            ndJson["fedStateConstr"] = json::array();
            nodesJson.push_back(ndJson);
        }

        auto& linksJson = j["links"] = json::array();
        for (auto& branchInfo : solver.branchInfos())
        {
            json linkJson = json::object();
            linkJson["id"] = branchInfo.second.id();
            linkJson["source"] = branchInfo.second.branch().bus0()->id();
            linkJson["target"] = branchInfo.second.branch().bus1()->id();
            linkJson["hasBreaker"] = branchInfo.second.hasBreaker();
            linkJson["closedStateConstr"] = json::array();
            linksJson.push_back(linkJson);
        }

        return j;
    }

    void addFrame(json& j, const PsrSolver& solver)
    {
        for (auto& ndJson : j["nodes"])
        {
            const auto& busInf = solver.busInfo(ndJson["id"]);
            ndJson["fedStateConstr"].push_back(static_cast<int>(busInf.fedStateConstr()));
            ndJson["isFed"].push_back(static_cast<int>(busInf.isFed()));
        }
        for (auto& ndJson : j["links"])
        {
            const auto& branchInf = solver.branchInfo(ndJson["id"]);
            ndJson["closedStateConstr"].push_back(static_cast<int>(branchInf.closedStateConstr()));
        }
    }
}
