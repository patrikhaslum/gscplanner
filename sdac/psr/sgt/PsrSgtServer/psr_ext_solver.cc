
#include "psr_ext_solver.h"

#define COLOUR_default "\033[00m"
#define COLOUR_red     "\033[22;31m"

#define VERBOSITY 2

#include <cpprest/http_client.h>
#include <boost/regex.hpp>
#include <iostream>
#include <cassert>

using namespace web;                        // Common features like URIs.
using namespace web::http;                  // Common HTTP functionality
using namespace web::http::client;          // HTTP client features

extern "C" ExternalSolver* create_object()
{
  return new PsrSolverForPOPF();
}

extern "C" void destroy_object(ExternalSolver* externalSolver)
{
  delete externalSolver;
}

PsrSolverForPOPF::PsrSolverForPOPF()
{
  // does nothing
}

PsrSolverForPOPF::~PsrSolverForPOPF()
{
  // nothing to do
}

void PsrSolverForPOPF::request_network(const std::string& config)
{
  // Create http_client to send the request
  http_client client(U("http://localhost:12345/"));

  // Build request URI and start the request.
  uri_builder builder(U("/network"));
  builder.append_query(U("config"), U(config));
  pplx::task<json::value> requestTask = client.request(methods::PUT, builder.to_string())
    // response handler:
    .then([=](http_response response)
    {
#if VERBOSITY >= 2
      std::cerr << "response status code: " << response.status_code() << std::endl;
#endif
      return response.extract_json(true);
    });

  try {
    // request and wait for result:
    requestTask.wait();
    json::value response = requestTask.get();
#if VERBOSITY >= 2
    std::cerr << "response JSON string: " << response << std::endl;
#endif
    json::object& main = response.as_object();
    // extract the bus data
    json::array& buses = main["buses"].as_array();
    unsigned int n_buses = buses.size();
    bus_has_gen.resize(n_buses);
    bus_is_faulty.resize(n_buses);
    for (unsigned int i = 0; i < n_buses; i++) {
      std::string name = buses[i].as_object()["name"].as_string();
      bool has_gen = buses[i].as_object()["has_generation"].as_bool();
      assert(bus_index.find(name) == bus_index.end());
      bus_index[name] = i;
      bus_has_gen[i] = has_gen;
      bus_is_faulty[i] = false;
#if VERBOSITY >= 1
      std::cerr << "bus " << name << " index = " << bus_index[name] << ", has gen = " << bus_has_gen[i] << std::endl;
#endif
    }
    // extract the branch data
    json::array& branches = main["branches"].as_array();
    unsigned int n_branches = branches.size();
    branch_end_1.resize(n_branches);
    branch_end_2.resize(n_branches);
    for (unsigned int i = 0; i < n_branches; i++) {
      std::string name = branches[i].as_object()["name"].as_string();
      assert(branch_index.find(name) == branch_index.end());
      branch_index[name] = i;
      //bool init_closed = branches[i].as_object()["init_closed"].as_bool();
      boost::regex decomp("branch_([0-9]+)_(bus_[0-9]+)_(bus_[0-9]+)", boost::regex::perl);
      boost::smatch m;
      bool ok = boost::regex_match(name, m, decomp);
      assert(ok);
#if VERBOSITY >= 1
      std::cerr << "branch " << name << " connects " << m[2] << " and " << m[3] << std::endl;
#endif
      auto b1 = bus_index.find(m[2]);
      if (b1 == bus_index.end()) {
	bus_index[m[2]] = n_buses;
	bus_has_gen.push_back(false);
	bus_is_faulty.push_back(true);
	branch_end_1[i] = n_buses;
	n_buses++;
      }
      else {
	branch_end_1[i] = b1->second;
      }
      auto b2 = bus_index.find(m[3]);
      if (b2 == bus_index.end()) {
	bus_index[m[3]] = n_buses;
	bus_has_gen.push_back(false);
	bus_is_faulty.push_back(true);
	branch_end_2[i] = n_buses;
	n_buses++;
      }
      else {
	branch_end_2[i] = b2->second;
      }
    }
  }
  catch (const std::exception &e) {
    std::cerr << "Error exception: " << e.what() << std::endl;
    assert(false);
  }
}

void PsrSolverForPOPF::loadSolver(std::string* parameters, int n)
{
#if VERBOSITY >= 1
  std::cerr << "load solver called with n = " << n << " and params";
  for (int i = 0; i < n; i++)
    std::cerr << " " << parameters[i];
  std::cerr << std::endl;
#endif
  assert(n >= 1);
  request_network(parameters[0]);
  char const* fluents_out[] = {"status", "fed", "unsafe"};
  char const* fluents_in[] = {"switch_state"};
  affected = std::list<std::string>(fluents_out, fluents_out+3);
  dependencies = std::list<std::string>(fluents_in, fluents_in+1);
}

bool PsrSolverForPOPF::request_status(const std::vector<bool>& is_closed)
{
  // Create http_client to send the request
  http_client client(U("http://localhost:12345/"));
  // Build request URI:
  uri_builder builder(U("/network/state"));
  // Construct JSON data for request body:
  std::string body = "{\"bus_fed_constraints\": [], \"branch_closed_constraints\": [";
  bool first = true;
  for (auto p = branch_index.begin(); p != branch_index.end(); p++) {
    std::string tmp = "[\"" + p-> first + "\", " + (is_closed[p->second] ? "true" : "false") + "]";
    if (!first) {
      body += "," + tmp;
    }
    else {
      body += tmp;
    }
    first = false;
  }
  body += "]}\n";

#if VERBOSITY >= 3
  std::cerr << "request body: " << body << std::endl;
#endif

  // make the request:
  pplx::task<json::value> requestTask =
    client.request(methods::PUT, builder.to_string(), U(body))
    // response handler:
    .then([=](http_response response)
    {
#if VERBOSITY >= 3
      std::cerr << "response status code: " << response.status_code() << std::endl;
#endif
      return response.extract_json(true);
    });

  try {
    // wait for result:
    requestTask.wait();
    json::value response = requestTask.get();
#if VERBOSITY >= 3
    std::cerr << "response JSON string: " << response << std::endl;
#endif
    json::object& main = response.as_object();
    bool ok = main["solver_status"].as_bool();
    return ok;
  }
  catch (const std::exception &e) {
    std::cerr << "Error exception: " << e.what() << std::endl;
    assert(false);
  }
}

