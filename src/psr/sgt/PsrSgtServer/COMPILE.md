
## Dependencies

*   [SmartGridToolBox](http://nicta.github.io/SmartGridToolbox/)
    ("SGT" for short).

    Dependencies and install instructions for SGT are well documented
    on its github page. The `boost` libraries can be installed through
    a package manager (apt or similar). For the `yaml-cpp` library,
    it's better to build from the source that is packaged with SGT,
    to ensure it is compatible.

*   [PowerTools](http://github.com/hhijazi/PowerTools).

    Although PowerTools is optional for SGT, it is required by the
    PSR-server. A source distribution of PowerTools is provided
    together with SGT, so it's not necessary to download separately.

*   [Ipopt](https://projects.coin-or.org/Ipopt).

    PowerTools depends on Ipopt. Ipopt in turn depends on a number
    of other packages. Some of these are provided (as source) with
    the Ipopt source distribution; they can also be installed
    separately (e.g., via package manager), but the library names
    are different from what Ipopt (and PowerTools) expect.

*   [Gurobi](http://gurobi.com/).

    Although Gurobi is listed as "optional" for PowerTools, the
    PSR-server requires it.

*   [cpprest](https://github.com/Microsoft/cpprestsdk) is used by
    the PSR-server.


## Compiling

Install Gurobi and Ipopt first. Then clone SGT, build and install the
third_party libraries (PowerTools and yaml-cpp) that come with it,
then build and install SGT. Finally, build and install cpprest.

After this is done, the usual

	./configure
	make psr_server

should suffice to build the server. The config/automake scripts may
require `libtool`.

Other tools provided are:

*   `setup_problem` generates AC-PSR instances from a NESTA network
    file, by calculating the goal state. This is not required (instance
    files are already in the repository), unless you want to generate
    instance files for new networks.

*   `minlp_planning` is the MINLP-based AC-PSR solver.

*   `libpsr` is a dynamic link library plugin for the POPF-TIF planner.
    It is not required to run the PSR-server or the hybrid-planner.
