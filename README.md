
# The Global State Constraints Planner

For a full description of the planner, see "Extending Classical
Planning with State Constraints: Heuristics and Search for Optimal
Planning" (Patrik Haslum, Franc Ivankovic, Miquel Ramirez, Dan Gordon,
Sylvie Thiebaux, Vikas Shivashankar and Dana S. Nau, Journal of AI
Research, vol. 62, pages 373-431, 2018).

## Setup

The planner requries python 2 (probably version 2.7 or later).

The hbw, linehaul and counters domain models need an LP solver; the
h+ heuristic implementation needs a MIP solver. The code is written
to use the python interface of the [Gurobi solver](http://gurobi.com/).
Gurobi is available free for non-commercial use under an academic
licence, but it can be quite complex to obtain and install, and it
does not support all platforms.

If you cannot use Gurobi, there is an option to fake it using
[PuLP](https://pythonhosted.org/PuLP/). PuLP is a python module that
provides a uniform interface to a number of different LP/MIP solvers.
To use this option, copy or rename the file `fake_grb_with_pulp.py`
to `gurobipy.py` (in the present directory) and make sure there is
no other file with that name in python's module-path.

The AC-PSR domain model, which has non-linear constraints, uses a
custom solver that is built on the
[SmartGridToolBox](http://nicta.github.io/SmartGridToolbox/) and
[PowerTools](http://github.com/hhijazi/PowerTools) libraries.
The AC-PSR solver is implemented as a separate server, which the
planner connects to via HTTP. The server code is in subdirectory
`psr/sgt/PsrSgtServer/`. It also includes the plugin module for
the POPF-TIF planner.
Please read the [notes on compiling the PSR server](src/psr/sgt/PsrSgtServer/COMPILE.md). It's complicated.

## Usage

There is a separate main script for each domain model. Details are
given below, but usage is fairly similar: The inputs are a problem
file (format varies with the domain), and optionally a planner
configuration, selected from the following:

*   `blind` : Breadth-first search.
*   `iw_1` or `iw_2` : BFS restricted to novelty 1 or 2.
*   `bfs_f_1` or `bfs_f_2` : Greedy best-first with a novelty-based heuristic.
*   `a_star_h0` : A* with the myopic heuristic (i.e., uniform cost search)
*   `a_star_hmax` : A* with h^max.
*   `a_star_hplus` : A* with h+.
*   `a_star_pdb_haslum_aaai07` : A* with the iPDB heuristic.
*   `ppa_star_hplus` : PrefPEA* with h+.
*   `ppa_star_hplus_r1` : PrefPEA* with h+ using the 1st weaker relaxation.
*   `ppa_star_pdb_trivial` : PrefPEA* with a PDB heuristic constructed from
    a trivial partitioning of the state variables (every variable that is
    mentioned in a primary goal, or in the trigger of a switched constraint
    if the problem has secondary goals, becomes a singleton pattern).
*   `ppa_star_pdb_naive` : PrefPEA* with a PDB heuristic constructed from
    a random partitioning of the primary state variables.
*   `ppa_star_pdb_haslum_aaai07` : PrefPEA* with iPDB.

The default planner configuration if none is specified is PrefPEA*
with h+.  Some of the solvers also have other parameters.

Some of the solvers also implement a plan validation mode. If more
arguments appear after all the optional ones have been filled, the
remaining are assumed to be the names of actions in a plan. In this
mode, no search for a plan is carried out and instead the given plan
is validated.


## Domain models

### hbw3

This is the JAIR version of hydraulic blocksworld.

Usage:

	python hbw3_solver.py <instance file> [config] [volume] [...plan...]

The instance file is in a custom format (file extension `.hbw`). The
instance collection used in experiments can be found in
`benchmarks/hydraulic-blocks-world/`

The `volume` is the volume of fluid in the reservoir (defaults to 10
if not specified). The volume can also be the keyword `unconstrained`,
in which case the secondary constraints are disabled.


### psr/sgt

The AC-PSR domain.

Usage:

	python psr_sgt_solver.py <instance file> [config] [...plan...]

The server that implements the AC-PSR solver (the "PSR-server") must
be running on localhost to run this planner.

The instance file is in YAML format. The instance collection used in
experiments can be found in `src/psr/sgt/PsrSgtServer/data/tests/`.
The instance file references a network model (in matpower format),
which is read by the PSR-server. The instance file can be placed
anywhere, but the path to the network model file that appears in it is
assumed to be relative to the directory that the server runs in.
The networks are drawn from the [NESTA](https://arxiv.org/abs/1411.0359)
collection, but slightly modified for consistency.


### psr/two_end_line

The linear DC version of the PSR domain from the ICAPS 2014 paper.

Usage:

	python psr_solver.py <instance file> [config]

This domain model uses only the LP solver, so it does not need the
PSR-server.

Instance files are in a custom format. The instance collection from
ICAPS 2014 are in `benchmarks/psr/icaps-2014/`.

**Known bug:** For a large number of these problems, the planner
reports that the initial state is invalid. This is probably a bug,
introduced sometime after we stopped using this domain as a test
case.


### linehaul

The Linehaul transportation domain.

Usage:

	python linehaul_solver.py <vrx file> <distance file> [config] [fleet]

The VRX file defines the problem instance. The distance file defines
the distance matrix between locations. Due to unclear copying
conditions, the instances and data used in experiments can not be
included in the repository.

The fleet specification is list of five integers separated by commas
(without spaces), representing the number available of each of the five
different vehicle types.


### counters

The Counters domain.

Usage:

	python counters_solver.py <instance file> [config]

The instance file is an FSTRIPS problem file for the counters domain
by Frances and Geffner. The set of instance files used for the
experiments in the JAIR paper are in `benchmarks/counters/fn-counters`.


### hbw2

The ICAPS 2014 version of hydraulic blocksworld (with recursive weight
summation).

Usage:

	python hbw2_solver.py <instance file> [config]

The instance file format is the same as for the hbw3 domain.

This domain model and driver script is in need of some updating.


## Alternative domain formulations

In addition to domain models and instance files for the global state
constraints planner, the repository contains alternative formulations
of some of the domains, suitable for use with other planners.

*   `benchmarks/counters/propositional` is a propositional (STRIPS)
    encoding of the counters domain and instances.

*   `benchmarks/hbw_numerc` contains the numeric (PDDL2.1) formulation
    of the hydraulic blocksworld domain, and a conversion script that
    will generate PDDL problem files from the instance files in the
    `hydraulic-blocks-world` directory. Note that there is a separate
    domain file for each number of cylinders in the problem (3, 4 or
    5). This is necessary since the numeric subset of PDDL does not
    have a "sum" operator. The domain files use a `:constraint`
    clause, which is an extension implemented by the ENHSP planner.
    To make an equivalent pure PDDL formulation, these constraints
    should be added to the precondition of every action and to the
    goal (as outlined in Section 4 of the paper).

*   `benchmarks/psr/for-popf` contains the domain and problem files for
    use with the POPF-TIF planner and plugin for the AC-PSR domain.


## Revisions

### Corrected PDB Implementation

There was an error in the initial implementation of the PDB heuristic.
It only affects domains with non-unit action costs, which among those
above is only the Linehaul domain. The corrected implementation works
a bit better for the Linehaul domain. As a result, the relevant lines
in Table 1 and Table 3 (Section 7 in the paper) change as follows:

<table border="1">
<tr>
<td>Problems</td>
<td>#</td>
<td>A*/blind</td>
<td>A*/h<sup>max</sup></td>
<td>A*/h<sup>+</sup></td>
<td>A*/PDB</td>
<td>PrefPEA*/h<sup>+</sup></td>
<td>PrefPEA*/PDB</td>
</tr>
<tr>
<td>2R/2A trucks</td><td align="right">6</td>
<td align="right">6</td><td align="right">6</td><td align="right">6</td><td align="right">6</td><td align="right">6</td><td align="right">6</td>
</tr>
<tr>
<td>3R/2A trucks</td><td align="right">19</td>
<td align="right">9</td><td align="right">19</td><td align="right">7</td><td align="right"><strike>9</strike> <b>15</b></td><td align="right">7</td><td align="right"> <strike>12</strike> <b>15</b></td>
</tr>
<tr>
<td>3R/3A trucks</td><td align="right">87</td>
<td align="right">7</td><td align="right">68</td><td align="right">6</td><td align="right"> <strike>7</strike> <b>15</b></td><td align="right">6</td><td align="right"> <strike>7</strike> <b>15</b></td>
</tr>
<tr>
<td>4R/3A trucks</td><td align="right">258</td>
<td align="right">7</td><td align="right">63</td><td align="right">4</td><td align="right"> <strike>7</strike> <b>14</b></td><td align="right">6</td><td align="right"> <strike>7</strike> <b>14</b></td>
</tr>
<tr>
<td>4R/4A trucks</td><td align="right">303</td>
<td align="right">7</td><td align="right">62</td><td align="right">4</td><td align="right">7</td><td align="right">4</td><td align="right">7</td>
</tr>
</table>

This does not substantially change the picture of the relative performance
of the different heuristics, or any of the conclusions of the experiments.
