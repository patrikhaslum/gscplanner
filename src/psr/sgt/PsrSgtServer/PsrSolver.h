#ifndef PSR_SOLVER_DOT_H
#define PSR_SOLVER_DOT_H

#include <SgtCore/Common.h>

#include <PowerTools++/PowerModel.h>
#include <PowerTools++/var.h>

class Arc; using PtBranch = Arc;
class Gen; using PtGen = Gen;
class Node; using PtBus = Node;
class Complex; using PtComplex = Complex;
class Net; using PtNetwork = Net;

namespace Sgt
{
    class BranchAbc;
    class Bus;
    class Gen;
    class Network;

    struct ModelBus
    {
        virtual ~ModelBus() = default;
    };

    struct AcRectModelBusBase : public ModelBus
    {
        var<> Vr;
        var<> Vi;
        PtComplex V;
    };

    struct AcRectModelBus : public AcRectModelBusBase
    {
        var<> fed;
    };

    struct AcRectSwitchingModelBus : public AcRectModelBusBase
    {
        var<int> fed;
    };

    struct NAcRectSwitchingModelBus : public ModelBus
    {
        std::vector<var<>> Vr;
        std::vector<var<>> Vi;
        std::vector<PtComplex> V;

        std::vector<var<int>> fed;

        void realloc(std::size_t n);
    };

    struct SocpModelBusBase : public ModelBus
    {
        var<> w;
        PtComplex V;
    };

    struct SocpModelBus : public SocpModelBusBase
    {
        var<> fed;
    };

    struct SocpSwitchingModelBus : public SocpModelBusBase
    {
        var<int> fed;
    };

    struct NSocpSwitchingModelBus : public ModelBus
    {
        std::vector<var<>> w;
        std::vector<PtComplex> V;

        std::vector<var<int>> fed;

        void realloc(std::size_t n);
    };

    struct ModelBranch
    {
        virtual ~ModelBranch() = default;
    };

    struct AcRectModelBranch : public ModelBranch
    {
        var<> Pi;
        var<> Qi;
        PtComplex Si;

        var<> Pj;
        var<> Qj;
        PtComplex Sj;
    };

    struct AcRectSwitchingModelBranch : public AcRectModelBranch
    {
        var<int> closed;
    };

    struct NAcRectSwitchingModelBranch : public ModelBranch
    {
        std::vector<var<>> Pi;
        std::vector<var<>> Qi;
        std::vector<PtComplex> Si;

        std::vector<var<>> Pj;
        std::vector<var<>> Qj;
        std::vector<PtComplex> Sj;

        std::vector<var<int>> closed;
        std::vector<var<int>> open;
        std::vector<var<int>> close;

        void realloc(std::size_t n);
    };

    struct SocpModelBranch : public AcRectModelBranch
    {
        var<> wr;
        var<> wi;
    };

    struct SocpSwitchingModelBranch : public SocpModelBranch
    {
        var<int> closed;
    };

    struct NSocpSwitchingModelBranch : public ModelBranch
    {
        std::vector<var<>> Pi;
        std::vector<var<>> Qi;
        std::vector<PtComplex> Si;

        std::vector<var<>> Pj;
        std::vector<var<>> Qj;
        std::vector<PtComplex> Sj;

        std::vector<var<>> wr;
        std::vector<var<>> wi;
        
        std::vector<var<int>> closed;
        std::vector<var<int>> open;
        std::vector<var<int>> close;

        void realloc(std::size_t n);
    };

    struct ModelGen
    {
        virtual ~ModelGen() = default;
    };

    struct ModelGenA : public ModelGen
    {
        var<> Pg;
        var<> Qg;
        PtComplex Sg;
    };

    using AcRectModelGen = ModelGenA;
    using AcRectSwitchingModelGen = ModelGenA;
    using SocpModelGen = ModelGenA;
    using SocpSwitchingModelGen = ModelGenA;

    struct NSwitchingModelGen : public ModelGen
    {
        std::vector<var<>> Pg;
        std::vector<var<>> Qg;
        std::vector<PtComplex> Sg;

        void realloc(std::size_t n);
    };
    using NSocpSwitchingModelGen = NSwitchingModelGen;
    using NAcRectSwitchingModelGen = NSwitchingModelGen;
    
    struct BaseModel
    {
        using ModBus = ModelBus;
        using ModBranch = ModelBranch;
        using ModGen = ModelGen;
    };

    struct AcRectModel
    {
        using ModBus = AcRectModelBus;
        using ModBranch = AcRectModelBranch;
        using ModGen = AcRectModelGen;
    };

    struct AcRectSwitchingModel
    {
        using ModBus = AcRectSwitchingModelBus;
        using ModBranch = AcRectSwitchingModelBranch;
        using ModGen = AcRectSwitchingModelGen;
    };

