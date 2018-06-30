#ifndef VIEWER_JSON_DOT_H
#define VIEWER_JSON_DOT_H

#include<SgtCore/json.h>

namespace Sgt
{
    class PsrSolver;

    nlohmann::json makeViewerJson(const PsrSolver& solver);
    
    void addFrame(nlohmann::json& j, const PsrSolver& solver);
}

#endif // VIEWER_JSON_DOT_H
