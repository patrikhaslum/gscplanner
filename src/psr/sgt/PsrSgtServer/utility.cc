#include "utility.h"

namespace Sgt
{
    bool isFixed(const var_& v)
    {
        switch(v.get_type())
        {
            case VarType::binary:
                return isFixed<bool>(static_cast<const var<bool>&>(v));
            case VarType::integ:
                return isFixed<int>(static_cast<const var<int>&>(v));
            case VarType::real:
                return isFixed<float>(static_cast<const var<float>&>(v));
            case VarType::longreal:
                return isFixed<double>(static_cast<const var<double>&>(v));
            case VarType::constant:
                return true;
        }
    }
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

    void safeAddConstr(Model& mod, const Constraint& c)
    {
        if (c._vars.size() > 0)
        {
            mod.addConstraint(c);
        }
    }
    
    bool hasGeneration(const Bus& bus)
    {
        bool result = bus.isInService() && bus.nInServiceGens() > 0;
        return result;
    }

    bool canFeedSelf(const Bus& bus)
    {
        Complex totLoad = bus.SZipTot();
        double maxP = 0;
        double minP = 0;
        double maxQ = 0;
        double minQ = 0;
        for (auto g : bus.gens())
        {
            if (g->isInService())
            {
                maxP += g->PMax();
                minP += g->PMin();
                maxQ += g->QMax();
                minQ += g->QMin();
            }
        }
        return (totLoad.real() >= minP &&
                totLoad.real() <= maxP &&
                totLoad.imag() >= minQ &&
                totLoad.imag() <= maxQ);
    }
}