    struct NAcRectSwitchingModel
    {
        using ModBus = NAcRectSwitchingModelBus;
        using ModBranch = NAcRectSwitchingModelBranch;
        using ModGen = NAcRectSwitchingModelGen;
    };

    struct SocpModel
    {
        using ModBus = SocpModelBus;
        using ModBranch = SocpModelBranch;
        using ModGen = SocpModelGen;
    };

    struct SocpSwitchingModel
    {
        using ModBus = SocpSwitchingModelBus;
        using ModBranch = SocpSwitchingModelBranch;
        using ModGen = SocpSwitchingModelGen;
    };

    struct NSocpSwitchingModel
    {
        using ModBus = NSocpSwitchingModelBus;
        using ModBranch = NSocpSwitchingModelBranch;
        using ModGen = NSocpSwitchingModelGen;
    };

    enum class Trivalent : int
    {
        NO = 0,
        YES = 1,
        MAYBE = 2
    };

    class PsrBusInfo
    {
        public:
            PsrBusInfo(ComponentPtr<Bus> bus);

            const std::string& id() const;
            
            Trivalent isFed() const
            {
                return isFed_;
            }
            void setIsFed(Trivalent isFed)
            {
                isFed_ = isFed;
            }
            
            bool isActive() const {return isFed_ != Trivalent::NO;}

            const Bus& bus() const {return *bus_;}
            Bus& bus() {return *bus_;}
            
            const PtBus& ptBus() const {return *ptBus_;}
            PtBus& ptBus() {return *ptBus_;}
            void setPtBus(PtBus* ptBus) {ptBus_ = ptBus;}

            template<typename TMod> const typename TMod::ModBus& modelBus() const 
            {
                return dynamic_cast<const typename TMod::ModBus&>(*modelBus_);
            }
            template<typename TMod> typename TMod::ModBus& modelBus() 
            {
                return dynamic_cast<typename TMod::ModBus&>(*modelBus_);
            }
            void setModelBus(std::unique_ptr<ModelBus>&& modelBus) {modelBus_ = std::move(modelBus);}

            void setFault();
            bool hasFault() const {return defaultFedStateConstr_ == Trivalent::NO;}

            bool finalRequireFed() const {return finalRequireFed_;}
            void setFinalRequireFed(bool finalRequireFed) {finalRequireFed_ = finalRequireFed;}

            Trivalent defaultFedStateConstr() const {return defaultFedStateConstr_;}
            void setDefaultFedStateConstr(Trivalent sc) {defaultFedStateConstr_ = sc;}

            Trivalent fedStateConstr() const {return fedStateConstr_;}
            void setFedStateConstr(Trivalent sc) {fedStateConstr_ = sc;}
            
            Trivalent tightenedFedStateConstr() const
            {
                return fedStateConstr_ == Trivalent::MAYBE ? isFed_ : fedStateConstr_;
            }
            

        private:
            ComponentPtr<Bus> bus_{nullptr};
            PtBus* ptBus_{nullptr};
            std::unique_ptr<ModelBus> modelBus_{nullptr};

            bool finalRequireFed_{true};

            Trivalent isFed_;

            Trivalent defaultFedStateConstr_{Trivalent::MAYBE};
            Trivalent fedStateConstr_{Trivalent::MAYBE};
    };

    struct PsrBranchInfo
    {
        public:
            PsrBranchInfo(ComponentPtr<BranchAbc> branch);
            
            const std::string& id() const;

            Trivalent isFed() const
            {
                return isFed_;
            }
            void setIsFed(Trivalent isFed)
            {
                isFed_ = isFed;
            }
            
            bool isActive() const {return isFed_ != Trivalent::NO;}
            
            const BranchAbc& branch() const {return *branch_;}
            BranchAbc& branch() {return *branch_;}
            
            const PtBranch& ptBranch() const {return *ptBranch_;}
            PtBranch& ptBranch() {return *ptBranch_;}
            void setPtBranch(PtBranch* ptBranch) {ptBranch_ = ptBranch;}
            
            template<typename TMod> const typename TMod::ModBranch& modelBranch() const
            {
                return dynamic_cast<const typename TMod::ModBranch&>(*modelBranch_);
            }
            template<typename TMod> typename TMod::ModBranch& modelBranch()
            {
                return dynamic_cast<typename TMod::ModBranch&>(*modelBranch_);
            }
            void setModelBranch(std::unique_ptr<ModelBranch>&& modelBranch) {modelBranch_ = std::move(modelBranch);}
            
            bool hasBreaker() const {return hasBreaker_;}
            bool breakerIsInitClosed() const {return breakerIsInitClosed_;}
            void setBreaker(bool isInitClosed);

