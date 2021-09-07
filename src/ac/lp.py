
# This class implements the "secondary" constraints; it is required
# to have a model, and constraints.
# constraints: a list of (trigger, constr) pairs; trigger is a
# partial valuation over the primary vars (simple condition);
# constr is interpreted only by the model
# model: an object that supports the relevant subset of the
# Gurobi model interface.

import logging
import subprocess
import os
import io

class Axioms(object):

    def __init__(self, task ):
        self.task = task
        self.variables = self.task.derived
        self.constraints = []
        self._negated_axioms = 0
        
        # create a list of primary state literals
        self.literals = []
        for var in self.task.state_vars:
            for val in range(var.domain_size()):
                self.literals.append((var.index, val))
        
        # create a list of derived atoms; since derived vars are binary,
        # each derived atom represents the non-default value of the var
        self.n_primary = len(self.literals)
        self.derived = []
        for i in range(len(self.task.derived)):
            var_name, default_value = self.task.derived[i]
            non_default_value = 1 - default_value
            self.derived.append((i, non_default_value))
        self.n_secondary = len(self.derived)

        ## create a symbol table mapping ASP atoms, without the +2 offset,
        ## to printable names
        self.symbol_table = dict()
        for i in range(len(self.literals)):
            var, val = self.literals[i]
            self.symbol_table[i] = self.task.primary_literal_name[(var, val)]
        for i in range(len(self.derived)):
            var, val = self.derived[i]
            self.symbol_table[self.n_primary + i] = self.task.derived_literal_name[(var, val)]

        # the actual axioms (rules) are not stored as constraints, but
        # we need to map the variables mentioned in the rules to our
        # numbering
        self.rules = []
        for axiom in self.task.sas_task.axioms:
            sa_cond = axiom.condition
            sa_eff = axiom.effect
            sa_eff_var, sa_eff_val = sa_eff
            assert sa_eff_var in self.task.secondary_var_map, "axiom effect " + str(sa_eff) + " on non-derived (" + str(self.task.sas_task.dump()) + ")"
            i = self.task.secondary_var_map[sa_eff_var]
            _, default_value = self.task.derived[i]
            non_default_value = 1 - default_value
            if sa_eff_val == default_value:
                # print("axiom effect " + str(sa_eff) + " sets default value (" + str(axiom.dump()) + ")")
                self._discarded_negated_axioms += 1
                continue
            head = self.n_primary + i
            body_pos = []
            body_neg = []
            for cond in sa_cond:
                c_var, c_val = cond
                if c_var in self.task.primary_var_map:
                    i = self.task.primary_var_map[c_var]
                    assert c_val in self.task.vars[i].domain, "condition " + str(cond) + " with invalid value for " + str(self.task.vars[i]) + " (" + str(self.task.sas_task.dump()) + ")"
                    k = self.literals.index((i, c_val))
                    body_pos.append(k)
                else:
                    assert c_var in self.task.secondary_var_map
                    i = self.task.secondary_var_map[c_var]
                    _, default_value = self.task.derived[i]
                    # condition derived_var == default_value corresponds
                    # to negation of derived atom
                    if c_val == default_value:
                        body_neg.append(self.n_primary + i)
                    else:
                        body_pos.append(self.n_primary + i)
            self.rules.append((head, body_pos, body_neg))
        logging.info('LP: ' + str(self._negated_axioms) + ' negated axioms discarded')
        
        # create constraints for all secondary action preconditions and
        # replace sec_precs in actions with set of constraint indices
        for i in range(len(self.task.actions)):
            if len(self.task.actions[i].sec_precs) > 0:
                sp_conds = list(self.task.actions[i].sec_precs)
                sp_indices = set()
                for cond in sp_conds:
                    self.constraints.append(([], cond))
                    sp_indices.add(len(self.constraints) - 1)
                self.task.actions[i].sec_precs = sp_indices
        
        # create constraints for secondary goals, and store their indices
        # in self.goal_constraints
        self.goal_constraints = set()
        sg_conds = [(self.task.secondary_var_map[var], val)
                    for (var, val) in self.task.sas_task.goal.pairs
                    if var in self.task.secondary_var_map]
        for cond in sg_conds:
            self.constraints.append(([], cond))
            self.goal_constraints.add(len(self.constraints) - 1)
        self.model = AxiomModel(self)

    def copy(self) :
        assert False

    def str_secondary_condition(self, indices, neg = False):
        '''
        indices is an iterable of ints, which represent derived atoms.
        '''
        conds = [ self.constraints[i] for i in indices ]
        return ', '.join([ ("not " if neg else "") + self.task.derived_literal_name[c[1]] for c in conds ])

    def str_rule(self, head, pos_body, neg_body):
        '''
        indices is an iterable of ints, which represent derived atoms.
        '''
        return self.symbol_table[head] + " :- " + \
            ', '.join([self.symbol_table[x] for x in pos_body]) + ", " + \
            ', '.join(["not " + self.symbol_table[x] for x in neg_body])

