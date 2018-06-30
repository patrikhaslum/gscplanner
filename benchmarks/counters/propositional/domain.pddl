
;; propositional version of the counters domain

(define (domain counters-propositional)
  (:requirements :strips :typing)
  (:types counter integer)

  (:predicates
   (value ?c - counter ?i - integer) ;; The value of counter ?c is ?i
   (next ?i ?j) ;; ?j = ?i + 1
   (less ?i ?j) ;; ?i < ?j
   (plan) ;; control predicate
   (ok ?c0 - counter ?c1 - counter) ;; value of ?c0 < value of ?c1
   )

  (:functions
   (total-cost)
   )

  (:action increment
   :parameters (?c - counter ?i - integer ?j - integer)
   :precondition (and (plan)
		      (value ?c ?i)
		      (next ?i ?j))
   :effect (and (not (value ?c ?i))
		(value ?c ?j)
		(increase (total-cost) 1)
		)
   )

  (:action decrement
   :parameters (?c - counter ?i - integer ?j - integer)
   :precondition (and (plan)
		      (value ?c ?i)
		      (next ?j ?i))
   :effect (and (not (value ?c ?i))
		(value ?c ?j)
		(increase (total-cost) 1)
		)
   )

  (:action check
   :parameters (?c0 - counter ?c1 - counter ?i0 - integer ?i1 - integer)
   :precondition (and (value ?c0 ?i0)
		      (value ?c1 ?i1)
		      (less ?i0 ?i1))
   :effect (and (not (plan)) ;; now in goal-checking mode
		(ok ?c0 ?c1))
   )

  )