            Trivalent defaultClosedStateConstr() const {return defaultClosedStateConstr_;}
            void setDefaultClosedStateConstr(Trivalent sc) {defaultClosedStateConstr_ = sc;}
            
            Trivalent closedStateConstr() const {return closedStateConstr_;}
            void setClosedStateConstr(Trivalent sc);
           
        private:
            ComponentPtr<BranchAbc> branch_{nullptr};
            PtBranch* ptBranch_{nullptr};
            std::unique_ptr<ModelBranch> modelBranch_{nullptr};

            bool hasBreaker_{false};
            bool breakerIsInitClosed_;

            Trivalent isFed_;

            Trivalent defaultClosedStateConstr_{Trivalent::MAYBE};
            Trivalent closedStateConstr_{Trivalent::MAYBE};
    };

    struct PsrGenInfo
    {
        public:
            PsrGenInfo(ComponentPtr<Gen> gen) : gen_(gen) {}

            const std::string& id() const;
            
            Trivalent isFed() const
            {
                return isFed_;
            }
            void setIsFed(Trivalent isFed)
            {
                isFed_ = isFed;
            }

            bool isActive() const {return isFed_ != Trivalent::NO;}
            
            const Gen& gen() const {return *gen_;}
            Gen& gen() {return *gen_;}
            
            const PtGen& ptGen() const {return *ptGen_;}
            PtGen& ptGen() {return *ptGen_;}
            void setPtGen(PtGen* ptGen) {ptGen_ = ptGen;}
            
            template<typename TMod> const typename TMod::ModGen& modelGen() const
            {
                return dynamic_cast<const typename TMod::ModGen&>(*modelGen_);
            }
            template<typename TMod> typename TMod::ModGen& modelGen()
            {
                return dynamic_cast<typename TMod::ModGen&>(*modelGen_);
            }
            void setModelGen(std::unique_ptr<ModelGen>&& modelGen) {modelGen_ = std::move(modelGen);}
            
        private:
            ComponentPtr<Gen> gen_{nullptr};
            PtGen* ptGen_{nullptr};
            std::unique_ptr<ModelGen> modelGen_{nullptr};
            
            Trivalent isFed_;
    };
  
   
    /// @brief Class to solve special PSR problems.
    ///
    /// In addition to the usual AC PowerFlow setup, we have a set of bus and branch state constraints.
    ///
    /// The bus fed constraints allow us to specify that the bus either must be fed or must not be fed by including a
    /// bus constraint of YES or NO respectively. For all other buses, we assume that a
    /// default state constraint of MAYBE is set. For the latter buses, we must not enforce any constraints
    /// that require us to know the fed state.
    ///
    /// The branch closed constraints apply to branches that have an associated circuit breaker (which is not
    /// explicitly modelled here). In such cases, we may again choose to specify that the branch must be either closed
    /// or open by using NO or YES constraints; all other branches must have a default
    /// MAYBE constraint set. Similar to the buses, the presence of MAYBE means that we
    /// must ignore all constraints related to the branch that require knowing whether the branch is fed or unfed.
    class PsrSolver
    {
        friend class Network;

        public:
            bool useSocp_{true};

        public:
            PsrSolver(Network& netw);
            virtual ~PsrSolver() = default;

            Network& network() {return *netw_;}
            const Network& network() const {return *netw_;}

            const PsrBusInfo& busInfo(const std::string& id) const {return busInfos_.at(id);}
            PsrBusInfo& busInfo(const std::string& id) {return busInfos_.at(id);}

            const std::map<std::string, PsrBusInfo>& busInfos() const {return busInfos_;}
            std::map<std::string, PsrBusInfo>& busInfos() {return busInfos_;}
            
            const PsrBranchInfo& branchInfo(const std::string& id) const {return branchInfos_.at(id);}
            PsrBranchInfo& branchInfo(const std::string& id) {return branchInfos_.at(id);}

            const std::map<std::string, PsrBranchInfo>& branchInfos() const {return branchInfos_;}
            std::map<std::string, PsrBranchInfo>& branchInfos() {return branchInfos_;}
            
            const PsrGenInfo& genInfo(const std::string& id) const {return genInfos_.at(id);}
            PsrGenInfo& genInfo(const std::string& id) {return genInfos_.at(id);}

            const std::map<std::string, PsrGenInfo>& genInfos() const {return genInfos_;}
            std::map<std::string, PsrGenInfo>& genInfos() {return genInfos_;}


            // Correct flow:
            //
            // 1. Create solver using a valid Network
            // 2. Call PsrBusInfo::setFault(...) as needed.
            // 3. reset() <- can choose to re-enter flow here at any point. 
            // 4. Set up all state constraints, using PsrBusInfo::setFedStateConstr(...) and
            //    PsrBranchInfo::setClosedStateConstr(...).
            // 5. Call lockInProblem().
            // 6. Call preCheck, socpCheck, socpSwitchingCheck, acRectCheck ... as many as needed.
            // 7. Go back to step 3 if desired.

