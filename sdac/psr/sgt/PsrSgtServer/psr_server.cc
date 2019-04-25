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
#include "utility.h"

#include <SgtCore/Common.h>
#include <SgtCore/json.h>
#include <SgtCore/Network.h>
#include <SgtCore/NetworkParser.h>
#include <SgtCore/Parser.h>

#include <cpprest/http_listener.h>
#include <cpprest/uri.h>
#include <cpprest/asyncrt_utils.h>

#include <boost/filesystem.hpp>
#include <boost/thread.hpp>

#include <regex>

using namespace Sgt;

using namespace web;
using namespace http;
using namespace utility;
using namespace http::experimental::listener;

using Json = Sgt::json;

class PsrServer
{
public:

    PsrServer(const std::string& url);

    pplx::task<void> open() {return listener_.open();}
    pplx::task<void> close() {return listener_.close();}

private:

    void handlePut(http_request message);

private:
    
    http_listener listener_;   
    unique_ptr<Network> nw_;
    PsrSolver* solver_;
};

static std::unique_ptr<PsrServer> gPsrServer;

void on_initialize(const std::string& address)
{
    uri_builder uri(address);

    auto addr = uri.to_uri().to_string();
    gPsrServer = std::unique_ptr<PsrServer>(new PsrServer(addr));
    gPsrServer->open().wait();
    
    std::cout << "PSR_SERVER: Listening for requests at: " << addr << std::endl;
}

void on_shutdown()
{
    gPsrServer->close().wait();
}

int main(int argc, char *argv[])
{
    std::string port = "12345";

    std::string address = "http://localhost:";
    address.append(port);

    std::string debugLevel = argc > 1 ? argv[1] : "none";

    if (debugLevel == "normal")
    {
        debugLogLevel() = LogLevel::NORMAL;
    }
    else if (debugLevel == "verbose")
    {
        debugLogLevel() = LogLevel::VERBOSE;
    }
    
    on_initialize(address);
    std::cout << "PSR_SERVER: Press ENTER to exit." << std::endl;

    //std::string line;
    //std::getline(std::cin, line);
    while (true) {
      boost::this_thread::sleep_for(boost::chrono::seconds(1800));
    }

    on_shutdown();
    return 0;
}

PsrServer::PsrServer(const std::string& url) : listener_(url)
{
    listener_.support(methods::PUT, std::bind(&PsrServer::handlePut, this, std::placeholders::_1));
}

void PsrServer::handlePut(http_request message)
{
    std::cout << "--------------------------------------------------------------------------------" << std::endl;
    std::cout << "PSR_SERVER: PUT received." << std::endl;

    auto query = web::uri::split_query(message.relative_uri().query());
    auto paths = http::uri::split_path(http::uri::decode(message.relative_uri().path()));
    
    sgtAssert(paths.size() > 0, "PSR_SERVER: bad URL");
    
    auto status = status_codes::NotFound;
    Json reply;

    if (paths[0] == "network")
    {
        if (paths.size() == 1)
        {
            std::cout << "PSR_SERVER: Put network." << std::endl; 
            sgtAssert(query.size() == 1, "PSR_SERVER: bad URL");
            std::string config = query.at("config");

            nw_.reset(new Network(100.0));
            nw_->setUseFlatStart(true);
            NetworkParser netwParser;
            netwParser.parse(config, *nw_);
           
            solver_ = new PsrSolver(*nw_);

            Parser<PsrSolver> psrParser;
            psrParser.registerParserPlugin<PsrParserPlugin>();
            psrParser.parse(config, *solver_);

            Json busesJson = Json::array();
            for (auto& busInf : solver_->busInfos())
            {
                const auto& S = busInf.second.bus().SZipTot();
                if (!busInf.second.hasFault() && !hasGeneration(busInf.second.bus()))
                {
                    busesJson.push_back(
                            {
                            {"name", busInf.second.bus().id()},
                            {"final_require_fed", busInf.second.finalRequireFed()},
                            {"has_generation", false},
                            {"P", S.real()},
                            {"Q", S.imag()}
                            });
                }
                if (!busInf.second.hasFault() && hasGeneration(busInf.second.bus()))
                {
                    busesJson.push_back(
                            {
                            {"name", busInf.second.bus().id()},
                            {"final_require_fed", false},
                            {"has_generation", true},
                            {"P", S.real()},
                            {"Q", S.imag()}
                            });
                }
            }

            Json branchesJson = Json::array();
            for (auto& branchInf : solver_->branchInfos())
            {
                if (branchInf.second.hasBreaker())
                {
                    // The PSR client only cares about branches that have a breaker.
                    branchesJson.push_back(
                            {
                            {"name", branchInf.second.branch().id()},
                            {"init_closed", branchInf.second.breakerIsInitClosed()}
                            });
                }
            }

            status = status_codes::OK;
            reply["buses"] = busesJson;
            reply["branches"] = branchesJson;
        }
        else if (paths[1] == "state")
        {
            std::cout << "PSR_SERVER: Put network state." << std::endl; 
            sgtAssert(paths.size() == 2, "PSR_SERVER: bad URL");
            
            auto json = Json::parse(message.extract_string(true).get());
            Json branchClosedStateConstrsJson = json["branch_closed_constraints"];
            Json busFedStateConstrsJson = json["bus_fed_constraints"];

            solver_->reset(); // Needs to happen before modifying state constrs, below.

            for (auto x : busFedStateConstrsJson)
            {
                solver_->busInfo(x[0]).setFedStateConstr(x[1] ? Trivalent::YES : Trivalent::NO);
            }

            for (auto x : branchClosedStateConstrsJson)
            {
                solver_->branchInfo(x[0]).setClosedStateConstr(
                        x[1] ? Trivalent::YES : Trivalent::NO);
            }

            reply = solver_->solve();

            std::cout << "PSR_SERVER: reply = " << reply << std::endl;
            
            status = status_codes::OK;
        }
    }

    std::cout << "--------------------------------------------------------------------------------" << std::endl;

    message.reply(status, reply.dump());
}
