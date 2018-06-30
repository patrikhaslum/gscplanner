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

#include <SgtCore/Branch.h>
#include <SgtCore/Bus.h>
#include <SgtCore/Gen.h>
#include <SgtCore/Zip.h>
#include <SgtCore/Network.h>
#include <SgtCore/PowerToolsSupport.h>
#include <SgtCore/Stopwatch.h>

#include <PowerTools++/Constraint.h>
#include <PowerTools++/Net.h>
#include <PowerTools++/PowerModel.h>

#include <algorithm>

#define REQUIRE_SOLVE_AC

namespace
{
    using namespace Sgt;

    var<> dummy; // This is a KLUDGE to get around PowerTools issue. Not used except as a placeholder.

    struct C123 {double c1; double c2; double c3;};

    void powerFlowConstants(const PtBranch& ptBranch, C123& cPi, C123&  cPj, C123&  cQi, C123&  cQj)
    {
        double inv_cc2_p_dd2 = 1.0 / (pow(ptBranch.cc,2)+pow(ptBranch.dd,2));

        cPi.c1 = ptBranch.g*inv_cc2_p_dd2;
        cPi.c2 = (-ptBranch.g*ptBranch.cc+ptBranch.b*ptBranch.dd)*inv_cc2_p_dd2;
        cPi.c3 = (-ptBranch.b*ptBranch.cc-ptBranch.g*ptBranch.dd)*inv_cc2_p_dd2;

        cPj.c1 = ptBranch.g;
        cPj.c2 = (-ptBranch.g*ptBranch.cc-ptBranch.b*ptBranch.dd)*inv_cc2_p_dd2;
        cPj.c3 = (-ptBranch.b*ptBranch.cc+ptBranch.g*ptBranch.dd)*inv_cc2_p_dd2;

        cQi.c1 = (0.5*ptBranch.ch+ptBranch.b)*inv_cc2_p_dd2;
        cQi.c2 = (-ptBranch.b*ptBranch.cc-ptBranch.g*ptBranch.dd)*inv_cc2_p_dd2;
        cQi.c3 = (-ptBranch.g*ptBranch.cc+ptBranch.b*ptBranch.dd)*inv_cc2_p_dd2;

        cQj.c1 = (0.5*ptBranch.ch+ptBranch.b);
        cQj.c2 = (-ptBranch.b*ptBranch.cc+ptBranch.g*ptBranch.dd)*inv_cc2_p_dd2;
        cQj.c3 = (-ptBranch.g*ptBranch.cc-ptBranch.b*ptBranch.dd)*inv_cc2_p_dd2;
    }
    
    void powerFlowBigM(const PtBranch& ptBranch, double& MPi, double& MPj, double& MQi, double& MQj)
    {
        const auto& src = *ptBranch.src;
        const auto& dest = *ptBranch.dest;

        C123 cPi; C123 cPj; C123 cQi; C123 cQj;
        powerFlowConstants(ptBranch, cPi, cPj, cQi, cQj);
                
        double srcVUb = std::max(std::abs(src.vbound.max), std::abs(src.vbound.min));
        double dstVUb = std::max(std::abs(dest.vbound.max), std::abs(dest.vbound.min));

        MPi = abs(cPi.c1) * pow(srcVUb, 2) + 2 * (abs(cPi.c2) + abs(cPi.c3)) * srcVUb * dstVUb;
        MPj = abs(cPj.c1) * pow(dstVUb, 2) + 2 * (abs(cPj.c2) + abs(cPj.c3)) * srcVUb * dstVUb;
        MQi = abs(cQi.c1) * pow(srcVUb, 2) + 2 * (abs(cQi.c2) + abs(cQi.c3)) * srcVUb * dstVUb;
        MQj = abs(cQj.c1) * pow(srcVUb, 2) + 2 * (abs(cQj.c2) + abs(cQj.c3)) * srcVUb * dstVUb;
    }

    std::pair<Constraint, Constraint> addBigMSwitchedEqualityConstr(
            const string& id, const Function& f, var<int>& on, double M, Model& mod)
    {
        std::pair<Constraint, Constraint> result;
        Constraint cL("l_" + id);
        cL += f;
        cL -= M * (1 - on);
        cL <= 0;
        safeAddConstr(mod, cL);

        Constraint cU("u_" + id);
        cU += f;
        cU += M * (1 - on);
        cU >= 0;
        safeAddConstr(mod, cU);

        return {cL, cU};
    }

    template <typename T> struct isVector
    {
        enum { value = false };
    };

    template <typename T> struct isVector<std::vector<T>>
    {
        enum { value = true };
    };
    
    template<typename T>
    typename std::enable_if<isVector<T>::value, typename T::value_type>::type& sz(T& x)
    {
        return x.size();
    }
    
    template<typename T>
    typename std::enable_if<!isVector<T>::value, typename T::value_type>::type& sz(T& x)
    {
        return 0;
    }

    template<typename T>
    typename std::enable_if<isVector<T>::value, typename T::value_type>::type& e(T& x, size_t i)
    {
        return x[i];
    }
    
    template<typename T>
    typename std::enable_if<!isVector<T>::value, T>::type& e(T& x, size_t i)
    {
        assert(i == 0);
        return x;
    }
}

namespace Sgt
{
    namespace
    {
        auto scString = [](const auto& infos, const auto& get)
        {
            string s = "\n";
            for (const auto& infoPair : infos)
            {
                auto scPair = get(infoPair.second);
                s += infoPair.first + " : " + to_string(static_cast<int>(scPair.first)) 
                    + " (" + to_string(static_cast<int>(scPair.second)) + ")\n";
            }
            return s;
        };

        void printBusFedScs(const map<string, PsrBusInfo>& infos)
        {
            sgtLogDebug(LogLevel::NORMAL) << scString(infos, [](const PsrBusInfo& busInf)
                    {return make_pair(busInf.fedStateConstr(), busInf.defaultFedStateConstr());});
        }
        
        void printBranchClosedScs(const map<string, PsrBranchInfo>& infos)
        {
            sgtLogDebug(LogLevel::NORMAL) << scString(infos, [](const PsrBranchInfo& branchInf)
                    {return make_pair(branchInf.closedStateConstr(), branchInf.defaultClosedStateConstr());});
        }

    }
        
    void NAcRectSwitchingModelBus::realloc(size_t n)
    {
        // NOTE: there is an issue with using vector<PtComplex>::resize(size_t sz). But this way is fine.
        Vr = vector<var<>>(n);
        Vi = vector<var<>>(n);
        V = vector<PtComplex>(n);
        fed = vector<var<int>>(n);
    }

    void NSocpSwitchingModelBus::realloc(size_t n)
    {
        // NOTE: there is an issue with using vector<PtComplex>::resize(size_t sz). But this way is fine.
        w = vector<var<>>(n);
        V = vector<PtComplex>(n);
        fed = vector<var<int>>(n);
    }
    
    void NAcRectSwitchingModelBranch::realloc(size_t n)
    {
        // NOTE: there is an issue with using vector<PtComplex>::resize(size_t sz). But this way is fine.
        Pi = vector<var<>>(n);
        Qi = vector<var<>>(n);
        Si = vector<PtComplex>(n);

        Pj = vector<var<>>(n);
        Qj = vector<var<>>(n);
        Sj = vector<PtComplex>(n);

        closed = vector<var<int>>(n);
        open = vector<var<int>>(n - 1);
        close = vector<var<int>>(n - 1);
    }
    
    void NSocpSwitchingModelBranch::realloc(size_t n)
    {
        // NOTE: there is an issue with using vector<PtComplex>::resize(size_t sz). But this way is fine.
        Pi = vector<var<>>(n);
        Qi = vector<var<>>(n);
        Si = vector<PtComplex>(n);

        Pj = vector<var<>>(n);
        Qj = vector<var<>>(n);
        Sj = vector<PtComplex>(n);

        wr = vector<var<>>(n);
        wi = vector<var<>>(n);
        
        closed = vector<var<int>>(n);
        open = vector<var<int>>(n - 1);
        close = vector<var<int>>(n - 1);
    }
        
    void NSocpSwitchingModelGen::realloc(size_t n)
    {
        // NOTE: there is an issue with using vector<PtComplex>::resize(size_t sz). But this way is fine.
        Pg = vector<var<>>(n);
        Qg = vector<var<>>(n);
        Sg = vector<PtComplex>(n);
    }