            /// @brief Reset solver state.
            ///
            /// Set all model objects to null. Set all state constraints to defaults.
            void reset();
            
            /// @brief Commit to problem, as defined by all state constraints and the faulty buses.
            ///
            /// Should not set any more state contraints or faulty buses until reset() is called again. 
            void lockInProblem();
            
            bool preCheck();
            bool acRectCheck();
            bool acRectSwitchingCheck();
            bool nAcRectSwitchingCheck(std::size_t n);
            bool socpCheck();
            bool socpSwitchingCheck();
            bool nSocpSwitchingCheck(std::size_t n);
   
            /// @brief lockInProblem(), preCheck, socpCheck (if specified), acRectCheck.
            bool solve();

            /// @brief Set the closed and fed state constraints according to switching model results.
            template<typename TMod> void applySwitchingResults();
            
            void printStateConstrs() const;
            void printIslands() const;
            template<typename TMod> void printSwitching() const;
            template<typename TMod> void printNSwitching() const;
            template<typename TMod> json getMinlpPlanJson() const;

        private:
            // Models:
            void makeAcRectModel();
            void makeAcRectSwitchingModel();
            void makeNAcRectSwitchingModel(std::size_t n);
            void makeSocpModel();
            void makeSocpSwitchingModel();
            void makeNSocpSwitchingModel(std::size_t n);
            
            template<typename TMod> void addModelObjects();

            // Variables:
            template<typename TMod> void addBusVrViVars(PsrBusInfo& busInf);

            template<typename TMod> void addBusWVars(PsrBusInfo& busInf);
            
            template<typename TMod> void addBusFedVars(PsrBusInfo& busInf);

            template<typename TMod> void addBusFedSwitchingVars(PsrBusInfo& busInf);
            
            template<typename TMod> void addBranchPQVars(PsrBranchInfo& branchInf);

            template<typename TMod> void addBranchWVars(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addBranchClosedSwitchingVars(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addGenVars(PsrGenInfo& genInf);
            
            template<typename TMod> void addNLinkingVars(PsrBranchInfo& branchInf);

            // Constraints:
            template<typename TMod> void addBusFedMatchingConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addBusFedMatchingSwitchingConstrs(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addAcRectPowerFlowConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addAcRectPowerFlowSwitchingConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addSocpConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addSocpSwitchingConstrs(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addNSocpSwitchingConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addKclConstrs(PsrBusInfo& busInf);

            template<typename TMod> void addKclSwitchingConstrs(PsrBusInfo& busInf);
            
            template<typename TMod> void addNKclSwitchingConstrs(PsrBusInfo& busInf);

            template<typename TMod> void addVoltageBoundConstrs(PsrBusInfo& busInf);
            
            template<typename TMod> void addVoltageBoundSwitchingConstrs(PsrBusInfo& busInf);

            template<typename TMod> void addThermalConstrs(PsrBranchInfo& branchInf);

            template<typename TMod> void addThermalSwitchingConstrs(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addNLinkingConstrs(PsrBranchInfo& branchInf);
            
            template<typename TMod> void addNSingleActionConstrs(); // TODO: n should come from model.

            template<typename TMod> void acPowerFlows(PsrBranchInfo& branchInf,
                    Function& fPi, Function& fPj, Function& fQi, Function& fQj, std::size_t i = 0);
            
            template<typename TMod> void socpPowerFlows(PsrBranchInfo& branchInf,
                    Function& fPi, Function& fPj, Function& fQi, Function& fQj, std::size_t i = 0);
            
            // Objective:
            template<typename TMod> void setMaxLoadObjective();

            template<typename TMod> void setMaxLoadSwitchingObjective();

            template<typename TMod> void setNSwitchingObjective();

            template<typename TMod> void addSpecialVoltageObjTerm(); // Prevents numerical issues for isolated nodes.

            template<typename TMod> void addBranchClosedObjTerm();
    
            // Utility:
            Trivalent branchIsFed(const PsrBranchInfo& branchInf);
            Trivalent genIsFed(const PsrGenInfo& genInf);

            bool setUnkIsInService(bool isInService); // Set in service of unknown status branches & recalc islands. 
            
        private:

            Network* netw_;
            std::unique_ptr<PtNetwork> ptNetw_;
            std::unique_ptr<PowerModel> powerModel_;
            std::size_t nTime_{0}; 
            std::map<std::string, PsrBusInfo> busInfos_;
            std::map<std::string, PsrBranchInfo> branchInfos_;
            std::map<std::string, PsrGenInfo> genInfos_;

            bool hasUnkStatusBranches_{false};
    };
}

#endif // PSR_SOLVER_DOT_H