unsigned int PsrSolverForPOPF::find(unsigned int e, std::vector<unsigned int>& mfs)
{
  assert(e < mfs.size());
  if (mfs[e] == e) {
    return e;
  }
  else {
    unsigned int c = find(mfs[e], mfs);
    mfs[e] = c;
    return c;
  }
}

void PsrSolverForPOPF::merge(unsigned int a, unsigned int b,
			     std::vector<unsigned int>& mfs)
{
  unsigned int c_a = find(a, mfs);
  unsigned int c_b = find(b, mfs);
  mfs[c_a] = c_b;
}

void PsrSolverForPOPF::compute_utc(const std::vector<bool>& is_closed,
				   const std::vector<bool>& base_set,
				   std::vector<bool>& utc_set)
{
  unsigned int n_buses = bus_index.size();
  unsigned int n_branches = branch_index.size();
  assert(is_closed.size() == n_branches);
  std::vector< unsigned int > conn;
  conn.resize(n_buses);
  for (unsigned int i = 0; i < n_buses; i++)
    conn[i] = i;
  for (unsigned int j = 0; j < n_branches; j++)
    if (is_closed[j])
      merge(branch_end_1[j], branch_end_2[j], conn);
  utc_set.resize(n_buses, false);
  for (unsigned int i = 0; i < n_buses; i++)
    if (base_set[i])
      utc_set[find(i, conn)] = true;
  for (unsigned int i = 0; i < n_buses; i++)
    if (utc_set[find(i, conn)])
      utc_set[i] = true;
  // std::cerr << "mfs:";
  // for (auto p = conn.begin(); p != conn.end(); p++)
  //   std::cerr << " " << (*p);
  // std::cerr << std::endl;
  // std::cerr << "utc:";
  // for (auto p = utc_set.begin(); p != utc_set.end(); p++)
  //   std::cerr << " " << (*p);
  // std::cerr << std::endl;
}

std::map<std::string,double>
PsrSolverForPOPF::callExternalSolver
(std::map<std::string,double> initialState, bool isHeuristic)
{
#if VERBOSITY >= 2
  std::cerr << COLOUR_red << "solver called!" << COLOUR_default << std::endl;
#endif

  unsigned int n_branches = branch_index.size();
  std::vector<bool> branch_closed(n_branches, false);
  std::vector<bool> branch_status_set(n_branches, false);
  boost::regex split("\\(switch_state ([a-z0-9_]+)\\)", boost::regex::perl);

  for (auto ist = initialState.begin(); ist != initialState.end(); ist++) {
    std::string fluent = ist->first;
    double value = ist->second;
#if VERBOSITY >= 4
    std::cerr << "fluent " << fluent << " = " << value << std::endl;
#endif
    boost::smatch m;
    bool ok = boost::regex_match(fluent, m, split);
    if (ok) {
      std::string b_name = m[1];
      auto b = branch_index.find(b_name);
      assert(b != branch_index.end());
#if VERBOSITY >= 3
      std::cerr << "branch " << b_name << " index = " << b->second
      		<< " end.1 = " << branch_end_1[b->second]
      		<< " end.2 = " << branch_end_2[b->second]
      		<< " status = " << value << std::endl;
#endif
      branch_status_set[b->second] = true;
      if (value > 0)
	branch_closed[b->second] = true;
    }
  }

  std::vector<bool> bus_fed;
  compute_utc(branch_closed, bus_has_gen, bus_fed);
  std::vector<bool> bus_unsafe;
  compute_utc(branch_closed, bus_is_faulty, bus_unsafe);
  bool status_ok = request_status(branch_closed);

  std::map<std::string,double> toReturn;
  for (auto b = bus_index.begin(); b != bus_index.end(); b++) {
    // fed fluent:
    std::string fluent = "(fed " + b->first + ")";
    toReturn[fluent] = (bus_fed[b->second] ? 1 : 0);
    // unsafe fluent:
    fluent = "(unsafe " + b->first + ")";
    toReturn[fluent] = (bus_unsafe[b->second] ? 1 : 0);
  }
  toReturn["(status)"] = (status_ok ? 1 : 0);

#if VERBOSITY >= 2
  std::cerr << COLOUR_red << "returning:" << COLOUR_default;
  for (auto i = toReturn.begin(); i != toReturn.end(); i++)
    std::cerr << " " << i->first << ":" << i->second;
  std::cerr << std::endl;
#endif

  return toReturn;
}

std::list<std::string> PsrSolverForPOPF::getParameters()
{
  // std::cerr << "returning specials:";
  // for (auto i = affected.begin(); i != affected.end(); i++)
  //   std::cerr << " " << (*i);
  // std::cerr << std::endl;
  return affected;
}

std::list<std::string> PsrSolverForPOPF::getDependencies()
{
  // std::cerr << "returning deps:";
  // for (auto i = dependencies.begin(); i != dependencies.end(); i++)
  //   std::cerr << " " << (*i);
  // std::cerr << std::endl;
  return dependencies; 
}