    PsrBusInfo::PsrBusInfo(ComponentPtr<Bus> bus) : bus_(bus)
    {
        if (!bus->isInService())
        {
            setFault();
        }
        else
        {
            defaultFedStateConstr_ = hasGeneration(*bus) ? Trivalent::YES : Trivalent::MAYBE;
        }
        setFedStateConstr(defaultFedStateConstr_);
    }
            
    const string& PsrBusInfo::id() const
    {
        return bus_->id();
    }

    void PsrBusInfo::setFault()
    {
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Fault in bus " << bus_->id() << endl;
        defaultFedStateConstr_ = Trivalent::NO;
        for (auto gen : bus_->gens())
        {
            gen->setIsInService(false);
        }
    }
            
    PsrBranchInfo::PsrBranchInfo(ComponentPtr<BranchAbc> branch) : branch_(branch)
    {
        defaultClosedStateConstr_ = branch->isInService() ? Trivalent::YES : Trivalent::NO;
        setClosedStateConstr(defaultClosedStateConstr_);
    }
    
    const string& PsrBranchInfo::id() const
    {
        return branch_->id();
    }
    
    void PsrBranchInfo::setBreaker(bool isInitClosed)
    {
        assert(branch_->isInService());
        hasBreaker_ = true;
        breakerIsInitClosed_ = isInitClosed;
        defaultClosedStateConstr_ = Trivalent::MAYBE;
    }

    void PsrBranchInfo::setClosedStateConstr(Trivalent sc)
    {
        closedStateConstr_ = sc;
        branch_->setIsInService(sc != Trivalent::NO);
    }
    
    const string& PsrGenInfo::id() const
    {
        return gen_->id();
    }

    PsrSolver::PsrSolver(Network& netw) : netw_(&netw)
    {
        // Set minimum voltage at all buses to zero.
        // If we don't know if a bus is fed, we may need it to have zero voltage.
        for (auto b : netw_->buses())
        {
            b->setVMagMin(0.0);
        }
        
        // Set minimum generation all gens to zero. If we need to isolate a generator, this *will* be enforced,
        // no matter what the bad consequences are.
        for (auto g : netw_->gens())
        {
            if (g->PMin() > 0.0)
            {
                g->setPMin(0.0);
            }

            if (g->QMin() > 0.0)
            {
                g->setQMin(0.0);
            }

            if (g->PMax() < 0.0)
            {
                g->setPMax(0.0);
            }
            
            if (g->QMax() < 0.0)
            {
                g->setQMax(0.0);
            }
        }

        // At this point, we don't know about any faults or breakers. Just create the info objects.
        // Later calls to setFault or setBreaker will update all data as required.
        for (auto bus : netw_->buses())
        {
            busInfos_.emplace(bus->id(), bus);
        }
        for (auto branch : netw_->branches())
        {
            branchInfos_.emplace(branch->id(), branch);
        }
        for (auto gen : netw_->gens())
        {
            genInfos_.emplace(gen->id(), gen);
        }
    }
            
    void PsrSolver::reset()
    {
        for (auto& busInf : busInfos_)
        {
            busInf.second.setModelBus(nullptr);
            busInf.second.setFedStateConstr(busInf.second.defaultFedStateConstr());
        }
        for (auto& branchInf : branchInfos_)
        {
            branchInf.second.setModelBranch(nullptr);
            branchInf.second.setClosedStateConstr(branchInf.second.defaultClosedStateConstr());
        }
        for (auto& genInf : genInfos_)
        {
            genInf.second.setModelGen(nullptr);
        }
    }
            
    void PsrSolver::lockInProblem()
    {
        // Set isFed for buses:
        
        // Check if definitely supplied:
        hasUnkStatusBranches_ = setUnkIsInService(false); // Calls solvePreprocess. Need to undo this, see below.
        for (auto& busInf : busInfos_)
        {
            busInf.second.setIsFed(busInf.second.bus().isSupplied() ? Trivalent::YES : Trivalent::MAYBE);
        }
        
        // Check if maybe supplied:
        setUnkIsInService(true); // Calls solvePreprocess. We want to keep this setting.
        for (auto& busInf : busInfos_)
        {
            if (busInf.second.isFed() == Trivalent::MAYBE)
            {
                auto definitelyNot = !busInf.second.bus().isSupplied();
                if (definitelyNot) busInf.second.setIsFed(Trivalent::NO);
            }
        }
        
        // Set isFed for branches and gens:
        
        for (auto& branchInf : branchInfos_)
        {
            branchInf.second.setIsFed(branchIsFed(branchInf.second));
        }
        
        for (auto& genInf : genInfos_)
        {
            genInf.second.setIsFed(genIsFed(genInf.second));
        }

        ptNetw_ = sgt2PowerTools(*netw_); // Set up the PowerTools network.
        for (auto ptBus : ptNetw_->nodes)
        {
            auto& busInf = busInfo(ptBus->_name);
            busInf.setPtBus(ptBus);
        }
        for (auto ptBranch : ptNetw_->arcs)
        {
            auto& branchInf = branchInfo(ptBranch->_name);
            branchInf.setPtBranch(ptBranch);
        }
        for (auto ptGen : ptNetw_->gens)
        {
            auto& genInf = genInfo(ptGen->_name);
            genInf.setPtGen(ptGen);
        }
    }
            
    bool PsrSolver::preCheck()
    {
        // Check if fedStateConstr is inconsistent with isFed.
        sgtLogDebug(LogLevel::NORMAL) << "preCheck" << endl;
        for (auto& busInf : busInfos_)
        {
            Trivalent sc = busInf.second.fedStateConstr();
            Trivalent isFed = busInf.second.isFed();

            if ((sc == Trivalent::NO && isFed == Trivalent::YES) || (sc == Trivalent::YES && isFed == Trivalent::NO))
            {
                return false;
            }
        }
        return true;
    }

    bool PsrSolver::acRectCheck()
    {
        sgtLogDebug(LogLevel::NORMAL) << "acRectCheck" << endl;
        LogIndent _;
        makeAcRectModel();
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;
        return success;
    }

    bool PsrSolver::acRectSwitchingCheck()
    {
        sgtLogDebug(LogLevel::NORMAL) << "acRectSwitchingCheck" << endl;
        LogIndent _;
        makeAcRectSwitchingModel();
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;
        return success;
    }

    bool PsrSolver::nAcRectSwitchingCheck(size_t n)
    {
        sgtLogDebug(LogLevel::NORMAL) << "nAcRectSwitchingCheck" << endl;
        LogIndent _;
        makeNAcRectSwitchingModel(n);
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;

        return success;
    }

    bool PsrSolver::socpCheck()
    {
        sgtLogDebug(LogLevel::NORMAL) << "socpCheck" << endl;
        LogIndent _;
        makeSocpModel();
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;
        return success;
    }
 
