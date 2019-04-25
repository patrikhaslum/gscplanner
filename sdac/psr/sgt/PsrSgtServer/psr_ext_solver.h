#ifndef LITTLETESTSOLVER_H
#define LITTLETESTSOLVER_H

#include "popfExternalSolver.h"
//#include "PsrSolver.h"
#include <vector>

class PsrSolverForPOPF : public ExternalSolver
{
  
 public:
  PsrSolverForPOPF();
  ~PsrSolverForPOPF();
  virtual void loadSolver(std::string* parameters, int n);
  virtual std::map<std::string,double>
    callExternalSolver(std::map<std::string,double> initialState, bool isHeuristic); 
  virtual std::list<std::string> getParameters();
  virtual std::list<std::string> getDependencies();

 private:
  std::list<std::string> affected;
  std::list<std::string> dependencies;
  std::map<std::string,unsigned int> branch_index;
  std::map<std::string,unsigned int> bus_index;
  std::vector<unsigned int> branch_end_1;
  std::vector<unsigned int> branch_end_2;
  std::vector<bool> bus_has_gen;
  std::vector<bool> bus_is_faulty;

  void request_network(const std::string& config);
  bool request_status(const std::vector<bool>& is_closed);
  // undirected transitive closure: input is_closed tells us which branches
  // are closed, base_set a set of busses that are "in" the set (true); the
  // output utc_set is the set of buses that have a path to a bus in the
  // base set via closed branches.
  void compute_utc(const std::vector<bool>& is_closed,
		   const std::vector<bool>& base_set,
		   std::vector<bool>& utc_set);
  unsigned int find(unsigned int e, std::vector<unsigned int>& mfs);
  void merge(unsigned int a, unsigned int b, std::vector<unsigned int>& mfs);

};

#endif // SOLVER_H
