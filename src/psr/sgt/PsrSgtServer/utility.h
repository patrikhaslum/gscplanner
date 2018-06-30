#ifndef UTILITY_DOT_H
#define UTILITY_DOT_H

#include<PowerTools++/Constraint.h>
#include<PowerTools++/Model.h>

#include<SgtCore/Bus.h>
#include<SgtCore/Gen.h>
#include<SgtCore/Network.h>

#include<algorithm>

namespace Sgt
{
    template<class T>
    typename std::enable_if<!std::numeric_limits<T>::is_integer, bool>::type almost_equal(T x, T y, int ulp)
    {
        return std::abs(x-y) < std::numeric_limits<T>::epsilon() * std::abs(x+y) * ulp || 
               std::abs(x-y) < std::numeric_limits<T>::min();
    }
    template<class T>
    typename std::enable_if<std::numeric_limits<T>::is_integer, bool>::type almost_equal(T x, T y, int ulp)
    {
        return x == y;
    }
    template<typename T> bool isFixed(const var<T>& v)
    {
        return almost_equal(v.get_lb(), v.get_ub(), 2); 
    }
    bool isFixed(const var_& v);
    char* getCmdOption(char** argv, int argc, const std::string & option);
    bool cmdOptionExists(char** argv, int argc, const std::string& option);
    void safeAddConstr(Model& mod, const Constraint& c);
    bool hasGeneration(const Bus& bus);
    bool canFeedSelf(const Bus& bus);
}

#endif // UTILITY_DOT_H