# Model class should obey certain elements of the Gurobi Model interface.
# It should have the following:
#     status (1 = loaded (but not solved, 2 = optimal, 3+ = bad...
#     copy(self)
#     reset(self) -> Set status to 1, reset any variables necessary
#     remove(self, constraint)
#     getConstrs(self) -> list of constraints
#     getVars(self) -> list of variables 
#     numvars(self) -> number of variables 
#     update(self)
#     optimize(self) -> Optimize the problem, setting any variables
#         as necessary

class AxiomModel:

    CLASP = os.path.join(os.environ['HOME'], 'pkg/ASP/clasp-3.3.6/build/bin/clasp')
    _check_count = 0

    def __init__(self, LP ):
        self.myLP = LP
        self.status = 1
        self.active = [True for i in range(len(self.myLP.constraints))]

    # Needed to imitate the Gurobi interface.
    def copy(self):
        result = AxiomModel( self.myLP )
        result.active = self.active[:]
        return result

    # Needed to imitate the Gurobi interface.
    def reset(self):
        logging.debug("AxiomModel: reset")
        self.status = 1
        self.active = [True for i in range(len(self.myLP.constraints))]

    # Needed to imitate the Gurobi interface.
    def getConstrs(self):
        return range(len(self.myLP.constraints))

    # Needed to imitate the Gurobi interface.
    # constraint: an object of the element type of list returned by getConstrs.
    def remove(self, constraint):
        logging.debug("AxiomModel: remove " + str(constraint) + " : " + str(self.myLP.constraints[constraint]))
        assert 0 <= constraint < len(self.myLP.constraints)
        self.active[constraint] = False

    # Needed to imitate the Gurobi interface.
    def getVars(self):
        return []

    @property
    def numvars(self):
        return 0

    # Needed to imitate the Gurobi interface.
    # Validate/update the model after having made changes.
    def update(self):
        return

    # The ASP checker supports only the strong relaxation, so optimize
    # will be called with an additional argument that is the current
    # primary state.
    def optimize(self, ps):
        logging.debug("AxiomModel: active = " + str(self.active) + ", ps = " + str(ps.get_valuation()))
        # Collect the active requiremens:
        reqs = []
        for i in range(len(self.myLP.constraints)):
            if self.active[i]:
                t, c = self.myLP.constraints[i]
                var, val = c
                reqs.append(c)
        ## shortcut: if requirements are empty, the model is always satisfiable
        if len(reqs) == 0:
            self.status = 2
            return
        # map requriements to atoms
        req_pos = []
        req_neg = []
        for var, val in reqs:
            _, default_val = self.myLP.task.derived[var]
            non_default_val = 1 - default_val
            p = self.myLP.n_primary + self.myLP.derived.index((var, non_default_val))
            if val == default_val:
                req_neg.append(p)
            else:
                req_pos.append(p)
        # Collect active literals from the primary state
        lits = dict()
        for (var, val) in ps.get_valuation():
            lits[var] = lits.get(var, []) + [val]
        # map literals to choice atom sets
        facts = []
        for var, vals in lits.items():
            choice = []
            for val in vals:
                i = self.myLP.literals.index((var, val))
                choice.append(i)
            facts.append(choice)
        # print("### optimize ###")
        # print("lits = " + str(lits) + " -> " + str(facts))
        # print("reqs = " + str(reqs) + " -> +" + str(req_pos) + " -" + str(req_neg))
        # print("atom mapping:")
        # for i in range(len(self.myLP.literals)):
        #     var, val = self.myLP.literals[i]
        #     print(" (primary) " + str(i) + ": " + self.myLP.task.primary_literal_name[(var, val)])
        # for i in range(len(self.myLP.derived)):
        #     var, val = self.myLP.derived[i]
        #     print(" (derived) " + str(self.myLP.n_primary + i) + ": " + self.myLP.task.derived_literal_name[(var, val)])
        # print("rules:")
        # for rule in self.myLP.rules:
        #     print(" " + str(rule))
        # print("################")
        #fname = "_check" + str(AxiomModel._check_count) + ".lp"
        asp = self.write_answer_set_program(None, facts, self.myLP.rules, req_pos, req_neg)
        ## increment counter to keep all lp files
        #AxiomModel._check_count += 1
        #is_sat = self.check_ASP(filename=fname)
        is_sat = self.check_ASP(text_in=asp)
        if is_sat is None:
            logging.error('Failed to solve ASP: ' + asp)
            assert is_sat is not None
        if is_sat:
            self.status = 2
        else:
            self.status = 3

    def write_answer_set_program(self, filename, facts, rules, pos_reqs, neg_reqs):
        if filename is not None:
            fout = open(filename, 'w')
        else:
            fout = io.StringIO('')
        # part 1: rules (excluding atomic constraints)
        for fact in facts:
            self.write_choice_rule(fout, fact)
        for rule in rules:
            head, pos_body, neg_body = rule
            self.write_basic_rule(fout, head, neg_body, pos_body)
        print(0, file=fout) # end of rules section
        # part 2: symbol table - can skip?
        for i in range(len(self.myLP.literals)):
            var, val = self.myLP.literals[i]
            print(str(i + 2) + " " + self.myLP.task.primary_literal_name[(var, val)].replace(' ', '_'), file=fout)
        for i in range(len(self.myLP.derived)):
            var, val = self.myLP.derived[i]
            print(str(self.myLP.n_primary + i + 2) + " " + self.myLP.task.derived_literal_name[(var, val)].replace(' ', '_'), file=fout)
        print(0, file=fout) # end of symbol table section
        # part 3(i): positive atomic requirements
        print("B+", file=fout)
        for atom in pos_reqs:
            print(atom + 2, file=fout)
        print(0, file=fout) # end of positive atomic requirements
        # part 3(ii): positive atomic requirements
        print("B-", file=fout)
        for atom in neg_reqs:
            print(atom + 2, file=fout)
        print(0, file=fout) # end of negative atomic requirements
        # part 4: number of models
        print(1, file=fout)
        if filename is None:
            result = fout.getvalue()
        else:
            result = filename
        fout.close()
        return result

    def write_choice_rule(self, fto, atoms):
        ## great... clasp doesn't support choice rules. We have to
        ## emulate them using some other mechanism.
        # if there's just one atom, we can make it a basic rule:
        if len(atoms) == 1:
            print(1, atoms[0] + 2, 0, 0, file=fto)
        # otherwise, we can write a | b | c as a :- not b, not c,
        # b :- not a, not c, c :- not a, not b
        else:
            for atom in atoms:
                print(1, atom + 2, len(atoms) - 1, len(atoms) - 1, end=' ', file=fto)
                for other_atom in atoms:
                    if other_atom != atom:
                        print(other_atom + 2, end=' ', file=fto)
            print(file=fto)

    def write_basic_rule(self, fto, head, neg_body, pos_body):
        print(1, head + 2, len(neg_body) + len(pos_body), len(neg_body), end=' ', file=fto)
        for atom in neg_body + pos_body:
            print(atom + 2, end=' ', file=fto)
        print(file=fto)

    def check_ASP(self, filename=None, text_in=None):
        assert filename is not None or text_in is not None
        try:
            if filename is not None:
                logging.debug( 'calling ' + AxiomModel.CLASP + ' ' + filename + ' ...' )
                result = subprocess.run([AxiomModel.CLASP, filename], capture_output = True, text = True, timeout = None)
            else:
                logging.debug( 'calling ' + AxiomModel.CLASP + ' ...' )
                result = subprocess.run([AxiomModel.CLASP], input=text_in, capture_output = True, text = True, timeout = None)
        except subprocess.TimeoutExpired as tx:
            logging.error( 'Call ' + AxiomModel.CLASP + ' ' + filename + ' timed out' )
            return None
        except subprocess.CalledProcessError as cpe:
            logging.error( 'Call ' + AxiomModel.CLASP + ' ' + filename + ' caused error ' + str(cpe) )
            return None
        for line in result.stdout.split('\n'):
            if line == 'SATISFIABLE':
                return True
            elif line == 'UNSATISFIABLE':
                return False
        logging.error( 'Call ' + AxiomModel.CLASP + ' ' + filename + ' generated ambiguous output ' + str(result.stdout) )
        return None
        
    # Needed to imitate the Gurobi interface.
    def printStats(self):
        return