    bool PsrSolver::socpSwitchingCheck()
    {
        sgtLogDebug(LogLevel::NORMAL) << "socpSwitchingCheck" << endl;
        LogIndent _;
        makeSocpSwitchingModel();
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;
        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Bus Fed:" << endl;
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            auto& var = busInf.second.modelBus<SocpSwitchingModel>().fed;
            sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
        }
        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Branch Closed:" << endl;
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto& var = branchInf.second.modelBranch<SocpSwitchingModel>().closed;
            sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
        }
        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        return success;
    }

    bool PsrSolver::nSocpSwitchingCheck(size_t n)
    {
        sgtLogDebug(LogLevel::NORMAL) << "nSocpSwitchingCheck" << endl;
        LogIndent _;
        makeNSocpSwitchingModel(n);
        sgtLogDebug(LogLevel::NORMAL) << "Model created, about to solve..." << endl;
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug() << "Model prior to solve:" << endl;
            printModel(*powerModel_->_model);
        }
        int retVal = powerModel_->solve();
        bool success = retVal != -1;
        sgtLogDebug(LogLevel::NORMAL) << "Done, success = " << success << endl;

        return success;
    }

    bool PsrSolver::solve()
    {
        bool ok = true;

        lockInProblem();

        // Print debug info.
        printStateConstrs();

        // Pre-check.
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Pre-check:" << endl;
        ok = preCheck();
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Pre-check status = " << ok << endl;

        // SOCP check.
        if (useSocp_ && ok) 
        {
            sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: SOCP:" << endl;
            ok = socpCheck();
            sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: SOCP status = " << ok << endl;
        }

        // Solve AC.
#ifdef REQUIRE_SOLVE_AC
        if (ok) 
        {
            sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: AC:" << endl;
            ok = acRectCheck();
            sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: AC status = " << ok << endl;
        }
#endif

        return ok;
    }
            
    template<typename TMod> void PsrSolver::applySwitchingResults()
    {
        for (auto& busInfo : busInfos_)
        {
            int fed = busInfo.second.modelBus<TMod>().fed.get_value();
            assert(fed == 0 || fed == 1);
            busInfo.second.setFedStateConstr(fed == 0 ? Trivalent::NO : Trivalent::YES);
        }
        
        for (auto& branchInfo : branchInfos_)
        {
            int closed = branchInfo.second.modelBranch<TMod>().closed.get_value();
            assert(closed == 0 || closed == 1);
            branchInfo.second.setClosedStateConstr(closed == 0 ? Trivalent::NO : Trivalent::YES);
        }
    }
    template void PsrSolver::applySwitchingResults<AcRectSwitchingModel>();
    template void PsrSolver::applySwitchingResults<SocpSwitchingModel>();
   
    void PsrSolver::printStateConstrs() const
    {
        sgtLogDebug(LogLevel::NORMAL) << endl;
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Solve: Bus fed constraints:";
        printBusFedScs(busInfos_);
        sgtLogDebug(LogLevel::NORMAL) << endl;
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Solve: Branch closed constraints:";
        printBranchClosedScs(branchInfos_);
        sgtLogDebug(LogLevel::NORMAL) << endl;
    }
            
    void PsrSolver::printIslands() const
    {
        auto islands = netw_->islands();
        sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: There are " << islands.size() << " islands." << endl;
        for (auto island : islands)
        {
            sgtLogDebug(LogLevel::NORMAL) << "PSR_SOLVER: Island " << island.idx
                << " : Fed = " << island.isSupplied << endl;
            for (auto bus : island.buses)
            {
                LogIndent _;
                sgtLogDebug(LogLevel::VERBOSE) << "PSR_SOLVER: Bus " << bus->id() << endl;
            }
        }
    }

    template<typename TMod> void PsrSolver::printSwitching() const
    {
        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Bus Fed:" << endl;
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            const auto& modBus = busInf.second.modelBus<TMod>();
            auto& var = modBus.fed;
            sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
        }

        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Branch Closed:" << endl;
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            const auto& modBranch = branchInf.second.modelBranch<TMod>();
            auto& var = modBranch.closed;
            sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
        }
    }
    template void PsrSolver::printSwitching<AcRectSwitchingModel>() const;
    template void PsrSolver::printSwitching<SocpSwitchingModel>() const;

    template<typename TMod> void PsrSolver::printNSwitching() const
    {
        if (debugLogLevel() == LogLevel::VERBOSE)
        {
            sgtLogDebug(LogLevel::VERBOSE) << "--------" << endl;
            sgtLogDebug(LogLevel::VERBOSE) << "Final Model:" << endl;
            printModel(*powerModel_->_model);
        }
        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Bus Fed:" << endl;
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            const auto& modBus = busInf.second.modelBus<TMod>();
            for (size_t i = 0; i < nTime_; ++i)
            {
                auto& var = modBus.fed[i];
                sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
            }
        }

        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Branch Closed:" << endl;
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            const auto& modBranch = branchInf.second.modelBranch<TMod>();

            for (size_t i = 0; i < nTime_; ++i)
            {
                auto& var = modBranch.closed[i];
                sgtLogDebug(LogLevel::NORMAL) << var._name << " " << var.get_value() << endl;
            }
        }

        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Bus Initial, Final:" << endl;
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            const auto& modBus = busInf.second.modelBus<TMod>();
            sgtLogDebug(LogLevel::NORMAL) << busInf.second.bus().id() << " " 
                << modBus.fed[0].get_value() << " " << modBus.fed[nTime_ - 1].get_value() << endl;
        }

        sgtLogDebug(LogLevel::NORMAL) << "--------" << endl;
        sgtLogDebug(LogLevel::NORMAL) << "Branch Init, Final:" << endl;
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            const auto& modBranch = branchInf.second.modelBranch<TMod>();
            sgtLogDebug(LogLevel::NORMAL) << branchInf.second.branch().id() << " " 
                << modBranch.closed[0].get_value() << " " << modBranch.closed[nTime_ - 1].get_value() << endl;
        }

        sgtLogMessage(LogLevel::NORMAL) << "--------" << endl;
        sgtLogMessage(LogLevel::NORMAL) << "Branch Actions:" << endl;
        for (size_t i = 0; i < nTime_ - 1; ++i)
        {
            sgtLogDebug(LogLevel::NORMAL) << "Step = " << i << " -> " << i + 1 << endl;
            LogIndent _;
            for (auto& branchInf : branchInfos_)
            {
                if (!branchInf.second.isActive()) continue;

                const auto& modBranch = branchInf.second.modelBranch<TMod>();
                const auto& open = modBranch.open[i];
                const auto& close = modBranch.close[i];
                if (open.get_value() == 1)
                {
                    sgtLogMessage(LogLevel::NORMAL) << "Open " << branchInf.second.branch().id() << endl;
                }
                if (close.get_value() == 1)
                {
                    sgtLogMessage(LogLevel::NORMAL) << "Close " << branchInf.second.branch().id() << endl;
                }
            }
        }
    }
    template void PsrSolver::printNSwitching<NAcRectSwitchingModel>() const;
    template void PsrSolver::printNSwitching<NSocpSwitchingModel>() const;
            
    template<typename TMod> json PsrSolver::getMinlpPlanJson() const
    {
        json result = json::array();
        for (size_t i = 0; i < nTime_ - 1; ++i)
        {
            for (auto& branchInf : branchInfos_)
            {
                if (!branchInf.second.isActive()) continue;

                const auto& modBranch = branchInf.second.modelBranch<TMod>();
                const auto& open = modBranch.open[i];
                const auto& close = modBranch.close[i];
                if ((open.get_value() == 1) || (close.get_value() == 1))
                {
                    result.push_back(branchInf.second.id());
                }
            }
        }
        return result;
    }
    template json PsrSolver::getMinlpPlanJson<NAcRectSwitchingModel>() const;
    template json PsrSolver::getMinlpPlanJson<NSocpSwitchingModel>() const;

    template<typename TMod> void PsrSolver::addModelObjects()
    {
        // Don't add anything from unsupplied islands.
        
        for (auto& busInf: busInfos_)
        {
            if (busInf.second.isActive())
            {
                busInf.second.setModelBus(make_unique<typename TMod::ModBus>());
            }
            else
            {
                busInf.second.setModelBus(nullptr);
            }
        }

        for (auto& branchInf: branchInfos_)
        {
            if (branchInf.second.isActive())
            {
                branchInf.second.setModelBranch(make_unique<typename TMod::ModBranch>());
            }
            else
            {
                branchInf.second.setModelBranch(nullptr);
            }
        }

        for (auto& genInf: genInfos_)
        {
            if (genInf.second.isActive())
            {
                genInf.second.setModelGen(make_unique<typename TMod::ModGen>());
            }
            else
            {
                genInf.second.setModelGen(nullptr);
            }
        }
    }

    void PsrSolver::makeAcRectModel()
    {
        nTime_ = 1;

        powerModel_ = make_unique<PowerModel>(ACRECT, ptNetw_.get(), ipopt);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<AcRectModel>();

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<AcRectModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusVrViVars<AcRectModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<AcRectModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedVars<AcRectModel>(busInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclConstrs<AcRectModel>(busInf.second);
            addVoltageBoundConstrs<AcRectModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto sc = branchInf.second.closedStateConstr();
            assert(sc != Trivalent::NO);

            if (sc == Trivalent::YES)
            {
                // The branch is definitely closed. It should obey power flow.
                addAcRectPowerFlowConstrs<AcRectModel>(branchInf.second);
            }
            
            // The branch is either maybe closed or definitely closed.
            // We know the thermal limits must be obeyed in either case.
            addThermalConstrs<AcRectModel>(branchInf.second);
        }

        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto sc = branchInf.second.closedStateConstr();
            assert(sc != Trivalent::NO);

            if (sc != Trivalent::MAYBE)
            {
                addBusFedMatchingConstrs<AcRectModel>(branchInf.second);
            }
        }
        
        setMaxLoadObjective<AcRectModel>();
        addSpecialVoltageObjTerm<AcRectModel>();
    }
    
    void PsrSolver::makeAcRectSwitchingModel()
    {
        nTime_ = 1;

        powerModel_ = make_unique<PowerModel>(ACRECT, ptNetw_.get(), bonmin);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<AcRectSwitchingModel>();

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<AcRectSwitchingModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusVrViVars<AcRectSwitchingModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<AcRectSwitchingModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedSwitchingVars<AcRectSwitchingModel>(busInf.second);
        }

        // Branch switch variables.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchClosedSwitchingVars<AcRectSwitchingModel>(branchInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclSwitchingConstrs<AcRectSwitchingModel>(busInf.second);
            addVoltageBoundSwitchingConstrs<AcRectSwitchingModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addAcRectPowerFlowSwitchingConstrs<AcRectSwitchingModel>(branchInf.second);
            addThermalSwitchingConstrs<AcRectSwitchingModel>(branchInf.second);
        }

        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBusFedMatchingSwitchingConstrs<AcRectSwitchingModel>(branchInf.second);
        }
        
        setMaxLoadSwitchingObjective<AcRectSwitchingModel>();
        addBranchClosedObjTerm<AcRectSwitchingModel>();
    }

    void PsrSolver::makeNAcRectSwitchingModel(size_t n)
    {
        nTime_ = n;

        powerModel_ = make_unique<PowerModel>(ACRECT, ptNetw_.get(), bonmin);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<NAcRectSwitchingModel>();

        // Resize arrays.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            busInf.second.modelBus<NAcRectSwitchingModel>().realloc(nTime_);
        }
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            branchInf.second.modelBranch<NAcRectSwitchingModel>().realloc(nTime_);
        }
        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            genInf.second.modelGen<NAcRectSwitchingModel>().realloc(nTime_);
        }

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<NAcRectSwitchingModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusVrViVars<NAcRectSwitchingModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<NAcRectSwitchingModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedSwitchingVars<NAcRectSwitchingModel>(busInf.second);

            // Enforce final state:
            auto& modBus = busInf.second.modelBus<NAcRectSwitchingModel>();
            modBus.fed[nTime_ - 1].set_lb(busInf.second.finalRequireFed());
            modBus.fed[nTime_ - 1].set_ub(busInf.second.finalRequireFed());
        }

        // Branch switch variables.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchClosedSwitchingVars<NAcRectSwitchingModel>(branchInf.second);

            // Enforce initial state:
            auto& modBranch = branchInf.second.modelBranch<NAcRectSwitchingModel>();
            modBranch.closed[0].set_lb(branchInf.second.breakerIsInitClosed());
            modBranch.closed[0].set_ub(branchInf.second.breakerIsInitClosed());

            addNLinkingVars<NAcRectSwitchingModel>(branchInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclSwitchingConstrs<NAcRectSwitchingModel>(busInf.second);
            addVoltageBoundSwitchingConstrs<NAcRectSwitchingModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addAcRectPowerFlowSwitchingConstrs<NAcRectSwitchingModel>(branchInf.second);
            addThermalSwitchingConstrs<NAcRectSwitchingModel>(branchInf.second);
        }

        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBusFedMatchingSwitchingConstrs<NAcRectSwitchingModel>(branchInf.second);
            addNLinkingConstrs<NAcRectSwitchingModel>(branchInf.second);
        }

        addNSingleActionConstrs<NAcRectSwitchingModel>();
       
        setNSwitchingObjective<NAcRectSwitchingModel>();
    }

    void PsrSolver::makeSocpModel()
    {
        nTime_ = 1;

        powerModel_ = make_unique<PowerModel>(SOCP, ptNetw_.get(), gurobi);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<SocpModel>();

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<SocpModel>(branchInf.second);
            addBranchWVars<SocpModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusWVars<SocpModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<SocpModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedVars<SocpModel>(busInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclConstrs<SocpModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto sc = branchInf.second.closedStateConstr();
            assert(sc != Trivalent::NO);

            if (sc == Trivalent::YES)
            {
                // The branch is definitely closed. It should obey power flow.
                addSocpConstrs<SocpModel>(branchInf.second);
            }
            
            // The branch is either maybe closed or definitely closed.
            // We know the thermal limits must be obeyed in either case.
            addThermalConstrs<SocpModel>(branchInf.second);
        }

        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto sc = branchInf.second.closedStateConstr();
            assert(sc != Trivalent::NO);

            if (sc != Trivalent::MAYBE)
            {
                addBusFedMatchingConstrs<SocpModel>(branchInf.second);
            }
        }

        
        setMaxLoadObjective<SocpModel>();
    }

    void PsrSolver::makeSocpSwitchingModel()
    {
        nTime_ = 1;

        powerModel_ = make_unique<PowerModel>(SOCP, ptNetw_.get(), gurobi);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<SocpSwitchingModel>();

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<SocpSwitchingModel>(branchInf.second);
            addBranchWVars<SocpSwitchingModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusWVars<SocpSwitchingModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<SocpSwitchingModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedSwitchingVars<SocpSwitchingModel>(busInf.second);
        }

        // Branch switch variables.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchClosedSwitchingVars<SocpSwitchingModel>(branchInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclSwitchingConstrs<SocpSwitchingModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addSocpSwitchingConstrs<SocpSwitchingModel>(branchInf.second);
            addThermalSwitchingConstrs<SocpSwitchingModel>(branchInf.second);
        }
         
        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBusFedMatchingSwitchingConstrs<SocpSwitchingModel>(branchInf.second);
        }
       
        setMaxLoadSwitchingObjective<SocpSwitchingModel>();
        addBranchClosedObjTerm<SocpSwitchingModel>();
    }

    void PsrSolver::makeNSocpSwitchingModel(size_t n)
    {
        nTime_ = n;

        powerModel_ = make_unique<PowerModel>(SOCP, ptNetw_.get(), gurobi);

        // Normally would do: powerModel_->build(), but we need custom behaviour - set up below.
        
        powerModel_->_model = new Model();
        powerModel_->_solver = new PTSolver(powerModel_->_model, powerModel_->_stype);

        // Initialize ModelBus, ModelBranch and ModelGen objects with model.
        addModelObjects<NSocpSwitchingModel>();

        // Resize arrays.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            busInf.second.modelBus<NSocpSwitchingModel>().realloc(nTime_);
        }
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            branchInf.second.modelBranch<NSocpSwitchingModel>().realloc(nTime_);
        }
        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            genInf.second.modelGen<NSocpSwitchingModel>().realloc(nTime_);
        }

        // Add variables to model:

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchPQVars<NSocpSwitchingModel>(branchInf.second);
            addBranchWVars<NSocpSwitchingModel>(branchInf.second);
        }

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusWVars<NSocpSwitchingModel>(busInf.second);
        }

        for (auto& genInf : genInfos_)
        {
            if (!genInf.second.isActive()) continue;

            addGenVars<NSocpSwitchingModel>(genInf.second);
        }

        // Bus fed variables.
        // Add separately at end to make easier to debug.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addBusFedSwitchingVars<NSocpSwitchingModel>(busInf.second);
            
            // Enforce final state:
            auto& modBus = busInf.second.modelBus<NSocpSwitchingModel>();
            modBus.fed[nTime_ - 1].set_lb(busInf.second.finalRequireFed());
            modBus.fed[nTime_ - 1].set_ub(busInf.second.finalRequireFed());
        }

        // Branch switch variables.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBranchClosedSwitchingVars<NSocpSwitchingModel>(branchInf.second);

            // Enforce initial state:
            auto& modBranch = branchInf.second.modelBranch<NSocpSwitchingModel>();
            modBranch.closed[0].set_lb(branchInf.second.breakerIsInitClosed());
            modBranch.closed[0].set_ub(branchInf.second.breakerIsInitClosed());

            addNLinkingVars<NSocpSwitchingModel>(branchInf.second);
        }

        // Add constraints:
        
        // Constraints at buses: 
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            addKclSwitchingConstrs<NSocpSwitchingModel>(busInf.second);
        }
        
        // Constraints at branches: 
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addSocpSwitchingConstrs<NSocpSwitchingModel>(branchInf.second);
            addThermalSwitchingConstrs<NSocpSwitchingModel>(branchInf.second);
        }
         
        // Bus fed matching constraints.
        // Add separately at end to make easier to debug.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            addBusFedMatchingSwitchingConstrs<NSocpSwitchingModel>(branchInf.second);
            addNLinkingConstrs<NSocpSwitchingModel>(branchInf.second);
        }

        addNSingleActionConstrs<NSocpSwitchingModel>();
       
        setNSwitchingObjective<NSocpSwitchingModel>();
    }

    template<typename TMod> void PsrSolver::addBranchPQVars(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();

        auto sc = branchInf.closedStateConstr();
        assert(sc != Trivalent::NO);

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& Pi = e(modBranch.Pi,i);
            auto& Pj = e(modBranch.Pj,i);
            auto& Qi = e(modBranch.Qi,i);
            auto& Qj = e(modBranch.Qj,i);
            auto& Si = e(modBranch.Si,i);
            auto& Sj = e(modBranch.Sj,i);

            Pi.init("pi_" + iStr + branchInf.id());
            Pi = 0.0;

            Pj.init("pj_" + iStr + branchInf.id());
            Pj = 0.0;

            Qi.init("qi_" + iStr + branchInf.id());
            Qi = 0.0;

            Qj.init("qj_" + iStr + branchInf.id());
            Qj = 0.0;

            powerModel_->_model->addVar(Pi);
            powerModel_->_model->addVar(Pj);
            powerModel_->_model->addVar(Qi);
            powerModel_->_model->addVar(Qj);

            Si = PtComplex("Si_" + iStr + branchInf.id(), &Pi, &Qi);
            Sj = PtComplex("Sj_" + iStr + branchInf.id(), &Pj, &Qj);
        }
    }

    template<typename TMod> void PsrSolver::addBranchWVars(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        auto sc = branchInf.closedStateConstr();
        assert(sc != Trivalent::NO);

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& wr = e(modBranch.wr,i);
            auto& wi = e(modBranch.wi,i);

            string wrName = "wr_" + iStr + branchInf.id();
            string wiName = "wi_" + iStr + branchInf.id();

            // TODO: check below.
            switch (sc)
            {
                case Trivalent::NO:
                    throw logic_error("Unexpected state constraint value.");
                case Trivalent::YES:
                    wr.init(wrName, 0.0, ptBranch.src->vbound.max*ptBranch.dest->vbound.max);
                    wr = 1.0;

                    wi.init(wiName, -ptBranch.src->vbound.max*ptBranch.dest->vbound.max,
                            ptBranch.src->vbound.max*ptBranch.dest->vbound.max);
                    wi = 0.0;
                    break;
                case Trivalent::MAYBE:
                    wr.init(wrName, 0.0, ptBranch.src->vbound.max*ptBranch.dest->vbound.max);
                    wr = 0.5;

                    wi.init(wiName, -ptBranch.src->vbound.max*ptBranch.dest->vbound.max,
                            ptBranch.src->vbound.max*ptBranch.dest->vbound.max);
                    wi = 0.0;
                    break;
            }

            powerModel_->_model->addVar(wr);
            powerModel_->_model->addVar(wi);
        }
    }

    template<typename TMod> void PsrSolver::addBusFedVars(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>(); 

        string varName = "fed_" + busInf.id();
        switch (busInf.tightenedFedStateConstr())
        {
            case Trivalent::NO:
                modBus.fed.init(varName, 0.0, 0.0);
                modBus.fed = 0.0;
                break;
            case Trivalent::YES:
                modBus.fed.init(varName, 1.0, 1.0);
                modBus.fed = 1.0;
                break;
            case Trivalent::MAYBE:
                modBus.fed.init(varName, 0.0, 1.0);
                modBus.fed = 0.5;
        }
        powerModel_->_model->addVar(modBus.fed);
    }

    template<typename TMod> void PsrSolver::addBusFedSwitchingVars(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>(); 

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& fed = e(modBus.fed,i);
            
            string varName = "fed_" + iStr + busInf.id();

            switch (busInf.tightenedFedStateConstr())
            {
                case Trivalent::NO:
                    fed.init(varName, 0, 0);
                    fed = 0;
                    break;
                case Trivalent::YES:
                    fed.init(varName, 1, 1);
                    fed = 1;
                    break;
                case Trivalent::MAYBE:
                    fed.init(varName, 0, 1);
                    fed = 1;
                    break;
            }
            fed._bounded_down = true; // KLUDGE: error in PowerTools init.
            fed._bounded_up = true; // KLUDGE: error in PowerTools init.
            powerModel_->_model->addVar(fed);
        }
    }

    template<typename TMod> void PsrSolver::addBranchClosedSwitchingVars(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>(); 

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& closed = e(modBranch.closed,i);
            
            string varName = "on_" + iStr + branchInf.id();

            switch (branchInf.closedStateConstr())
            {
                case Trivalent::NO:
                    closed.init(varName, 0, 0);
                    closed = 0;
                    break;
                case Trivalent::YES:
                    closed.init(varName, 1, 1);
                    closed = 1;
                    break;
                case Trivalent::MAYBE:
                    closed.init(varName, 0, 1);
                    closed = 1;
            }
            closed._bounded_down = true; // KLUDGE: error in PowerTools init.
            closed._bounded_up = true; // KLUDGE: error in PowerTools init.
            powerModel_->_model->addVar(closed);
        }
    }

    template<typename TMod> void PsrSolver::addBusVrViVars(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        auto& ptBus = busInf.ptBus();

        auto sc = busInf.tightenedFedStateConstr();
        
        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            string vrName = "vr_" + iStr + busInf.id();
            string viName = "vi_" + iStr + busInf.id();

            auto& Vr = e(modBus.Vr,i);
            auto& Vi = e(modBus.Vi,i);
            auto& V = e(modBus.V,i);

            switch (sc)
            {
                case Trivalent::NO:
                    Vr.init(vrName, 0.0, 0.0);
                    Vr = 0.0;

                    Vi.init(viName, 0.0, 0.0);
                    Vi = 0.0;
                    break;
                case Trivalent::YES:
                case Trivalent::MAYBE:
                    double ub = ptBus.vbound.max;
                    Vr.init(vrName, -ub, ub);
                    Vr = ptBus.vs;

                    Vi.init(viName, -ub, ub);
                    Vi = 0.0;
                    break;
            }

            powerModel_->_model->addVar(Vr);
            powerModel_->_model->addVar(Vi);

            V = PtComplex("V_" + busInf.id(), &Vr, &Vi);
        }
    }
 
    template<typename TMod> void PsrSolver::addBusWVars(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        auto& ptBus = busInf.ptBus();

        auto sc = busInf.tightenedFedStateConstr();

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& w = e(modBus.w,i);
            auto& V = e(modBus.V,i);

            string wName = "w_" + busInf.id();

            // TODO: Check below.
            switch (sc)
            {
                case Trivalent::NO:
                    w.init(wName, 0.0, 0.0);
                    w = 0.0;
                    break;
                case Trivalent::YES:
                    w.init(wName, pow(ptBus.vbound.min, 2), pow(ptBus.vbound.max, 2));
                    w = pow(ptBus.vs, 2);
                    break;
                case Trivalent::MAYBE:
                    w.init(wName, 0.0, pow(ptBus.vbound.max, 2));
                    w = 0.5;
                    break;
            }
            powerModel_->_model->addVar(w);

            V = PtComplex("V_" + busInf.id(), &dummy, &dummy, &w); V.lift();
        }
    }
 
    template<typename TMod> void PsrSolver::addGenVars(PsrGenInfo& genInf)
    {
        auto& modGen = genInf.modelGen<TMod>();
        auto& ptGen = genInf.ptGen();
        auto& ptBus = *ptGen._bus;

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& Pg = e(modGen.Pg,i);
            auto& Qg = e(modGen.Qg,i);
            auto& Sg = e(modGen.Sg,i);

            assert(busInfos_.at(ptBus._name).fedStateConstr() == Trivalent::YES); // Active gen must be fed.

            Pg.init("pg_" + genInf.id(), ptGen.pbound.min, ptGen.pbound.max);
            Pg = 0.0;
            powerModel_->_model->addVar(Pg);

            Qg.init("qg_" + genInf.id(), ptGen.qbound.min, ptGen.qbound.max);
            Qg = 0.0;
            powerModel_->_model->addVar(Qg);

            Sg = PtComplex("Sg_" + genInf.id(), &Pg, &Qg);
        }
    }
               
    template<typename TMod> void PsrSolver::addNLinkingVars(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        for (size_t i = 0; i < nTime_ - 1; ++i)
        {
            string suffix = to_string(i) + "_" + ptBranch._name;
            switch (branchInf.closedStateConstr())
            {
                case Trivalent::NO:
                    modBranch.close[i].init("close_" + suffix, 0, 0);
                    modBranch.close[i] = 0;

                    modBranch.open[i].init("open_" + suffix, 0, 0);
                    modBranch.open[i] = 0;
                    break;
                case Trivalent::YES:
                    modBranch.close[i].init("close_" + suffix, 0, 0);
                    modBranch.close[i] = 0;

                    modBranch.open[i].init("open_" + suffix, 0, 0);
                    modBranch.open[i] = 0;
                    break;
                case Trivalent::MAYBE:
                    modBranch.close[i].init("close_" + suffix, 0, 1);
                    modBranch.close[i] = 0;

                    modBranch.open[i].init("open_" + suffix, 0, 1);
                    modBranch.open[i] = 0;
                    break;
            }
            modBranch.open[i]._bounded_down = true; // KLUDGE: error in PowerTools init.
            modBranch.open[i]._bounded_up = true; // KLUDGE: error in PowerTools init.
            modBranch.close[i]._bounded_down = true; // KLUDGE: error in PowerTools init.
            modBranch.close[i]._bounded_up = true; // KLUDGE: error in PowerTools init.
            powerModel_->_model->addVar(modBranch.open[i]);
            powerModel_->_model->addVar(modBranch.close[i]);
        }
    }
                
    template<typename TMod> void PsrSolver::addBusFedMatchingConstrs(PsrBranchInfo& branchInf)
    {
        auto& ptBranch = branchInf.ptBranch();

        auto& fromFedVar = busInfo(ptBranch.src->_name).modelBus<TMod>().fed;
        auto& toFedVar = busInfo(ptBranch.dest->_name).modelBus<TMod>().fed;

        Constraint c("match_fed_" + ptBranch.src->_name + "_" + ptBranch.dest->_name);
        c += fromFedVar;
        c -= toFedVar;
        c = 0;
        safeAddConstr(*powerModel_->_model, c);
    }

    template<typename TMod> void PsrSolver::addBusFedMatchingSwitchingConstrs(PsrBranchInfo& branchInf)
    {
        // This is a big-M formulation of the switching constraint.
        
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            auto& fromFedVar = e(busInfo(ptBranch.src->_name).template modelBus<TMod>().fed,i);
            auto& toFedVar = e(busInfo(ptBranch.dest->_name).template modelBus<TMod>().fed,i);

            auto& closed = e(modBranch.closed,i);

            {
                Constraint c("match_fed_u_" + iStr + ptBranch.src->_name + "_" + ptBranch.dest->_name);
                c += fromFedVar - toFedVar - (1 - closed);
                c <= 0;
                safeAddConstr(*powerModel_->_model, c);
            }

            {
                Constraint c("match_fed_l_" + iStr + ptBranch.src->_name + "_" + ptBranch.dest->_name);
                c += fromFedVar - toFedVar + (1 - closed);
                c >= 0;
                safeAddConstr(*powerModel_->_model, c);
            }
        }
    }

    template<typename TMod> void PsrSolver::addAcRectPowerFlowConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>(); 

        Function fPi; Function fPj; Function fQi; Function fQj;
        acPowerFlows<TMod>(branchInf, fPi, fPj, fQi, fQj);

        Constraint flowPFrom("flow_" + modBranch.Pi._name);

        flowPFrom += fPi;
        flowPFrom = 0;
        safeAddConstr(*powerModel_->_model, flowPFrom);

        Constraint flowPTo("flow_" + modBranch.Pj._name);
        flowPTo += fPj;
        flowPTo = 0;
        safeAddConstr(*powerModel_->_model, flowPTo);

        Constraint flowQFrom("flow_" + modBranch.Qi._name);
        flowQFrom += fQi;
        flowQFrom = 0;
        safeAddConstr(*powerModel_->_model, flowQFrom);

        Constraint flowQTo("flow_" + modBranch.Qj._name);
        flowQTo += fQj;
        flowQTo = 0;
        safeAddConstr(*powerModel_->_model, flowQTo);
    }

    template<typename TMod> void PsrSolver::addAcRectPowerFlowSwitchingConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>(); 

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";
            Function fPi; Function fPj; Function fQi; Function fQj;

            acPowerFlows<TMod>(branchInf, fPi, fPj, fQi, fQj, i);

            double MPi; double MPj; double MQi; double MQj;
            powerFlowBigM(branchInf.ptBranch(), MPi, MPj, MQi, MQj);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Pi,i)._name,
                    fPi, e(modBranch.closed,i), MPi, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Pj,i)._name,
                    fPj, e(modBranch.closed,i), MPj, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Qi,i)._name,
                    fQi, e(modBranch.closed,i), MQi, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Qj,i)._name,
                    fQj, e(modBranch.closed,i), MQj, *powerModel_->_model);
        }
    }

    template<typename TMod> void PsrSolver::addSocpConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();

        Function fPi; Function fPj; Function fQi; Function fQj;
        socpPowerFlows<TMod>(branchInf, fPi, fPj, fQi, fQj);

        auto& ptBranch = branchInf.ptBranch();

        auto& src = *ptBranch.src;
        auto& srcModBus = busInfos_.at(src._name).template modelBus<TMod>();

        auto& dest = *ptBranch.dest;
        auto& destModBus = busInfos_.at(dest._name).template modelBus<TMod>();
        
        Constraint flowPFrom("flow_" + modBranch.Pi._name);
        flowPFrom += fPi;
        flowPFrom = 0;
        safeAddConstr(*powerModel_->_model, flowPFrom);

        Constraint flowPTo("flow_" + modBranch.Pj._name);
        flowPTo += fPj;
        flowPTo = 0;
        safeAddConstr(*powerModel_->_model, flowPTo);

        Constraint flowQFrom("flow_" + modBranch.Qi._name);
        flowQFrom += fQi;
        flowQFrom = 0;
        safeAddConstr(*powerModel_->_model, flowQFrom);

        Constraint flowQTo("flow_" + modBranch.Qj._name);
        flowQTo += fQj;
        flowQTo = 0;
        safeAddConstr(*powerModel_->_model, flowQTo);

        Constraint SOCP("socp_" + ptBranch._name);
        SOCP += srcModBus.w*destModBus.w;
        SOCP -= ((modBranch.wr)^2);
        SOCP -= ((modBranch.wi)^2);
        SOCP >= 0;
        safeAddConstr(*powerModel_->_model, SOCP);
    }

    template<typename TMod> void PsrSolver::addSocpSwitchingConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>(); 

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            Function fPi; Function fPj; Function fQi; Function fQj;
            socpPowerFlows<TMod>(branchInf, fPi, fPj, fQi, fQj, i);

            double MPi; double MPj; double MQi; double MQj;
            powerFlowBigM(branchInf.ptBranch(), MPi, MPj, MQi, MQj);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Pi,i)._name,
                    fPi, e(modBranch.closed,i), MPi, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Pj,i)._name,
                    fPj, e(modBranch.closed,i), MPj, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Qi,i)._name,
                    fQi, e(modBranch.closed,i), MQi, *powerModel_->_model);

            addBigMSwitchedEqualityConstr("flow_" + e(modBranch.Qj,i)._name,
                    fQj, e(modBranch.closed,i), MQj, *powerModel_->_model);

            auto& ptBranch = branchInf.ptBranch();

            auto& src = *ptBranch.src;
            auto& srcModBus = busInfos_.at(src._name).template modelBus<TMod>();

            auto& dest = *ptBranch.dest;
            auto& destModBus = busInfos_.at(dest._name).template modelBus<TMod>();

            // TODO: I think doesn't need any switching treatment, check.
            Constraint socp("socp_" + iStr + ptBranch._name);
            socp += e(srcModBus.w,i)*e(destModBus.w,i);
            socp -= (e(modBranch.wr,i)^2);
            socp -= (e(modBranch.wi,i)^2);
            socp >= 0;
            safeAddConstr(*powerModel_->_model, socp);
        }
    }

    // addKclConstrs sets the power flowing in via lines and generation equal to the power flowing out
    // via the load. The load is set to zero if the correponding bus is not fed, as determined by
    // fedVar. If we don't know whether the bus if fed or not, we can't formulate KCL, hence
    // the check. 
    template<typename TMod> void PsrSolver::addKclConstrs(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        var<>& fedVar = modBus.fed;
        PtBus& ptBus = busInf.ptBus();

        Constraint KCL_P("kcl_p_" + busInf.id());
        Constraint KCL_Q("kcl_q_" + busInf.id());

        // Power flowing out of node via lines.
        for (auto ptBranch : ptBus.get_out())
        {
            auto& branchInf = branchInfo(ptBranch->_name);
            if (!branchInf.isActive()) continue;

            auto& modBranch = branchInf.modelBranch<TMod>();

            KCL_P += modBranch.Pi; 
            KCL_Q += modBranch.Qi; 
        }

        // Power flowing out of node via lines.
        for (auto ptBranch : ptBus.get_in())
        {
            auto& branchInf = branchInfo(ptBranch->_name);
            if (!branchInf.isActive()) continue;

            auto& modBranch = branchInf.modelBranch<TMod>();

            KCL_P += modBranch.Pj; 
            KCL_Q += modBranch.Qj;
        }

        // Real power flowing out of node via shunts.
        KCL_P += ptBus.gs()*(modBus.V.square_magnitude());
        KCL_Q -= ptBus.bs()*(modBus.V.square_magnitude());

        // Power flowing out node via load.
        KCL_P += ptBus.pl() * fedVar; // TODO: Is this the right place?
        KCL_Q += ptBus.ql() * fedVar;

        // Power flowing into node via gens.
        for (auto ptGen : ptBus._gen)
        {
            auto& genInfo = genInfos_.at(ptGen->_name);
            if (!genInfo.isActive()) continue;

            auto& modGen = genInfo.modelGen<TMod>();
            KCL_P -= modGen.Pg;
            KCL_Q -= modGen.Qg; 
        }

        KCL_P = 0;
        KCL_Q = 0;

        safeAddConstr(*powerModel_->_model, KCL_P);
        safeAddConstr(*powerModel_->_model, KCL_Q);
    }

    template<typename TMod> void PsrSolver::addKclSwitchingConstrs(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        PtBus& ptBus = busInf.ptBus();
        
        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";

            Constraint KCL_P("kcl_p_" + iStr + ptBus._name);
            Constraint KCL_Q("kcl_q_" + iStr + ptBus._name);

            // Power flowing out of node via lines.
            for (auto ptBranch : ptBus.get_out())
            {
                auto& branchInf = branchInfo(ptBranch->_name);
                if (!branchInf.isActive()) continue;

                auto& modBranch = branchInf.modelBranch<TMod>();

                KCL_P += e(modBranch.Pi,i); // Note: will be zero if branch is off, bc thermal switching constrs. 
                KCL_Q += e(modBranch.Qi,i); // Note: will be zero if branch is off, bc thermal switching constrs. 
            }

            // Power flowing out of node via lines.
            for (auto ptBranch : ptBus.get_in())
            {
                auto& branchInf = branchInfo(ptBranch->_name);
                if (!branchInf.isActive()) continue;

                auto& modBranch = branchInf.modelBranch<TMod>();

                KCL_P += e(modBranch.Pj,i); // Note: will be zero if branch is off, bc thermal switching constrs. 
                KCL_Q += e(modBranch.Qj,i); // Note: will be zero if branch is off, bc thermal switching constrs.;
            }

            // Real power flowing out of node via shunts.
            KCL_P += ptBus.gs()*(e(modBus.V,i).square_magnitude());
            KCL_Q -= ptBus.bs()*(e(modBus.V,i).square_magnitude());

            // Power flowing out node via load.
            auto& fed = e(modBus.fed,i);
            KCL_P += ptBus.pl() * fed;
            KCL_Q += ptBus.ql() * fed;

            // Power flowing into node via gens.
            for (auto ptGen : ptBus._gen)
            {
                auto& genInf = genInfo(ptGen->_name);
                if (!genInf.isActive()) continue;

                auto& modGen = genInf.modelGen<TMod>();

                KCL_P -= e(modGen.Pg,i); // This constrains generation for unfed buses.
                KCL_Q -= e(modGen.Qg,i); // This constrains generation for unfed buses.
            }

            KCL_P = 0;
            KCL_Q = 0;

            safeAddConstr(*powerModel_->_model, KCL_P);
            safeAddConstr(*powerModel_->_model, KCL_Q);
        }
    }

    template<typename TMod> void PsrSolver::addVoltageBoundConstrs(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        PtBus& ptBus = busInf.ptBus();

        Constraint V_UB("v_ub_" + busInf.id());
        V_UB += (modBus.V.square_magnitude());
        V_UB <= pow(ptBus.vbound.max, 2);
        safeAddConstr(*powerModel_->_model, V_UB);

        Constraint V_LB("v_lb_" + busInf.id());
        V_LB += (modBus.V.square_magnitude());
        V_LB >= pow(ptBus.vbound.min, 2);
        safeAddConstr(*powerModel_->_model, V_LB);
    }

    template<typename TMod> void PsrSolver::addVoltageBoundSwitchingConstrs(PsrBusInfo& busInf)
    {
        auto& modBus = busInf.modelBus<TMod>();
        PtBus& ptBus = busInf.ptBus();

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";
            Constraint V_UB("v_ub_" + iStr + busInf.id());
            V_UB += e(modBus.V,i).square_magnitude();
            V_UB -= pow(ptBus.vbound.max, 2) * e(modBus.fed,i);
            V_UB <= 0;
            safeAddConstr(*powerModel_->_model, V_UB);

            Constraint V_LB("v_lb_" + iStr + busInf.id());
            V_LB += e(modBus.V,i).square_magnitude();
            V_LB -= pow(ptBus.vbound.min, 2) * e(modBus.fed,i);
            V_LB >= 0;
            safeAddConstr(*powerModel_->_model, V_LB);
        }
    }

    template<typename TMod> void PsrSolver::addThermalConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        Constraint thermalLimitFrom("thermal_lim_from_" + ptBranch._name);
        thermalLimitFrom += modBranch.Si.square_magnitude();
        thermalLimitFrom <= pow(ptBranch.limit, 2);
        safeAddConstr(*powerModel_->_model, thermalLimitFrom);

        Constraint thermalLimitTo("thermal_lim_to_" + ptBranch._name);
        thermalLimitTo += modBranch.Sj.square_magnitude();
        thermalLimitTo <= pow(ptBranch.limit, 2);
        safeAddConstr(*powerModel_->_model, thermalLimitTo);
    }

    template<typename TMod> void PsrSolver::addThermalSwitchingConstrs(PsrBranchInfo& branchInf)
    {
        // Guarantees that P and Q variables for branches will be zero of branch is off.
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        for (size_t i = 0; i < nTime_; ++i)
        {
            string iStr = nTime_ == 1 ? "" : to_string(i) + "_";
            Constraint thermalLimitFrom("thermal_lim_from_" + iStr + ptBranch._name);
            thermalLimitFrom += e(modBranch.Si,i).square_magnitude();
            thermalLimitFrom -=  pow(ptBranch.limit, 2) * e(modBranch.closed,i);
            thermalLimitFrom <= 0.0;
            safeAddConstr(*powerModel_->_model, thermalLimitFrom);

            Constraint thermalLimitTo("thermal_lim_to_" + iStr + ptBranch._name);
            thermalLimitTo += e(modBranch.Sj,i).square_magnitude();
            thermalLimitTo -=  pow(ptBranch.limit, 2) * e(modBranch.closed,i);
            thermalLimitTo <= 0.0;
            safeAddConstr(*powerModel_->_model, thermalLimitTo);
        }
    }

    template<typename TMod> void PsrSolver::addNLinkingConstrs(PsrBranchInfo& branchInf)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        for (size_t i = 0; i < nTime_ - 1; ++i)
        {
            Constraint c("link_on_" + to_string(i) + "_" + ptBranch._name);
            c += modBranch.closed[i + 1] - modBranch.closed[i] + modBranch.open[i] - modBranch.close[i];
            c = 0;
            safeAddConstr(*powerModel_->_model, c);
        }
    }
    
    template<typename TMod> void PsrSolver::addNSingleActionConstrs()
    {
        for (size_t i = 0; i < nTime_ - 1; ++i)
        {
            Constraint c("single_action_" + to_string(i));
            for (auto& branchInf : branchInfos_)
            {
                auto& modBranch = branchInf.second.modelBranch<TMod>();

                c += modBranch.open[i] + modBranch.close[i];
                c <= 1;
            }
            safeAddConstr(*powerModel_->_model, c);
        }
    }

    template<typename TMod> void PsrSolver::acPowerFlows(PsrBranchInfo& branchInf,
            Function& fPi, Function& fPj, Function& fQi, Function& fQj, size_t i)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        auto& src = *ptBranch.src;
        auto& srcModBus = busInfos_.at(src._name).template modelBus<TMod>();

        auto& dest = *ptBranch.dest;
        auto& destModBus = busInfos_.at(dest._name).template modelBus<TMod>();

        C123 cPi; C123 cPj; C123 cQi; C123 cQj;
        powerFlowConstants(ptBranch, cPi, cPj, cQi, cQj);

        fPi += e(modBranch.Pi,i);
        fPi -= cPi.c1*(e(srcModBus.V,i).square_magnitude());
        fPi -= cPi.c2*(e(srcModBus.Vr,i)*e(destModBus.Vr,i) + e(srcModBus.Vi,i)*e(destModBus.Vi,i));
        fPi -= cPi.c3*(e(srcModBus.Vi,i)*e(destModBus.Vr,i) - e(srcModBus.Vr,i)*e(destModBus.Vi,i));

        fPj += e(modBranch.Pj,i);
        fPj -= cPj.c1*(e(destModBus.V,i).square_magnitude());
        fPj -= cPj.c2*(e(destModBus.Vr,i)*e(srcModBus.Vr,i) + e(destModBus.Vi,i)*e(srcModBus.Vi,i));
        fPj -= cPj.c3*(e(destModBus.Vi,i)*e(srcModBus.Vr,i) - e(destModBus.Vr,i)*e(srcModBus.Vi,i));

        fQi += e(modBranch.Qi,i);
        fQi += cQi.c1*(e(srcModBus.V,i).square_magnitude());
        fQi += cQi.c2*(e(destModBus.Vr,i)*e(srcModBus.Vr,i) + e(destModBus.Vi,i)*e(srcModBus.Vi,i));
        fQi -= cQi.c3*(e(srcModBus.Vi,i)*e(destModBus.Vr,i) - e(srcModBus.Vr,i)*e(destModBus.Vi,i));

        fQj += e(modBranch.Qj,i);
        fQj += cQj.c1*(e(destModBus.V,i).square_magnitude());
        fQj += cQj.c2*(e(destModBus.Vr,i)*e(srcModBus.Vr,i) + e(destModBus.Vi,i)*e(srcModBus.Vi,i));
        fQj -= cQj.c3*(e(destModBus.Vi,i)*e(srcModBus.Vr,i) - e(destModBus.Vr,i)*e(srcModBus.Vi,i));
    }

    template<typename TMod> void PsrSolver::socpPowerFlows(PsrBranchInfo& branchInf,
            Function& fPi, Function& fPj, Function& fQi, Function& fQj, size_t i)
    {
        auto& modBranch = branchInf.modelBranch<TMod>();
        auto& ptBranch = branchInf.ptBranch();

        auto& src = *ptBranch.src;
        auto& srcModBus = busInfos_.at(src._name).template modelBus<TMod>();

        auto& dest = *ptBranch.dest;
        auto& destModBus = busInfos_.at(dest._name).template modelBus<TMod>();

        C123 cPi; C123 cPj; C123 cQi; C123 cQj;
        powerFlowConstants(ptBranch, cPi, cPj, cQi, cQj);

        fPi += e(modBranch.Pi,i);
        fPi -= cPi.c1*e(srcModBus.w,i);
        fPi -= cPi.c2*e(modBranch.wr,i);
        fPi -= cPi.c3*e(modBranch.wi,i);

        fPj += e(modBranch.Pj,i);
        fPj -= cPj.c1*e(destModBus.w,i);
        fPj -= cPj.c2*e(modBranch.wr,i);
        fPj += cPj.c3*e(modBranch.wi,i);

        fQi += e(modBranch.Qi,i);
        fQi += cQi.c1*e(srcModBus.w,i);
        fQi += cQi.c2*e(modBranch.wr,i);
        fQi -= cQi.c3*e(modBranch.wi,i);

        fQj += e(modBranch.Qj,i);
        fQj += cQj.c1*e(destModBus.w,i);
        fQj += cQj.c2*e(modBranch.wr,i);
        fQj += cQj.c3*e(modBranch.wi,i);
    }

    template<typename TMod> void PsrSolver::setMaxLoadObjective()
    {
        Function* obj = new Function();
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            auto& modBus = busInf.second.modelBus<TMod>();
            *obj += busInf.second.ptBus().pl() * modBus.fed;
        }
        powerModel_->_model->setObjective(obj);
        powerModel_->_model->setObjectiveType(maximize);
    }
 
    template<typename TMod> void PsrSolver::setMaxLoadSwitchingObjective()
    {
        Function* obj = new Function();
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            auto& modBus = busInf.second.modelBus<TMod>();
            *obj += busInf.second.ptBus().pl() * modBus.fed;
        }
        powerModel_->_model->setObjective(obj);
        powerModel_->_model->setObjectiveType(maximize);
    }
 
    template<typename TMod> void PsrSolver::setNSwitchingObjective()
    {
        Function* obj = new Function();

        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            auto& modBus = busInf.second.modelBus<TMod>();

            for (size_t i = 0; i < nTime_; ++i) *obj -= 1e-3 * busInf.second.ptBus().pl() * modBus.fed[i];
        }

        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto& modBranch = branchInf.second.modelBranch<TMod>();

            for (size_t i = 0; i < nTime_; ++i) *obj -= 1e-3 * modBranch.closed[i];
            for (size_t i = 0; i < nTime_ - 1; ++i) *obj += modBranch.open[i];
            for (size_t i = 0; i < nTime_ - 1; ++i) *obj += modBranch.close[i];
        }

        powerModel_->_model->setObjective(obj);
        powerModel_->_model->setObjectiveType(minimize);
    }

    template<typename TMod> void PsrSolver::addSpecialVoltageObjTerm()
    {
        // Prevents numerical issues for isolated nodes.
        // TODO: experiment, rethink.
        for (auto& busInf : busInfos_)
        {
            if (!busInf.second.isActive()) continue;

            auto& modBus = busInf.second.modelBus<TMod>();
            *powerModel_->_model->_obj += 1e-2 * (modBus.Vr + modBus.Vi);
        }
    }
    
    template<typename TMod> void PsrSolver::addBranchClosedObjTerm()
    {
        // Prevents numerical issues for isolated nodes.
        for (auto& branchInf : branchInfos_)
        {
            if (!branchInf.second.isActive()) continue;

            auto& modBranch = branchInf.second.modelBranch<TMod>();

            *powerModel_->_model->_obj += 1e-2 * modBranch.closed;
        }
    }
    
    Trivalent PsrSolver::branchIsFed(const PsrBranchInfo& branchInf)
    {
        switch (branchInf.closedStateConstr())
        {
            case Trivalent::NO:
                {
                    return Trivalent::NO;
                }
            case Trivalent::MAYBE:
                {
                    // Don't know if branch is closed. But is either bus is NO, then the answer is NO.
                    const auto& bus0Inf = busInfo(branchInf.branch().bus0()->id());
                    const auto& bus1Inf = busInfo(branchInf.branch().bus1()->id());
                    return (bus0Inf.isFed() == Trivalent::NO && bus1Inf.isFed() == Trivalent::NO) 
                        ? Trivalent::NO : Trivalent::MAYBE;
                }
            case Trivalent::YES:
                {
                    // Branch is closed. So it's supplied status is same as either bus. 
                    const auto& bus0Fed = busInfo(branchInf.branch().bus0()->id()).isFed();
                    const auto& bus1Fed = busInfo(branchInf.branch().bus1()->id()).isFed();
                    assert(bus0Fed == bus1Fed);
                    return bus0Fed;
                }
        }
    }
            
    Trivalent PsrSolver::genIsFed(const PsrGenInfo& genInf)
    {
        // Same status as its bus, unless out of service.
        return !genInf.gen().isInService() ? Trivalent::NO : busInfo(genInf.gen().bus()->id()).isFed();
    }

    bool PsrSolver::setUnkIsInService(bool isInService)
    {
        bool hasUnknown = false;
        for (auto& branchInf : branchInfos_)
        {
            if (branchInf.second.closedStateConstr() == Trivalent::MAYBE)
            {
                hasUnknown = true;
                branchInf.second.branch().setIsInService(isInService);
            }
        }
        netw_->solvePreprocess();
        return hasUnknown;
    }
}
