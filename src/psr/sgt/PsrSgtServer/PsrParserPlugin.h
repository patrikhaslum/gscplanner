#ifndef PSR_PARSER_PLUGIN_DOT_H
#define PSR_PARSER_PLUGIN_DOT_H

#include "PsrSolver.h"

#include <SgtCore/Parser.h>

namespace Sgt
{
    class PsrParserPlugin : public ParserPlugin<PsrSolver>
    {
        public:
            virtual ~PsrParserPlugin() = default;

            virtual const char* key() const override
            {
                return "psr";
            }

        public:
            virtual void parse(const YAML::Node& nd, PsrSolver& solver, const ParserBase& parser) const override;
    };

}

#endif // PSR_PARSER_PLUGIN_DOT_H
