
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

*   [Ipopt](https://projects.coin-or.org/Ipopt) or
    [Bonmin](https://www.coin-or.org/download/source/Bonmin/)

    PowerTools depends on Ipopt. Ipopt in turn depends on a number
    of other packages, some of which are alternatives/optional.
    (A minimal set appears to be `HSL` and `metis`.) These can be
    compiled from source, or in some cases installed via a package
    manager.

    Bonmin is a superset of Ipopt (supporting also mixed-integer
    non-linear programming). The MINLP-based AC-PSR solver
    (`minlp_planning`) requires PowerTools to be built with Bonmin
    in order to run.

*   [Gurobi](http://gurobi.com/).

    Although Gurobi is listed as "optional" for PowerTools, the
    PSR-server requires it.

*   [cpprest](https://github.com/Microsoft/cpprestsdk) is used by
    the PSR-server.


## Compiling

Install Gurobi and Ipopt/Bonmin first. Then clone SGT, build and install
the third_party libraries (PowerTools and yaml-cpp) that come with it,
then build and install SGT. Finally, build and install cpprest.

After this is done, the usual

	./configure
	make psr_server

should suffice to build the server. The configure script has options
for customising the Gurobi install location. The config/automake
scripts may require `libtool`.

Other tools provided are:

*   `setup_problem` generates AC-PSR instances from a NESTA network
    file, by calculating the goal state. This is not required (instance
    files are already in the repository), unless you want to generate
    instance files for new networks.

*   `minlp_planning` is the MINLP-based AC-PSR solver.

*   `libpsr` is a dynamic link library plugin for the POPF-TIF planner.
    It is not required to run the PSR-server or the hybrid-planner.
